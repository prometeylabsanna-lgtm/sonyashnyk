from pathlib import Path

from django.db import models

from apps.core.image_webp import IMAGE_EXTENSIONS, convert_file_to_webp_content, is_already_webp


class Certificate(models.Model):
    """Сертифікат власного виробництва (PDF/зображення)."""

    title = models.CharField("Назва", max_length=200)
    title_ru = models.CharField("Назва (RU)", max_length=200, blank=True, default="")
    series = models.CharField("Серія / продукт", max_length=120, blank=True)
    series_ru = models.CharField("Серія / продукт (RU)", max_length=120, blank=True, default="")
    file = models.FileField(
        "Файл (PDF/зображення)",
        upload_to="certificates/",
        blank=True,
        null=True,
        help_text="PDF лишається як є; зображення автоматично конвертуються в WebP.",
    )
    product = models.ForeignKey(
        "catalog.Product", verbose_name="Товар", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="certificates",
    )
    is_active = models.BooleanField("Показувати на сайті", default=True)
    order = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        verbose_name = "Сертифікат"
        verbose_name_plural = "Сертифікати"
        ordering = ["order", "-id"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.file and self.file.name:
            name = self.file.name
            ext = Path(name).suffix.lower()
            if ext != ".pdf" and ext in IMAGE_EXTENSIONS and not is_already_webp(name):
                converted = convert_file_to_webp_content(self.file, original_name=name)
                if converted is not None:
                    self.file = converted
        super().save(*args, **kwargs)
