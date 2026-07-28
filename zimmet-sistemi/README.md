# Zimmet ve Stok Yonetim Sistemi

Django 5 + PostgreSQL tabanli, kurumsal kullanima uygun Stok ve Zimmet Yonetim Sistemi.
Cihazlar tek tek (seri no ile) degil, **stok mantigiyla** takip edilir: ayni urun tek bir kayittir
ve yalnizca toplam adedi tutulur. Kac adedin zimmette oldugu aktif zimmet kayitlarindan
hesaplanir.

## Ozellikler

- Rol tabanli erisim: **Admin** (tam yonetim) ve **Personel** (yalnizca kendi profili ve cihazlari)
- Kullanici adi veya e-posta ile giris, "Beni Hatirla", sifremi unuttum, sifreyi goster/gizle
- Sirket, Calisan, Cihaz (stok) ve Zimmet icin tam CRUD
- **Stok mantigi**: cihaz yalnizca *ad* ve *toplam adet* ile tutulur; zimmet verildikce bosta adet
  azalir, iade alindikca artar. Toplam adet hicbir zaman degismez.
- Otomatik durum: `Bosta (N)` / `Zimmette (N)` / `Tamami Zimmette` / `Stok Yok` (kullanici girmez)
- Ayni cihazdan birden fazla kisiye, stok adedi kadar zimmet verilebilir
- Arama/filtreleme (cihaz adi, calisan, sirket, teslim/iade tarihi, durum) ve sayfalama
- Chart.js grafikleri ve stok bazli istatistik kartlari iceren Dashboard
- **Gercek zamanli bildirim merkezi**: yeni cihaz, yeni zimmet, iade olaylarinda otomatik bildirim
- **Global canli arama**: navbar'dan cihaz ve personel icinde anlik arama
- **Excel disa/ice aktarma**: stok listesini .xlsx olarak indirme, .xlsx'ten toplu cihaz ekleme
- **Iki ayri PDF tutanak**: teslimde *Zimmet Tutanagi*, iadede *Iade Teslim Tutanagi*
  (hasarsiz/hasarli/eksik kutucuklari ile)
- **Karanlik / Aydinlik tema**: kullanici bazinda (localStorage) saklanan tema tercihi
- Sidebar daraltma/genisletme, hafif sayfa gecis animasyonlari, 4K'ya kadar responsive tasarim
- Sistem genelinde ActivityLog (giris/cikis, olusturma/guncelleme/silme, zimmetleme/iade) ve IP kaydi
- Ozellestirilmis Django Admin paneli
- Ornek veri uretimi icin `seed_data` yonetim komutu

## Teknolojiler

Python 3.11+, Django 5.x, PostgreSQL, Bootstrap 5, Bootstrap Icons, Chart.js, Pillow, django-environ,
Faker, openpyxl, reportlab

## Proje Yapisi

```
zimmet_sistemi/
├── manage.py
├── requirements.txt
├── .env.example
├── config/                 # Django proje ayarlari (settings, urls, wsgi, asgi)
├── apps/
│   ├── accounts/            # Kimlik dogrulama, roller, profil
│   ├── inventory/            # Sirket/Calisan/Cihaz(stok)/Zimmet
│   │   ├── pdf.py                       # Teslim ve iade tutanaklari
│   │   ├── management/commands/seed_data.py
│   │   └── templatetags/inventory_extras.py
│   └── dashboard/            # Yonetim paneli
├── common/                  # middleware.py, context_processors.py, utils.py
├── templates/                # Tum HTML sablonlari
├── static/                  # CSS/JS
└── media/                   # Kullanici yuklemeleri (calisan profil fotograflari)
```

## Kurulum (Docker - tavsiye edilen)

