# Runbook — Observability & Alerts (Stage 3)

## Alerts
### Failover Detected (Blue → Green or Green → Blue)
**Meaning:** The log-watcher saw requests now served by the other pool (pool header changed).  
**Action:**
1. Check `docker ps` and container logs:
   - `docker logs app_blue` and `docker logs app_green`
2. Inspect Nginx access logs: `tail -n 200 ./logs/access.log | grep pool`
3. If primary is unhealthy, keep Green active and investigate app logs; if primary recovered, allow it to return to active.

### High Error Rate (> ERROR_RATE_THRESHOLD)
**Meaning:** > threshold % of requests in last WINDOW_SIZE were 5xx.  
**Action:**
1. Check upstream logs for increasing 5xx (app_blue/app_green).
2. If errors are from primary, consider switching ACTIVE_POOL to the healthy backend:
   - Edit `.env` → change `ACTIVE_POOL=green` and reload Nginx:
     ```bash
     docker compose up -d --force-recreate nginx
     ```
3. Open the app to run smoke tests.

## Maintenance mode
Set `MAINTENANCE_MODE=1` in `.env` to temporarily suppress alerts (useful when running planned chaos drills). After maintenance, set back to `0`.

## How to verify alerts
1. Trigger chaos: `curl -X POST http://localhost:8081/chaos/start?mode=error`
2. Confirm failover via `curl http://localhost:8080/version` and check Slack for a Failover alert.
3. Simulate 5xx spike (generate many failing requests) and verify a High Error Rate alert.

## Notes
- Alerts are rate-limited by `ALERT_COOLDOWN_SEC` to prevent spam.
- All configuration is in `.env`.
