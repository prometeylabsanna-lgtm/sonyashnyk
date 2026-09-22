"""PickupPoint ModelFormSet для CMS-секції контактів."""

from django import forms
from django.forms import BaseModelFormSet, modelformset_factory
from django.forms.widgets import CheckboxInput

from apps.core.admin_site_content_widgets import CmsAdminTextInputWidget, CmsAdminTextareaWidget
from apps.core.models import PickupPoint
from apps.core.pickup_points import ensure_default_pickup_points, extract_map_embed_src


def _tel_value(value: str) -> str:
    return "".join(ch for ch in (value or "") if ch.isdigit() or ch == "+")


class PickupPointForm(forms.ModelForm):
    class Meta:
        model = PickupPoint
        fields = (
            "title",
            "title_ru",
            "address",
            "address_ru",
            "phone",
            "phone_raw",
            "hours",
            "hours_ru",
            "map_embed",
            "order",
            "is_active",
        )
        widgets = {
            "title": CmsAdminTextInputWidget(),
            "title_ru": CmsAdminTextInputWidget(),
            "address": CmsAdminTextInputWidget(),
            "address_ru": CmsAdminTextInputWidget(),
            "phone": CmsAdminTextInputWidget(),
            "phone_raw": CmsAdminTextInputWidget(),
            "hours": CmsAdminTextInputWidget(),
            "hours_ru": CmsAdminTextInputWidget(),
            "map_embed": CmsAdminTextareaWidget(attrs={"rows": 3}),
            "order": forms.HiddenInput(),
            "is_active": CheckboxInput(attrs={"class": "pickup-point-row__checkbox"}),
        }
        help_texts = {
            "title": "Коротка назва, наприклад «Крамниця на Хрещатику».",
            "address": "Вулиця і місто. Зараз можна лишити заглушку.",
            "phone": "Якщо порожнє — на сайті буде телефон із налаштувань.",
            "phone_raw": "Номер для дзвінка з телефону: лише цифри та +.",
            "hours": "Якщо порожнє — графік із налаштувань сайту.",
            "map_embed": (
                "У Google Maps: «Поділитися» → «Вбудувати карту» → вставте сюди скопійований код. "
                "Порожнє — карта-заглушка."
            ),
        }

    def clean_phone_raw(self):
        return _tel_value(self.cleaned_data.get("phone_raw") or "")

    def clean_map_embed(self):
        raw = (self.cleaned_data.get("map_embed") or "").strip()
        if not raw:
            return ""
        if not extract_map_embed_src(raw):
            raise forms.ValidationError(
                "Не вдалося розпізнати карту. Скопіюйте код ще раз із Google Maps "
                "(Поділитися → Вбудувати карту)."
            )
        return raw

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("DELETE"):
            return cleaned
        title = (cleaned.get("title") or "").strip()
        address = (cleaned.get("address") or "").strip()
        if not title and not address:
            return cleaned
        if not title:
            self.add_error("title", "Вкажіть назву крамниці.")
        if not address:
            self.add_error("address", "Вкажіть адресу.")
        return cleaned


class PickupPointBaseFormSet(BaseModelFormSet):
    def save(self, commit=True):
        super().save(commit=False)
        for obj in self.deleted_objects:
            obj.delete()
        order = 0
        saved = []
        for form in self.forms:
            if not hasattr(form, "cleaned_data") or form.cleaned_data.get("DELETE"):
                continue
            title = (form.cleaned_data.get("title") or "").strip()
            address = (form.cleaned_data.get("address") or "").strip()
            if not title or not address:
                continue
            obj = form.save(commit=False)
            obj.order = order
            order += 1
            if commit:
                obj.save()
            saved.append(obj)
        if commit:
            self.save_m2m()
        return saved


def build_pickup_point_formset(data=None, files=None):
    ensure_default_pickup_points()
    FormSet = modelformset_factory(
        PickupPoint,
        form=PickupPointForm,
        formset=PickupPointBaseFormSet,
        extra=0,
        can_delete=True,
    )
    queryset = PickupPoint.objects.all().order_by("order", "id")
    return FormSet(data=data, files=files, queryset=queryset, prefix="pickup_points")
