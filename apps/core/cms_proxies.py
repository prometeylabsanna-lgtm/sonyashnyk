"""Proxy-моделі CMS-секцій (слоти sidebar). Імпортуються з admin."""

from apps.core.models import SiteSettings


class HomeHeroSettings(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = "Головна — Hero"
        verbose_name_plural = "Головна — Hero"


class HomeTrustSettings(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = "Головна — Довіра"
        verbose_name_plural = "Головна — Довіра"


class HomeCategoriesSettings(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = "Головна — Категорії"
        verbose_name_plural = "Головна — Категорії"


class HomeHitsSettings(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = "Головна — Хіти"
        verbose_name_plural = "Головна — Хіти"


class HomeNewsSettings(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = "Головна — Новинки"
        verbose_name_plural = "Головна — Новинки"


class HomeStorySettings(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = "Головна — Історії"
        verbose_name_plural = "Головна — Історії"


class HomeBenefitsSettings(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = "Головна — Переваги"
        verbose_name_plural = "Головна — Переваги"


class HomeSaleSettings(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = "Головна — Акції"
        verbose_name_plural = "Головна — Акції"


class HomeReviewsSettings(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = "Головна — Відгуки"
        verbose_name_plural = "Головна — Відгуки"


class SiteHeaderSettings(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = "Шапка"
        verbose_name_plural = "Шапка"


class SiteFooterSettings(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = "Підвал"
        verbose_name_plural = "Підвал"


class SiteLeadModalSettings(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = "Модалка заявки"
        verbose_name_plural = "Модалка заявки"


class SiteFabSettings(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = "Кнопка звʼязку"
        verbose_name_plural = "Кнопка звʼязку"


class AboutIntroSettings(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = "Про нас — Інтро"
        verbose_name_plural = "Про нас — Інтро"


class AboutShelvesSettings(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = "Про нас — Полички"
        verbose_name_plural = "Про нас — Полички"


class AboutTimelineSettings(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = "Про нас — Хронологія"
        verbose_name_plural = "Про нас — Хронологія"


class AboutPhilosophySettings(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = "Про нас — Філософія"
        verbose_name_plural = "Про нас — Філософія"


class AboutWhySettings(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = "Про нас — Чому ми"
        verbose_name_plural = "Про нас — Чому ми"


class AboutProduceSettings(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = "Про нас — CTA"
        verbose_name_plural = "Про нас — CTA"


class DeliveryPageSettings(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = "Доставка і оплата"
        verbose_name_plural = "Доставка і оплата"


class CertificatesPageSettings(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = "Сертифікати — сторінка"
        verbose_name_plural = "Сертифікати — сторінка"


class ContactsPageSettings(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = "Контакти"
        verbose_name_plural = "Контакти"


class OfferPageSettings(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = "Оферта"
        verbose_name_plural = "Оферта"


class PrivacyPageSettings(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = "Політика"
        verbose_name_plural = "Політика"


class CatalogPageSettings(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = "Каталог — сторінка"
        verbose_name_plural = "Каталог — сторінка"


class SearchPageSettings(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = "Пошук"
        verbose_name_plural = "Пошук"


class CartPageSettings(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = "Кошик"
        verbose_name_plural = "Кошик"


class CheckoutPageSettings(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = "Оформлення"
        verbose_name_plural = "Оформлення"


class ThankYouPageSettings(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = "Дякуємо"
        verbose_name_plural = "Дякуємо"


class Error404Settings(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = "Сторінка 404"
        verbose_name_plural = "Сторінка 404"


class SiteCartDrawerSettings(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = "Шторка кошика"
        verbose_name_plural = "Шторка кошика"


class CatalogFiltersSettings(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = "Каталог — фільтри"
        verbose_name_plural = "Каталог — фільтри"


class WishlistPageSettings(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = "Обране"
        verbose_name_plural = "Обране"


class ProductPageSettings(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = "Картка товару"
        verbose_name_plural = "Картка товару"
