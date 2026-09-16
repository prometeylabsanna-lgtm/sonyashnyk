"""Форми адмінки каталогу."""

from django import forms

from .admin_widgets import CharacteristicsKeyValueWidget
from .models import Product


class ProductAdminForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = "__all__"
        widgets = {
            "characteristics": CharacteristicsKeyValueWidget(),
        }

    def clean_characteristics(self):
        value = self.cleaned_data.get("characteristics")
        if value in (None, ""):
            return {}
        if isinstance(value, dict):
            return value
        raise forms.ValidationError("Характеристики мають бути парами «назва → значення».")
