from django.test import TestCase

from apps.core.site_content_registry import CONTENT_SECTIONS, all_registry_block_keys


class SiteContentRegistryTests(TestCase):
    def test_unique_block_keys(self):
        keys = all_registry_block_keys()
        self.assertEqual(len(keys), len(set(keys)))

    def test_unique_admin_model_names(self):
        names = [s.admin_model_name for s in CONTENT_SECTIONS]
        self.assertEqual(len(names), len(set(names)))

    def test_visibility_keys_in_blocks(self):
        for section in CONTENT_SECTIONS:
            if not section.visibility_key:
                continue
            self.assertIn(
                (section.page_slug, section.visibility_key),
                section.blocks,
                msg=section.admin_model_name,
            )
