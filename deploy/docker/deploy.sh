#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

DOMAIN="${DOMAIN:-sonjashnik.ua}"

free_host_ports() {
  systemctl stop nginx "gunicorn-*" 2>/dev/null || true
  systemctl disable nginx "gunicorn-*" 2>/dev/null || true
}

read -r -a COMPOSE_FILE <<< "$(bash deploy/docker/compose-file.sh)"
COMPOSE=(docker compose "${COMPOSE_FILE[@]}")

echo "==> compose: ${COMPOSE[*]}"
free_host_ports

"${COMPOSE[@]}" up -d --build

echo "==> waiting for /healthz/"
ok=0
for _ in $(seq 1 60); do
  if [ -f "/etc/letsencrypt/live/${DOMAIN}/fullchain.pem" ]; then
    if curl -sfk --resolve "${DOMAIN}:443:127.0.0.1" "https://${DOMAIN}/healthz/" >/dev/null; then
      ok=1
      break
    fi
  elif curl -sf "http://127.0.0.1/healthz/" >/dev/null; then
    ok=1
    break
  fi
  sleep 5
done

echo "==> services"
"${COMPOSE[@]}" ps

if [ "$ok" -ne 1 ]; then
  echo "FATAL: /healthz/ не відповів. Останні логи web:"
  "${COMPOSE[@]}" logs --tail=80 web nginx || true
  exit 1
fi

echo "==> healthz OK"
