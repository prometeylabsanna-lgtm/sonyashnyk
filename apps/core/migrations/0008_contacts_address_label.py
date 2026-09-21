from django.db import migrations


def rename_address_label(apps, schema_editor):
    SiteBlock = apps.get_model("core", "SiteBlock")
    block = SiteBlock.objects.filter(page="contacts", key="label_address").first()
    if block is None:
        return
    updates = []
    if (block.text_html or "").strip() == "Точка видачі":
        block.text_html = "Адреса"
        updates.append("text_html")
    if (block.text_html_ru or "").strip() == "Точка выдачи":
        block.text_html_ru = "Адрес"
        updates.append("text_html_ru")
    if updates:
        block.save(update_fields=updates)


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0007_pickup_points"),
    ]

    operations = [
        migrations.RunPython(rename_address_label, migrations.RunPython.noop),
    ]
