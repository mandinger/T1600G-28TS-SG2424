#!/bin/bash

# Description:  It contains scripts related ssh commands.
# Author:       Luciano Sampaio 
# Date:         20-Dec-2020

runSSH () {
  # d "\n" -> Delimiter is a newline.
  # -n 1   -> One element per line.
  target="$1"
  sshOptions=(
    "-o" "BatchMode=yes"
    "-o" "ConnectTimeout=10"
    "-o" "StrictHostKeyChecking=no"
    "-o" "UserKnownHostsFile=/dev/null"
    "-o" "KexAlgorithms=+diffie-hellman-group1-sha1"
    "-o" "HostKeyAlgorithms=+ssh-rsa,+ssh-dss"
    "-o" "PubkeyAcceptedAlgorithms=+ssh-rsa"
    "-o" "Ciphers=aes128-ctr,aes192-ctr,aes256-ctr,aes128-cbc,3des-cbc"
  )

  # Prefer generated key when available.
  if [ -n "${SSH_PUBLIC_KEY_PATH_AND_NAME+x}" ] && [ -f "$SSH_PUBLIC_KEY_PATH_AND_NAME" ]; then
    sshOptions+=("-i" "$SSH_PUBLIC_KEY_PATH_AND_NAME" "-o" "IdentitiesOnly=yes")
  fi

  xargs -d "\n" -n 1 | ssh -T "${sshOptions[@]}" "$target" #>> out.txt
}

createSSHKeyPair () {
  logDebug "Creating SSH Key Pair: $1"

  sshKeyFolder=$(dirname "$1")
  mkdir -p "$sshKeyFolder"

  # -N Password
  # -q Quiet
  ssh-keygen -t rsa -b 2048 -f "$1" -N "" -q
}

sshKeyPairExists () {
  # $1 - key path without .pub extension
  privateKeyPath="$1"
  publicKeyPath="${1}.pub"

  [ -f "$privateKeyPath" ] && [ -f "$publicKeyPath" ] && return 0 || return 1
}

ensureSSHKeyPair () {
  # $1 - key path without .pub extension
  keyPath="$1"

  if ( ! sshKeyPairExists "$keyPath" ); then
    logInfo "SSH key pair not found or incomplete. Generating a new key pair."
    deleteFile "$keyPath"
    deleteFile "${keyPath}.pub"
    createSSHKeyPair "$keyPath"
  fi
}

copySSHKeyToTFTPFolder () {
  copyFileToTFTPFolder $1
}

createSSHConfigFile () {
  logDebug "Creating SSH Config File: $1"

  touch $1

  appendSSHConfigInfo $1
}

appendSSHConfigInfo () {
  file=$1
  textToSearch="# Specific Settings for $DEVICE_IP"

  if ( ! textExistsInFile "$file" "$textToSearch"); then
    logDebug "Appending Specific Settings for: $DEVICE_IP"

    (
      echo "$textToSearch"
      echo "Host $DEVICE_IP"
      echo -e "\tHostName $DEVICE_IP"
      echo -e "\tHostKeyAlgorithms +ssh-dss"
      echo -e "\tPubkeyAcceptedAlgorithms +ssh-rsa"
      echo -e "\tKexAlgorithms +diffie-hellman-group1-sha1"
      echo -e "\tCiphers aes128-ctr,aes192-ctr,aes256-ctr,aes128-cbc,3des-cbc"
      echo -e "\tAddKeysToAgent yes"
      echo -e "\tIdentityFile $SSH_PUBLIC_KEY_PATH_AND_NAME"
      echo -e "\tIdentitiesOnly yes"
    ) | xargs -d "\n" -n 1 >> $file
  fi
}
