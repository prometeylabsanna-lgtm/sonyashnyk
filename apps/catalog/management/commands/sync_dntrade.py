"""Синхронізація каталогу з Navkolo DNTrade.

Приклади:
  python3 manage.py sync_dntrade --list-stores
  python3 manage.py sync_dntrade --dry-run --limit 20
  python3 manage.py sync_dntrade --skip-images --purge-missing   # без фото
  python3 manage.py sync_dntrade --purge-missing                 # з фото (cron 03:15 Kyiv)
"""

from __future__ import annotations

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.catalog.dntrade.client import DntradeApiError, DntradeClient
from apps.catalog.dntrade.sync import DEFAULT_CATALOG_STORE_ID, sync_catalog


class Command(BaseCommand):
    help = "Імпорт товарів / цін / залишків / фото з Navkolo DNTrade (склад Перемоги)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--list-stores",
            action="store_true",
            help="Показати склади з API і вийти.",
        )
        parser.add_argument(
            "--store-id",
            default="",
            help="UUID складу для каталогу (інакше DNTRADE_STORE_ID / Перемоги 5).",
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
        parser.add_argument(
            "--purge-missing",
            action="store_true",
            help="Видалити з сайту DNTrade-товари, яких немає в поточному імпорті.",
        )

    def handle(self, *args, **options):
        try:
            client = DntradeClient()
        except DntradeApiError as exc:
            raise CommandError(str(exc)) from exc

        if options["list_stores"]:
            self._print_stores(client)
            return

        store_id = (
            options["store_id"]
            or getattr(settings, "DNTRADE_STORE_ID", "")
            or DEFAULT_CATALOG_STORE_ID
        ).strip()

        self.stdout.write(
            f"Старт sync DNTrade (store={store_id}, "
            f"limit={options['limit']}, offset={options['offset']}, "
            f"dry_run={options['dry_run']}, "
            f"skip_images={options['skip_images']}, "
            f"purge_missing={options['purge_missing']})"
        )

        try:
            stats = sync_catalog(
                client=client,
                store_id=store_id,
                dry_run=options["dry_run"],
                limit=options["limit"],
                offset=options["offset"],
                skip_images=options["skip_images"],
                purge_missing=options["purge_missing"],
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
            f"excluded={stats.skipped_excluded}, "
            f"purged={stats.purged}, "
            f"errors={len(stats.errors)}"
        ))
        for err in stats.errors[:20]:
            self.stdout.write(self.style.ERROR(f"  ! {err}"))

    def _print_stores(self, client: DntradeClient) -> None:
        stores = client.list_stores()
        if not stores:
            self.stdout.write("Складів немає.")
            return
        self.stdout.write("Склади DNTrade (DNTRADE_STORE_ID у .env):")
        for store in stores:
            sell = "sell" if store.get("is_sell") else "stock"
            self.stdout.write(
                f"  {store.get('id')}  |  {store.get('title')}  |  "
                f"{sell}  |  status={store.get('status')}  |  {store.get('address') or '—'}"
            )
        current = getattr(settings, "DNTRADE_STORE_ID", "") or DEFAULT_CATALOG_STORE_ID
        self.stdout.write(f"\nПоточний / дефолт: {current} (Перемоги 5)")
