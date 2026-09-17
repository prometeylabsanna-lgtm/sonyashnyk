"""Форми рівнів категорій для адмінки «Меню»."""

from django import forms

from apps.core.admin_guidelines import help_for_category_field

from .models import Category


def _apply_category_field_hints(form, level: int):
    for name, field in form.fields.items():
        tip = help_for_category_field(name, level)
        if tip:
            field.help_text = tip


class RootCategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = (
            "name", "erp_name", "slug", "image", "description", "order", "is_active",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_category_field_hints(self, 1)

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.parent = None
        if commit:
            obj.save()
        return obj


class SubCategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = (
            "name", "erp_name", "slug", "parent", "image",
            "description", "order", "is_active",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["parent"].queryset = Category.objects.filter(parent__isnull=True)
        self.fields["parent"].required = True
        self.fields["parent"].label = "1 рівень (головна категорія)"
        self.fields["parent"].help_text = "До якої головної категорії належить цей розділ."
        _apply_category_field_hints(self, 2)

    def clean_parent(self):
        parent = self.cleaned_data.get("parent")
        if parent is None:
            raise forms.ValidationError("Оберіть головну категорію.")
        if parent.parent_id is not None:
            raise forms.ValidationError("Оберіть саме 1 рівень (без батьківської).")
        return parent


class SubSubCategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = (
            "name", "erp_name", "slug", "parent", "image",
            "description", "order", "is_active",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["parent"].queryset = Category.objects.filter(
            parent__isnull=False, parent__parent__isnull=True,
        )
        self.fields["parent"].required = True
        self.fields["parent"].label = "2 рівень (підкатегорія)"
        self.fields["parent"].help_text = "До якої підкатегорії належить це уточнення."
        _apply_category_field_hints(self, 3)

    def clean_parent(self):
        parent = self.cleaned_data.get("parent")
        if parent is None:
            raise forms.ValidationError("Оберіть підкатегорію.")
        if parent.parent_id is None or (parent.parent and parent.parent.parent_id is not None):
            raise forms.ValidationError("Оберіть саме 2 рівень (не головну і не 3 рівень).")
        return parent
