import re

from django import forms

from .models import Lead

PHONE_RE = re.compile(r"^\+380\d{9}$")


class LeadForm(forms.ModelForm):
    honeypot = forms.CharField(required=False, widget=forms.HiddenInput)

    class Meta:
        model = Lead
        fields = ["lead_type", "name", "phone", "email", "message", "product", "source_page"]
        widgets = {
            "lead_type": forms.HiddenInput(),
            "product": forms.HiddenInput(),
            "source_page": forms.HiddenInput(),
            "name": forms.TextInput(attrs={"placeholder": "Ваше ім'я"}),
            "phone": forms.TextInput(attrs={"placeholder": "+380", "inputmode": "tel"}),
            "email": forms.EmailInput(attrs={"placeholder": "email@example.com"}),
            "message": forms.Textarea(attrs={"rows": 3, "placeholder": "Повідомлення"}),
        }

    def clean_honeypot(self):
        """Прихоняте поле від спам-ботів — має завжди лишатись порожнім."""
        value = self.cleaned_data.get("honeypot")
        if value:
            raise forms.ValidationError("Виявлено спам.")
        return value

    def clean_phone(self):
        phone = self.cleaned_data.get("phone", "").replace(" ", "").replace("(", "").replace(")", "").replace("-", "")
        if phone and not PHONE_RE.match(phone):
            raise forms.ValidationError("Введіть телефон у форматі +380XXXXXXXXX")
        return phone

    def clean(self):
        cleaned = super().clean()
        lead_type = cleaned.get("lead_type")
        phone = cleaned.get("phone")
        email = cleaned.get("email")

        if lead_type == "newsletter" and not email:
            self.add_error("email", "Вкажіть email для підписки.")
        elif lead_type != "newsletter" and not phone:
            self.add_error("phone", "Вкажіть номер телефону.")
        return cleaned
