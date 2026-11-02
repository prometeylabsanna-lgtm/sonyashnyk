"""Тести резолву іконок: шапка vs плитки головної."""

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.templatetags.static import static

from apps.catalog.icons import (
    HOME_CATEGORY_ICONS,
    HOME_CATEGORY_TILES,
    NAV_CATEGORY_ICONS,
    category_icon_url,
)
from apps.catalog.models import Category
from apps.core.block_defaults import STATIC_FALLBACKS
from apps.core.models import SiteBlock


class CategoryIconsSplitTests(TestCase):
    def setUp(self):
        self.root = Category.objects.create(
            name="Насіння",
            slug="nasinnia",
            order=1,
            is_active=True,
        )

    def test_home_tiles_registered_in_cms_defaults(self):
        for _slug, key, _label, path in HOME_CATEGORY_TILES:
            self.assertEqual(STATIC_FALLBACKS.get(("home", key)), path)

    def test_nav_uses_header_static_when_no_upload(self):
        url = category_icon_url(self.root, for_nav=True)
        self.assertEqual(url, static(NAV_CATEGORY_ICONS["nasinnia"]))

    def test_home_uses_watercolor_static_when_no_cms(self):
        url = category_icon_url(self.root, for_nav=False)
        self.assertEqual(url, static(HOME_CATEGORY_ICONS["nasinnia"]))

    def test_nav_upload_does_not_override_home_tile(self):
        png = SimpleUploadedFile(
            "nav-icon.png",
            b"\x89PNG\r\n\x1a\n" + b"\x00" * 32,
            content_type="image/png",
        )
        self.root.image = png
        self.root.save()

        nav_url = category_icon_url(self.root, for_nav=True)
        home_url = category_icon_url(self.root, for_nav=False)

        self.assertTrue(nav_url)
        self.assertNotEqual(nav_url, home_url)
        self.assertEqual(home_url, static(HOME_CATEGORY_ICONS["nasinnia"]))

    def test_cms_tile_overrides_home_static_only(self):
        png = SimpleUploadedFile(
            "tile.png",
            b"\x89PNG\r\n\x1a\n" + b"\x00" * 32,
            content_type="image/png",
        )
        block = SiteBlock.objects.create(
            page="home",
            key="categories_tile_nasinnia_image",
            label="Плитка: Насіння",
            content_type=SiteBlock.ContentType.IMAGE,
            image=png,
        )

        home_url = category_icon_url(self.root, for_nav=False)
        nav_url = category_icon_url(self.root, for_nav=True)

        self.assertEqual(home_url, block.image.url)
        self.assertEqual(nav_url, static(NAV_CATEGORY_ICONS["nasinnia"]))
