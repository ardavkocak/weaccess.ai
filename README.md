# weaccess.ai — Ofis Portalı (HR Portal)

Şirket içi operasyonları tek bir web arayüzünden yönetmeyi amaçlayan bir
Django uygulaması (**office-portal**) etrafında toplanmış monorepo.
office-portal, aşağıdaki modülleri kendi içinde (tek process, tek port)
barındırır:

- **Zimmet Yönetimi** — şirket cihaz envanteri ve personel zimmet kayıtları
- **Görev Takibi** — ofis içi günlük görev sırası, Discord entegrasyonu
- **Yemek Sistemi** — aylık yemek menüsü duyuruları ve katılım anketleri
- **İK Otomasyonu** — doğum günü ve iş yıldönümü hatırlatmaları
- **Aylık Takip** — çalışma saati ve izin durumu hesaplama
- **Dokümantasyon** — banka sözleşme/form belgelerinin taranıp Google
  Sheets'e aktarılması
- **Hatırlatıcı Bot** — Google Sheets satış pipeline'ını izleyip Discord'a
  bildirim gönderen bot (ayrı bir container'da çalışır, portal panelinden
  yönetilir)

## Klasör yapısı

```
office-portal/            Ana Django uygulaması (tüm modüller burada birleşir)
ofis-gorev-takibi/         Görev Takibi + Yemek modülünün veri kaynağı (submodule)
discord-bot/                Hatırlatıcı Bot (submodule, ayrı container)
aylik-takip/                 Aylık Takip'in kaynak projesi (submodule)
dokumantasyon-otomasyon/     Dokümantasyon'un kaynak projesi (submodule)
zimmet-sistemi/              Zimmet Yönetimi'nin standalone/kaynak hali
ik-otomasyon/                İK Otomasyonu'nun standalone/kaynak hali
```

Bazı klasörler git submodule'dür (bkz. `.gitmodules`); klonlarken
`--recurse-submodules` kullanın:

```bash
git clone --recurse-submodules <repo-url>
```

## Çalıştırma

### Production — tek komutla tüm servisler

Kök dizindeki `docker-compose.yml`, tüm servisleri (office-portal, zimmet,
görev takibi, İK, aylık takip, dokümantasyon) tek seferde ayağa kaldırır:

```bash
cp docker-compose.override.yml.example docker-compose.override.yml
# override dosyasını doldurun: şifreler, SECRET_KEY, ALLOWED_HOSTS, portlar
docker compose up -d --build
```

`discord-bot` bu dosyada tanımlı değildir — office-portal onu Docker socket
üzerinden, panelin **Hatırlatıcı Bot** ayarlar sayfasından girilen
token/servis hesabı bilgileriyle ayrıca oluşturup yönetir.

### Yerel geliştirme

Her alt proje kendi `docker-compose.yml`/`docker-compose.override.yml`
çiftiyle bağımsız olarak da çalıştırılabilir (ilgili klasördeki README'ye
bakın).

## Erişim

Varsayılan olarak office-portal `http://localhost:8000/` (ya da
override'da tanımladığınız port) üzerinden yayınlanır; diğer tüm modüllere
buradan (sol menü / Dashboard) erişilir.
