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

    def test_contacts_page_lists_stores_and_drops_map(self):
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
        self.assertNotIn("contacts-map", html)
        self.assertNotIn("<iframe", html)
