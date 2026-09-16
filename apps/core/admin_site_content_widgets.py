"""CMS widgets — стандартні класи Unfold (світлі в light / темні в dark)."""

from django.contrib.admin.widgets import AdminTextareaWidget, AdminTextInputWidget
from unfold.widgets import INPUT_CLASSES, TEXTAREA_CLASSES


class CmsAdminTextInputWidget(AdminTextInputWidget):
    def __init__(self, attrs=None):
        attrs = dict(attrs or {})
        existing = attrs.get("class", "")
        merged = list(INPUT_CLASSES)
        if existing:
            merged = list(dict.fromkeys([*merged, *existing.split()]))
        attrs["class"] = " ".join(merged)
        super().__init__(attrs=attrs)


class CmsAdminTextareaWidget(AdminTextareaWidget):
    def __init__(self, attrs=None):
        attrs = dict(attrs or {})
        rows = attrs.pop("rows", 4)
        existing = attrs.get("class", "")
        merged = list(TEXTAREA_CLASSES)
        if existing:
            merged = list(dict.fromkeys([*merged, *existing.split()]))
        attrs["class"] = " ".join(merged)
        attrs["rows"] = rows
        super().__init__(attrs=attrs)


def apply_readable_widget(widget):
    """Застосувати стандартні Unfold input/textarea (тема light/dark)."""
    from django.forms.widgets import CheckboxInput, ClearableFileInput, Select
    from unfold.widgets import UnfoldAdminTextareaWidget, UnfoldAdminTextInputWidget

    if isinstance(widget, (CheckboxInput, ClearableFileInput, Select)):
        return widget
    if isinstance(widget, (UnfoldAdminTextInputWidget, AdminTextInputWidget)):
        return CmsAdminTextInputWidget(attrs=widget.attrs)
    if isinstance(widget, (UnfoldAdminTextareaWidget, AdminTextareaWidget)):
        rows = widget.attrs.get("rows", 4)
        return CmsAdminTextareaWidget(attrs={**widget.attrs, "rows": rows})
    return widget
