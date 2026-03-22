from types import SimpleNamespace

from webapp.actions import get_action
from webapp.profile_builder import merged_profile
from webapp.runner import build_execution_context


def test_profile_materialization_creates_runtime_files(tmp_path) -> None:
    switch = SimpleNamespace(
        id=77,
        device_ip="192.168.0.3",
        device_name="SW-01",
        device_location="LAB",
        device_contact_info="",
        admin_username="admin",
        bot_username="bot",
        bot_privilege="admin",
        tftp_source_ip="",
    )
    action = get_action("set_vlans")
    assert action is not None

    profile = merged_profile(
        {
            "vlans": [
                {
                    "vlan_id": "20",
                    "vlan_name": "Servers",
                    "untagged_ports": "1/0/1-2",
                    "tagged_ports": "1/0/3",
                    "untagged_lag": "",
                    "tagged_lag": "1",
                    "pvid_ports": "1/0/1-2",
                    "pvid_lag_ports": "1",
                    "ip_address": "10.20.0.2",
                    "subnet_mask": "255.255.255.0",
                }
            ]
        }
    )

    from webapp import runner as runner_module
    original = runner_module.get_settings

    def fake_settings():
        settings = original()
        return SimpleNamespace(**{**settings.__dict__, "data_dir": tmp_path})

    runner_module.get_settings = fake_settings  # type: ignore[assignment]

    try:
        context = build_execution_context(
            action=action,
            job_id=500,
            switch=switch,
            profile_data=profile,
            input_payload={},
            admin_password="pw1",
            bot_password="pw2",
        )
    finally:
        runner_module.get_settings = original  # type: ignore[assignment]

    assert context.bot_password_output.parent.exists()
    assert (tmp_path / "runtime" / "job-500" / "profile" / "vlan" / "1.sh").exists()
    assert context.env["VLAN_PATH_OF_VARIABLES_WITH_FILTER"].endswith("*.sh")
