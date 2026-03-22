from datetime import datetime, timezone

from webapp.jobs import switch_has_active_job
from webapp.models import Job, Switch


def test_switch_active_job_detection(db_session) -> None:
    switch = Switch(
        name="switch-a",
        device_ip="192.168.0.10",
        model="T1600G-28TS",
        device_name="Switch A",
        device_location="Lab",
        device_contact_info="",
        admin_username="admin",
        bot_username="bot",
        bot_privilege="admin",
        tftp_source_ip="",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(switch)
    db_session.commit()

    assert not switch_has_active_job(db_session, switch.id)

    db_session.add(
        Job(
            switch_id=switch.id,
            created_by_user_id=1,
            action_key="backup",
            status="running",
            input_payload_json="{}",
            created_at=datetime.now(timezone.utc),
        )
    )
    db_session.commit()

    assert switch_has_active_job(db_session, switch.id)
