from django.test import Client, TestCase

from apps.core.models import PickupPoint, SiteSettings
from apps.core.pickup_points import ensure_default_pickup_points, get_pickup_points


class PickupPointTests(TestCase):
    def test_seed_four_placeholders_once(self):
        self.assertEqual(PickupPoint.objects.count(), 4)
        self.assertEqual(ensure_default_pickup_points(), 0)
        self.assertEqual(
            PickupPoint.objects.filter(address="м. Київ, адреса уточнюється").count(),
            4,
        )

    def test_inactive_hidden_and_phone_falls_back(self):
        ensure_default_pickup_points()
        SiteSettings.objects.update_or_create(
            pk=1,
            defaults={"phone": "+38 (067) 000-00-01", "phone_raw": "+380670000001", "work_hours": "Пн–Сб 9:00–18:00"},
        )
        first = PickupPoint.objects.order_by("order", "id").first()
        first.is_active = False
        first.save(update_fields=["is_active"])
        points = get_pickup_points(lang="uk")
        self.assertEqual(len(points), 3)
        self.assertEqual(points[0].phone, "+38 (067) 000-00-01")
        self.assertEqual(points[0].phone_raw, "+380670000001")
        self.assertEqual(points[0].hours, "Пн–Сб 9:00–18:00")

    def test_contacts_page_lists_stores_and_map(self):
        SiteSettings.objects.update_or_create(
            pk=1,
            defaults={"instagram_url": "https://instagram.com/sonyashnyk"},
        )
        response = Client().get("/kontakty/")
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn("Крамниця 1", html)
        self.assertIn("Крамниця 4", html)
        self.assertIn("https://instagram.com/sonyashnyk", html)
        self.assertIn("Telegram", html)
        self.assertIn("contacts-store__map", html)
        self.assertIn("maps.google.com/maps", html)
        self.assertIn("<iframe", html)

    def test_custom_map_embed_iframe_src(self):
        from apps.core.pickup_points import extract_map_embed_src, map_src_for_raw

        raw = (
            '<iframe src="https://www.google.com/maps/embed?pb=!1m18!1m12" '
            'width="600" height="450" style="border:0;" allowfullscreen></iframe>'
        )
        self.assertEqual(
            extract_map_embed_src(raw),
            "https://www.google.com/maps/embed?pb=!1m18!1m12",
        )
        self.assertIn("google.com", map_src_for_raw(""))
        point = PickupPoint.objects.order_by("order", "id").first()
        point.map_embed = raw
        point.save(update_fields=["map_embed"])
        html = Client().get("/kontakty/").content.decode()
        self.assertIn("https://www.google.com/maps/embed?pb=!1m18!1m12", html)
        self.assertNotIn("javascript:", html)
