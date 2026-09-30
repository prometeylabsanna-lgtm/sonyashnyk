#!/usr/bin/env bash
# Щоденний імпорт каталогу з DNTrade (з фото), о 03:15 Europe/Kyiv.
set -euo pipefail
cd /app
exec python manage.py sync_dntrade --purge-missing
