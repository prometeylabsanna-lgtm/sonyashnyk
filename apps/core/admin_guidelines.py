"""Підказки для CMS-полів (help_text)."""

IMAGE_PROFILES = {
    "hero": "Рекомендовано ~1600×900, JPG/WebP. Порожнє — static fallback.",
    "story": "Рекомендовано ~800×640. Порожнє — static/img/home/story-*.jpg.",
    "timeline": "Рекомендовано квадрат ~320×320.",
    "produce": "Широкий фон ~1024×778.",
    "block": "Завантажте зображення або залиште порожнім для static fallback.",
}

TEXT_LIMITS = {
    "title": "До ~80 символів для комфортного вигляду.",
    "lead": "1–2 речення.",
    "cta": "Короткий текст кнопки.",
}


def help_for_image(profile: str = "block") -> str:
    return IMAGE_PROFILES.get(profile, IMAGE_PROFILES["block"])


def help_for_key(key: str) -> str:
    if key.endswith("_title") or key.endswith("_name"):
        return TEXT_LIMITS["title"]
    if "lead" in key or key.endswith("_text"):
        return TEXT_LIMITS["lead"]
    if "cta" in key or key.endswith("_btn") or key.endswith("_label"):
        return TEXT_LIMITS["cta"]
    if key.endswith("_image"):
        if "story" in key:
            return help_for_image("story")
        if "timeline" in key:
            return help_for_image("timeline")
        if "produce" in key:
            return help_for_image("produce")
        return help_for_image("block")
    return ""
