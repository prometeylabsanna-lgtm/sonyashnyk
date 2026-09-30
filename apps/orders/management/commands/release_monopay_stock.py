"""Повернення резерву залишку Monopay.

Приклади:
  python3 manage.py release_monopay_stock --expired
  python3 manage.py release_monopay_stock --failed
  python3 manage.py release_monopay_stock --expired --failed --dry-run
  python3 manage.py release_monopay_stock --order SN-XXXX
"""

from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError

from apps.orders.models import Order
from apps.orders.stock import release_order_stock, release_stale_monopay_orders, reserve_minutes


class Command(BaseCommand):
    help = (
        "Повертає залишок для Monopay: прострочені pending (--expired) "
        "та вже failed/refunded без повернення (--failed)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--expired",
            action="store_true",
            help=f"Pending Monopay старші за {reserve_minutes()} хв → failed + повернення.",
        )
        parser.add_argument(
            "--failed",
            action="store_true",
            help="Разове повернення для failed/refunded, де stock_released=False.",
        )
        parser.add_argument(
            "--minutes",
            type=int,
            default=None,
            help="Перевизначити поріг прострочення (хв) для --expired.",
        )
        parser.add_argument(
            "--order",
            default="",
            help="Номер конкретного замовлення.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Лише показати, що буде зроблено.",
        )

    def handle(self, *args, **options):
        order_number = (options["order"] or "").strip()
        do_expired = options["expired"]
        do_failed = options["failed"]
        dry_run = options["dry_run"]

        if not order_number and not do_expired and not do_failed:
            raise CommandError("Вкажіть --expired, --failed і/або --order.")

        if order_number:
            self._handle_one(order_number, dry_run=dry_run)
            return

        total = 0
        if do_expired:
            total += self._handle_expired(minutes=options["minutes"], dry_run=dry_run)
        if do_failed:
            total += self._handle_failed(dry_run=dry_run)

        prefix = "[dry-run] " if dry_run else ""
        self.stdout.write(self.style.SUCCESS(f"{prefix}Оброблено замовлень: {total}"))

    def _handle_one(self, order_number: str, *, dry_run: bool) -> None:
        order = Order.objects.filter(order_number=order_number).first()
        if not order:
            raise CommandError(f"Замовлення {order_number} не знайдено.")
        if order.payment_status == Order.PaymentStatus.PAID:
            raise CommandError(f"{order_number}: оплачено — залишок не повертаємо.")
        if order.stock_released:
            self.stdout.write(f"{order_number}: уже повернуто.")
            return
        if dry_run:
            self.stdout.write(f"[dry-run] {order_number}: буде повернуто.")
            return
        mark_failed = order.payment_status == Order.PaymentStatus.PENDING
        ok = release_order_stock(order, mark_failed=mark_failed)
        self.stdout.write(self.style.SUCCESS(f"{order_number}: {'повернуто' if ok else 'пропущено'}"))

    def _handle_expired(self, *, minutes: int | None, dry_run: bool) -> int:
        from datetime import timedelta

        from django.utils import timezone

        mins = minutes if minutes is not None else reserve_minutes()
        cutoff = timezone.now() - timedelta(minutes=mins)
        qs = Order.objects.filter(
            payment_method=Order.PaymentMethod.MONOPAY,
            payment_status=Order.PaymentStatus.PENDING,
            stock_released=False,
            created_at__lt=cutoff,
        )
        if dry_run:
            count = qs.count()
            for num in qs.values_list("order_number", flat=True)[:50]:
                self.stdout.write(f"[dry-run] expired → {num}")
            return count
        return release_stale_monopay_orders(minutes=mins)

    def _handle_failed(self, *, dry_run: bool) -> int:
        qs = Order.objects.filter(
            payment_method=Order.PaymentMethod.MONOPAY,
            payment_status__in=(Order.PaymentStatus.FAILED, Order.PaymentStatus.REFUNDED),
            stock_released=False,
        )
        if dry_run:
            count = qs.count()
            for num in qs.values_list("order_number", flat=True)[:50]:
                self.stdout.write(f"[dry-run] failed/refunded → {num}")
            return count
        done = 0
        for order in qs.iterator():
            if release_order_stock(order):
                done += 1
                self.stdout.write(f"повернуто {order.order_number}")
        return done
