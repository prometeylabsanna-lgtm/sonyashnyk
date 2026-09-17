"""HeroSlide ModelFormSet для CMS-секції hero."""

from django import forms
from django.forms import BaseModelFormSet, modelformset_factory
from unfold.widgets import UnfoldAdminFileFieldWidget, UnfoldBooleanWidget

from apps.core.admin_site_content_widgets import CmsAdminTextInputWidget, CmsAdminTextareaWidget
from apps.core.hero_slides import ensure_default_hero_slides
from apps.core.models import HeroSlide


class HeroSlideForm(forms.ModelForm):
    class Meta:
        model = HeroSlide
        fields = (
            "eyebrow",
            "title",
            "lead",
            "image",
            "alt_text",
            "cta1_text",
            "cta1_url",
            "cta2_text",
            "cta2_url",
            "order",
            "is_active",
        )
        widgets = {
            "eyebrow": CmsAdminTextInputWidget(),
            "title": CmsAdminTextInputWidget(),
            "lead": CmsAdminTextareaWidget(attrs={"rows": 3}),
            "image": UnfoldAdminFileFieldWidget(),
            "alt_text": CmsAdminTextInputWidget(),
            "cta1_text": CmsAdminTextInputWidget(),
            "cta1_url": CmsAdminTextInputWidget(),
            "cta2_text": CmsAdminTextInputWidget(),
            "cta2_url": CmsAdminTextInputWidget(),
            "order": forms.HiddenInput(),
            "is_active": UnfoldBooleanWidget(),
        }
        help_texts = {
            "eyebrow": "Маленький рядок над заголовком (до ~40 символів). Можна порожнім.",
            "title": "Головний заголовок слайда — до ~60 символів.",
            "lead": "Підпис під заголовком — 1–2 короткі речення.",
            "image": "Фото банера ≈ 1600×900 px. Якщо не завантажити — буде стандартне.",
            "alt_text": "Короткий опис фото для доступності (до ~80 символів).",
            "cta1_text": "Текст першої кнопки — 2–4 слова.",
            "cta1_url": "Куди веде перша кнопка (наприклад /katalog/).",
            "cta2_text": "Текст другої кнопки — 2–4 слова. Можна порожнім.",
            "cta2_url": "Куди веде друга кнопка.",
        }

    def clean(self):
        cleaned = super().clean()
        if self.cleaned_data.get("DELETE"):
            return cleaned
        title = (cleaned.get("title") or "").strip()
        image = cleaned.get("image")
        has_existing = bool(getattr(self.instance, "pk", None) and self.instance.image)
        if not title and not image and not has_existing:
            return cleaned
        if not title:
            self.add_error("title", "Вкажіть заголовок слайда.")
        return cleaned


class HeroSlideBaseFormSet(BaseModelFormSet):
    def save(self, commit=True):
        slides = super().save(commit=False)
        for obj in self.deleted_objects:
            obj.delete()
        order = 0
        saved = []
        for form in self.forms:
            if not hasattr(form, "cleaned_data") or form.cleaned_data.get("DELETE"):
                continue
            title = (form.cleaned_data.get("title") or "").strip()
            image = form.cleaned_data.get("image")
            has_existing = bool(form.instance.pk and form.instance.image)
            if not title and not image and not has_existing:
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


def build_hero_slide_formset(data=None, files=None):
    ensure_default_hero_slides()
    FormSet = modelformset_factory(
        HeroSlide,
        form=HeroSlideForm,
        formset=HeroSlideBaseFormSet,
        extra=1,
        can_delete=True,
    )
    queryset = HeroSlide.objects.all().order_by("order", "id")
    return FormSet(data=data, files=files, queryset=queryset, prefix="hero_slides")
