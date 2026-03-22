# Dockerized Multi-Switch Management Platform Plan

Implemented scope in this repository:
- FastAPI backend + server-rendered web UI
- SQLite persistence for users, roles, switches, encrypted credentials, profiles, jobs, and events
- Script-wrapper action runner for the existing Bash/Expect automation
- Docker + Docker Compose deployment using host networking
- Risky actions visible but disabled in v1 (`firmware`, `factory reset`, `restore backup`, `reboot`)

See `webapp/`, `scripts/run_switch_action.sh`, `Dockerfile`, and `docker-compose.yml` for implementation details.
