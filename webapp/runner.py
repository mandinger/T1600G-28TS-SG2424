from __future__ import annotations

import base64
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .actions import ActionDefinition
from .config import get_settings
from .profile_builder import merged_profile, write_profile_files
from .switch_env_overrides import switch_env_values_for_runner


@dataclass
class ExecutionContext:
    command: list[str]
    env: dict[str, str]
    log_path: Path
    bot_password_output: Path


def _b64_json(value: dict[str, Any]) -> str:
    return base64.b64encode(json.dumps(value).encode("utf-8")).decode("ascii")


def build_execution_context(
    action: ActionDefinition,
    job_id: int,
    switch: Any,
    profile_data: dict[str, Any],
    input_payload: dict[str, Any],
    admin_password: str,
    bot_password: str,
) -> ExecutionContext:
    settings = get_settings()
    profile = merged_profile(profile_data)

    runtime_dir = settings.data_dir / "runtime" / f"job-{job_id}"
    profile_dir = runtime_dir / "profile"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    profile_dir.mkdir(parents=True, exist_ok=True)

    vlan_dir, lacp_dir = write_profile_files(profile_dir, profile)

    backup_dir = settings.data_dir / "backup" / f"switch-{switch.id}"
    firmware_dir = settings.data_dir / "firmware"
    tftp_dir = settings.data_dir / "tftp"
    cert_dir = settings.data_dir / "certificates" / f"switch-{switch.id}"
    ssh_dir = settings.data_dir / "ssh" / f"switch-{switch.id}"
    jobs_dir = settings.data_dir / "jobs"

    for path in (backup_dir, firmware_dir, tftp_dir, cert_dir, ssh_dir, jobs_dir):
        path.mkdir(parents=True, exist_ok=True)

    log_path = jobs_dir / f"job-{job_id}.log"
    bot_password_output = runtime_dir / "bot_password.txt"

    env = os.environ.copy()
    env.update(
        {
            "ACTION_FUNCTION": action.function_name,
            "ACTION_KEY": action.key,
            "ACTION_INPUT_B64": _b64_json(input_payload),
            "RUNNER_BOT_PASSWORD_FILE": str(bot_password_output),
            "DEVICE_IP": switch.device_ip,
            "DEVICE_NAME": switch.device_name,
            "DEVICE_LOCATION": switch.device_location,
            "DEVICE_CONTACT_INFO": switch.device_contact_info,
            "USER_ADMIN": switch.admin_username,
            "USER_BOT": switch.bot_username,
            "USER_BOT_PRIVILEGE": switch.bot_privilege,
            "APP_ADMIN_PASSWORD": admin_password,
            "APP_BOT_PASSWORD": bot_password,
            "SSH_PUBLIC_KEY_PATH": f"{ssh_dir}/",
            "BACKUP_PATH": f"{backup_dir}/",
            "FIRMWARE_PATH": f"{firmware_dir}/",
            "TFTP_DIRECTORY": f"{tftp_dir}/",
            "HTTPS_FILES_PATH": f"{cert_dir}/",
            "VLAN_PATH_OF_VARIABLES": str(vlan_dir),
            "VLAN_PATH_OF_VARIABLES_WITH_FILTER": str(vlan_dir / "*.sh"),
            "LACP_PATH_OF_GROUPS_VARIABLES": str(lacp_dir / "*.sh"),
            "RUNNER_TFTP_IP": switch.tftp_source_ip or settings.tftp_ip,
        }
    )

    # Apply per-switch environment values stored directly on switch entity.
    env.update(switch_env_values_for_runner(switch))

    command = [str(settings.repo_root / "scripts" / "run_switch_action.sh")]
    return ExecutionContext(command=command, env=env, log_path=log_path, bot_password_output=bot_password_output)
