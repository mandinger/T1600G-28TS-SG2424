from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DEFAULT_PROFILE: dict[str, Any] = {
    "time_zone": "UTC-03:00",
    "primary_ntp_server": "200.160.7.186",
    "secondary_ntp_server": "200.160.0.8",
    "ntp_update_rate": "12",
    "ip_remote_logging_server": "10.0.2.5",
    "log_level": 6,
    "size_of_jumbo_frame": 9216,
    "sdm_preference": "enterpriseV4",
    "eee_interfaces": "1/0/1-24",
    "eee_lacps": "1-6",
    "lacp_load_balance": "src-dst-mac",
    "static_route_destination_ip": "0.0.0.0",
    "static_route_subnet_mask": "0.0.0.0",
    "static_route_default_gateway_ip": "192.168.0.2",
    "static_route_default_gateway_distance": 1,
    "https_certificate": "switch.lan.homelab.crt",
    "https_certificate_key": "switch.lan.homelab.key",
    "firmware_file_name": "T1600G-28TS-V3-20200805",
    "firmware_url": "https://static.tp-link.com/2020/202009/20200922/T1600G-28TS(UN)_V3_20200805.zip",
    "vlans": [
        {
            "vlan_id": "1",
            "vlan_name": "System-VLAN",
            "untagged_ports": "",
            "tagged_ports": "",
            "untagged_lag": "",
            "tagged_lag": "",
            "pvid_ports": "",
            "pvid_lag_ports": "",
            "ip_address": "",
            "subnet_mask": "",
        },
        {
            "vlan_id": "10",
            "vlan_name": "Device",
            "untagged_ports": "1/0/1-28",
            "tagged_ports": "",
            "untagged_lag": "",
            "tagged_lag": "1-8",
            "pvid_ports": "1/0/1-28",
            "pvid_lag_ports": "1-8",
            "ip_address": "172.16.10.2",
            "subnet_mask": "255.255.255.240",
        },
    ],
    "lacp_groups": [
        {"ports": "1/0/1-4", "group_id": "1", "port_priority": "0", "mode": "active"},
        {"ports": "1/0/5-8", "group_id": "2", "port_priority": "0", "mode": "active"},
        {"ports": "1/0/9-12", "group_id": "3", "port_priority": "0", "mode": "active"},
        {"ports": "1/0/13-16", "group_id": "4", "port_priority": "0", "mode": "active"},
        {"ports": "1/0/17-20", "group_id": "5", "port_priority": "0", "mode": "active"},
        {"ports": "1/0/21-24", "group_id": "6", "port_priority": "0", "mode": "active"},
        {"ports": "1/0/25-27", "group_id": "7", "port_priority": "0", "mode": "static"},
        {"ports": "1/0/28", "group_id": "8", "port_priority": "0", "mode": "static"},
    ],
}


def default_profile() -> dict[str, Any]:
    return json.loads(json.dumps(DEFAULT_PROFILE))


def merged_profile(profile: dict[str, Any] | None) -> dict[str, Any]:
    out = default_profile()
    if not profile:
        return out

    for key, value in profile.items():
        out[key] = value

    if "vlans" not in out or not isinstance(out["vlans"], list):
        out["vlans"] = default_profile()["vlans"]

    if "lacp_groups" not in out or not isinstance(out["lacp_groups"], list):
        out["lacp_groups"] = default_profile()["lacp_groups"]

    return out


def write_profile_files(base_dir: Path, profile: dict[str, Any]) -> tuple[Path, Path]:
    vlan_dir = base_dir / "vlan"
    lacp_dir = base_dir / "lacp"
    vlan_dir.mkdir(parents=True, exist_ok=True)
    lacp_dir.mkdir(parents=True, exist_ok=True)

    for path in vlan_dir.glob("*.sh"):
        path.unlink()
    for path in lacp_dir.glob("*.sh"):
        path.unlink()

    vlans = profile.get("vlans") or []
    for index, vlan in enumerate(vlans, start=1):
        vlan_file = vlan_dir / f"{index}.sh"
        vlan_file.write_text(
            "\n".join(
                [
                    f'VLAN_ID="{vlan.get("vlan_id", "")}"',
                    f'VLAN_NAME="{vlan.get("vlan_name", "")}"',
                    "",
                    "#VLAN",
                    f'UNTAGGED_PORTS="{vlan.get("untagged_ports", "")}"',
                    f'TAGGED_PORTS="{vlan.get("tagged_ports", "")}"',
                    f'UNTAGGED_LAG="{vlan.get("untagged_lag", "")}"',
                    f'TAGGED_LAG="{vlan.get("tagged_lag", "")}"',
                    "",
                    "#PVID",
                    f'PVID_PORTS="{vlan.get("pvid_ports", "")}"',
                    f'PVID_LAG_PORTS="{vlan.get("pvid_lag_ports", "")}"',
                    "",
                    "#Interface",
                    f'IP_ADDRESS="{vlan.get("ip_address", "")}"',
                    f'SUBNET_MASK="{vlan.get("subnet_mask", "")}"',
                    "",
                ]
            ),
            encoding="utf-8",
        )

    lacp_groups = profile.get("lacp_groups") or []
    for index, group in enumerate(lacp_groups, start=1):
        group_file = lacp_dir / f"{index}.sh"
        group_file.write_text(
            "\n".join(
                [
                    f'PORTS="{group.get("ports", "")}"',
                    f'GROUP_ID="{group.get("group_id", "")}"',
                    f'PORT_PRIORITY="{group.get("port_priority", "0")}"',
                    f'MODE="{group.get("mode", "active")}"',
                    "",
                ]
            ),
            encoding="utf-8",
        )

    return vlan_dir, lacp_dir
