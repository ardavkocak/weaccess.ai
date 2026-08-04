# Hatırlatıcı Discord Botu

Google Sheets'teki "Sales Pipeline" tablosunu periyodik olarak okuyup şu olaylarda
Discord'a bildirim atar, ve kullanıcılar bu bildirimleri slash komutlarla
kendi tercihlerine göre ayarlayabilir:

- 🆕 Yeni fırsat eklendiğinde
- 🔄 Satış Aşaması / Fırsat Durumu değiştiğinde
- ❌ Fırsat "Kaybedildi" olarak işaretlendiğinde
- ⏰ Bir fırsat, "Devam Ediyor" durumundayken belirli bir süre güncellenmediğinde

## 1. Discord Bot Uygulaması Oluşturma

1. https://discord.com/developers/applications adresine git, **New Application**.
2. **Bot** sekmesinden bot oluştur, **Reset Token** ile token'ı al (bu değeri `.env`'e `DISCORD_TOKEN` olarak yazacaksın).
3. Aynı sekmede **Privileged Gateway Intents** altında **Server Members Intent**'i aç.
4. **OAuth2 > URL Generator** sekmesinde:
   - Scopes: `bot`, `applications.commands`
   - Bot Permissions: `Send Messages`, `Embed Links`, `Read Message History`
   - Oluşan URL ile botu sunucuna davet et.

## 2. Google Sheets Erişimi (Servis Hesabı)

1. https://console.cloud.google.com adresinde bir proje oluştur (veya mevcut birini kullan).
2. **APIs & Services > Library** üzerinden **Google Sheets API**'yi etkinleştir.
3. **APIs & Services > Credentials > Create Credentials > Service Account** ile bir servis hesabı oluştur.
4. Servis hesabının **Keys** sekmesinden **JSON** formatında bir anahtar indir; bu dosyayı proje klasörüne `credentials.json` adıyla koy.
5. İndirdiğin JSON içindeki `client_email` adresini kopyala (örn. `xxx@xxx.iam.gserviceaccount.com`).
6. Google Sheets dosyasını aç, **Paylaş** butonuyla bu e-posta adresine en azından **Görüntüleyici (Viewer)** izni ver.
7. Sheet URL'sindeki ID'yi kopyala:
   `https://docs.google.com/spreadsheets/d/BURASI_SPREADSHEET_ID/edit` → `SPREADSHEET_ID` olarak `.env`'e yaz.

> Not: Şu an web sitesindeki verileri Sheets'e sen aktarıyorsun; bot yalnızca Sheets'i okur.
> İstersen ileride bu aktarımı da Apps Script ile yarı otomatik hale getirebiliriz.

## 3. Ortam Değişkenleri

```bash
cp .env.example .env
# .env dosyasını doldur: DISCORD_TOKEN, SPREADSHEET_ID, WORKSHEET_NAME
```

`WORKSHEET_NAME` görseldeki gibi sekme adına birebir eşit olmalı (örn. `Sales Pipeline`).
Sütun başlıkları da `config.py` içindeki `COL_*` sabitleriyle birebir aynı olmalı;
tablo başlıklarını değiştirirsen `config.py`'yi de güncelle.

