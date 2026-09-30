#!/usr/bin/env bash
# Повернення резерву Monopay: прострочені pending + разові failed/refunded.
set -euo pipefail
cd /app
exec python manage.py release_monopay_stock --expired --failed
