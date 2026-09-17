"""Конвертує static PNG/JPG у WebP і (опційно) оновлює посилання в коді.

Використання:
  ./venv/bin/python3 manage.py convert_static_to_webp
  ./venv/bin/python3 manage.py convert_static_to_webp --dry-run
"""

from __future__ import annotations

from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from apps.core.image_webp import (
    IMAGE_EXTENSIONS,
    convert_path_to_webp,
    should_skip_static_path,
)

SKIP_DIR_PARTS = {"venv", ".git", "node_modules", "__pycache__", "media", ".cursor"}


class Command(BaseCommand):
    help = "Конвертує static/img PNG/JPG → WebP і оновлює посилання в коді."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Лише показати, що буде змінено.",
        )
        parser.add_argument(
            "--keep-originals",
            action="store_true",
            help="Не видаляти PNG/JPG після конвертації.",
        )
        parser.add_argument(
            "--skip-code",
            action="store_true",
            help="Не замінювати розширення у коді/шаблонах.",
        )

    def handle(self, *args, **options):
        dry = options["dry_run"]
        delete_original = not options["keep_originals"]
        static_root = Path(settings.BASE_DIR) / "static" / "img"
        if not static_root.is_dir():
            self.stderr.write(f"Немає {static_root}")
            return

        converted: list[tuple[Path, Path]] = []
        for path in sorted(static_root.rglob("*")):
            if not path.is_file():
                continue
            if should_skip_static_path(path):
                self.stdout.write(f"skip favicon: {path.relative_to(settings.BASE_DIR)}")
                continue
            if path.suffix.lower() not in (IMAGE_EXTENSIONS - {".webp"}):
                continue
            if dry:
                self.stdout.write(f"would convert: {path.relative_to(settings.BASE_DIR)}")
                converted.append((path, path.with_suffix(".webp")))
                continue
            dest = convert_path_to_webp(path, delete_original=delete_original)
            if dest:
                converted.append((path, dest))
                self.stdout.write(f"ok: {path.name} → {dest.name}")

        self.stdout.write(self.style.SUCCESS(f"Файлів: {len(converted)}"))

        if options["skip_code"] or not converted:
            return

        replacements = {
            src.name: dest.name
            for src, dest in converted
            if src.suffix.lower() != ".webp"
        }
        # також загальні заміни розширень для шляхів img/
        if dry:
            self.stdout.write(f"would update code refs for {len(replacements)} filenames")
            return

        updated_files = 0
        base = Path(settings.BASE_DIR)
        for path in base.rglob("*"):
            if not path.is_file():
                continue
            if any(part in SKIP_DIR_PARTS for part in path.parts):
                continue
            if path.suffix.lower() not in {".py", ".html", ".css", ".js", ".md"}:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            new = text
            for old_name, new_name in replacements.items():
                if old_name in new:
                    new = new.replace(old_name, new_name)
            if new != text:
                path.write_text(new, encoding="utf-8")
                updated_files += 1
                self.stdout.write(f"  code: {path.relative_to(base)}")
        self.stdout.write(self.style.SUCCESS(f"Оновлено файлів коду: {updated_files}"))
