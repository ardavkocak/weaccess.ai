"""Portal genelinde kullanilan sablon filtreleri."""
from django import template

register = template.Library()


@register.filter
def startswith(value, prefix):
    """Sidebar'da bir modulun 'aktif' sayilip sayilmayacagini belirlemek icin.

    Entegre edilmis modullerin gercek URL'leri tek bir path'e sabit degildir
    (orn. Zimmet hem /operasyonlar/zimmet/ hem /envanter/... altinda gezinir);
    bu yuzden esitlik yerine on ek karsilastirmasi kullanilir.
    """
    if value is None:
        return False
    return str(value).startswith(str(prefix))


@register.filter
def matches_any_prefix(path, prefixes):
    """
    Bir modulun Sidebar'da 'aktif' (accordion'u acik) sayilip sayilmayacagini
    belirler. Bir modulun birden fazla path on eki olabilir (orn. Zimmet hem
    /operasyonlar/zimmet/ hem /envanter/... altinda gezinir).
    """
    if not path or not prefixes:
        return False
    return any(str(path).startswith(str(prefix)) for prefix in prefixes)
