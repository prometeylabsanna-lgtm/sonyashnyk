"""Форми рівнів категорій для адмінки «Меню»."""

from django import forms

from .models import Category


class RootCategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = (
            "name", "erp_name", "slug", "image", "description", "order", "is_active",
        )

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
        self.fields["parent"].label = "Головна категорія"
        self.fields["parent"].help_text = "Оберіть батьківську головну категорію."
        self.fields["image"].help_text = (
            "Необовʼязково. Якщо порожньо — на сайті соняшник. "
            "Окремі іконки овочів/інструментів не використовуємо."
        )

    def clean_parent(self):
        parent = self.cleaned_data.get("parent")
        if parent is None:
            raise forms.ValidationError("Оберіть головну категорію.")
        if parent.parent_id is not None:
            raise forms.ValidationError("Батьківська має бути головною категорією (рівень 1).")
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
        self.fields["parent"].label = "Підкатегорія"
        self.fields["parent"].help_text = "Оберіть батьківську підкатегорію (рівень 2)."
        self.fields["image"].help_text = (
            "Необовʼязково. Якщо порожньо — на сайті соняшник."
        )

    def clean_parent(self):
        parent = self.cleaned_data.get("parent")
        if parent is None:
            raise forms.ValidationError("Оберіть підкатегорію.")
        if parent.parent_id is None or (parent.parent and parent.parent.parent_id is not None):
            raise forms.ValidationError("Батьківська має бути підкатегорією (не головною і не рівнем 3).")
        return parent
