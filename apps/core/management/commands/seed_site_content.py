from django.core.management.base import BaseCommand

from apps.core.block_defaults import (
    get_block_content_type,
    get_block_default,
    get_block_label,
)
from apps.core.hero_slides import ensure_default_hero_slides
from apps.core.models import SiteBlock, SiteSettings
from apps.core.site_content_registry import all_registry_block_keys


class Command(BaseCommand):
    help = "Ідемпотентний seed SiteBlock + HeroSlide + SiteSettings solo"

    def handle(self, *args, **options):
        SiteSettings.get_solo()
        created_blocks = 0
        for page, key in all_registry_block_keys():
            _, was_created = SiteBlock.objects.get_or_create(
                page=page,
                key=key,
                defaults={
                    "label": get_block_label(page, key),
                    "content_type": get_block_content_type(page, key),
                    "text_html": get_block_default(page, key),
                },
            )
            if was_created:
                created_blocks += 1
        slides = ensure_default_hero_slides()
        self.stdout.write(
            self.style.SUCCESS(
                f"Seed OK: blocks +{created_blocks}, hero slides +{slides}"
            )
        )
