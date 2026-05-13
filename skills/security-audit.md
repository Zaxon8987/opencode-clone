name: security-audit
description: OWASP Top 10 audit, dependency scanning, secrets detection, threat modeling
instructions: |
  Run a security audit covering:
  1. Dependency vulnerabilities (npm audit, pip audit, trivy)
  2. Hardcoded secrets in source code
  3. OWASP Top 10: SQL injection, XSS, CSRF, auth bypass
  4. CI/CD pipeline security
  5. Dockerfile/container best practices
  Report findings with severity, location, and fix recommendation.
