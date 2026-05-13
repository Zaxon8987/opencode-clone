name: deploy-check
description: Pre-deploy readiness checklist, rollback planning, health checks
instructions: |
  Before deployment, verify:
  1. All tests pass (unit, integration, e2e)
  2. No lint/type errors
  3. Database migrations are zero-downtime
  4. Health check endpoints respond correctly
  5. Rollback plan exists
  6. Feature flags are in place for risky changes
  After deploy: monitor logs, error rates, and latency for 10 minutes.
