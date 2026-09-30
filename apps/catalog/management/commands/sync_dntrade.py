"""Синхронізація каталогу з Navkolo DNTrade.

Приклади:
  python3 manage.py sync_dntrade --list-stores
  python3 manage.py sync_dntrade --dry-run --limit 20
  python3 manage.py sync_dntrade --skip-images
  python3 manage.py sync_dntrade
"""

from __future__ import annotations

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.catalog.dntrade.client import DntradeApiError, DntradeClient
from apps.catalog.dntrade.sync import sync_catalog


class Command(BaseCommand):
    help = "Імпорт товарів / цін / залишків / фото з Navkolo DNTrade."

    def add_arguments(self, parser):
        parser.add_argument(
            "--list-stores",
            action="store_true",
            help="Показати склади з API і вийти.",
        )
        parser.add_argument(
            "--store-id",
            default="",
            help="UUID складу для каталогу (інакше DNTRADE_STORE_ID з .env).",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Обмежити кількість товарів (для тесту).",
        )
        parser.add_argument(
            "--offset",
            type=int,
            default=0,
            help="Зміщення у списку товарів DNTrade (для тесту).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Лише прочитати API, без запису в БД.",
        )
        parser.add_argument(
            "--skip-images",
            action="store_true",
            help="Не завантажувати фото.",
        )

    def handle(self, *args, **options):
        try:
            client = DntradeClient()
        except DntradeApiError as exc:
            raise CommandError(str(exc)) from exc

        if options["list_stores"]:
            self._print_stores(client)
            return

        store_id = (options["store_id"] or getattr(settings, "DNTRADE_STORE_ID", "") or "").strip()
        if not store_id:
            self.stdout.write(self.style.WARNING(
                "DNTRADE_STORE_ID порожній — товари без store_id часто без категорій. "
                "Спочатку: python3 manage.py sync_dntrade --list-stores"
            ))

        self.stdout.write(
            f"Старт sync DNTrade (store={store_id or '—'}, "
            f"limit={options['limit']}, offset={options['offset']}, "
            f"dry_run={options['dry_run']}, "
            f"skip_images={options['skip_images']})"
        )

        try:
            stats = sync_catalog(
                client=client,
                store_id=store_id or None,
                dry_run=options["dry_run"],
                limit=options["limit"],
                offset=options["offset"],
                skip_images=options["skip_images"],
                progress=lambda msg: self.stdout.write(f"  … {msg}"),
            )
        except DntradeApiError as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(self.style.SUCCESS(
            "Готово: "
            f"fetched={stats.products_fetched}, "
            f"created={stats.products_created}, "
            f"updated={stats.products_updated}, "
            f"variants={stats.variants_upserted}, "
            f"images={stats.images_downloaded}, "
            f"skipped={stats.skipped}, "
            f"errors={len(stats.errors)}"
        ))
        for err in stats.errors[:20]:
            self.stdout.write(self.style.ERROR(f"  ! {err}"))

    def _print_stores(self, client: DntradeClient) -> None:
        stores = client.list_stores()
        if not stores:
            self.stdout.write("Складів немає.")
            return
        self.stdout.write("Склади DNTrade (вкажіть DNTRADE_STORE_ID у .env):")
        for store in stores:
            sell = "sell" if store.get("is_sell") else "stock"
            self.stdout.write(
                f"  {store.get('id')}  |  {store.get('title')}  |  "
                f"{sell}  |  status={store.get('status')}  |  {store.get('address') or '—'}"
            )
        current = getattr(settings, "DNTRADE_STORE_ID", "") or ""
        if current:
            self.stdout.write(f"\nПоточний DNTRADE_STORE_ID={current}")
        else:
            self.stdout.write(
                "\nРекомендація для каталогу: "
                "A8C66C69-8DDC-4711-96EC-1D079C3FD303 (Основний)"
            )
