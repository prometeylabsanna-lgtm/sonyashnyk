#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

mkdir -p /var/backups/sonyashnyk
STAMP="$(date +%F-%H%M)"
OUT="/var/backups/sonyashnyk/db-${STAMP}.sql.gz"

read -r -a COMPOSE_FILE <<< "$(bash deploy/docker/compose-file.sh)"
docker compose "${COMPOSE_FILE[@]}" exec -T db \
  sh -c 'pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB"' | gzip > "$OUT"

echo "$OUT"
find /var/backups/sonyashnyk -name 'db-*.sql.gz' -mtime +14 -delete
