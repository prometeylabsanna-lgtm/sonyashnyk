from django.urls import path

from . import views

app_name = "catalog"

urlpatterns = [
    # /katalog/aktsiyi/ має йти РАНІШЕ загального <slug:slug>/, інакше "aktsiyi"
    # буде сприйнято як звичайний slug категорії.
    path("aktsiyi/", views.sale, name="sale"),
    path("<slug:slug>/", views.category, name="category"),
]
