from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from .actions import get_action, list_actions
from .config import get_settings
from .database import Base, SessionLocal, engine
from .deps import get_db, require_role
from .jobs import enqueue_job, switch_has_active_job
from .models import EncryptedCredential, Job, Role, Switch, SwitchProfile, User
from .profile_builder import default_profile, merged_profile
from .schemas import (
    ActionExecutionRequest,
    JobResponse,
    LoginRequest,
    LoginResponse,
    ProfileResponse,
    ProfileUpdateRequest,
    SwitchCreateRequest,
    SwitchResponse,
    SwitchUpdateRequest,
)
from .security import create_session, delete_session, encrypt_secret, hash_password, verify_password

app = FastAPI(title="Switch Control Plane", version="1.0.0")
settings = get_settings()

templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent / "templates"))
app.mount("/static", StaticFiles(directory=str(Path(__file__).resolve().parent / "static")), name="static")


ROLE_NAMES = ("viewer", "operator", "admin")


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _read_token_from_request(request: Request) -> str | None:
    auth = request.headers.get("Authorization", "")
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    cookie_token = request.cookies.get("session_token")
    if cookie_token:
        return cookie_token
    return None


def _switch_to_schema(switch: Switch) -> SwitchResponse:
    return SwitchResponse(
        id=switch.id,
        name=switch.name,
        device_ip=switch.device_ip,
        model=switch.model,
        device_name=switch.device_name,
        device_location=switch.device_location,
        device_contact_info=switch.device_contact_info,
        admin_username=switch.admin_username,
        bot_username=switch.bot_username,
        bot_privilege=switch.bot_privilege,
        tftp_source_ip=switch.tftp_source_ip,
        created_at=switch.created_at,
        updated_at=switch.updated_at,
    )


def _job_to_schema(job: Job) -> JobResponse:
    return JobResponse(
        id=job.id,
        switch_id=job.switch_id,
        created_by_user_id=job.created_by_user_id,
        action_key=job.action_key,
        status=job.status,
        exit_code=job.exit_code,
        error_message=job.error_message,
        created_at=job.created_at,
        started_at=job.started_at,
        finished_at=job.finished_at,
    )


def _ensure_bootstrap() -> None:
    Base.metadata.create_all(bind=engine)
    settings.data_dir.mkdir(parents=True, exist_ok=True)

    db = SessionLocal()
    try:
        for role_name in ROLE_NAMES:
            role = db.query(Role).filter(Role.name == role_name).first()
            if not role:
                db.add(Role(name=role_name))
        db.commit()

        admin = db.query(User).filter(User.username == settings.bootstrap_admin_username).first()
        if not admin:
            admin_role = db.query(Role).filter(Role.name == "admin").first()
            if not admin_role:
                raise RuntimeError("Admin role missing during bootstrap")

            db.add(
                User(
                    username=settings.bootstrap_admin_username,
                    password_hash=hash_password(settings.bootstrap_admin_password),
                    role_id=admin_role.id,
                    is_active=True,
                )
            )
            db.commit()
    finally:
        db.close()


