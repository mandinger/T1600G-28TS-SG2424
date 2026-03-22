from __future__ import annotations

import json
import subprocess
import threading
from datetime import datetime, timezone

from sqlalchemy import and_
from sqlalchemy.orm import Session

from .actions import ActionDefinition
from .config import get_settings
from .database import SessionLocal
from .models import EncryptedCredential, Job, JobEvent, Switch, User
from .runner import build_execution_context
from .security import decrypt_secret, encrypt_secret

_switch_lock_guard = threading.Lock()
_switch_locks: dict[int, threading.Lock] = {}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def get_switch_lock(switch_id: int) -> threading.Lock:
    with _switch_lock_guard:
        lock = _switch_locks.get(switch_id)
        if lock is None:
            lock = threading.Lock()
            _switch_locks[switch_id] = lock
        return lock


def append_event(db: Session, job_id: int, message: str, level: str = "info") -> None:
    db.add(JobEvent(job_id=job_id, level=level, message=message))
    db.commit()


def switch_has_active_job(db: Session, switch_id: int) -> bool:
    return (
        db.query(Job)
        .filter(and_(Job.switch_id == switch_id, Job.status.in_(["pending", "running"])))
        .first()
        is not None
    )


def enqueue_job(db: Session, switch: Switch, user: User, action: ActionDefinition, payload: dict) -> Job:
    if switch_has_active_job(db, switch.id):
        raise ValueError("A job is already running for this switch.")

    job = Job(
        switch_id=switch.id,
        created_by_user_id=user.id,
        action_key=action.key,
        input_payload_json=json.dumps(payload),
        status="pending",
        created_at=_utcnow(),
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    thread = threading.Thread(target=execute_job, args=(job.id, action), daemon=True)
    thread.start()

    return job


def execute_job(job_id: int, action: ActionDefinition) -> None:
    db = SessionLocal()
    switch_lock: threading.Lock | None = None

    try:
        job = db.get(Job, job_id)
        if not job:
            return

        switch = db.get(Switch, job.switch_id)
        if not switch:
            job.status = "failed"
            job.error_message = "Switch not found"
            job.finished_at = _utcnow()
            db.commit()
            return

        switch_lock = get_switch_lock(switch.id)
        switch_lock.acquire()

        job.status = "running"
        job.started_at = _utcnow()
        db.commit()
        append_event(db, job.id, f"Starting action '{action.key}'.")

        credentials = switch.credentials
        if credentials is None:
            credentials = EncryptedCredential(switch_id=switch.id, admin_password_enc="", bot_password_enc="")
            db.add(credentials)
            db.commit()

        profile = switch.profile
        profile_data = {}
        if profile:
            try:
                profile_data = json.loads(profile.profile_json)
            except json.JSONDecodeError:
                profile_data = {}

        payload = json.loads(job.input_payload_json)
        admin_password = decrypt_secret(credentials.admin_password_enc)
        bot_password = decrypt_secret(credentials.bot_password_enc)

        context = build_execution_context(
            action=action,
            job_id=job.id,
            switch=switch,
            profile_data=profile_data,
            input_payload=payload,
            admin_password=admin_password,
            bot_password=bot_password,
        )

        job.log_path = str(context.log_path)
        db.commit()

        with context.log_path.open("w", encoding="utf-8") as log_file:
            process = subprocess.Popen(
                context.command,
                cwd=str(get_settings().repo_root),
                env=context.env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )

            assert process.stdout is not None
            for line in process.stdout:
                text = line.rstrip("\n")
                log_file.write(line)
                log_file.flush()
                append_event(db, job.id, text)

            exit_code = process.wait()

        if context.bot_password_output.exists():
            new_bot_password = context.bot_password_output.read_text(encoding="utf-8").strip()
            if new_bot_password:
                credentials.bot_password_enc = encrypt_secret(new_bot_password)
                db.commit()
                append_event(db, job.id, "Bot password rotated and stored in encrypted credentials.")

        job.exit_code = exit_code
        job.finished_at = _utcnow()
        if exit_code == 0:
            job.status = "succeeded"
            job.error_message = ""
            append_event(db, job.id, "Action completed successfully.")
        else:
            job.status = "failed"
            job.error_message = f"Script exited with code {exit_code}."
            append_event(db, job.id, job.error_message, level="error")
        db.commit()

    except Exception as exc:
        job = db.get(Job, job_id)
        if job:
            job.status = "failed"
            job.finished_at = _utcnow()
            job.error_message = str(exc)
            db.commit()
            append_event(db, job.id, f"Unhandled execution error: {exc}", level="error")
    finally:
        if switch_lock and switch_lock.locked():
            switch_lock.release()
        db.close()
