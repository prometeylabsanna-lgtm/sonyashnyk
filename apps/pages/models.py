from django.db import models


class Certificate(models.Model):
    """Сертифікат власного виробництва (PDF/зображення)."""

    title = models.CharField("Назва", max_length=200)
    series = models.CharField("Серія / продукт", max_length=120, blank=True)
    file = models.FileField("Файл (PDF/зображення)", upload_to="certificates/", blank=True, null=True)
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
