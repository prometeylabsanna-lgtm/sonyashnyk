#!/usr/bin/env bash
# Друкує аргументи compose: HTTP, доки немає сертифіката; HTTPS — після certbot.
set -euo pipefail

DOMAIN="${DOMAIN:-sonjashnik.ua}"
if [ -f "/etc/letsencrypt/live/${DOMAIN}/fullchain.pem" ]; then
  echo "-f docker-compose.prod.yml"
else
  echo "-f docker-compose.yml"
fi
