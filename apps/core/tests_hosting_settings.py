"""Після прибирання Vercel рантайм лишається на Postgres і DO-шляхах."""

from django.conf import settings
from django.test import SimpleTestCase


class DigitalOceanRuntimeTests(SimpleTestCase):
    def test_postgres_and_local_media_without_vercel_switch(self):
        self.assertFalse(hasattr(settings, "IS_VERCEL"))
        engine = settings.DATABASES["default"]["ENGINE"]
        self.assertIn("postgresql", engine)
        self.assertNotIn("sqlite", engine)
        self.assertTrue(str(settings.MEDIA_ROOT).endswith("media"))
        hosts = ",".join(settings.ALLOWED_HOSTS).lower()
        self.assertNotIn("vercel.app", hosts)
        self.assertIn(
            "whitenoise.middleware.WhiteNoiseMiddleware",
            settings.MIDDLEWARE,
        )
        self.assertIn(
            "whitenoise",
            settings.STORAGES["staticfiles"]["BACKEND"],
        )
        self.assertEqual(
            settings.DATABASES["default"]["OPTIONS"].get("connect_timeout"),
            3,
        )
        self.assertNotIn("sslmode", settings.DATABASES["default"]["OPTIONS"])
