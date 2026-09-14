from django.db import models


class SiteSettings(models.Model):
    """Глобальні налаштування сайту (singleton, pk=1)."""

    instagram_url = models.URLField("Instagram", blank=True, default="")
    tiktok_url = models.URLField("TikTok", blank=True, default="")
    telegram_url = models.URLField("Telegram", blank=True, default="")

    class Meta:
        verbose_name = "Налаштування сайту"
        verbose_name_plural = "Налаштування сайту"

    def __str__(self):
        return "Налаштування сайту"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class HeroSlide(models.Model):
    """Слайд головного банера на головній сторінці."""

    eyebrow = models.CharField("Надпис над заголовком", max_length=120, blank=True)
    title = models.CharField("Заголовок", max_length=200)
    lead = models.TextField("Підпис", blank=True)
    image = models.ImageField("Зображення", upload_to="banners/", blank=True, null=True)
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
    """Пункт «чому нам довіряють» / коротка перевага. Використовується у двох секціях."""

    class Section(models.TextChoices):
        TRUST = "trust", "Смуга довіри (під хедером)"
        INFO = "info", "Інфо-картки (переваги)"

    section = models.CharField("Секція", max_length=10, choices=Section.choices, default=Section.TRUST)
    icon = models.CharField(
        "Іконка", max_length=30, default="leaf",
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
    """Відгук клієнта для секції J на головній."""

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
