import re

from django import forms

from .models import Order
from .nova_poshta import is_configured as np_is_configured

PHONE_RE = re.compile(r"^\+380\d{9}$")


class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            "full_name", "phone", "email",
            "delivery_method", "city", "warehouse",
            "np_city_ref", "np_warehouse_ref",
            "payment_method", "comment", "promo_code",
            "agreed_to_data_processing",
        ]
        widgets = {
            "delivery_method": forms.RadioSelect(),
            "payment_method": forms.RadioSelect(),
            "full_name": forms.TextInput(attrs={"placeholder": "Прізвище, ім'я", "autocomplete": "name"}),
            "phone": forms.TextInput(attrs={
                "placeholder": "+380", "inputmode": "tel", "autocomplete": "tel", "data-phone-mask": True,
            }),
            "email": forms.EmailInput(attrs={"placeholder": "email@example.com", "autocomplete": "email"}),
            "city": forms.TextInput(attrs={
                "placeholder": "Почніть вводити місто",
                "autocomplete": "off",
                "data-np-city-input": True,
            }),
            "warehouse": forms.TextInput(attrs={
                "placeholder": "Відділення / поштомат / адреса",
                "autocomplete": "off",
                "data-np-warehouse-input": True,
            }),
            "np_city_ref": forms.HiddenInput(attrs={"data-np-city-ref": True}),
            "np_warehouse_ref": forms.HiddenInput(attrs={"data-np-warehouse-ref": True}),
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
        payment = cleaned.get("payment_method")
        city = (cleaned.get("city") or "").strip()
        warehouse = (cleaned.get("warehouse") or "").strip()
        city_ref = (cleaned.get("np_city_ref") or "").strip()
        warehouse_ref = (cleaned.get("np_warehouse_ref") or "").strip()

        if delivery and delivery != Order.DeliveryMethod.PICKUP and not city:
            self.add_error("city", "Вкажіть місто доставки")

        if delivery in (
            Order.DeliveryMethod.NP_BRANCH,
            Order.DeliveryMethod.NP_LOCKER,
            Order.DeliveryMethod.UKRPOSHTA,
        ) and not warehouse:
            self.add_error("warehouse", "Вкажіть відділення або поштомат")

        if delivery == Order.DeliveryMethod.NP_COURIER and not warehouse:
            self.add_error("warehouse", "Вкажіть адресу доставки")

        # Якщо НП API увімкнено — вимагаємо ref для відділення/поштомату
        if np_is_configured() and delivery in (
            Order.DeliveryMethod.NP_BRANCH,
            Order.DeliveryMethod.NP_LOCKER,
        ):
            if city and not city_ref:
                self.add_error("city", "Оберіть місто зі списку підказок")
            if warehouse and not warehouse_ref:
                self.add_error("warehouse", "Оберіть відділення зі списку підказок")

        if payment == Order.PaymentMethod.CASH_PICKUP and delivery != Order.DeliveryMethod.PICKUP:
            self.add_error("payment_method", "Оплата при самовивозі доступна лише для самовивозу")

        if not cleaned.get("agreed_to_data_processing"):
            self.add_error("agreed_to_data_processing", "Потрібна згода на обробку персональних даних")
        return cleaned
