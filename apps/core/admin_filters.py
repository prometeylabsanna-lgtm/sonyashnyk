"""Випадаючі фільтри Unfold зверху changelist без префікса «За …»."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from django.contrib import admin
from django.contrib.admin.views.main import ChangeList
from django.core.validators import EMPTY_VALUES
from django.db.models import Field, Model, QuerySet
from django.http import HttpRequest
from unfold.contrib.filters.admin.dropdown_filters import (
    ChoicesDropdownFilter,
    DropdownFilter,
    RelatedDropdownFilter,
)
from unfold.contrib.filters.admin.mixins import DropdownMixin, ValueMixin
from unfold.contrib.filters.forms import DropdownForm

ALL_OPTION = ["", "Усі"]


def horizontal_options_for(list_filter) -> dict[str, dict[str, bool]]:
    """Усі фільтри з list_filter — зверху (horizontal)."""
    options: dict[str, dict[str, bool]] = {}
    for item in list_filter:
        if isinstance(item, (tuple, list)):
            key = item[0]
        elif isinstance(item, type):
            key = getattr(item, "parameter_name", None)
        else:
            key = item
        if key:
            options[str(key)] = {"horizontal": True}
    return options


def _yield_dropdown(
    *,
    title: str,
    name: str,
    choices: list,
    value: Any,
    form_class=DropdownForm,
    multiple: bool = False,
) -> Iterator[dict]:
    yield {
        "form": form_class(
            label=str(title).strip(),
            name=name,
            choices=choices,
            data={name: value},
            multiple=multiple,
        ),
    }


class CleanDropdownFilter(DropdownFilter):
    """SimpleListFilter → select зверху, підпис = title, дефолт «Усі»."""

    form_class = DropdownForm
    all_option = ALL_OPTION

    def choices(self, changelist: ChangeList) -> Iterator:
        add_facets = getattr(changelist, "add_facets", False)
        facet_counts = self.get_facet_queryset(changelist) if add_facets else None
        choices = [self.all_option] if self.all_option else []
        for i, choice in enumerate(self.lookup_choices):
            if add_facets and facet_counts:
                count = facet_counts[f"{i}__c"]
                choices.append((choice[0], f"{choice[1]} ({count})"))
            else:
                choices.append(choice)
        yield from _yield_dropdown(
            title=self.title,
            name=self.parameter_name,
            choices=choices,
            value=self.value(),
            form_class=self.form_class,
            multiple=getattr(self, "multiple", False),
        )


class CleanChoicesDropdownFilter(ChoicesDropdownFilter):
    all_option = ALL_OPTION

    def choices(self, changelist: ChangeList) -> Iterator:
        add_facets = getattr(changelist, "add_facets", False)
        facet_counts = self.get_facet_queryset(changelist) if add_facets else None
        choices = [self.all_option] if self.all_option else []
        for i, choice in enumerate(self.field.flatchoices):
            if add_facets and facet_counts:
                count = facet_counts[f"{i}__c"]
                choices.append((choice[0], f"{choice[1]} ({count})"))
            else:
                choices.append(choice)
        yield from _yield_dropdown(
            title=self.title,
            name=self.lookup_kwarg,
            choices=choices,
            value=self.value(),
            form_class=self.form_class,
            multiple=getattr(self, "multiple", False),
        )


class CleanRelatedDropdownFilter(RelatedDropdownFilter):
    all_option = ALL_OPTION

    def choices(self, changelist: ChangeList) -> Iterator:
        add_facets = getattr(changelist, "add_facets", False)
        facet_counts = self.get_facet_queryset(changelist) if add_facets else None
        if add_facets and facet_counts:
            choices = [self.all_option]
            for pk_val, val in self.lookup_choices:
                count = facet_counts[f"{pk_val}__c"]
                choices.append((pk_val, f"{val} ({count})"))
        else:
            choices = [self.all_option, *self.lookup_choices]
        yield from _yield_dropdown(
            title=self.title,
            name=self.lookup_kwarg,
            choices=choices,
            value=self.value(),
            form_class=self.form_class,
            multiple=getattr(self, "multiple", False),
        )


class CleanBooleanDropdownFilter(ValueMixin, DropdownMixin, admin.BooleanFieldListFilter):
    all_option = ALL_OPTION

    def choices(self, changelist: ChangeList) -> Iterator:
        choices = [
            self.all_option,
            ("1", "Так"),
            ("0", "Ні"),
        ]
        yield from _yield_dropdown(
            title=self.title,
            name=self.lookup_kwarg,
            choices=choices,
            value=self.value(),
            form_class=self.form_class,
        )


class CleanAllValuesDropdownFilter(ValueMixin, DropdownMixin, admin.AllValuesFieldListFilter):
    all_option = ALL_OPTION

    def __init__(
        self,
        field: Field,
        request: HttpRequest,
        params: dict[str, str],
        model: type[Model],
        model_admin: admin.ModelAdmin,
        field_path: str,
    ) -> None:
        super().__init__(field, request, params, model, model_admin, field_path)
        # Короткі підписи як на вітрині
        if field_path == "brand":
            self.title = "Бренд"
        elif field_path == "country_of_origin":
            self.title = "Країна виробник"

    def queryset(self, request: HttpRequest, queryset: QuerySet) -> QuerySet | None:
        if self.value() not in EMPTY_VALUES:
            return super().queryset(request, queryset)
        return queryset

    def choices(self, changelist: ChangeList) -> Iterator:
        choices = [self.all_option]
        for val in self.lookup_choices:
            if val in EMPTY_VALUES:
                continue
            choices.append((str(val), str(val)))
        yield from _yield_dropdown(
            title=self.title,
            name=self.lookup_kwarg,
            choices=choices,
            value=self.value(),
            form_class=self.form_class,
        )


class ProductAvailabilityFilter(CleanDropdownFilter):
    title = "Наявність"
    parameter_name = "availability"

    def lookups(self, request: HttpRequest, model_admin: admin.ModelAdmin):
        return (
            ("in_stock", "В наявності"),
            ("out_of_stock", "Немає в наявності"),
        )

    def queryset(self, request: HttpRequest, queryset: QuerySet) -> QuerySet:
        in_stock_ids = queryset.filter(variants__stock_qty__gt=0).values("pk")
        if self.value() == "in_stock":
            return queryset.filter(pk__in=in_stock_ids).distinct()
        if self.value() == "out_of_stock":
            return queryset.exclude(pk__in=in_stock_ids).distinct()
        return queryset


class TopDropdownFiltersMixin:
    """Фільтри зверху; бічний sheet вимкнено."""

    list_filter_sheet = False
    list_filter_submit = False