Docker ile PostgreSQL'i ayrica kurmaniza gerek yoktur; veritabani da konteyner olarak calisir.
Gereken tek sey [Docker](https://www.docker.com/products/docker-desktop/)'tir.

```bash
cp docker-compose.override.yml.example docker-compose.override.yml   # yalnizca ilk kurulumda
docker compose build
docker compose up
```

Uygulama `http://localhost:8000/accounts/login/` adresinde acilir.

Ilk `up` sirasinda konteyner sunlari kendisi yapar (manuel adim yoktur):

1. PostgreSQL'in hazir olmasini bekler (`pg_isready`)
2. `python manage.py migrate` calistirir
3. `python manage.py collectstatic` calistirir
4. gunicorn ile uygulamayi baslatir

### Yapilandirma dosyalari

| Dosya | Git'e girer mi | Icerik |
|---|---|---|
| `docker-compose.yml` | **Evet** | Yalnizca yapi: servisler, imaj, volume'lar, saglik kontrolu. Hicbir sir ya da ortama ozgu deger icermez. |
| `docker-compose.override.yml` | **Hayir** | Tum degiskenler: sifreler, `SECRET_KEY`, port eslemesi. |
| `docker-compose.override.yml.example` | **Evet** | Yukaridakinin sirsiz sablonu. |

> Override dosyasi olmadan uygulama **calismaz** (port eslemesi ve veritabani kimlik bilgileri
> orada). Bu bilincli bir tercihtir: `docker-compose.yml` git'e girdigi icin hicbir gizli deger
> barindirmaz. Ilk kurulumda `.example` dosyasini kopyalamayi unutmayin.

Compose, ayni dizindeki `docker-compose.override.yml` dosyasini **otomatik** okur ve
`docker-compose.yml` ile birlestirir; ekstra bir `-f` parametresi gerekmez.

> `DB_HOST` ve `DB_PORT` `docker-compose.yml` icinde sabitlenmistir (`db:5432`), cunku
> konteynerler birbirine servis adiyla ulasir. `.env` icindeki `DB_HOST=127.0.0.1` degeri
> Docker'da kullanilmaz; konteyner icinde kendi localhost'una isaret ederdi.
>
> `.env` dosyasi Docker icin **gerekli degildir** (yerel, Docker'siz kurulumda kullanilir).
> Docker'da tum degerler `docker-compose.override.yml` dosyasindan gelir.

### Sik kullanilan Docker komutlari

```bash
docker compose up -d                  # arka planda calistir
docker compose logs -f web            # uygulama loglarini izle
docker compose down                   # durdur (veri korunur)
docker compose down -v                # durdur ve VERITABANINI DE SIL
docker compose build --no-cache       # imaji sifirdan insa et
docker compose restart web            # yalnizca uygulamayi yeniden baslat
```

### Konteyner icinde Django komutu calistirma

```bash
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py seed_data       # ornek veri yukle
docker compose exec web python manage.py test apps.accounts
docker compose exec db psql -U zimmet_user -d zimmet_db  # veritabanina baglan
```

### Portu degistirme

8000 portu doluysa `docker-compose.override.yml` icindeki `web.ports` degerini duzenleyin:

```yaml
    ports:
      - "8001:8000"     # host:konteyner
```

### Mevcut veritabanini Docker'a tasima

Docker'daki PostgreSQL **bos baslar**; yerel kurulumunuzdaki veriler otomatik gelmez.
Tasimak isterseniz:

```bash
# 1) Yerel veritabanindan yedek alin (Docker'i baslatmadan once, yerel postgres calisirken)
pg_dump -h 127.0.0.1 -U zimmet_user -d zimmet_db -f yedek.sql

# 2) Docker'i baslatin
docker compose up -d

# 3) Yedegi konteynerdeki veritabanina yukleyin
docker compose exec -T db psql -U zimmet_user -d zimmet_db < yedek.sql
```

Profil fotograflari (`media/`) icin bir sey yapmaniz gerekmez: bu klasor konteynere
dogrudan baglanir, mevcut dosyalar aninda gorunur.

### Kalici veri

| Yol | Tur | Icerik |
|---|---|---|
| `./media/` | Host klasoru (bind mount) | Yuklenen profil fotograflari |
| `./staticfiles/` | Host klasoru (bind mount) | Toplanan statik dosyalar (her acilista yeniden uretilir) |
| `postgres_data` | Named volume | Veritabani |

`media/` ve `staticfiles/` proje dizininde durur; dogrudan gorebilir ve yedekleyebilirsiniz.
`docker compose down` (parametresiz) veriyi **silmez**. `docker compose down -v` yalnizca
`postgres_data` volume'unu (veritabanini) siler; host klasorlerine dokunmaz.

### Sunucuya alirken (production)

Imaj mimariden bagimsizdir: hem x86_64 hem arm64 icin tum bagimliliklarin hazir wheel'i
vardir, derleyici gerekmez. **Imaji sunucunun kendisinde `docker compose build` ile insa
edin** — Apple Silicon Mac'te insa edilen imaj arm64 olur ve x86_64 sunucuda calismaz.
(Alternatif: `docker buildx build --platform linux/amd64`.)

Sunucudaki `docker-compose.override.yml` icinde mutlaka degistirin:

- `SECRET_KEY` - yeni bir anahtar uretin:
  `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`
- `POSTGRES_PASSWORD` ve `DB_PASSWORD` - ayni ve guclu bir deger olmali
- `ALLOWED_HOSTS` - sunucunun alan adi / IP'si
- `DEBUG: "False"`

`DEBUG=False` yaptiginizda statik dosyalar WhiteNoise sayesinde calismaya devam eder, ancak
**profil fotograflari (media) sunulmaz**: Django `DEBUG=False` iken media servis etmez.
Sunucuda `media/` klasorunu bir reverse proxy (nginx) ile sunun ya da S3 benzeri bir
depolamaya alin. Bu yuzden yerel Docker varsayilani `DEBUG=True`'dur.

---

## Kurulum (Docker olmadan, yerel)

### 1. Sanal ortam olusturun ve bagimliliklari kurun

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. PostgreSQL veritabani olusturun

```sql
CREATE DATABASE zimmet_db;
CREATE USER zimmet_user WITH PASSWORD 'zimmet_pass';
ALTER ROLE zimmet_user SET client_encoding TO 'utf8';
GRANT ALL PRIVILEGES ON DATABASE zimmet_db TO zimmet_user;
```

### 3. Ortam degiskenlerini ayarlayin

```bash
cp .env.example .env
```

`.env` dosyasindaki `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` degerlerini kendi
PostgreSQL kurulumunuza gore duzenleyin. `SECRET_KEY` degerini production'da mutlaka degistirin.

### 4. Migration'lari calistirin

```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Ornek verileri yukleyin (opsiyonel ama tavsiye edilir)

```bash
python manage.py seed_data
```

Bu komut 3 sirket (Craniocatch, Engelsiz Ceviri, Nevisoft), 25 calisan, 14 cihaz stogu ve
30 zimmet kaydi olusturur. Ayrica asagidaki test hesaplarini da olusturur:

- **Admin girisi:** kullanici adi `admin` / sifre `Admin12345!`
- **Personel girisi:** olusturulan calisanlardan bazilarinin e-posta adresleri (konsol ciktisinda
  gorunur) / sifre `Personel12345!`

Verileri sifirlayip yeniden olusturmak icin: `python manage.py seed_data --reset`

Kendi superuser hesabinizi olusturmak isterseniz:

```bash
python manage.py createsuperuser
```

> Not: Admin panelinden veya `createsuperuser` ile olusturulan hesaplarin `role` alanini
> `admin` olarak ayarlamayi unutmayin (varsayilan deger `staff`'tir).

### 6. Statik dosyalari toplayin (production icin)

```bash
python manage.py collectstatic --noinput
```

### 7. Sunucuyu baslatin

```bash
python manage.py runserver
```

Tarayicida `http://127.0.0.1:8000/accounts/login/` adresine gidin.

## Is Kurallari

- Cihazin **toplam adedi** hicbir islemde degismez; yalnizca yonetici elle guncelleyebilir.
- **Bosta adet = toplam adet - aktif zimmet sayisi** olarak hesaplanir; ayrica saklanmaz, bu sayede
  stok sayaci ile zimmet kayitlari arasinda tutarsizlik olusamaz.
- Bosta adet 0 iken yeni zimmet olusturulamaz. Es zamanli isteklerde stogun asilmamasi icin cihaz
  satiri `select_for_update` ile kilitlenir.
- Toplam adet, halihazirda zimmette olan adedin altina dusurulemez.
- Iade alindiginda `Assignment.returned = True` ve `returned_date` otomatik atanir; adet stoga doner.
- Iade durumu (hasarsiz/hasarli/eksik) yalnizca iade tutanagina yazilir; toplam adedi etkilemez.
- Personel rolundeki kullanicilar yalnizca kendi profillerini ve kendilerine zimmetli/gecmis
  cihazlarini gorebilir; yonetim ekranlarina ve admin paneline erisemezler.
- Sistemde yapilan onemli islemler (giris, cikis, olusturma, guncelleme, silme, zimmetleme, iade)
  otomatik olarak `ActivityLog` tablosuna, kullanici ve IP adresi bilgisiyle birlikte kaydedilir.

## Gelistirme Notlari

- Form alanlarina Bootstrap siniflari `BootstrapFormMixin` araciligiyla otomatik uygulanir.
- Zimmetleme/iade is mantigi `apps/inventory/services.py` icinde toplanmistir; view katmani ince
  tutulmustur.
- PDF tutanaklar `apps/inventory/pdf.py` icinde uretilir. Teslim ve iade belgeleri ortak yapi
  taslarini paylasir ancak birbirinden bagimsiz tasarimlardir.
- Stok sayaclari `Device.objects.with_stock_counts()` ile tek sorguda annotate edilir (N+1 onlenir).
- `common/middleware.py` icindeki `CurrentRequestMiddleware`, sinyallerin (signals.py) aktif
  kullaniciya ve IP adresine view'a parametre gecirmeden erisebilmesini saglar.
- Yetkilendirme `apps/inventory/mixins.py` icindeki `AdminRequiredMixin` ile saglanir.
