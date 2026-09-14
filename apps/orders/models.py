from decimal import Decimal

from django.db import models


class Order(models.Model):
    """Оформлене замовлення (не заявка з форми) — окремий об'єкт обліку."""

    class DeliveryMethod(models.TextChoices):
        NP_BRANCH = "np_branch", "Нова Пошта — відділення"
        NP_LOCKER = "np_locker", "Нова Пошта — поштомат"
        NP_COURIER = "np_courier", "Нова Пошта — курʼєр"
        UKRPOSHTA = "ukrposhta", "Укрпошта"
        PICKUP = "pickup", "Самовивіз"

    class PaymentMethod(models.TextChoices):
        LIQPAY = "liqpay", "Оплата карткою (LiqPay)"
        COD = "cod", "Оплата при отриманні (накладений платіж)"
        CASH_PICKUP = "cash_pickup", "Оплата при самовивозі"

    class PaymentStatus(models.TextChoices):
        PENDING = "pending", "Очікує оплати"
        PAID = "paid", "Оплачено"
        FAILED = "failed", "Помилка оплати"

    class Status(models.TextChoices):
        NEW = "new", "Нове"
        PROCESSING = "processing", "В обробці"
        SHIPPED = "shipped", "Відправлено"
        DONE = "done", "Виконано"

    order_number = models.CharField("Номер замовлення", max_length=20, unique=True, editable=False)

    full_name = models.CharField("ПІБ", max_length=180)
    phone = models.CharField("Телефон", max_length=32)
    email = models.EmailField("Email", blank=True)

    delivery_method = models.CharField("Спосіб доставки", max_length=16, choices=DeliveryMethod.choices)
    city = models.CharField("Місто", max_length=120, blank=True)
    warehouse = models.CharField("Відділення / адреса", max_length=200, blank=True)
    np_city_ref = models.CharField("NP CityRef", max_length=64, blank=True)
    np_warehouse_ref = models.CharField("NP WarehouseRef", max_length=64, blank=True)

    payment_method = models.CharField("Спосіб оплати", max_length=16, choices=PaymentMethod.choices)
    payment_status = models.CharField(
        "Статус оплати", max_length=16, choices=PaymentStatus.choices, default=PaymentStatus.PENDING,
    )
    status = models.CharField("Статус замовлення", max_length=16, choices=Status.choices, default=Status.NEW)

    comment = models.TextField("Коментар до замовлення", blank=True)
    promo_code = models.CharField("Промокод", max_length=40, blank=True)
    discount_total = models.DecimalField("Сума знижки", max_digits=10, decimal_places=2, default=Decimal("0"))
    subtotal = models.DecimalField("Сума товарів", max_digits=10, decimal_places=2, default=Decimal("0"))
    total = models.DecimalField("До сплати", max_digits=10, decimal_places=2, default=Decimal("0"))

    agreed_to_data_processing = models.BooleanField("Згода на обробку даних", default=False)
    created_at = models.DateTimeField("Створено", auto_now_add=True)

    class Meta:
        verbose_name = "Замовлення"
        verbose_name_plural = "Замовлення"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Замовлення {self.order_number}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self._generate_order_number()
        super().save(*args, **kwargs)

    def _generate_order_number(self):
        from django.utils import timezone

        prefix = timezone.now().strftime("%y%m%d")
        last = Order.objects.filter(order_number__startswith=prefix).count() + 1
        return f"{prefix}-{last:04d}"


class PromoCode(models.Model):
    """Промокод зі знижкою у % або фіксованою сумою."""

    class DiscountType(models.TextChoices):
        PERCENT = "percent", "Відсоток"
        FIXED = "fixed", "Фіксована сума"

    code = models.CharField("Код", max_length=40, unique=True)
    discount_type = models.CharField(
        "Тип знижки", max_length=10, choices=DiscountType.choices, default=DiscountType.PERCENT,
    )
    amount = models.DecimalField("Розмір знижки", max_digits=10, decimal_places=2)
    min_subtotal = models.DecimalField(
        "Мін. сума товарів", max_digits=10, decimal_places=2, default=Decimal("0"),
    )
    is_active = models.BooleanField("Активний", default=True)
    valid_until = models.DateField("Діє до", null=True, blank=True)

    class Meta:
        verbose_name = "Промокод"
        verbose_name_plural = "Промокоди"
        ordering = ["code"]

    def __str__(self):
        return self.code

    def clean(self):
        from django.core.exceptions import ValidationError

        self.code = (self.code or "").strip().upper()
        if self.amount <= 0:
            raise ValidationError({"amount": "Розмір знижки має бути більшим за 0."})
        if self.discount_type == self.DiscountType.PERCENT and self.amount > 100:
            raise ValidationError({"amount": "Відсоток не може перевищувати 100."})

    def save(self, *args, **kwargs):
        self.code = (self.code or "").strip().upper()
        super().save(*args, **kwargs)

    def is_usable(self, subtotal: Decimal) -> tuple[bool, str]:
        from django.utils import timezone

        if not self.is_active:
            return False, "Промокод неактивний."
        if self.valid_until and self.valid_until < timezone.localdate():
            return False, "Термін дії промокоду минув."
        if subtotal < self.min_subtotal:
            return False, f"Мінімальна сума для коду — {self.min_subtotal} ₴."
        return True, ""

    def calc_discount(self, subtotal: Decimal) -> Decimal:
        if subtotal <= 0:
            return Decimal("0")
        if self.discount_type == self.DiscountType.PERCENT:
            discount = (subtotal * self.amount / Decimal("100")).quantize(Decimal("0.01"))
        else:
            discount = self.amount
        if discount > subtotal:
            discount = subtotal
        return discount


class OrderItem(models.Model):
    """Позиція замовлення. Ціна й назва фіксуються на момент купівлі (снапшот)."""

    order = models.ForeignKey(Order, verbose_name="Замовлення", on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(
        "catalog.Product", verbose_name="Товар", null=True, on_delete=models.SET_NULL, related_name="order_items",
    )
    variant = models.ForeignKey(
        "catalog.ProductVariant", verbose_name="Варіант", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="order_items",
    )
    product_name = models.CharField("Назва товару (на момент купівлі)", max_length=255)
    variant_label = models.CharField("Варіант (на момент купівлі)", max_length=80, blank=True)
    price = models.DecimalField("Ціна за од.", max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField("Кількість", default=1)

    class Meta:
        verbose_name = "Позиція замовлення"
        verbose_name_plural = "Позиції замовлення"

    def __str__(self):
        return f"{self.product_name} × {self.quantity}"

    @property
    def line_total(self):
        return self.price * self.quantity
