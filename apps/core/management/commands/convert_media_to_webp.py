"""Конвертує вже завантажені media-зображення в WebP і оновлює шляхи в БД.

  ./venv/bin/python3 manage.py convert_media_to_webp
"""

from __future__ import annotations

from pathlib import Path

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from apps.catalog.models import Category, ProductImage
from apps.core.image_webp import convert_file_to_webp_content, is_already_webp
from apps.core.models import HeroSlide, SiteBlock


class Command(BaseCommand):
    help = "Конвертує існуючі ImageField у media → WebP."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        dry = options["dry_run"]
        total = 0
        for label, qs, field in (
            ("Category", Category.objects.exclude(image="").exclude(image__isnull=True), "image"),
            ("ProductImage", ProductImage.objects.exclude(image="").exclude(image__isnull=True), "image"),
            ("HeroSlide", HeroSlide.objects.exclude(image="").exclude(image__isnull=True), "image"),
            ("SiteBlock", SiteBlock.objects.exclude(image="").exclude(image__isnull=True), "image"),
        ):
            for obj in qs.iterator():
                f = getattr(obj, field)
                if not f or not f.name or is_already_webp(f.name):
                    continue
                total += 1
                if dry:
                    self.stdout.write(f"would: {label} {obj.pk} {f.name}")
                    continue
                try:
                    converted = convert_file_to_webp_content(f, original_name=f.name)
                except Exception as exc:
                    self.stderr.write(f"fail {label} {obj.pk}: {exc}")
                    continue
                if converted is None:
                    continue
                old_name = f.name
                # зберегти новий файл через поле (без повторної конвертації — вже webp)
                getattr(obj, field).save(converted.name, converted, save=False)
                obj.save(update_fields=[field])
                # прибрати старий файл, якщо лишився
                try:
                    storage = f.storage
                    if old_name != getattr(obj, field).name and storage.exists(old_name):
                        storage.delete(old_name)
                except Exception:
                    pass
                self.stdout.write(f"ok: {label}#{obj.pk} → {getattr(obj, field).name}")

        self.stdout.write(self.style.SUCCESS(f"Оброблено: {total}"))