## 4. Yerel Çalıştırma (test için)

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python bot.py
```

## 5. Docker Compose ile Çalıştırma

Bu repo yalnızca bot backend'ini içerir (web arayüzü yok — ayrı bir repoda geliştirilecek).

```bash
cp .env.example .env
# .env dosyasını doldur (bkz. bölüm 3)
docker compose up -d --build
docker compose logs -f
```

Veritabanı (`./data`) host'ta bind-mount ile kalıcıdır; `credentials.json` salt-okunur
olarak bağlanır. `weaccess.ai` monorepo'suna submodule olarak eklendiyse `start-all.ps1`
bu servisi otomatik ayağa kaldırır (bkz. o reponun README'si).

## 6. Kullanım (Slash Komutları)

| Komut | Açıklama |
|---|---|
| `/bildirim-ekle tur:<...> firma:<opsiyonel> kanal:<opsiyonel> kaynak:<opsiyonel>` | Yeni bir bildirim aboneliği oluşturur. Firma boşsa tüm firmalar, kanal boşsa DM. `kaynak` verilmezse sunucunun ana sheet'i, verilirse kendi `/sheet-ekle` ile eklediğin bir sheet'in bildirimlerini yönlendirir. |
| `/bildirim-listele` | Kendi aboneliklerini listeler. |
| `/bildirim-sil id:<...>` | Belirtilen aboneliği siler. |
| `/rapor` | Anlık pipeline özetini gösterir (sadece sana görünür, sunucunun ana sheet'i). |
| `/sheet-ekle etiket:<...> spreadsheet_id:<...> sekme_adi:<...> dakika:<opsiyonel> eskime_gun:<opsiyonel>` | Kendi kişisel Google Sheet kaynağını ekler (aynı etiketle tekrar çalıştırırsan günceller). Aynı botu birden fazla kişi, herkes kendi sheet'iyle kullanabilir. |
| `/sheet-listele` | Kendi eklediğin sheet kaynaklarını listeler. |
| `/sheet-sil etiket:<...>` | Kendi eklediğin bir sheet'i siler (ilişkili bildirim abonelikleri de temizlenir). |
| `/ayar kanal <#kanal>` | *(Yönetici)* Sahipsiz bildirimlerin düşeceği varsayılan kanalı ayarlar (ana sheet için). |
| `/ayar olay-kanal tur:<...> <#kanal>` | *(Yönetici)* Belirli bir olay türü için sunucu geneli varsayılan kanal atar (ana sheet için). |
| `/ayar siklik <dakika>` | *(Yönetici)* Ana sheet'in kontrol sıklığını değiştirir. |
| `/ayar eskime-esigi <gün>` | *(Yönetici)* Ana sheet için kaç gün güncellenmeyen fırsatın "eski" sayılacağını ayarlar. |
| `/ayar sheet <spreadsheet_id> <sekme_adı>` | *(Yönetici)* Sunucunun ana sheet'ini/sekmesini değiştirir. |

Örnek: Sadece "ESBAŞ" firması kaybedildiğinde DM almak için:
```
/bildirim-ekle tur:Fırsat kaybedildiğinde firma:ESBAŞ
```

### Kişisel Sheet Kaynakları (Çoklu Kullanıcı)

Aynı bot, aynı sunucuda birden fazla kişi tarafından, herkes kendi Google Sheet'iyle
kullanılabilir. Sunucunun tek bir "ana" sheet'i (`/ayar sheet`, yönetici) dışında,
her kullanıcı kendi kişisel sheet kaynaklarını da ekleyebilir:

```
/sheet-ekle etiket:musteri-a spreadsheet_id:<link veya id> sekme_adi:"Sales Pipeline"
```

- Bir kişi birden fazla sheet ekleyebilir, her biri farklı bir `etiket` ile ayırt edilir.
- Her kişisel sheet, sunucunun ana sheet'inden tamamen bağımsız ve izole taranır
  (kendi kontrol sıklığı/eskime eşiği ayarlanabilir, `dakika`/`eskime_gun` parametreleriyle).
- Varsayılan olarak, kişisel bir sheet'teki olaylar **sahibine doğrudan DM** olarak gider.
  Bunu değiştirmek istersen (örn. bir kanala veya başka bir kişiye de gitsin), aynı sheet
  için `/bildirim-ekle kaynak:musteri-a ...` ile ek/override abonelik tanımlayabilirsin.
- Google servis hesabının (`credentials.json`), eklenen her kişisel sheet'e de en az
  Görüntüleyici izniyle paylaşılmış olması gerekir (bkz. bölüm 2).
- Bir kullanıcı sunucudan ayrılırsa (kick/ban dahil), botu kullanmayı bıraktığı varsayılır:
  kendi eklediği tüm kişisel sheet'ler (ve bunların poll döngüleri) ile tüm bildirim
  abonelikleri (ana sheet dahil) otomatik olarak silinir.

## Sınırlamalar / Sonraki Adımlar

- Şu an Excel dosyası okunmuyor, sadece Google Sheets okunuyor (görüşmede belirttiğin gibi
  ikisi ayrı ayrı güncellendiği için tek bir "doğruluk kaynağı" seçmek gerekiyordu).
  İstersen Microsoft Graph API ile Excel Online desteği de ekleyebiliriz.
- Notlardaki serbest metinden ("Gelecek hafta kararlarını bildirecekler" gibi) otomatik
  tarih/hatırlatma çıkarımı şu an yapılmıyor; istersen bir sonraki adımda bunu da ekleyebiliriz.
