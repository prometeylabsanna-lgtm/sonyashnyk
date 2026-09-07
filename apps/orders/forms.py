import re

from django import forms

from .models import Order

PHONE_RE = re.compile(r"^\+380\d{9}$")


class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            "full_name", "phone", "email",
            "delivery_method", "city", "warehouse",
            "payment_method", "comment", "promo_code",
            "agreed_to_data_processing",
        ]
        widgets = {
            "delivery_method": forms.RadioSelect(),
            "payment_method": forms.RadioSelect(),
            "full_name": forms.TextInput(attrs={"placeholder": "Прізвище, ім'я"}),
            "phone": forms.TextInput(attrs={"placeholder": "+380", "inputmode": "tel"}),
            "email": forms.EmailInput(attrs={"placeholder": "email@example.com"}),
            "city": forms.TextInput(attrs={"placeholder": "Місто"}),
            "warehouse": forms.TextInput(attrs={"placeholder": "№ відділення / поштомату / адреса"}),
            "comment": forms.Textarea(attrs={"rows": 3, "placeholder": "Коментар до замовлення (необов'язково)"}),
            "promo_code": forms.TextInput(attrs={"placeholder": "Промокод (якщо є)"}),
        }
        labels = {
            "full_name": "ПІБ отримувача",
            "phone": "Телефон",
            "email": "Email (необов'язково)",
            "delivery_method": "Спосіб доставки",
            "city": "Місто",
            "warehouse": "Відділення / адреса",
            "payment_method": "Спосіб оплати",
            "comment": "Коментар до замовлення",
            "promo_code": "Промокод",
            "agreed_to_data_processing": "Погоджуюсь на обробку персональних даних",
        }

    def clean_phone(self):
        phone = self.cleaned_data["phone"].replace(" ", "").replace("(", "").replace(")", "").replace("-", "")
        if not PHONE_RE.match(phone):
            raise forms.ValidationError("Введіть телефон у форматі +380XXXXXXXXX")
        return phone

    def clean(self):
        cleaned = super().clean()
        delivery = cleaned.get("delivery_method")
        if delivery and delivery != "pickup" and not cleaned.get("city"):
            self.add_error("city", "Вкажіть місто доставки")
        if delivery in ("np_branch", "np_locker", "ukrposhta") and not cleaned.get("warehouse"):
            self.add_error("warehouse", "Вкажіть відділення або адресу")
        if not cleaned.get("agreed_to_data_processing"):
            self.add_error("agreed_to_data_processing", "Потрібна згода на обробку персональних даних")
        return cleaned
