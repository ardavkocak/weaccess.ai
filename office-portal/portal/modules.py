"""
Portaldeki "Operasyonlar" mod ullerinin tek dogruluk kaynagi.

Sidebar, Dashboard karti listesi ve mod ul placeholder sayfalari hepsi bu
listeden beslenir. Ileride bir mod ul gercek projeye baglanacagi zaman
yalnizca ilgili kaydin `url` (veya entegrasyon) bilgisini guncellemek
yeterli olur; sablonlarda tekrar tekrar link/ikon tanimlamaya gerek kalmaz.

Her mod ul, kaynak proje klasorune referansla eslendi (bkz. `source`) —
boylece hangi placeholder'in hangi mevcut projeye karsilik geldigi net kalir.

`integration_key`, `integrations/registry.py` icindeki adapter'lardan
hangisine bagli oldugunu belirtir (bkz. `integrations/` paketi). Birden
fazla modul ayni adapter'i paylasabilir (orn. gorev-takibi + yemek ->
office_bot), cunku ikisi de ayni kaynak projeden gelir.

Bir modul gercek projeyle entegre edildiginde `url_name` (gercek Django
URL adi, orn. "dashboard:home") ve `active_prefix` (Sidebar'da o modulun
"aktif" gorunmesi gereken path on eki, orn. "/envanter/") eklenir. Bu
alanlar yoksa Sidebar/Dashboard hala genel ModulePlaceholderView'a
baglanir; boylece entegrasyon modul modul, sablonlara dokunmadan ilerler.
"""

