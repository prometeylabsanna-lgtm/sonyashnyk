"""Кастомні поля моделей."""

from pathlib import Path

from django.db.models.fields.files import ImageField, ImageFieldFile

from apps.core.image_webp import convert_file_to_webp_content, is_already_webp


class WebPImageFieldFile(ImageFieldFile):
    def save(self, name, content, save=True):
        if content is not None:
            original = getattr(content, "name", None) or name
            converted = convert_file_to_webp_content(content, original_name=original)
            if converted is not None:
                content = converted
                name = converted.name
            elif not is_already_webp(name):
                name = f"{Path(original).stem}.webp"
        super().save(name, content, save=save)


class WebPImageField(ImageField):
    """ImageField, яке при збереженні конвертує файл у WebP."""

    attr_class = WebPImageFieldFile

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        return name, "django.db.models.ImageField", args, kwargs
