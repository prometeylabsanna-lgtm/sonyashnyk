from django.db import migrations, models


def create_solo(apps, schema_editor):
    SiteSettings = apps.get_model("core", "SiteSettings")
    SiteSettings.objects.get_or_create(pk=1)


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0002_review_city"),
    ]

    operations = [
        migrations.CreateModel(
            name="SiteSettings",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("instagram_url", models.URLField(blank=True, default="", verbose_name="Instagram")),
                ("tiktok_url", models.URLField(blank=True, default="", verbose_name="TikTok")),
                ("telegram_url", models.URLField(blank=True, default="", verbose_name="Telegram")),
            ],
            options={
                "verbose_name": "Налаштування сайту",
                "verbose_name_plural": "Налаштування сайту",
            },
        ),
        migrations.RunPython(create_solo, migrations.RunPython.noop),
    ]
