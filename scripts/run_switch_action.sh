#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

# Load original project scripts.
. "$ROOT_DIR/lib/Environment.sh"
. "$ROOT_DIR/command/Config.sh"
. "$ROOT_DIR/command/Enable.sh"
. "$ROOT_DIR/command/Management.sh"
. "$ROOT_DIR/lib/Base64.sh"
. "$ROOT_DIR/lib/Credential.sh"
. "$ROOT_DIR/lib/Directory.sh"
. "$ROOT_DIR/lib/File.sh"
. "$ROOT_DIR/lib/FileMode.sh"
. "$ROOT_DIR/lib/FileOwner.sh"
. "$ROOT_DIR/lib/Https.sh"
. "$ROOT_DIR/lib/IP.sh"
. "$ROOT_DIR/lib/Log.sh"
. "$ROOT_DIR/lib/PackageManager.sh"
. "$ROOT_DIR/lib/Service.sh"
. "$ROOT_DIR/lib/SSH.sh"
. "$ROOT_DIR/lib/String.sh"
. "$ROOT_DIR/lib/Telnet.sh"
. "$ROOT_DIR/lib/TFTP.sh"
. "$ROOT_DIR/option/AllSetupScripts.sh"
. "$ROOT_DIR/option/Backup.sh"
. "$ROOT_DIR/option/DeviceDescription.sh"
. "$ROOT_DIR/option/DoSDefend.sh"
. "$ROOT_DIR/option/EEE.sh"
. "$ROOT_DIR/option/FactorySettings.sh"
. "$ROOT_DIR/option/Firmware.sh"
. "$ROOT_DIR/option/HTTP.sh"
. "$ROOT_DIR/option/HTTPS.sh"
. "$ROOT_DIR/option/Interface.sh"
. "$ROOT_DIR/option/IPRouting.sh"
. "$ROOT_DIR/option/JumboSize.sh"
. "$ROOT_DIR/option/LACP.sh"
. "$ROOT_DIR/option/PasswordEncryption.sh"
. "$ROOT_DIR/option/PVID.sh"
. "$ROOT_DIR/option/Reboot.sh"
. "$ROOT_DIR/option/RemoteLogging.sh"
. "$ROOT_DIR/option/RestoreSettingsFromLatestBackup.sh"
. "$ROOT_DIR/option/SDMPreference.sh"
. "$ROOT_DIR/option/SSH.sh"
. "$ROOT_DIR/option/StaticIP.sh"
. "$ROOT_DIR/option/StaticRouting.sh"
. "$ROOT_DIR/option/SystemTimeUsingNTPServer.sh"
. "$ROOT_DIR/option/Telnet.sh"
. "$ROOT_DIR/option/User.sh"
. "$ROOT_DIR/option/Vlan.sh"

# Load .env defaults without overriding switch-specific runtime variables.
initializeEnvironmentConfig "$ROOT_DIR"

override_var() {
  local var_name="$1"
  local value="${!var_name-}"
  if [[ -n "$value" ]]; then
    printf -v "$var_name" "%s" "$value"
  fi
}

# Runtime overrides for multi-switch execution.
override_var DEVICE_IP
override_var DEVICE_NAME
override_var DEVICE_LOCATION
override_var DEVICE_CONTACT_INFO
override_var USER_ADMIN
override_var USER_BOT
override_var USER_BOT_PRIVILEGE
override_var TFTP_DIRECTORY
override_var SSH_PUBLIC_KEY_PATH
override_var TIME_ZONE
override_var PRIMARY_NTP_SERVER
override_var SECONDARY_NTP_SERVER
override_var NTP_UPDATE_RATE
override_var IP_REMOTE_LOGGING_SERVER
override_var LOG_LEVEL
override_var SIZE_OF_JUMBO_FRAME
override_var SDM_PREFERENCE
override_var EEE_INTERFACES
override_var EEE_LACPS
override_var LACP_LOAD_BALANCE
override_var VLAN_PATH_OF_VARIABLES
override_var VLAN_PATH_OF_VARIABLES_WITH_FILTER
override_var LACP_PATH_OF_GROUPS_VARIABLES
override_var STATIC_ROUTE_DESTINATION_IP
override_var STATIC_ROUTE_SUBNET_MASK
override_var STATIC_ROUTE_DEFAULT_GATEWAY_IP
override_var STATIC_ROUTE_DEFAULT_GATEWAY_DISTANCE
override_var FIRMWARE_FILE_NAME
override_var FIRMWARE_URL
override_var FIRMWARE_PATH
override_var BACKUP_PATH
override_var HTTPS_FILES_PATH
override_var HTTPS_CERTIFICATE
override_var HTTPS_CERTIFICATE_KEY

# Recompute dependent constants after overrides.
SSH_PUBLIC_KEY_FULLNAME="${SSH_PUBLIC_KEY_NAME}.pub"
SSH_PUBLIC_KEY_PATH_AND_NAME="${SSH_PUBLIC_KEY_PATH}${SSH_PUBLIC_KEY_NAME}"
SSH_PUBLIC_KEY_PATH_AND_FULLNAME="${SSH_PUBLIC_KEY_PATH}${SSH_PUBLIC_KEY_FULLNAME}"
SSH_CONFIG_FILE_PATH_AND_FULLNAME="${SSH_PUBLIC_KEY_PATH}${SSH_CONFIG_FILE}"

