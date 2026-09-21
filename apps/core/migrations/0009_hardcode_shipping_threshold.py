from django.db import migrations

_PLACEHOLDER = "{threshold}"


def replace_threshold_placeholder(apps, schema_editor):
    SiteBlock = apps.get_model("core", "SiteBlock")
    SiteSettings = apps.get_model("core", "SiteSettings")
    settings = SiteSettings.objects.filter(pk=1).first()
    amount = str(getattr(settings, "free_shipping_threshold", None) or 1500)
    for block in SiteBlock.objects.all().iterator():
        updates = []
        for field in ("text_html", "text_html_ru"):
            value = getattr(block, field, None) or ""
            if _PLACEHOLDER in value:
                setattr(block, field, value.replace(_PLACEHOLDER, amount))
                updates.append(field)
        if updates:
            block.save(update_fields=updates)


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0008_contacts_address_label"),
    ]

    operations = [
        migrations.RunPython(replace_threshold_placeholder, migrations.RunPython.noop),
    ]
