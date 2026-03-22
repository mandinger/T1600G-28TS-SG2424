from webapp.actions import ACTIONS, get_action, list_actions


def test_registry_has_27_actions() -> None:
    assert len(ACTIONS) == 27


def test_risky_actions_disabled_in_v1() -> None:
    action_keys = {a["key"]: a for a in list_actions()}
    for key in {"upgrade_firmware", "reboot", "factory_reset", "restore_latest_backup"}:
        assert key in action_keys
        assert action_keys[key]["enabled"] is False


def test_static_ip_requires_current_ip_input() -> None:
    action = get_action("set_static_ip")
    assert action is not None
    assert "current_ip" in action.required_inputs