HTTPS_CERTIFICATE_PATH_AND_NAME="${HTTPS_FILES_PATH}${HTTPS_CERTIFICATE}"
HTTPS_CERTIFICATE_KEY_PATH_AND_NAME="${HTTPS_FILES_PATH}${HTTPS_CERTIFICATE_KEY}"

FIRMWARE_FILE_NAME_BIN="${FIRMWARE_FILE_NAME}.bin"
FIRMWARE_FILE_NAME_ZIP="${FIRMWARE_FILE_NAME}.zip"

mkdir -p "$SSH_PUBLIC_KEY_PATH" "$TFTP_DIRECTORY" "$BACKUP_PATH" "$FIRMWARE_PATH" "$HTTPS_FILES_PATH"

# Compatibility shims for container runtime.
installPackage() {
  logInfo "Package install skipped in container runtime: $*"
}

packageManager() {
  logInfo "Package manager action skipped in container runtime: $*"
}

installTFTPServer() {
  mkdir -p "$TFTP_DIRECTORY"
  logInfo "TFTP installation step replaced with container runtime shim."
}

addTFTPConfigFile() {
  logInfo "Skipping host TFTP config file mutation in container runtime."
}

changeFileMode() {
  chmod "$@" 2>/dev/null || true
}

changeFileOwner() {
  chown "$@" 2>/dev/null || true
}

changeServiceStatus() {
  logInfo "Service status operation skipped in container runtime: $*"
}

startService() { true; }
stopService() { true; }

copyFileToTFTPFolder() {
  local source="$1"
  local destination_name="${2:-$(basename "$1")}"
  cp -p "$source" "${TFTP_DIRECTORY}${destination_name}"
}

copyFileFromTFTPFolder() {
  local source_name="$1"
  local destination_path="$2"
  cp -p "${TFTP_DIRECTORY}${source_name}" "$destination_path"
}

deleteFileFromTFTPFolder() {
  local source_name="$1"
  rm -f "${TFTP_DIRECTORY}${source_name}"
}

getPassword() {
  local key="$1"
  if [[ "$key" == "$USER_ADMIN_PASSWORD_KEY" ]]; then
    printf "%s" "${APP_ADMIN_PASSWORD:-}"
    return 0
  fi

  if [[ "$key" == "$USER_BOT" ]]; then
    printf "%s" "${APP_BOT_PASSWORD:-}"
    return 0
  fi

  printf ""
}

savePassword() {
  local key="$1"
  local value="$2"
  if [[ "$key" == "$USER_BOT" && -n "${RUNNER_BOT_PASSWORD_FILE:-}" ]]; then
    printf "%s" "$value" > "$RUNNER_BOT_PASSWORD_FILE"
  fi
}

getIpAddress() {
  if [[ -n "${RUNNER_TFTP_IP:-}" ]]; then
    printf "%s" "$RUNNER_TFTP_IP"
    return 0
  fi
  hostname -I | awk '{print $1}'
}

TFTP_RUN_PID=""
startTFTPServer() {
  logInfo "Starting internal TFTP process."
  mkdir -p "$TFTP_DIRECTORY"
  chmod -R 777 "$TFTP_DIRECTORY" || true

  if [[ -n "$TFTP_RUN_PID" ]] && kill -0 "$TFTP_RUN_PID" 2>/dev/null; then
    return 0
  fi

  if command -v in.tftpd >/dev/null 2>&1; then
    in.tftpd --listen --secure --create "$TFTP_DIRECTORY" >/dev/null 2>&1 &
    TFTP_RUN_PID="$!"
    sleep 1
  else
    logInfo "in.tftpd not found; TFTP dependent actions may fail."
  fi
}

stopTFTPServer() {
  logInfo "Stopping internal TFTP process."
  if [[ -n "$TFTP_RUN_PID" ]] && kill -0 "$TFTP_RUN_PID" 2>/dev/null; then
    kill "$TFTP_RUN_PID" 2>/dev/null || true
  fi
  TFTP_RUN_PID=""
  chmod -R 400 "$TFTP_DIRECTORY" || true
}

cleanup() {
  stopTFTPServer || true
}
trap cleanup EXIT

ACTION_FUNCTION="${ACTION_FUNCTION:-}"
if [[ -z "$ACTION_FUNCTION" ]]; then
  echo "ACTION_FUNCTION environment variable is required." >&2
  exit 2
fi

if ! declare -F "$ACTION_FUNCTION" >/dev/null 2>&1; then
  echo "Action function '$ACTION_FUNCTION' is not defined." >&2
  exit 2
fi

current_ip_from_payload() {
  python3 - <<'PY'
import base64
import json
import os

payload_b64 = os.getenv("ACTION_INPUT_B64", "")
if not payload_b64:
    print("")
    raise SystemExit(0)

try:
    payload = json.loads(base64.b64decode(payload_b64.encode("ascii")).decode("utf-8"))
except Exception:
    print("")
    raise SystemExit(0)

print(str(payload.get("current_ip", "")))
PY
}

if [[ "$ACTION_FUNCTION" == "setStaticIP" ]]; then
  current_ip="$(current_ip_from_payload)"
  if [[ -z "$current_ip" ]]; then
    echo "Missing required input: current_ip" >&2
    exit 3
  fi
  printf "%s\n" "$current_ip" | setStaticIP
else
  "$ACTION_FUNCTION"
fi
