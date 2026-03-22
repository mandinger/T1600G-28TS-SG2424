from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Any


@dataclass(frozen=True)
class SwitchEnvField:
    attr_name: str
    env_name: str
    default_value: str
    label: str


def _env_default(env_name: str, fallback: str) -> str:
    value = os.getenv(env_name, "").strip()
    return value if value else fallback


SWITCH_ENV_FIELDS: tuple[SwitchEnvField, ...] = (
    SwitchEnvField("ssh_version", "SSH_VERSION", _env_default("SSH_VERSION", "v2"), "SSH Version"),
    SwitchEnvField("password_length", "PASSWORD_LENGTH", _env_default("PASSWORD_LENGTH", "31"), "Password Length"),
    SwitchEnvField("time_zone", "TIME_ZONE", _env_default("TIME_ZONE", "UTC-03:00"), "Time Zone"),
    SwitchEnvField(
        "primary_ntp_server",
        "PRIMARY_NTP_SERVER",
        _env_default("PRIMARY_NTP_SERVER", "200.160.7.186"),
        "Primary NTP Server",
    ),
    SwitchEnvField(
        "secondary_ntp_server",
        "SECONDARY_NTP_SERVER",
        _env_default("SECONDARY_NTP_SERVER", "200.160.0.8"),
        "Secondary NTP Server",
    ),
    SwitchEnvField("ntp_update_rate", "NTP_UPDATE_RATE", _env_default("NTP_UPDATE_RATE", "12"), "NTP Update Rate"),
    SwitchEnvField(
        "ip_remote_logging_server",
        "IP_REMOTE_LOGGING_SERVER",
        _env_default("IP_REMOTE_LOGGING_SERVER", "10.0.2.5"),
        "Remote Logging Server IP",
    ),
    SwitchEnvField("log_level", "LOG_LEVEL", _env_default("LOG_LEVEL", "6"), "Log Level"),
    SwitchEnvField(
        "size_of_jumbo_frame",
        "SIZE_OF_JUMBO_FRAME",
        _env_default("SIZE_OF_JUMBO_FRAME", "9216"),
        "Jumbo Frame Size",
    ),
    SwitchEnvField("sdm_preference", "SDM_PREFERENCE", _env_default("SDM_PREFERENCE", "enterpriseV4"), "SDM Preference"),
    SwitchEnvField("eee_interfaces", "EEE_INTERFACES", _env_default("EEE_INTERFACES", "1/0/1-24"), "EEE Interfaces"),
    SwitchEnvField("eee_lacps", "EEE_LACPS", _env_default("EEE_LACPS", "1-6"), "EEE LACPs"),
    SwitchEnvField(
        "lacp_load_balance",
        "LACP_LOAD_BALANCE",
        _env_default("LACP_LOAD_BALANCE", "src-dst-mac"),
        "LACP Load Balance",
    ),
    SwitchEnvField(
        "static_route_destination_ip",
        "STATIC_ROUTE_DESTINATION_IP",
        _env_default("STATIC_ROUTE_DESTINATION_IP", "0.0.0.0"),
        "Static Route Destination IP",
    ),
    SwitchEnvField(
        "static_route_subnet_mask",
        "STATIC_ROUTE_SUBNET_MASK",
        _env_default("STATIC_ROUTE_SUBNET_MASK", "0.0.0.0"),
        "Static Route Subnet Mask",
    ),
    SwitchEnvField(
        "static_route_default_gateway_ip",
        "STATIC_ROUTE_DEFAULT_GATEWAY_IP",
        _env_default("STATIC_ROUTE_DEFAULT_GATEWAY_IP", "192.168.0.2"),
        "Default Gateway IP",
    ),
    SwitchEnvField(
        "static_route_default_gateway_distance",
        "STATIC_ROUTE_DEFAULT_GATEWAY_DISTANCE",
        _env_default("STATIC_ROUTE_DEFAULT_GATEWAY_DISTANCE", "1"),
        "Default Gateway Distance",
    ),
    SwitchEnvField(
        "firmware_file_name",
        "FIRMWARE_FILE_NAME",
        _env_default("FIRMWARE_FILE_NAME", "T1600G-28TS-V3-20200805"),
        "Firmware File Name",
    ),
    SwitchEnvField(
        "firmware_url",
        "FIRMWARE_URL",
        _env_default(
            "FIRMWARE_URL",
            "https://static.tp-link.com/2020/202009/20200922/T1600G-28TS(UN)_V3_20200805.zip",
        ),
        "Firmware URL",
    ),
    SwitchEnvField(
        "https_certificate",
        "HTTPS_CERTIFICATE",
        _env_default("HTTPS_CERTIFICATE", "switch.lan.homelab.crt"),
        "HTTPS Certificate",
    ),
    SwitchEnvField(
        "https_certificate_key",
        "HTTPS_CERTIFICATE_KEY",
        _env_default("HTTPS_CERTIFICATE_KEY", "switch.lan.homelab.key"),
        "HTTPS Certificate Key",
    ),
    SwitchEnvField(
        "https_certificate_short_name",
        "HTTPS_CERTIFICATE_SHORT_NAME",
        _env_default("HTTPS_CERTIFICATE_SHORT_NAME", "certificate.crt"),
        "HTTPS Certificate Short Name",
    ),
    SwitchEnvField(
        "https_certificate_key_short_name",
        "HTTPS_CERTIFICATE_KEY_SHORT_NAME",
        _env_default("HTTPS_CERTIFICATE_KEY_SHORT_NAME", "certificate.key"),
        "HTTPS Certificate Key Short Name",
    ),
)

SWITCH_FIELD_NAMES: tuple[str, ...] = tuple(field.attr_name for field in SWITCH_ENV_FIELDS)
SWITCH_FIELD_DEFAULTS: dict[str, str] = {field.attr_name: field.default_value for field in SWITCH_ENV_FIELDS}
SWITCH_FIELD_TO_ENV: dict[str, str] = {field.attr_name: field.env_name for field in SWITCH_ENV_FIELDS}


def normalize_switch_env_field_value(field_name: str, raw_value: Any) -> str:
    default_value = SWITCH_FIELD_DEFAULTS[field_name]
    if raw_value is None:
        return default_value

    value = str(raw_value).strip()
    return value if value else default_value


def switch_env_form_values(switch: Any) -> dict[str, str]:
    values: dict[str, str] = {}
    for field in SWITCH_ENV_FIELDS:
        values[field.attr_name] = normalize_switch_env_field_value(field.attr_name, getattr(switch, field.attr_name, None))
    return values


def switch_env_values_for_runner(switch: Any) -> dict[str, str]:
    values: dict[str, str] = {}
    for field in SWITCH_ENV_FIELDS:
        values[field.env_name] = normalize_switch_env_field_value(field.attr_name, getattr(switch, field.attr_name, None))
    return values
