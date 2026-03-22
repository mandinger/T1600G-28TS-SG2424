#!/bin/bash

# Description:  Scripts to setup the Switch Tplink SFP T1600G-28TS-SG2424.
# Author:       Luciano Sampaio
# Date:         20-Dec-2020
# Usage:        ./setup.sh

# Dependencies
. lib/Environment.sh
. command/Config.sh
. command/Enable.sh
. command/Management.sh
. lib/Base64.sh
. lib/Credential.sh
. lib/Directory.sh
. lib/File.sh
. lib/FileMode.sh
. lib/FileOwner.sh
. lib/Https.sh
. lib/IP.sh
. lib/Log.sh
. lib/PackageManager.sh
. lib/Service.sh
. lib/SSH.sh
. lib/String.sh
. lib/Telnet.sh
. lib/TFTP.sh
. option/AllSetupScripts.sh
. option/Backup.sh
. option/DeviceDescription.sh
. option/DoSDefend.sh
. option/EEE.sh
. option/FactorySettings.sh
. option/Firmware.sh
. option/HTTP.sh
. option/HTTPS.sh
. option/Interface.sh
. option/IPRouting.sh
. option/JumboSize.sh
. option/LACP.sh
. option/PasswordEncryption.sh
. option/PVID.sh
. option/Reboot.sh
. option/RemoteLogging.sh
. option/RestoreSettingsFromLatestBackup.sh
. option/SDMPreference.sh
. option/SSH.sh
. option/StaticIP.sh
. option/StaticRouting.sh
. option/SystemTimeUsingNTPServer.sh
. option/Telnet.sh
. option/User.sh
. option/Vlan.sh

# Load config from .env/.env.example and apply defaults.
SCRIPT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
initializeEnvironmentConfig "$SCRIPT_ROOT"

# Variables
exitOption=0
amountOfOptions=26

userHasProvidedArguments () {
  # 0 True and 1 False
  [ $# -ge 1 ] && return 0 || return 1
}
if (userHasProvidedArguments $*) ; then
  chosenOption=$1
else
  chosenOption=-1
fi

# Methods
sendBreakLine () {
  echo ""
}

runChosenOption () {
  sendBreakLine
  case $1 in
   #0) is the option to exit the application. There is nothing to do here.
    1)
      runAllSetupScripts ;;
    2)
      setStaticIP ;;
    3)
      enableSSH ;;
    4)
      enablePasswordEncryption ;;
    5)
      createBotUser ;;
    6)
      setLACP ;;
    7)
      setVlans ;;
    8)
      setPVID ;;
    9)
      setIPRouting ;;
    10)
      setInterfaces ;;
    11)
      setStaticRoutingToDefaultGateway ;;
    12)
      setSystemTimeUsingNTPServer ;;
    13)
      enableHTTPS ;;
    14)
      disableHTTP ;;
    15)
      setJumboSize ;;
    16)
      enableDoSDefend ;;
    17)
      setDeviceDescription ;;
    18)
      setSDMPreference ;;
    19)
      enableRemoteLogging ;;
    20)
      disableTelnet ;;
    21)
      enableEEE ;;
    22)
      upgradeFirmware ;;
    23)
      backup ;;
    24)
      reboot ;;
    25)
      resetWithFactorySettings ;;
    26)
      restoreSettingsFromLatestBackup ;;
  esac
  sendBreakLine
}

displayMenu() {
  index=0
  echo "Type the number of the option you want to execute. [$index-$1]"
  echo "$((index++)) - Exit."
  echo "$((index++)) - Setup Switch from Zero to Hero!"
  echo "$((index++)) - Set static IP."
  echo "$((index++)) - Enable SSH."
  echo "$((index++)) - Enable Password Encryption."
  echo "$((index++)) - Create Bot User."
  echo "$((index++)) - Set Link Aggregation Control Protocol."
  echo "$((index++)) - Set Vlans."
  echo "$((index++)) - Set PVID."
  echo "$((index++)) - Set IP Routing."
  echo "$((index++)) - Set Interfaces."
  echo "$((index++)) - Set IPv4 Static Routing to Default Gateway."
  echo "$((index++)) - Set System Time from NTP Server."
  echo "$((index++)) - Enable HTTPS."
  echo "$((index++)) - Disable HTTP."
  echo "$((index++)) - Set Jumbo Size."
  echo "$((index++)) - Enable DoS Defend."
  echo "$((index++)) - Set Device Description."
  echo "$((index++)) - Set SDM Preference."
  echo "$((index++)) - Enable Remote Logging."
  echo "$((index++)) - Disable Telnet."
  echo "$((index++)) - Enable EEE."
  echo "$((index++)) - Upgrade Firmware."
  echo "$((index++)) - Backup."
  echo "$((index++)) - Reboot."
  echo "$((index++)) - Reset with Factory Settings."
  echo "$((index++)) - Restore Settings from Latest Backup."
}

userHasChosenAValidOption() {
  # 0 True and 1 False
  [ $1 -ge 0 ] && [ $1 -le $2 ] && return 0 || return 1
}

getChosenOption () {
  chosenOption=$1
  amountOfOptions=$2

  until userHasChosenAValidOption $chosenOption $amountOfOptions
  do
    displayMenu $amountOfOptions
    read chosenOption
  done

  return $chosenOption
}

userWantsToExit() {
  # 0 True and 1 False
  [ $1 -eq $exitOption ] && return 0 || return 1
}

until userWantsToExit $chosenOption
do
  getChosenOption $chosenOption $amountOfOptions
  chosenOption=$?

  runChosenOption $chosenOption

  chosenOption=0
done
