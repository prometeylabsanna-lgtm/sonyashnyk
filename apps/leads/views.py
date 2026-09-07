from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .forms import LeadForm


@require_POST
def lead_create(request):
    """Універсальний обробник заявок: модалка телефону, «1 клік», контактна форма, підписка.

    Повертає JSON — фронтовий JS сам показує повідомлення про успіх без перезавантаження сторінки.
    """
    form = LeadForm(request.POST)
    if form.is_valid():
        form.save()
        return JsonResponse({"ok": True, "message": "Дякуємо! Ми зв'яжемося з вами найближчим часом."})
    return JsonResponse({"ok": False, "errors": form.errors}, status=400)
