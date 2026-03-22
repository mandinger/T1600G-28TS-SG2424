# T1600G-28TS-SG2424
Scripts to Setup the Switch Tplink SFP T1600G-28TS-SG2424.

## Dockerized Web Control Plane (v1)
This repository now includes a FastAPI web/API control plane that wraps the existing shell utilities for multi-switch operations.

### Features
- Docker Compose deployment with `network_mode: host`.
- Server-rendered web UI with RBAC login (`admin`, `operator`, `viewer`).
- SQLite data model for:
- `users`, `roles`, `switches`, `encrypted_credentials`, `switch_profiles`, `jobs`, `job_events`.
- Action registry exposing all 27 utilities.
- Risky operations are visible but disabled in v1:
- `upgrade_firmware`, `reboot`, `factory_reset`, `restore_latest_backup`.
- Per-switch execution lock: only one active job per switch at a time.

### Run with Docker Compose
1. Create `.env` from `.env.example` and set at least:
```bash
cp .env.example .env
```
2. Build and start:
```bash
docker compose up --build -d
```
3. Open:
`http://localhost:8000/ui`

Default bootstrap admin credentials come from:
- `APP_BOOTSTRAP_ADMIN_USERNAME`
- `APP_BOOTSTRAP_ADMIN_PASSWORD`

### API Endpoints
- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET/POST /api/switches`
- `GET/PATCH/DELETE /api/switches/{switch_id}`
- `GET/PUT /api/switches/{switch_id}/profile`
- `GET /api/actions`
- `POST /api/switches/{switch_id}/actions/{action_key}`
- `GET /api/jobs`
- `GET /api/jobs/{job_id}`
- `GET /api/jobs/{job_id}/logs`

#### Options you can execute:
0. Exit.
1. Setup Switch from Zero to Hero!
2. Prepare Host Machine.
3. Set static IP
4. Enable SSH.
5. Enable Password Encryption.
6. Create Bot User.
7. Set Link Aggregation Control Protocol (LACP).
8. Set Vlans.
9. Set PVID.
10. Enable IPV4 routing.
11. Set Interfaces.
12. Set IPv4 Static Routing to Default Gateway.
13. Set System Time from NTP Server.
14. Enable HTTPS.
15. Disable HTTP.
16. Set Jumbo Size.
17. Enable DoS Defend.
18. Set Device Description.
19. Set SDM Preference.
20. Enable Remote Logging.
21. Disable Telnet.
22. Enable EEE.
23. Upgrade Firmware.
24. Backup.
25. Reboot.
26. Reset with Factory Settings.
27. Restore Settings from Latest Backup.

#### Credentials:
1. Create a strong password for the admin user and store it in the secret manager. After you hit enter, a password will be asked.
```bash
    secret-tool store --label="switch-user-admin" password "switch-user-admin"
```

2. Retrieve the admin's password.
```bash
    secret-tool lookup password "switch-user-admin"
```

#### Contact-Info:
1. Add your email as the contact-info, but in order to avoid spammers, encode it in base64.
```bash
    echo "your-email@something.com" | base64
```

2. Decode your email from base64 to use it as the contact-info.
```bash
    echo "eW91ci1lbWFpbEBzb21ldGhpbmcuY29tCg==" | base64 --decode
```

#### Add ip in the hosts file:
1. Add the switch's ip in the hosts file so we can connect using its name and not its ip.
```bash
    sudo nano /etc/hosts
    192.168.0.3 switch.lan.homelab
```

#### Run:
1. Run the application on the terminal.
```bash
    ./Setup.sh
    or
    ./Setup.sh <option number>
```
