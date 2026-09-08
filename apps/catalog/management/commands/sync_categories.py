"""Синхронізує дерево категорій з apps.catalog.category_tree.

Використання: python3 manage.py sync_categories
"""

from django.core.management.base import BaseCommand

from apps.catalog.category_tree import CATEGORY_TREE
from apps.catalog.models import Category
from apps.core.utils import slugify_uk


class Command(BaseCommand):
    help = "Створює/оновлює повне дерево категорій (до 3 рівнів)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--deactivate-missing",
            action="store_true",
            help="Деактивувати категорії, яких немає в дереві (обережно).",
        )

    def handle(self, *args, **options):
        seen_ids = set()
        for order, node in enumerate(CATEGORY_TREE):
            self._sync_node(node, parent=None, order=order, seen_ids=seen_ids)

        if options["deactivate_missing"]:
            qs = Category.objects.exclude(pk__in=seen_ids).filter(is_active=True)
            n = qs.update(is_active=False)
            self.stdout.write(f"Деактивовано відсутніх: {n}")

        self.stdout.write(self.style.SUCCESS(
            f"Синхронізовано категорій: {len(seen_ids)}"
        ))

    def _sync_node(self, node, parent, order, seen_ids):
        if isinstance(node, str):
            name, children = node, []
        else:
            name, children = node[0], node[1]

        slug = self._slug_for(name, parent)
        obj = self._find_existing(name, slug, parent)

        if obj is None:
            obj = Category(name=name, parent=parent, slug=slug, order=order)
            obj.save()
            created = True
        else:
            created = False
            changed = False
            if obj.name != name:
                obj.name = name
                changed = True
            if obj.parent_id != (parent.pk if parent else None):
                obj.parent = parent
                changed = True
            if obj.order != order:
                obj.order = order
                changed = True
            if not obj.is_active:
                obj.is_active = True
                changed = True
            if obj.slug != slug and not Category.objects.filter(slug=slug).exclude(pk=obj.pk).exists():
                obj.slug = slug
                changed = True
            if changed:
                obj.save()

        seen_ids.add(obj.pk)
        mark = "+" if created else "="
        self.stdout.write(f"  {mark} {obj.slug} ({obj.name})")

        for child_order, child in enumerate(children):
            self._sync_node(child, parent=obj, order=child_order, seen_ids=seen_ids)

    def _find_existing(self, name, slug, parent):
        """Знаходить категорію для оновлення / переносу, без створення дублікатів."""
        obj = Category.objects.filter(slug=slug).first()
        if obj is not None:
            return obj

        if parent is not None:
            obj = Category.objects.filter(name=name, parent=parent).first()
            if obj is not None:
                return obj

        if parent is None:
            return Category.objects.filter(name=name, parent__isnull=True).first()

        # «Інші» завжди унікальні під батьком — не підхоплюємо чужі
        base = slugify_uk(name) or "item"
        if base == "inshi":
            return None

        # Перенос: та сама назва / базовий slug з іншим parent (напр. був корінь)
        obj = Category.objects.filter(slug=base).first()
        if obj is not None:
            return obj
        return Category.objects.filter(name=name).order_by("id").first()

    def _slug_for(self, name, parent):
        base = slugify_uk(name) or "item"
        # Унікальні «Інші» під різними батьками
        if base == "inshi" and parent is not None:
            return f"inshi-{parent.slug}"
        return base
