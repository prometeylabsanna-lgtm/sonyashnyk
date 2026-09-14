"""
Vercel Python entrypoint (WSGI → Django).

Без env на Vercel міграції можуть не пройти (Postgres недоступний) —
тоді сайт все одно піднімається з порожніми даними.
"""

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

from django.core.wsgi import get_wsgi_application

app = get_wsgi_application()

try:
    from django.core.management import call_command

    call_command("migrate", interactive=False, run_syncdb=False)
except Exception:
    pass
