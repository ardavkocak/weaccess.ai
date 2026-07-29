# Ofis Portalı — İskelet (Faz 1)

Bu proje, `weaccess.ai` çalışma alanındaki bağımsız otomasyon projelerini
(**Zimmet Sistemi**, **Ofis Görev Takibi**, **İK Otomasyonu**, **Aylık
Takip**, **Dokümantasyon Otomasyonu**) tek bir kurumsal arayüz altında
birleştirecek olan Django tabanlı "kabuk" (shell) uygulamadır.

**Bu aşamada hiçbir mevcut modülün koduna dokunulmamıştır.** Yalnızca
ortak Sidebar / Header / Dashboard / Tema iskeleti kurulmuştur. Her modül
şu an sidebar'da yer alan bir bekleme (placeholder) sayfasına açılır.

Tasarım dili doğrudan `zimmet-sistemi` referans alınarak oluşturulmuştur
(Bootstrap 5 + Bootstrap Icons, CSS değişkenleriyle açık/koyu tema,
sidebar daraltma, kart/tablo/pill-badge bileşenleri).

## Kurulum

```bash
cd office-portal
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

python manage.py migrate
python manage.py createsuperuser   # portale giriş yapacak kullanıcı
python manage.py runserver
```

Tarayıcıda `http://127.0.0.1:8000/` adresine gidin; giriş sayfasına
yönlendirilirsiniz. Oluşturduğunuz superuser bilgileriyle giriş yapın.

## Yapı

```
office-portal/
├── manage.py
├── config/                  # Django proje ayarları (settings, urls, wsgi, asgi)
├── portal/                  # Kabuk uygulaması
│   ├── modules.py           # "Operasyonlar" modül listesi — TEK doğruluk kaynağı
│   ├── context_processors.py# Modül listesini tüm şablonlara taşır
│   ├── views.py             # Dashboard + ortak placeholder view'lar
│   └── urls.py
├── templates/
│   ├── base.html            # Ortak Layout (Sidebar + Header + içerik)
│   ├── partials/
│   │   ├── sidebar.html     # Ortak Sidebar
│   │   ├── header.html      # Ortak Header (tema anahtarı, kullanıcı menüsü)
│   │   └── messages.html    # Ortak bildirim/mesaj şeridi
│   ├── dashboard/dashboard.html
│   ├── modules/placeholder.html  # Her modül için ortak "bekleniyor" sayfası
│   ├── profile.html
│   └── registration/login.html
└── static/
    ├── css/theme.css         # Ortak tasarım sistemi (zimmet-sistemi'nden uyarlandı)
    └── js/main.js            # Sidebar daraltma, tema geçişi, ortak davranışlar
```

## Yeni modül eklemek (placeholder → gerçek entegrasyon)

1. `portal/modules.py` içindeki `MODULES` listesine yeni kaydı ekleyin
   (slug, isim, ikon, renk, açıklama, kaynak proje). Sidebar ve Dashboard
   kartı otomatik güncellenir.
2. Modül gerçek projeyle entegre edilmeye hazır olduğunda,
   `portal/views.py` içindeki `ModulePlaceholderView` yerine o modüle özel
   bir view/app bağlanır; Layout, Sidebar, Header, tema hiç değişmez.

## Notlar

- Kimlik doğrulama şu an Django'nun yerleşik `auth` sistemini kullanır
  (tek portal girişi). Mevcut modüllerin kendi auth'ları (zimmet-sistemi,
  ofis-gorev-takibi) ile birleştirme sonraki fazın konusudur.
- Mevcut 5 proje bu iskelete henüz **bağlanmamıştır**; onlar kendi
  klasörlerinde, kendi portlarında çalışmaya devam eder.