@app.on_event("startup")
def on_startup() -> None:
    _ensure_bootstrap()


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/auth/login", response_model=LoginResponse)
def api_login(payload: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    user = db.query(User).filter(User.username == payload.username).first()
    if not user or not user.is_active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_session(db, user.id)
    role_name = user.role.name if user.role else "viewer"
    return LoginResponse(access_token=token, role=role_name)


@app.post("/api/auth/logout")
def api_logout(request: Request, db: Session = Depends(get_db), _: User = Depends(require_role("viewer"))) -> dict[str, str]:
    token = _read_token_from_request(request)
    if token:
        delete_session(db, token)
    return {"status": "ok"}


@app.get("/api/switches", response_model=list[SwitchResponse])
def api_list_switches(_: User = Depends(require_role("viewer")), db: Session = Depends(get_db)) -> list[SwitchResponse]:
    switches = db.query(Switch).order_by(Switch.name.asc()).all()
    return [_switch_to_schema(item) for item in switches]


@app.post("/api/switches", response_model=SwitchResponse)
def api_create_switch(
    payload: SwitchCreateRequest,
    _: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
) -> SwitchResponse:
    existing = db.query(Switch).filter(Switch.name == payload.name).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Switch name already exists")

    now = utcnow()
    switch = Switch(
        name=payload.name,
        device_ip=payload.device_ip,
        model=payload.model,
        device_name=payload.device_name,
        device_location=payload.device_location,
        device_contact_info=payload.device_contact_info,
        admin_username=payload.admin_username,
        bot_username=payload.bot_username,
        bot_privilege=payload.bot_privilege,
        tftp_source_ip=payload.tftp_source_ip,
        created_at=now,
        updated_at=now,
    )
    db.add(switch)
    db.commit()
    db.refresh(switch)

    credentials = EncryptedCredential(
        switch_id=switch.id,
        admin_password_enc=encrypt_secret(payload.admin_password),
        bot_password_enc=encrypt_secret(payload.bot_password),
    )
    profile = SwitchProfile(switch_id=switch.id, profile_json=json.dumps(default_profile()))
    db.add(credentials)
    db.add(profile)
    db.commit()
    db.refresh(switch)

    return _switch_to_schema(switch)


@app.get("/api/switches/{switch_id}", response_model=SwitchResponse)
def api_get_switch(switch_id: int, _: User = Depends(require_role("viewer")), db: Session = Depends(get_db)) -> SwitchResponse:
    switch = db.get(Switch, switch_id)
    if not switch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Switch not found")
    return _switch_to_schema(switch)


@app.patch("/api/switches/{switch_id}", response_model=SwitchResponse)
def api_update_switch(
    switch_id: int,
    payload: SwitchUpdateRequest,
    _: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
) -> SwitchResponse:
    switch = db.get(Switch, switch_id)
    if not switch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Switch not found")

    data = payload.model_dump(exclude_unset=True)
    for field in (
        "name",
        "device_ip",
        "model",
        "device_name",
        "device_location",
        "device_contact_info",
        "admin_username",
        "bot_username",
        "bot_privilege",
        "tftp_source_ip",
    ):
        if field in data and data[field] is not None:
            setattr(switch, field, data[field])

    switch.updated_at = utcnow()

    credentials = switch.credentials
    if credentials is None:
        credentials = EncryptedCredential(switch_id=switch.id, admin_password_enc="", bot_password_enc="")
        db.add(credentials)

    if payload.admin_password is not None:
        credentials.admin_password_enc = encrypt_secret(payload.admin_password)
    if payload.bot_password is not None:
        credentials.bot_password_enc = encrypt_secret(payload.bot_password)

    db.commit()
    db.refresh(switch)
    return _switch_to_schema(switch)


@app.delete("/api/switches/{switch_id}")
def api_delete_switch(switch_id: int, _: User = Depends(require_role("admin")), db: Session = Depends(get_db)) -> dict[str, str]:
    switch = db.get(Switch, switch_id)
    if not switch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Switch not found")

    db.delete(switch)
    db.commit()
    return {"status": "deleted"}


@app.get("/api/switches/{switch_id}/profile", response_model=ProfileResponse)
def api_get_profile(switch_id: int, _: User = Depends(require_role("viewer")), db: Session = Depends(get_db)) -> ProfileResponse:
    profile = db.query(SwitchProfile).filter(SwitchProfile.switch_id == switch_id).first()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Switch profile not found")

    try:
        profile_json = json.loads(profile.profile_json)
    except json.JSONDecodeError:
        profile_json = default_profile()

    return ProfileResponse(switch_id=switch_id, profile=profile_json, updated_at=profile.updated_at)


@app.put("/api/switches/{switch_id}/profile", response_model=ProfileResponse)
def api_put_profile(
    switch_id: int,
    payload: ProfileUpdateRequest,
    _: User = Depends(require_role("operator")),
    db: Session = Depends(get_db),
) -> ProfileResponse:
    switch = db.get(Switch, switch_id)
    if not switch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Switch not found")

    profile = db.query(SwitchProfile).filter(SwitchProfile.switch_id == switch_id).first()
    normalized = merged_profile(payload.profile)
    if not profile:
        profile = SwitchProfile(switch_id=switch_id, profile_json=json.dumps(normalized))
        db.add(profile)
    else:
        profile.profile_json = json.dumps(normalized)
        profile.updated_at = utcnow()
    db.commit()
    db.refresh(profile)

    return ProfileResponse(switch_id=switch_id, profile=normalized, updated_at=profile.updated_at)


@app.get("/api/actions")
def api_actions(_: User = Depends(require_role("viewer"))) -> dict[str, Any]:
    return {"actions": list_actions()}


@app.post("/api/switches/{switch_id}/actions/{action_key}", response_model=JobResponse)
def api_run_action(
    switch_id: int,
    action_key: str,
    payload: ActionExecutionRequest,
    current_user: User = Depends(require_role("operator")),
    db: Session = Depends(get_db),
) -> JobResponse:
    switch = db.get(Switch, switch_id)
    if not switch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Switch not found")

    action = get_action(action_key)
    if not action:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Action not found")

    if not action.enabled:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Action is disabled in v1 safety policy")

    input_payload = payload.input or {}
    missing = [field for field in action.required_inputs if not str(input_payload.get(field, "")).strip()]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Missing required input fields: {', '.join(missing)}",
        )

    try:
        job = enqueue_job(db, switch=switch, user=current_user, action=action, payload=input_payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return _job_to_schema(job)


@app.get("/api/jobs")
def api_list_jobs(_: User = Depends(require_role("viewer")), db: Session = Depends(get_db)) -> dict[str, Any]:
    jobs = db.query(Job).order_by(Job.created_at.desc()).all()
    return {"jobs": [_job_to_schema(job).model_dump() for job in jobs]}


@app.get("/api/jobs/{job_id}", response_model=JobResponse)
def api_get_job(job_id: int, _: User = Depends(require_role("viewer")), db: Session = Depends(get_db)) -> JobResponse:
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return _job_to_schema(job)


@app.get("/api/jobs/{job_id}/logs")
def api_get_job_logs(job_id: int, _: User = Depends(require_role("viewer")), db: Session = Depends(get_db)) -> PlainTextResponse:
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    if not job.log_path:
        return PlainTextResponse("", status_code=status.HTTP_200_OK)

    path = Path(job.log_path)
    if not path.exists():
        return PlainTextResponse("", status_code=status.HTTP_200_OK)

    return PlainTextResponse(path.read_text(encoding="utf-8"), status_code=status.HTTP_200_OK)


# UI routes
@app.get("/")
def root() -> RedirectResponse:
    return RedirectResponse(url="/ui", status_code=status.HTTP_302_FOUND)


@app.get("/ui/login", response_class=HTMLResponse)
def ui_login_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("login.html", {"request": request, "error": ""})


@app.post("/ui/login")
def ui_login_submit(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)) -> HTMLResponse:
    user = db.query(User).filter(User.username == username).first()
    if not user or not user.is_active or not verify_password(password, user.password_hash):
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"}, status_code=401)

    token = create_session(db, user.id)
    response = RedirectResponse(url="/ui", status_code=status.HTTP_302_FOUND)
    response.set_cookie("session_token", token, httponly=True, samesite="lax")
    return response


