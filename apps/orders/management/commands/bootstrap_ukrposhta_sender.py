"""Одноразове створення клієнта-відправника Укрпошти з env."""

from django.core.management.base import BaseCommand, CommandError

from apps.orders.ukrposhta import UkrposhtaError
from apps.orders.ukrposhta_shipments import bootstrap_sender_client


class Command(BaseCommand):
    help = "Створює відправника Укрпошти (eCom) і друкує UUID для .env"

    def handle(self, *args, **options):
        try:
            result = bootstrap_sender_client()
        except UkrposhtaError as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(self.style.SUCCESS("Відправника створено."))
        self.stdout.write(f"UKRPOSHTA_SENDER_UUID={result['uuid']}")
        self.stdout.write(f"UKRPOSHTA_SENDER_ADDRESS_ID={result['address_id']}")
        self.stdout.write("Додайте ці значення в .env і перезапустіть web.")
