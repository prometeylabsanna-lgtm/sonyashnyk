"""Форми адмінки каталогу."""

from django import forms

from apps.core.admin_site_content_widgets import CmsTinyMCEWidget
from .admin_widgets import CharacteristicsKeyValueWidget
from .category_tree import pack_measure_kind
from .filter_models import (
    LEGACY_PRODUCT_FIELDS,
    PACK_FILTER_SLUGS,
    CatalogFilterValue,
    ProductAttribute,
)
from .filters import active_catalog_filters
from .models import Product


def _attr_field_name(slug: str) -> str:
    return f"attr_{slug}"


class ProductAdminForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = "__all__"
        widgets = {
            "characteristics": CharacteristicsKeyValueWidget(),
            "characteristics_ru": CharacteristicsKeyValueWidget(),
            "description": CmsTinyMCEWidget(attrs={"rows": 14}),
            "description_ru": CmsTinyMCEWidget(attrs={"rows": 14}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = self.instance
        current_by_slug = {}
        if instance and instance.pk:
            current_by_slug = {
                a.catalog_filter.slug: a.value
                for a in instance.filter_attrs.select_related("catalog_filter")
            }
            for slug, field in LEGACY_PRODUCT_FIELDS.items():
                if slug not in current_by_slug:
                    legacy_val = getattr(instance, field, "") or ""
                    if legacy_val:
                        current_by_slug[slug] = legacy_val
            pack_val = (instance.pack_volume or "").strip()
            if pack_val:
                kind = pack_measure_kind(instance.category, pack_val)
                if kind not in current_by_slug:
                    current_by_slug[kind] = pack_val

        self._catalog_filters = list(active_catalog_filters())
        for cf in self._catalog_filters:
            fname = _attr_field_name(cf.slug)
            current = current_by_slug.get(cf.slug, "")
            choices = [("", "—")]
            seen = set()
            for value in (
                CatalogFilterValue.objects.filter(catalog_filter=cf, is_active=True)
                .order_by("order", "value")
                .values_list("value", flat=True)
            ):
                choices.append((value, value))
                seen.add(value)
            if current and current not in seen:
                choices.append((current, f"{current} (не в довіднику)"))
            self.fields[fname] = forms.ChoiceField(
                label=cf.name,
                required=False,
                choices=choices,
                initial=current,
                help_text="Значення з довідника «Фільтри».",
            )

        # Старі CharField ховаємо — керування через attr_*
        for field in (*LEGACY_PRODUCT_FIELDS.values(), "pack_volume"):
            if field in self.fields:
                self.fields[field].widget = forms.HiddenInput()
                self.fields[field].required = False

        for fname in ("characteristics", "characteristics_ru"):
            if fname in self.fields:
                self.fields[fname].widget = CharacteristicsKeyValueWidget()

    def _clean_char_dict(self, field_name):
        value = self.cleaned_data.get(field_name)
        if value in (None, ""):
            return {}
        if isinstance(value, dict):
            return value
        raise forms.ValidationError("Характеристики мають бути парами «назва → значення».")

    def clean_characteristics(self):
        return self._clean_char_dict("characteristics")

    def clean_characteristics_ru(self):
        return self._clean_char_dict("characteristics_ru")

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Синхрон legacy-полів до збереження Product
        for cf in self._catalog_filters:
            fname = _attr_field_name(cf.slug)
            raw = (self.cleaned_data.get(fname) or "").strip()
            legacy = LEGACY_PRODUCT_FIELDS.get(cf.slug)
            if legacy:
                setattr(instance, legacy, raw)
        pack_val = ""
        for slug in PACK_FILTER_SLUGS:
            raw = (self.cleaned_data.get(_attr_field_name(slug)) or "").strip()
            if raw:
                pack_val = raw
                break
        instance.pack_volume = pack_val
        if commit:
            instance.save()
            self.save_m2m()
            self._save_attributes(instance)
        else:
            self._pending_attrs = True
        return instance

    def _save_attributes(self, instance):
        for cf in self._catalog_filters:
            fname = _attr_field_name(cf.slug)
            raw = (self.cleaned_data.get(fname) or "").strip()
            if raw:
                ProductAttribute.objects.update_or_create(
                    product=instance,
                    catalog_filter=cf,
                    defaults={"value": raw},
                )
            else:
                ProductAttribute.objects.filter(
                    product=instance,
                    catalog_filter=cf,
                ).delete()

    def save_attributes_after_commit(self, instance):
        """Викликати з ModelAdmin, якщо save(commit=False) не використовується."""
        self._save_attributes(instance)
