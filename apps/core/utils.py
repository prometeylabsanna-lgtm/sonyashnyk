"""Спільні хелпери для всіх застосунків."""

import re

from django.utils.text import slugify
from unidecode import unidecode

UA_PHONE_RE = re.compile(r"^\+380\d{9}$")


def normalize_ua_phone(value: str) -> str:
    """Прибирає пробіли та роздільники з номера, лишаючи +380XXXXXXXXX."""
    return (value or "").replace(" ", "").replace("(", "").replace(")", "").replace("-", "")


def slugify_uk(text):
    """Транслітерує кирилицю в латину та повертає ASCII-безпечний slug для URL."""
    return slugify(unidecode(text))


def make_unique_slug(model_cls, base_text, slug_field="slug", instance_pk=None):
    """Генерує унікальний slug у межах моделі, додаючи "-2", "-3"... при колізії."""
    base_slug = slugify_uk(base_text) or "item"
    slug = base_slug
    counter = 2
    queryset = model_cls.objects.all()
    while queryset.filter(**{slug_field: slug}).exclude(pk=instance_pk).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1
    return slug
