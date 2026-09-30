from django.test import SimpleTestCase

from apps.core.templatetags.site_content import render_cms_rich


class CmsRichRenderTests(SimpleTestCase):
    def test_real_html_renders_tags(self):
        html = render_cms_rich("<p><strong>тест</strong></p><ul><li>один</li></ul>")
        self.assertIn("<strong>тест</strong>", html)
        self.assertIn("<li>один</li>", html)
        self.assertNotIn("&lt;p&gt;", html)

    def test_escaped_html_from_admin_is_unescaped(self):
        raw = "&lt;p&gt;&lt;strong&gt;тест тест&lt;/strong&gt;&lt;/p&gt; &lt;ul&gt; &lt;li&gt;тест&lt;/li&gt; &lt;/ul&gt;"
        html = render_cms_rich(raw)
        self.assertIn("<strong>тест тест</strong>", html)
        self.assertIn("<li>тест</li>", html)
        self.assertNotIn("&lt;p&gt;", html)
        self.assertNotIn("&amp;lt;", html)

    def test_plain_text_becomes_paragraph(self):
        html = render_cms_rich("Просто текст без тегів")
        self.assertEqual(html, "<p>Просто текст без тегів</p>")
