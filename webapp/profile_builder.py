from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .switch_env_overrides import SWITCH_FIELD_NAMES

DEFAULT_PROFILE: dict[str, Any] = {
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

_DEPRECATED_PROFILE_KEYS: set[str] = set(SWITCH_FIELD_NAMES) | {"env_overrides"}


def default_profile() -> dict[str, Any]:
    return json.loads(json.dumps(DEFAULT_PROFILE))


def merged_profile(profile: dict[str, Any] | None) -> dict[str, Any]:
    out = default_profile()
    if not profile:
        return out

    for key, value in profile.items():
        if key in _DEPRECATED_PROFILE_KEYS:
            continue
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
