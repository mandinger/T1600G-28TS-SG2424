#!/bin/bash

# Description:  Loads configuration from .env (without overwriting pre-set vars)
#               and applies default values when variables are missing.

setEnvIfUnset() {
  # $1 - variable name
  # $2 - default value
  var_name="$1"
  default_value="$2"

  if [ -z "${!var_name+x}" ]; then
    printf -v "$var_name" "%s" "$default_value"
    export "$var_name"
  fi
}

loadEnvDefaultsFile() {
  # $1 - path to .env-like file
  env_file="$1"
  [ -f "$env_file" ] || return 0

  while IFS= read -r line || [ -n "$line" ]; do
    # Trim leading/trailing spaces.
    line="${line#"${line%%[![:space:]]*}"}"
    line="${line%"${line##*[![:space:]]}"}"

    # Skip comments/empty lines/non assignments.
    [ -z "$line" ] && continue
    [[ "$line" == \#* ]] && continue
    [[ "$line" == *"="* ]] || continue

    key="${line%%=*}"
    value="${line#*=}"

    # Normalize key and trim value.
    key="${key//[[:space:]]/}"
    value="${value#"${value%%[![:space:]]*}"}"
    value="${value%"${value##*[![:space:]]}"}"

    # Only handle valid shell variable names.
    [[ "$key" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]] || continue

    # Strip wrapping single or double quotes.
    if [[ "$value" == \"*\" && "$value" == *\" ]]; then
      value="${value:1:-1}"
    elif [[ "$value" == \'*\' && "$value" == *\' ]]; then
      value="${value:1:-1}"
    fi

    if [ -z "${!key+x}" ]; then
      printf -v "$key" "%s" "$value"
      export "$key"
    fi
  done < "$env_file"
}

initializeEnvironmentConfig() {
  # $1 - repo root folder
  root_path="$1"
  if [ -z "$root_path" ]; then
    root_path="."
  fi

  loadEnvDefaultsFile "${root_path}/.env"
  loadEnvDefaultsFile "${root_path}/.env.example"

  # Core settings.
  setEnvIfUnset DEBUG "false"
  setEnvIfUnset DEVICE_IP "switch.lan.homelab"
  setEnvIfUnset DEVICE_NAME "T1600G-28TS"
  setEnvIfUnset DEVICE_LOCATION "DC-BR-SE-AJU-SWITCH-01"
  setEnvIfUnset DEVICE_CONTACT_INFO "bHNhbXBhaW93ZWJAZ21haWwuY29tCg=="

  setEnvIfUnset USER_ADMIN "admin"
  setEnvIfUnset USER_ADMIN_PASSWORD_KEY "switch-user-admin"
  setEnvIfUnset USER_BOT "switch-user-bot"
  setEnvIfUnset USER_BOT_PRIVILEGE "admin"
  setEnvIfUnset PASSWORD_LENGTH "31"

  # Paths and service defaults (container-friendly fallback paths).
  setEnvIfUnset TFTP_USER_GROUP "tftp:tftp"
  setEnvIfUnset TFTP_DIRECTORY "${root_path}/data/runtime-default/tftp/"
  setEnvIfUnset TFTP_CONFIG_DIRECTORY "/etc/default/tftpd-hpa"
  setEnvIfUnset TFTP_SERVICE_NAME "tftpd-hpa"

  setEnvIfUnset SSH_VERSION "v2"
  setEnvIfUnset SSH_PUBLIC_KEY_PATH "${root_path}/data/runtime-default/ssh/"
  setEnvIfUnset SSH_PUBLIC_KEY_NAME "id_rsa_tplink"
  setEnvIfUnset SSH_CONFIG_FILE "config"

  setEnvIfUnset TIME_ZONE "UTC-03:00"
  setEnvIfUnset PRIMARY_NTP_SERVER "200.160.7.186"
  setEnvIfUnset SECONDARY_NTP_SERVER "200.160.0.8"
  setEnvIfUnset NTP_UPDATE_RATE "12"

  setEnvIfUnset IP_REMOTE_LOGGING_SERVER "10.0.2.5"
  setEnvIfUnset LOG_LEVEL "6"

  setEnvIfUnset HTTPS_FILES_PATH "${root_path}/data/runtime-default/certificates/"
  setEnvIfUnset HTTPS_CERTIFICATE "switch.lan.homelab.crt"
  setEnvIfUnset HTTPS_CERTIFICATE_KEY "switch.lan.homelab.key"
  setEnvIfUnset HTTPS_CERTIFICATE_SHORT_NAME "certificate.crt"
  setEnvIfUnset HTTPS_CERTIFICATE_KEY_SHORT_NAME "certificate.key"

  setEnvIfUnset SIZE_OF_JUMBO_FRAME "9216"
  setEnvIfUnset SDM_PREFERENCE "enterpriseV4"
  setEnvIfUnset EEE_INTERFACES "1/0/1-24"
  setEnvIfUnset EEE_LACPS "1-6"

  setEnvIfUnset OPTION_FOLDER "option"
  setEnvIfUnset LACP_LOAD_BALANCE "src-dst-mac"

  if [ -z "${LACP_PATH_OF_GROUPS_VARIABLES+x}" ]; then
    LACP_PATH_OF_GROUPS_VARIABLES="${OPTION_FOLDER}/lacp/*.sh"
    export LACP_PATH_OF_GROUPS_VARIABLES
  fi

  if [ -z "${VLAN_PATH_OF_VARIABLES+x}" ]; then
    VLAN_PATH_OF_VARIABLES="${OPTION_FOLDER}/vlan"
    export VLAN_PATH_OF_VARIABLES
  fi

  if [ -z "${VLAN_PATH_OF_VARIABLES_WITH_FILTER+x}" ]; then
    VLAN_PATH_OF_VARIABLES_WITH_FILTER="${VLAN_PATH_OF_VARIABLES}/*.sh"
    export VLAN_PATH_OF_VARIABLES_WITH_FILTER
  fi

  setEnvIfUnset STATIC_ROUTE_DESTINATION_IP "0.0.0.0"
  setEnvIfUnset STATIC_ROUTE_SUBNET_MASK "0.0.0.0"
  setEnvIfUnset STATIC_ROUTE_DEFAULT_GATEWAY_IP "192.168.0.2"
  setEnvIfUnset STATIC_ROUTE_DEFAULT_GATEWAY_DISTANCE "1"

  setEnvIfUnset FIRMWARE_FILE_NAME "T1600G-28TS-V3-20200805"
  setEnvIfUnset FIRMWARE_URL "https://static.tp-link.com/2020/202009/20200922/T1600G-28TS(UN)_V3_20200805.zip"
  setEnvIfUnset FIRMWARE_PATH "firmware/"

  setEnvIfUnset BACKUP_PATH "backup/"
  setEnvIfUnset BACKUP_NAME "backup-startup-config-"
  setEnvIfUnset BACKUP_EXTENSION ".cfg"

  # Derived values.
  if [ -z "${SSH_PUBLIC_KEY_FULLNAME+x}" ]; then
    SSH_PUBLIC_KEY_FULLNAME="${SSH_PUBLIC_KEY_NAME}.pub"
    export SSH_PUBLIC_KEY_FULLNAME
  fi

  if [ -z "${SSH_PUBLIC_KEY_PATH_AND_NAME+x}" ]; then
    SSH_PUBLIC_KEY_PATH_AND_NAME="${SSH_PUBLIC_KEY_PATH}${SSH_PUBLIC_KEY_NAME}"
    export SSH_PUBLIC_KEY_PATH_AND_NAME
  fi

  if [ -z "${SSH_PUBLIC_KEY_PATH_AND_FULLNAME+x}" ]; then
    SSH_PUBLIC_KEY_PATH_AND_FULLNAME="${SSH_PUBLIC_KEY_PATH}${SSH_PUBLIC_KEY_FULLNAME}"
    export SSH_PUBLIC_KEY_PATH_AND_FULLNAME
  fi

  if [ -z "${SSH_CONFIG_FILE_PATH_AND_FULLNAME+x}" ]; then
    SSH_CONFIG_FILE_PATH_AND_FULLNAME="${SSH_PUBLIC_KEY_PATH}${SSH_CONFIG_FILE}"
    export SSH_CONFIG_FILE_PATH_AND_FULLNAME
  fi

  if [ -z "${HTTPS_CERTIFICATE_PATH_AND_NAME+x}" ]; then
    HTTPS_CERTIFICATE_PATH_AND_NAME="${HTTPS_FILES_PATH}${HTTPS_CERTIFICATE}"
    export HTTPS_CERTIFICATE_PATH_AND_NAME
  fi

  if [ -z "${HTTPS_CERTIFICATE_KEY_PATH_AND_NAME+x}" ]; then
    HTTPS_CERTIFICATE_KEY_PATH_AND_NAME="${HTTPS_FILES_PATH}${HTTPS_CERTIFICATE_KEY}"
    export HTTPS_CERTIFICATE_KEY_PATH_AND_NAME
  fi

  if [ -z "${FIRMWARE_FILE_NAME_BIN+x}" ]; then
    FIRMWARE_FILE_NAME_BIN="${FIRMWARE_FILE_NAME}.bin"
    export FIRMWARE_FILE_NAME_BIN
  fi

  if [ -z "${FIRMWARE_FILE_NAME_ZIP+x}" ]; then
    FIRMWARE_FILE_NAME_ZIP="${FIRMWARE_FILE_NAME}.zip"
    export FIRMWARE_FILE_NAME_ZIP
  fi
}