MODULES = [
    {
        "slug": "zimmet",
        "name": "Zimmet Yönetimi",
        "icon": "bi-boxes",
        "color": "blue",
        "description": "Şirket cihaz envanteri ve personel zimmet kayıtlarının yönetimi.",
        "source": "zimmet-sistemi",
        "integration_key": "inventory",
        "url_name": "dashboard:home",
        "active_prefixes": ["/operasyonlar/zimmet/", "/envanter/"],
        "children": [
            {"name": "Dashboard", "icon": "bi-grid-1x2", "url_name": "dashboard:home"},
            {"name": "Çalışanlar", "icon": "bi-people", "url_name": "inventory:employee-list"},
            {"name": "Cihazlar", "icon": "bi-box-seam", "url_name": "inventory:device-list"},
            {"name": "Şirketler", "icon": "bi-building", "url_name": "inventory:company-list"},
            {"name": "Zimmet Kayıtları", "icon": "bi-clipboard-check", "url_name": "inventory:assignment-list"},
        ],
    },
    {
        "slug": "gorev-takibi",
        "name": "Görev Takibi",
        "icon": "bi-list-check",
        "color": "green",
        "description": "Ofis içi günlük görev sırası, Discord entegrasyonu ve görev geçmişi.",
        "source": "ofis-gorev-takibi",
        "integration_key": "office_bot",
        "url_name": "office_bot:duty_dashboard",
        "active_prefixes": ["/operasyonlar/gorev-takibi/"],
        "children": [
            {"name": "Dashboard", "icon": "bi-grid-1x2", "url_name": "office_bot:duty_dashboard"},
            {"name": "Personeller", "icon": "bi-people", "url_name": "office_bot:employee_list"},
            {"name": "Görev Sırası", "icon": "bi-list-ol", "url_name": "office_bot:queue"},
            {"name": "Görev Geçmişi", "icon": "bi-clock-history", "url_name": "office_bot:history"},
            {"name": "Discord Ayarları", "icon": "bi-discord", "url_name": "office_bot:settings_discord"},
            {"name": "Bildirim Saatleri", "icon": "bi-alarm", "url_name": "office_bot:settings_schedule"},
            {"name": "Günlük Ayarlar", "icon": "bi-sliders", "url_name": "office_bot:settings_general"},
            {"name": "Test İşlemleri", "icon": "bi-terminal", "url_name": "office_bot:test_actions"},
        ],
    },
    {
        "slug": "yemek",
        "name": "Yemek Sistemi",
        "icon": "bi-cup-hot",
        "color": "amber",
        "description": "Aylık yemek menüsü duyuruları ve katılım anketleri.",
        "source": "ofis-gorev-takibi",
        "integration_key": "office_bot",
        "url_name": "office_bot:meal_dashboard",
        "active_prefixes": ["/operasyonlar/yemek/"],
        "children": [
            {"name": "Dashboard", "icon": "bi-grid-1x2", "url_name": "office_bot:meal_dashboard"},
            {"name": "Test İşlemleri", "icon": "bi-terminal", "url_name": "office_bot:meal_test_actions"},
        ],
    },
    {
        "slug": "ik-otomasyon",
        "name": "İK Otomasyonu",
        "icon": "bi-person-badge",
        "color": "purple",
        "description": "Doğum günü ve iş yıldönümü hatırlatma otomasyonu.",
        "source": "ik-otomasyon",
        "integration_key": "hr",
        "url_name": "hr:dashboard",
        "active_prefixes": ["/operasyonlar/ik-otomasyon/"],
    },
    {
        "slug": "aylik-takip",
        "name": "Aylık Takip",
        "icon": "bi-calendar3",
        "color": "teal",
        "description": "Aylık çalışma saati ve izin durumu hesaplama aracı.",
        "source": "aylik-takip",
        "integration_key": "monthly_tracking",
        "url_name": "monthly_tracking:dashboard",
        "active_prefixes": ["/operasyonlar/aylik-takip/"],
    },
    {
        "slug": "dokumantasyon",
        "name": "Dokümantasyon",
        "icon": "bi-file-earmark-text",
        "color": "red",
        "description": "Banka sözleşme/form belgelerinin taranıp Google Sheets'e aktarılması.",
        "source": "dokumantasyon-otomasyon",
        "integration_key": "documentation",
        "url_name": "documentation:dashboard",
        "active_prefixes": ["/operasyonlar/dokumantasyon/"],
    },
    {
        "slug": "discord-bot",
        "name": "Hatırlatıcı Bot",
        "icon": "bi-discord",
        "color": "slate",
        "description": "Google Sheets satış pipeline'ını izleyip Discord'a bildirim/hatırlatma gönderen bot; ayrı bir container'da çalışır.",
        "source": "discord-bot",
        "integration_key": "discordbot",
        "url_name": "discordbot:dashboard",
        "active_prefixes": ["/operasyonlar/discord-bot/"],
    },
]

_MODULES_BY_SLUG = {module["slug"]: module for module in MODULES}


def get_module(slug):
    """Verilen slug'a karsilik gelen modul tanimini dondurur, yoksa None."""
    return _MODULES_BY_SLUG.get(slug)


def get_module_url(module):
    """
    Bir modulun gercek gidecegi URL'i dondurur.

    Entegre edilmis modullerde `url_name` gercek view'a isaret eder; henuz
    entegre edilmemis (varsayimsal, ileride eklenecek) moduller icin genel
    ModulePlaceholderView'a duser. Sidebar VE Dashboard karti AYNI bu
    fonksiyonu kullanir; boylece iki yerde ayri ayri link mantigi
    tekrarlanmaz (bkz. templates/partials/sidebar.html, dashboard/dashboard.html).
    """
    from django.urls import reverse

    if module.get("url_name"):
        return reverse(module["url_name"])
    return reverse("portal:module", kwargs={"slug": module["slug"]})


def get_module_status(module):
    """Bir modulun bagli oldugu adapter'in (varsa) health_check sonucunu dondurur."""
    from integrations.registry import get_integration

    integration = get_integration(module.get("integration_key"))
    if integration:
        return integration.health_check()
    return False, "Bu modül için entegrasyon tanımlı değil."
