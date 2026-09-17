from django.core.management.base import BaseCommand

from apps.core.block_defaults import (
    get_block_content_type,
    get_block_default,
    get_block_label,
)
from apps.core.block_defaults_ru import get_block_default_ru
from apps.core.hero_slides import DEFAULT_HERO_SLIDES, ensure_default_hero_slides
from apps.core.models import HeroSlide, SiteBlock, SiteSettings
from apps.core.site_content_registry import all_registry_block_keys


class Command(BaseCommand):
    help = "Ідемпотентний seed SiteBlock + HeroSlide + SiteSettings (+ RU)"

    def handle(self, *args, **options):
        settings = SiteSettings.get_solo()
        updated_settings = []
        if not settings.address_ru:
            settings.address_ru = "г. Киев, Крещатик 1"
            updated_settings.append("address_ru")
        if not settings.work_hours_ru:
            settings.work_hours_ru = "Пн–Сб 9:00–18:00"
            updated_settings.append("work_hours_ru")
        if updated_settings:
            settings.save(update_fields=updated_settings)

        created_blocks = 0
        filled_ru = 0
        for page, key in all_registry_block_keys():
            defaults = {
                "label": get_block_label(page, key),
                "content_type": get_block_content_type(page, key),
                "text_html": get_block_default(page, key),
                "text_html_ru": get_block_default_ru(page, key),
            }
            block, was_created = SiteBlock.objects.get_or_create(
                page=page,
                key=key,
                defaults=defaults,
            )
            if was_created:
                created_blocks += 1
            elif not (block.text_html_ru or "").strip():
                ru = get_block_default_ru(page, key)
                if ru:
                    block.text_html_ru = ru
                    block.save(update_fields=["text_html_ru"])
                    filled_ru += 1

        slides = ensure_default_hero_slides()
        hero_ru = 0
        for idx, slide in enumerate(HeroSlide.objects.order_by("order", "id")):
            if idx >= len(DEFAULT_HERO_SLIDES):
                break
            src = DEFAULT_HERO_SLIDES[idx]
            fields = []
            mapping = (
                ("title_ru", "title_ru"),
                ("lead_ru", "lead_ru"),
                ("cta1_text_ru", "cta1_text_ru"),
                ("cta2_text_ru", "cta2_text_ru"),
                ("alt_text_ru", "title_ru"),
            )
            for attr, key in mapping:
                if not getattr(slide, attr, ""):
                    val = src.get(key, "")
                    if val:
                        setattr(slide, attr, val)
                        fields.append(attr)
            if fields:
                slide.save(update_fields=fields)
                hero_ru += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Seed OK: blocks +{created_blocks}, ru filled {filled_ru}, "
                f"hero +{slides}, hero ru {hero_ru}"
            )
        )
