#!/usr/bin/env bash
# Щоденний імпорт каталогу з DNTrade (cron / docker).
set -euo pipefail
cd /app
exec python manage.py sync_dntrade
