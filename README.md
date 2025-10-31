## Stage 3 — Observability & Alerts (Log-Watcher + Slack)

### Pre-reqs
- Docker and Docker Compose installed
- A Slack Incoming Webhook URL

### Setup
1. Copy `.env.example` → `.env` and fill `SLACK_WEBHOOK_URL` and any values you want to change.
2. Ensure `nginx.conf.template` is in repo root and `docker-compose.yml` is updated (as provided).
3. Start stack:
   ```bash
   docker compose up -d --build
