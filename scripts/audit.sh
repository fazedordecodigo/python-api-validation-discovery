#!/bin/sh
# Auditoria: mesmos argv de loop.yaml (bandit, gitleaks, pip-audit, trivy).
set -eu

if [ "$#" -eq 0 ]; then
  bandit -q -r .
  trivy fs --offline-scan --skip-db-update .
else
  bandit -q -r "$@"
  trivy fs --offline-scan --skip-db-update "$@"
fi

gitleaks detect --no-git --redact --no-banner --source .
pip-audit
