from django.db import models


class Lead(models.Model):
    """Заявка з сайту (модалка, «1 клік», контактна форма, кнопка «Передзвоніть»).

    Усі звернення з сайту потрапляють сюди — в адмінку їх бачить і обробляє менеджер.
    """

    class LeadType(models.TextChoices):
        PHONE_MODAL = "phone_modal", "Модальне вікно (телефон/знижка)"
        BUY_ONE_CLICK = "buy_one_click", "Купити в 1 клік"
        CONTACT_FORM = "contact_form", "Форма на сторінці «Контакти»"
        CALLBACK = "callback", "Кнопка «Передзвоніть мені»"
        NEWSLETTER = "newsletter", "Підписка на email-розсилку"

    class Status(models.TextChoices):
        NEW = "new", "Нова"
        IN_PROGRESS = "in_progress", "В обробці"
        DONE = "done", "Опрацьована"

    lead_type = models.CharField("Тип заявки", max_length=32, choices=LeadType.choices, default=LeadType.PHONE_MODAL)
    name = models.CharField("Ім'я", max_length=120, blank=True)
    phone = models.CharField("Телефон", max_length=32, blank=True)
    email = models.EmailField("Email", blank=True)
    message = models.TextField("Повідомлення", blank=True)

    product = models.ForeignKey(
        "catalog.Product", verbose_name="Товар", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="leads",
    )
    source_page = models.CharField("Сторінка джерела", max_length=255, blank=True)
    status = models.CharField("Статус", max_length=16, choices=Status.choices, default=Status.NEW)
    created_at = models.DateTimeField("Створено", auto_now_add=True)

    class Meta:
        verbose_name = "Заявка"
        verbose_name_plural = "Заявки"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_lead_type_display()} — {self.phone or self.email}"
