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
            "TIME_ZONE": str(profile.get("time_zone", "UTC-03:00")),
            "PRIMARY_NTP_SERVER": str(profile.get("primary_ntp_server", "")),
            "SECONDARY_NTP_SERVER": str(profile.get("secondary_ntp_server", "")),
            "NTP_UPDATE_RATE": str(profile.get("ntp_update_rate", "12")),
            "IP_REMOTE_LOGGING_SERVER": str(profile.get("ip_remote_logging_server", "")),
            "LOG_LEVEL": str(profile.get("log_level", 6)),
            "SIZE_OF_JUMBO_FRAME": str(profile.get("size_of_jumbo_frame", 9216)),
            "SDM_PREFERENCE": str(profile.get("sdm_preference", "enterpriseV4")),
            "EEE_INTERFACES": str(profile.get("eee_interfaces", "")),
            "EEE_LACPS": str(profile.get("eee_lacps", "")),
            "LACP_LOAD_BALANCE": str(profile.get("lacp_load_balance", "src-dst-mac")),
            "STATIC_ROUTE_DESTINATION_IP": str(profile.get("static_route_destination_ip", "0.0.0.0")),
            "STATIC_ROUTE_SUBNET_MASK": str(profile.get("static_route_subnet_mask", "0.0.0.0")),
            "STATIC_ROUTE_DEFAULT_GATEWAY_IP": str(profile.get("static_route_default_gateway_ip", "")),
            "STATIC_ROUTE_DEFAULT_GATEWAY_DISTANCE": str(profile.get("static_route_default_gateway_distance", 1)),
            "FIRMWARE_FILE_NAME": str(profile.get("firmware_file_name", "T1600G-28TS-V3-20200805")),
            "FIRMWARE_URL": str(profile.get("firmware_url", "")),
            "HTTPS_CERTIFICATE": str(profile.get("https_certificate", "switch.lan.homelab.crt")),
            "HTTPS_CERTIFICATE_KEY": str(profile.get("https_certificate_key", "switch.lan.homelab.key")),
            "RUNNER_TFTP_IP": switch.tftp_source_ip or get_settings().tftp_ip,
        }
    )

    command = [str(settings.repo_root / "scripts" / "run_switch_action.sh")]
    return ExecutionContext(command=command, env=env, log_path=log_path, bot_password_output=bot_password_output)
