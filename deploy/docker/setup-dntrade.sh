#!/usr/bin/env bash
# Добігати setup DNTrade на проді (коли SSH знову доступний).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
HOST="${DEPLOY_HOST:-root@206.189.60.124}"
SSH_KEY="${SSH_KEY:-$HOME/.ssh/id_ed25519}"
SSH=(ssh -o BatchMode=yes -o ConnectTimeout=15 -i "$SSH_KEY" "$HOST")
RSYNC=(rsync -avz -e "ssh -i $SSH_KEY -o BatchMode=yes -o ConnectTimeout=15")
DEST=/var/www/sonyashnyk
API_KEY="${DNTRADE_API_KEY:-ycyyi3rl8tdox1y1az1cuou2fdbwcqvfydpgbrqctxoq4ohed0kl}"
STORE_ID="${DNTRADE_STORE_ID:-9043f685-1aa5-49d5-af2d-c8777cf814f5}"

echo "==> rsync code"
"${RSYNC[@]}" \
  "$ROOT/apps/catalog/dntrade/" \
  "$HOST:$DEST/apps/catalog/dntrade/"
"${RSYNC[@]}" \
  "$ROOT/apps/catalog/management/commands/sync_dntrade.py" \
  "$HOST:$DEST/apps/catalog/management/commands/"
"${RSYNC[@]}" \
  "$ROOT/apps/catalog/migrations/0021_dntrade_fields.py" \
  "$HOST:$DEST/apps/catalog/migrations/"
"${RSYNC[@]}" \
  "$ROOT/apps/catalog/models.py" \
  "$ROOT/apps/catalog/admin.py" \
  "$HOST:$DEST/apps/catalog/"
"${RSYNC[@]}" \
  "$ROOT/config/settings.py" \
  "$HOST:$DEST/config/"
"${RSYNC[@]}" \
  "$ROOT/docker-compose.prod.yml" \
  "$HOST:$DEST/"
"${RSYNC[@]}" \
  "$ROOT/deploy/cron/" \
  "$HOST:$DEST/deploy/cron/"

echo "==> env + migrate + cron + sync"
"${SSH[@]}" "bash -s" <<REMOTE
set -euo pipefail
cd $DEST
if grep -q '^DNTRADE_API_KEY=' .env; then
  sed -i 's/^DNTRADE_API_KEY=.*/DNTRADE_API_KEY=$API_KEY/' .env
else
  printf '\n# Navkolo DNTrade\nDNTRADE_API_KEY=$API_KEY\n' >> .env
fi
if grep -q '^DNTRADE_STORE_ID=' .env; then
  sed -i 's/^DNTRADE_STORE_ID=.*/DNTRADE_STORE_ID=$STORE_ID/' .env
else
  echo 'DNTRADE_STORE_ID=$STORE_ID' >> .env
fi
if grep -q '^DNTRADE_BASE_URL=' .env; then
  sed -i 's|^DNTRADE_BASE_URL=.*|DNTRADE_BASE_URL=https://api.dntrade.com.ua|' .env
else
  echo 'DNTRADE_BASE_URL=https://api.dntrade.com.ua' >> .env
fi
chmod +x deploy/cron/sync-dntrade.sh
grep '^DNTRADE_' .env
docker compose -f docker-compose.prod.yml up -d --build web dntrade-cron
docker compose -f docker-compose.prod.yml exec -T web python manage.py migrate catalog --noinput
echo "==> full sync without images (long)"
docker compose -f docker-compose.prod.yml exec -T web python manage.py sync_dntrade --skip-images
docker compose -f docker-compose.prod.yml ps
REMOTE

echo "==> DONE"
