"""Sablonlara ortak baglam (context) saglayan yardimcilar."""
from django.urls import reverse

from .modules import MODULES, get_module_url


def sidebar_modules(request):
    """
    Sidebar'daki 'Operasyonlar' bolumunu her sayfada kullanilabilir kilar.

    Yalnizca URL reversal (ucuz, I/O yapmaz) eklenir. Adapter'larin
    `health_check()`'i (bazilari canli TCP baglantisi dener) BILEREK
    buraya eklenmez — bu context processor HER istekte calisir; bir
    servisin kapali olmasi, sitedeki HER sayfayi yavaslatirdi. Gercek
    baglanti durumu yalnizca Dashboard'da (bkz. views.DashboardView) ve
    ilgili modulun kendi sayfasinda hesaplanir.

    Bir modulun `children` listesi varsa (alt menu / accordion), her alt
    ogeye de `url` eklenir; Sidebar bu sayede tek bir yerden (bu fonksiyon)
    tum linkleri hazir alir, sablon icinde tekrar {% url %} cozumlemesi
    yapmaz.
    """
    modules = []
    for module in MODULES:
        entry = {**module, "link_url": get_module_url(module)}
        if module.get("children"):
            entry["children"] = [
                {**child, "url": reverse(child["url_name"])} for child in module["children"]
            ]
        modules.append(entry)
    return {"sidebar_modules": modules}
