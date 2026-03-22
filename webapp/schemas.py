from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


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
