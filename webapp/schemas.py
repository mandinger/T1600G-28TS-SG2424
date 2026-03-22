from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field
from .switch_env_overrides import SWITCH_FIELD_DEFAULTS


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str


class SwitchCreateRequest(BaseModel):
    name: str
    device_ip: str
    model: str = "T1600G-28TS"
    device_name: str = "T1600G-28TS"
    device_location: str = "DC-BR-SE-AJU-SWITCH-01"
    device_contact_info: str = ""
    admin_username: str = "admin"
    admin_password: str = ""
    bot_username: str = "switch-user-bot"
    bot_privilege: str = "admin"
    bot_password: str = ""
    tftp_source_ip: str = ""
    ssh_version: str = SWITCH_FIELD_DEFAULTS["ssh_version"]
    password_length: str = SWITCH_FIELD_DEFAULTS["password_length"]
    time_zone: str = SWITCH_FIELD_DEFAULTS["time_zone"]
    primary_ntp_server: str = SWITCH_FIELD_DEFAULTS["primary_ntp_server"]
    secondary_ntp_server: str = SWITCH_FIELD_DEFAULTS["secondary_ntp_server"]
    ntp_update_rate: str = SWITCH_FIELD_DEFAULTS["ntp_update_rate"]
    ip_remote_logging_server: str = SWITCH_FIELD_DEFAULTS["ip_remote_logging_server"]
    log_level: str = SWITCH_FIELD_DEFAULTS["log_level"]
    size_of_jumbo_frame: str = SWITCH_FIELD_DEFAULTS["size_of_jumbo_frame"]
    sdm_preference: str = SWITCH_FIELD_DEFAULTS["sdm_preference"]
    eee_interfaces: str = SWITCH_FIELD_DEFAULTS["eee_interfaces"]
    eee_lacps: str = SWITCH_FIELD_DEFAULTS["eee_lacps"]
    lacp_load_balance: str = SWITCH_FIELD_DEFAULTS["lacp_load_balance"]
    static_route_destination_ip: str = SWITCH_FIELD_DEFAULTS["static_route_destination_ip"]
    static_route_subnet_mask: str = SWITCH_FIELD_DEFAULTS["static_route_subnet_mask"]
    static_route_default_gateway_ip: str = SWITCH_FIELD_DEFAULTS["static_route_default_gateway_ip"]
    static_route_default_gateway_distance: str = SWITCH_FIELD_DEFAULTS["static_route_default_gateway_distance"]
    firmware_file_name: str = SWITCH_FIELD_DEFAULTS["firmware_file_name"]
    firmware_url: str = SWITCH_FIELD_DEFAULTS["firmware_url"]
    https_certificate: str = SWITCH_FIELD_DEFAULTS["https_certificate"]
    https_certificate_key: str = SWITCH_FIELD_DEFAULTS["https_certificate_key"]
    https_certificate_short_name: str = SWITCH_FIELD_DEFAULTS["https_certificate_short_name"]
    https_certificate_key_short_name: str = SWITCH_FIELD_DEFAULTS["https_certificate_key_short_name"]


class SwitchUpdateRequest(BaseModel):
    name: str | None = None
    device_ip: str | None = None
    model: str | None = None
    device_name: str | None = None
    device_location: str | None = None
    device_contact_info: str | None = None
    admin_username: str | None = None
    admin_password: str | None = None
    bot_username: str | None = None
    bot_privilege: str | None = None
    bot_password: str | None = None
    tftp_source_ip: str | None = None
    ssh_version: str | None = None
    password_length: str | None = None
    time_zone: str | None = None
    primary_ntp_server: str | None = None
    secondary_ntp_server: str | None = None
    ntp_update_rate: str | None = None
    ip_remote_logging_server: str | None = None
    log_level: str | None = None
    size_of_jumbo_frame: str | None = None
    sdm_preference: str | None = None
    eee_interfaces: str | None = None
    eee_lacps: str | None = None
    lacp_load_balance: str | None = None
    static_route_destination_ip: str | None = None
    static_route_subnet_mask: str | None = None
    static_route_default_gateway_ip: str | None = None
    static_route_default_gateway_distance: str | None = None
    firmware_file_name: str | None = None
    firmware_url: str | None = None
    https_certificate: str | None = None
    https_certificate_key: str | None = None
    https_certificate_short_name: str | None = None
    https_certificate_key_short_name: str | None = None


class SwitchResponse(BaseModel):
    id: int
    name: str
    device_ip: str
    model: str
    device_name: str
    device_location: str
    device_contact_info: str
    admin_username: str
    bot_username: str
    bot_privilege: str
    tftp_source_ip: str
    ssh_version: str
    password_length: str
    time_zone: str
    primary_ntp_server: str
    secondary_ntp_server: str
    ntp_update_rate: str
    ip_remote_logging_server: str
    log_level: str
    size_of_jumbo_frame: str
    sdm_preference: str
    eee_interfaces: str
    eee_lacps: str
    lacp_load_balance: str
    static_route_destination_ip: str
    static_route_subnet_mask: str
    static_route_default_gateway_ip: str
    static_route_default_gateway_distance: str
    firmware_file_name: str
    firmware_url: str
    https_certificate: str
    https_certificate_key: str
    https_certificate_short_name: str
    https_certificate_key_short_name: str
    created_at: datetime
    updated_at: datetime


class ProfileResponse(BaseModel):
    switch_id: int
    profile: dict[str, Any]
    updated_at: datetime


class ProfileUpdateRequest(BaseModel):
    profile: dict[str, Any] = Field(default_factory=dict)


class ActionExecutionRequest(BaseModel):
    input: dict[str, Any] = Field(default_factory=dict)


class JobResponse(BaseModel):
    id: int
    switch_id: int
    created_by_user_id: int
    action_key: str
    status: str
    exit_code: int | None
    error_message: str
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None


class JobListResponse(BaseModel):
    jobs: list[JobResponse]
