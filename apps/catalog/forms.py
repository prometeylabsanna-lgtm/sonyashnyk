"""Форми адмінки каталогу."""

from django import forms

from .admin_widgets import CharacteristicsKeyValueWidget
from .filter_models import FilterOption, FilterType
from .models import Product


def _filter_value_choices(filter_type, current=""):
    """Choices з довідника + поточне значення, якщо його ще немає в довіднику."""
    choices = [("", "—")]
    seen = set()
    for value in (
        FilterOption.objects.filter(filter_type=filter_type, is_active=True)
        .order_by("order", "value")
        .values_list("value", flat=True)
    ):
        choices.append((value, value))
        seen.add(value)
    if current and current not in seen:
        choices.append((current, f"{current} (не в довіднику)"))
    return choices


class ProductAdminForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = "__all__"
        widgets = {
            "characteristics": CharacteristicsKeyValueWidget(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = self.instance
        mapping = (
            (FilterType.BRAND, "brand"),
            (FilterType.COUNTRY, "country_of_origin"),
            (FilterType.VOLUME, "pack_volume"),
            (FilterType.POWER, "power"),
        )
        for filter_type, field_name in mapping:
            current = getattr(instance, field_name, "") if instance and instance.pk else ""
            if field_name in self.fields:
                self.fields[field_name] = forms.ChoiceField(
                    label=self.fields[field_name].label,
                    required=False,
                    choices=_filter_value_choices(filter_type, current),
                    help_text=(
                        "Значення з довідника «Фільтри». "
                        "Нові значення додавайте в Каталог → Фільтри."
                    ),
                )

    def clean_characteristics(self):
        value = self.cleaned_data.get("characteristics")
        if value in (None, ""):
            return {}
        if isinstance(value, dict):
            return value
        raise forms.ValidationError("Характеристики мають бути парами «назва → значення».")
