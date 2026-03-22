from webapp.actions import ACTIONS, get_action, list_actions


def test_registry_has_26_actions() -> None:
    assert len(ACTIONS) == 26


def test_risky_actions_disabled_in_v1() -> None:
    action_keys = {a["key"]: a for a in list_actions()}
    for key in {"upgrade_firmware", "reboot", "factory_reset", "restore_latest_backup"}:
        assert key in action_keys
        assert action_keys[key]["enabled"] is False


def test_prepare_host_machine_not_exposed() -> None:
    action_keys = {a["key"]: a for a in list_actions()}
    assert "prepare_host_machine" not in action_keys


def test_option_numbers_are_contiguous_without_gap() -> None:
    option_numbers = sorted([a["option_number"] for a in list_actions()])
    assert option_numbers == list(range(1, 27))


def test_static_ip_requires_current_ip_input() -> None:
    action = get_action("set_static_ip")
    assert action is not None
    assert "current_ip" in action.required_inputs
