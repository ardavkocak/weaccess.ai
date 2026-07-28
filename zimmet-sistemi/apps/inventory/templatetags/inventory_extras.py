"""Sablonlarda kullanilan ozel filtreler ve etiketler."""
from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def querystring_replace(context, **kwargs):
    """Mevcut GET parametrelerini koruyarak belirtilenleri degistiren querystring uretir.

    QueryDict'in kendi urlencode() metodu kullanilir; django.utils.http.urlencode
    bir QueryDict'i doseq=False ile kodlarken degerleri liste olarak alip
    'page=%5B2%5D' ([2]) gibi bozuk ciktilar uretir.
    """
    params = context["request"].GET.copy()
    for key, value in kwargs.items():
        if value is None:
            params.pop(key, None)
        else:
            params[key] = value
    return params.urlencode()