@app.post("/ui/logout")
def ui_logout(request: Request, db: Session = Depends(get_db), _: User = Depends(require_role("viewer"))) -> RedirectResponse:
    token = _read_token_from_request(request)
    if token:
        delete_session(db, token)

    response = RedirectResponse(url="/ui/login", status_code=status.HTTP_302_FOUND)
    response.delete_cookie("session_token")
    return response


def _ui_context(db: Session, current_user: User) -> dict[str, Any]:
    switches = db.query(Switch).order_by(Switch.name.asc()).all()
    jobs = db.query(Job).order_by(Job.created_at.desc()).limit(30).all()
    return {
        "user": current_user,
        "switches": switches,
        "jobs": jobs,
        "actions": list_actions(),
    }


@app.get("/ui", response_class=HTMLResponse)
def ui_dashboard(request: Request, current_user: User = Depends(require_role("viewer")), db: Session = Depends(get_db)) -> HTMLResponse:
    context = _ui_context(db, current_user)
    context.update({"request": request})
    return templates.TemplateResponse("dashboard.html", context)


@app.get("/ui/switches/{switch_id}", response_class=HTMLResponse)
def ui_switch_detail(
    switch_id: int,
    request: Request,
    current_user: User = Depends(require_role("viewer")),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    switch = db.get(Switch, switch_id)
    if not switch:
        raise HTTPException(status_code=404, detail="Switch not found")

    profile = db.query(SwitchProfile).filter(SwitchProfile.switch_id == switch_id).first()
    try:
        profile_payload = json.loads(profile.profile_json) if profile else {}
    except json.JSONDecodeError:
        profile_payload = {}
    profile_json = merged_profile(profile_payload)

    jobs = db.query(Job).filter(Job.switch_id == switch_id).order_by(Job.created_at.desc()).limit(20).all()

    return templates.TemplateResponse(
        "switch_detail.html",
        {
            "request": request,
            "user": current_user,
            "switch": switch,
            "profile_json": json.dumps(profile_json, indent=2),
            "actions": list_actions(),
            "jobs": jobs,
            "has_active_job": switch_has_active_job(db, switch_id),
        },
    )


@app.post("/ui/switches/new")
def ui_create_switch(
    name: str = Form(...),
    device_ip: str = Form(...),
    admin_password: str = Form(default=""),
    bot_password: str = Form(default=""),
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    payload = SwitchCreateRequest(name=name, device_ip=device_ip, admin_password=admin_password, bot_password=bot_password)
    api_create_switch(payload, current_user, db)
    return RedirectResponse(url="/ui", status_code=status.HTTP_302_FOUND)


@app.post("/ui/switches/{switch_id}/update")
def ui_update_switch(
    switch_id: int,
    name: str = Form(...),
    device_ip: str = Form(...),
    model: str = Form(default="T1600G-28TS"),
    device_name: str = Form(default="T1600G-28TS"),
    device_location: str = Form(default=""),
    device_contact_info: str = Form(default=""),
    admin_username: str = Form(default="admin"),
    admin_password: str = Form(default=""),
    bot_username: str = Form(default="switch-user-bot"),
    bot_privilege: str = Form(default="admin"),
    bot_password: str = Form(default=""),
    tftp_source_ip: str = Form(default=""),
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    payload = SwitchUpdateRequest(
        name=name,
        device_ip=device_ip,
        model=model,
        device_name=device_name,
        device_location=device_location,
        device_contact_info=device_contact_info,
        admin_username=admin_username,
        admin_password=admin_password if admin_password else None,
        bot_username=bot_username,
        bot_privilege=bot_privilege,
        bot_password=bot_password if bot_password else None,
        tftp_source_ip=tftp_source_ip,
    )
    api_update_switch(switch_id, payload, current_user, db)
    return RedirectResponse(url=f"/ui/switches/{switch_id}", status_code=status.HTTP_302_FOUND)


@app.post("/ui/switches/{switch_id}/delete")
def ui_delete_switch(
    switch_id: int,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    api_delete_switch(switch_id, current_user, db)
    return RedirectResponse(url="/ui", status_code=status.HTTP_302_FOUND)


@app.post("/ui/switches/{switch_id}/profile")
def ui_update_profile(
    switch_id: int,
    profile_json: str = Form(...),
    current_user: User = Depends(require_role("operator")),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    try:
        profile_data = json.loads(profile_json)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=422, detail=f"Invalid profile JSON: {exc}") from exc

    payload = ProfileUpdateRequest(profile=profile_data)
    api_put_profile(switch_id, payload, current_user, db)
    return RedirectResponse(url=f"/ui/switches/{switch_id}", status_code=status.HTTP_302_FOUND)


@app.post("/ui/switches/{switch_id}/actions/{action_key}")
def ui_run_action(
    switch_id: int,
    action_key: str,
    current_ip: str = Form(default=""),
    current_user: User = Depends(require_role("operator")),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    payload: dict[str, Any] = {}
    if current_ip.strip():
        payload["current_ip"] = current_ip.strip()

    api_run_action(
        switch_id=switch_id,
        action_key=action_key,
        payload=ActionExecutionRequest(input=payload),
        current_user=current_user,
        db=db,
    )
    return RedirectResponse(url=f"/ui/switches/{switch_id}", status_code=status.HTTP_302_FOUND)


@app.get("/ui/jobs/{job_id}", response_class=HTMLResponse)
def ui_job_detail(
    job_id: int,
    request: Request,
    current_user: User = Depends(require_role("viewer")),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    log_text = ""
    if job.log_path:
        path = Path(job.log_path)
        if path.exists():
            log_text = path.read_text(encoding="utf-8")

    return templates.TemplateResponse(
        "job_detail.html",
        {
            "request": request,
            "user": current_user,
            "job": job,
            "log_text": log_text,
        },
    )


@app.exception_handler(HTTPException)
def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    if request.url.path.startswith("/api"):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    if exc.status_code in (401, 403):
        return RedirectResponse(url="/ui/login", status_code=status.HTTP_302_FOUND)

    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
