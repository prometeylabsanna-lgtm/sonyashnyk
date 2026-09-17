from django.db import models

from apps.core.fields import WebPImageField


class SiteSettings(models.Model):
    """Глобальні налаштування сайту (singleton, pk=1)."""

    site_name = models.CharField("Назва сайту", max_length=128, default="Соняшник")
    phone = models.CharField("Телефон", max_length=32, blank=True, default="+38 (067) 123-45-67")
    phone_raw = models.CharField(
        "Телефон для tel:",
        max_length=32,
        blank=True,
        default="+380671234567",
        help_text="Лише цифри та +, для посилання tel:",
    )
    email = models.EmailField("Email", blank=True, default="")
    address = models.CharField("Адреса / точка видачі", max_length=255, blank=True, default="м. Київ, Хрещатик 1")
    work_hours = models.CharField("Графік роботи", max_length=120, blank=True, default="Пн–Сб 9:00–18:00")
    free_shipping_threshold = models.PositiveIntegerField(
        "Безкоштовна доставка від (₴)",
        default=1500,
    )
    meta_description = models.CharField("Meta description (за замовчуванням)", max_length=300, blank=True, default="")

    instagram_url = models.URLField("Instagram", blank=True, default="")
    tiktok_url = models.URLField("TikTok", blank=True, default="")
    telegram_url = models.URLField("Telegram", blank=True, default="")

    class Meta:
        verbose_name = "Налаштування сайту"
        verbose_name_plural = "Налаштування сайту"

    def __str__(self):
        return self.site_name or "Налаштування сайту"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    @classmethod
    def load(cls):
        return cls.get_solo()


class SiteBlock(models.Model):
    """Один контент-ключ секції: текст / фото / url / visibility."""

    class Page(models.TextChoices):
        HOME = "home", "Головна"
        SITE = "site", "Сайт"
        ABOUT = "about", "Про нас"
        DELIVERY = "delivery", "Доставка"
        CERTIFICATES = "certificates", "Сертифікати"
        CONTACTS = "contacts", "Контакти"
        OFFER = "offer", "Оферта"
        PRIVACY = "privacy", "Політика"
        CATALOG = "catalog", "Каталог"
        SEARCH = "search", "Пошук"
        CART = "cart", "Кошик"
        CHECKOUT = "checkout", "Оформлення"
        THANKYOU = "thankyou", "Дякуємо"
        ERROR = "error", "Помилки"
        WISHLIST = "wishlist", "Обране"
        PRODUCT = "product", "Товар"

    class ContentType(models.TextChoices):
        TEXT = "text", "Текст"
        IMAGE = "image", "Фото"
        URL = "url", "Посилання"
        VIDEO = "video", "Відео"

    page = models.CharField("Сторінка", max_length=32, choices=Page.choices)
    key = models.CharField("Ключ", max_length=64)
    label = models.CharField("Підпис у адмінці", max_length=128, blank=True, default="")
    content_type = models.CharField(
        "Тип",
        max_length=16,
        choices=ContentType.choices,
        default=ContentType.TEXT,
    )
    text_html = models.TextField("Текст / HTML", blank=True, default="")
    image = WebPImageField("Зображення", upload_to="blocks/", blank=True, null=True)
    link_url = models.CharField("URL посилання", max_length=512, blank=True, default="")
    link_label = models.CharField("Текст посилання", max_length=128, blank=True, default="")
    video_embed_url = models.URLField("Embed URL відео", blank=True, default="")
    video_file = models.FileField("Файл відео", upload_to="blocks/video/", blank=True, null=True)
    sort_order = models.PositiveSmallIntegerField("Порядок", default=0)
    is_active = models.BooleanField("Активний", default=True)

    class Meta:
        verbose_name = "Блок контенту"
        verbose_name_plural = "Блоки контенту"
        constraints = [
            models.UniqueConstraint(fields=["page", "key"], name="unique_site_block_page_key"),
        ]
        ordering = ["page", "sort_order", "key"]

    def __str__(self):
        return f"{self.page}.{self.key}"

    @property
    def cache_key(self) -> str:
        return f"{self.page}.{self.key}"


class HeroSlide(models.Model):
    """Слайд головного банера на головній сторінці (CollectionMedia)."""

    eyebrow = models.CharField("Надпис над заголовком", max_length=120, blank=True)
    title = models.CharField("Заголовок", max_length=200)
    lead = models.TextField("Підпис", blank=True)
    image = WebPImageField("Зображення", upload_to="banners/", blank=True, null=True)
    alt_text = models.CharField("Alt зображення", max_length=200, blank=True, default="")
    cta1_text = models.CharField("Текст кнопки 1", max_length=60, default="Дивитись каталог")
    cta1_url = models.CharField("Посилання кнопки 1", max_length=255, default="/katalog/")
    cta2_text = models.CharField("Текст кнопки 2", max_length=60, blank=True, default="До акцій")
    cta2_url = models.CharField("Посилання кнопки 2", max_length=255, blank=True, default="/katalog/aktsiyi/")
    order = models.PositiveIntegerField("Порядок", default=0)
    is_active = models.BooleanField("Активний", default=True)

    class Meta:
        verbose_name = "Слайд банера"
        verbose_name_plural = "Слайди банера"
        ordering = ["order", "id"]

    def __str__(self):
        return self.title


class HighlightPoint(models.Model):
    """Пункт «чому нам довіряють» / коротка перевага. ListItem."""

    class Section(models.TextChoices):
        TRUST = "trust", "Смуга довіри (під хедером)"
        INFO = "info", "Інфо-картки (переваги)"

    section = models.CharField("Секція", max_length=10, choices=Section.choices, default=Section.TRUST)
    icon = models.CharField(
        "Іконка",
        max_length=30,
        default="leaf",
        help_text="Ключ іконки: leaf, truck, shield, card, chat, phone, seed, years",
    )
    title = models.CharField("Заголовок", max_length=120)
    text = models.CharField("Текст", max_length=200, blank=True)
    order = models.PositiveIntegerField("Порядок", default=0)
    is_active = models.BooleanField("Активний", default=True)

    class Meta:
        verbose_name = "Перевага"
        verbose_name_plural = "Переваги"
        ordering = ["order", "id"]

    def __str__(self):
        return self.title


class Review(models.Model):
    """Відгук клієнта для секції на головній. ListItem."""

    name = models.CharField("Ім'я", max_length=120)
    city = models.CharField("Місто", max_length=80, blank=True)
    text = models.TextField("Текст відгуку")
    rating = models.PositiveSmallIntegerField("Оцінка (1–5)", default=5)
    order = models.PositiveIntegerField("Порядок", default=0)
    is_active = models.BooleanField("Активний", default=True)

    class Meta:
        verbose_name = "Відгук"
        verbose_name_plural = "Відгуки"
        ordering = ["order", "-id"]

    def __str__(self):
        return f"{self.name} ({self.rating}★)"
