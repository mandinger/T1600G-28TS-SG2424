from types import SimpleNamespace

from webapp.switch_env_overrides import (
    SWITCH_ENV_FIELDS,
    SWITCH_FIELD_DEFAULTS,
    normalize_switch_env_field_value,
    switch_env_form_values,
    switch_env_values_for_runner,
)


def test_normalize_switch_env_field_value_uses_default_for_empty() -> None:
    assert normalize_switch_env_field_value("time_zone", "") == SWITCH_FIELD_DEFAULTS["time_zone"]


def test_switch_env_form_values_populates_all_fields() -> None:
    switch = SimpleNamespace(time_zone="UTC+00:00")
    values = switch_env_form_values(switch)
    assert set(values.keys()) == {field.attr_name for field in SWITCH_ENV_FIELDS}
    assert values["time_zone"] == "UTC+00:00"


def test_switch_env_values_for_runner_maps_to_env_names() -> None:
    switch = SimpleNamespace(time_zone="UTC+00:00")
    env = switch_env_values_for_runner(switch)
    assert env["TIME_ZONE"] == "UTC+00:00"
    assert "PRIMARY_NTP_SERVER" in env
