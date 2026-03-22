from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ActionDefinition:
    key: str
    option_number: int
    display_name: str
    function_name: str
    description: str
    risky: bool = False
    enabled: bool = True
    required_inputs: tuple[str, ...] = ()


ACTIONS: tuple[ActionDefinition, ...] = (
    ActionDefinition("setup_zero_to_hero", 1, "Setup Switch from Zero to Hero", "runAllSetupScripts", "Run the full setup pipeline."),
    ActionDefinition("prepare_host_machine", 2, "Prepare Host Machine", "prepareHostMachine", "Prepare runtime directories and dependencies inside the container."),
    ActionDefinition("set_static_ip", 3, "Set static IP", "setStaticIP", "Configure static management IP via telnet bootstrap.", required_inputs=("current_ip",)),
    ActionDefinition("enable_ssh", 4, "Enable SSH", "enableSSH", "Enable SSH and install public key."),
    ActionDefinition("enable_password_encryption", 5, "Enable Password Encryption", "enablePasswordEncryption", "Enable password encryption service."),
    ActionDefinition("create_bot_user", 6, "Create Bot User", "createBotUser", "Create automation user and generate password."),
    ActionDefinition("set_lacp", 7, "Set LACP", "setLACP", "Configure LACP load balancing and groups."),
    ActionDefinition("set_vlans", 8, "Set VLANs", "setVlans", "Create VLANs and assign interfaces/LAGs."),
    ActionDefinition("set_pvid", 9, "Set PVID", "setPVID", "Set PVID for ports and LAGs."),
    ActionDefinition("enable_ipv4_routing", 10, "Enable IPv4 routing", "setIPRouting", "Enable IPv4 routing at switch level."),
    ActionDefinition("set_interfaces", 11, "Set Interfaces", "setInterfaces", "Configure VLAN interfaces and IP addresses."),
    ActionDefinition("set_default_route", 12, "Set Default IPv4 Static Route", "setStaticRoutingToDefaultGateway", "Configure default static route."),
    ActionDefinition("set_system_time_ntp", 13, "Set System Time via NTP", "setSystemTimeUsingNTPServer", "Configure NTP servers and timezone."),
    ActionDefinition("enable_https", 14, "Enable HTTPS", "enableHTTPS", "Enable secure web management with uploaded certificate and key."),
    ActionDefinition("disable_http", 15, "Disable HTTP", "disableHTTP", "Disable insecure HTTP management."),
    ActionDefinition("set_jumbo_size", 16, "Set Jumbo Frame Size", "setJumboSize", "Set global jumbo frame size."),
    ActionDefinition("enable_dos_defend", 17, "Enable DoS Defend", "enableDoSDefend", "Enable configured DoS prevention settings."),
    ActionDefinition("set_device_description", 18, "Set Device Description", "setDeviceDescription", "Apply hostname, location, and contact info."),
    ActionDefinition("set_sdm_preference", 19, "Set SDM Preference", "setSDMPreference", "Configure SDM template preference."),
    ActionDefinition("enable_remote_logging", 20, "Enable Remote Logging", "enableRemoteLogging", "Configure remote syslog target and level."),
    ActionDefinition("disable_telnet", 21, "Disable Telnet", "disableTelnet", "Disable telnet service after SSH setup."),
    ActionDefinition("enable_eee", 22, "Enable EEE", "enableEEE", "Enable Energy Efficient Ethernet on configured interfaces."),
    ActionDefinition("upgrade_firmware", 23, "Upgrade Firmware", "upgradeFirmware", "Upgrade firmware via TFTP.", risky=True, enabled=False),
    ActionDefinition("backup", 24, "Backup", "backup", "Create startup-config backup over TFTP."),
    ActionDefinition("reboot", 25, "Reboot", "reboot", "Reboot switch.", risky=True, enabled=False),
    ActionDefinition("factory_reset", 26, "Reset with Factory Settings", "resetWithFactorySettings", "Reset configuration except IP.", risky=True, enabled=False),
    ActionDefinition("restore_latest_backup", 27, "Restore from Latest Backup", "restoreSettingsFromLatestBackup", "Restore startup config from latest backup.", risky=True, enabled=False),
)


ACTION_MAP = {action.key: action for action in ACTIONS}


def list_actions() -> list[dict[str, Any]]:
    return [
        {
            "key": action.key,
            "option_number": action.option_number,
            "display_name": action.display_name,
            "description": action.description,
            "risky": action.risky,
            "enabled": action.enabled,
            "required_inputs": list(action.required_inputs),
            "disabled_reason": "Disabled in v1 safety policy." if not action.enabled else "",
        }
        for action in ACTIONS
    ]


def get_action(action_key: str) -> ActionDefinition | None:
    return ACTION_MAP.get(action_key)
