# Dokümantasyon Otomasyonu — Banka Sözleşme & Form → Google Sheets / Excel

Bir bankanın **"Sözleşmeler ve Formlar"** sayfasının URL'sini alır; sayfadaki tüm
doküman (PDF, DOC, XLS...) bağlantılarını başlıklarıyla birlikte çıkarır ve
banka adıyla açılan bir sekmeye **paylaşılan Google Sheets** dosyasına yazar
(isteğe bağlı olarak yerel bir **Excel** dosyasına da kaydedilebilir).

Belirli bir bankaya bağımlı değildir — sayfadaki tüm doküman bağlantılarını
tarayarak çalışır. Sayfa JavaScript ile yükleniyorsa otomatik olarak
(Playwright ile) gerçek bir tarayıcıda açılıp öyle okunur — bu sayede her
banka sitesinde çalışır.

## Kullanım şekilleri

1. **Web arayüzü** (`app.py`) — Banka adı ve sayfa linkini girip tek tıkla
   Google Sheets'e aktarma. Önerilen kullanım şekli.
2. **Komut satırı** (`main.py`) — Tek bir bankayı yerel bir Excel dosyasına aktarma.

---

## Kurulum (yerel geliştirme)

Python 3.10+ gereklidir.

```bash
python -m pip install -r requirements.txt
python -m playwright install chromium
```

### Google Sheets bağlantısı için tek seferlik kurulum

1. **Google Cloud Console'a git:** https://console.cloud.google.com/
2. Yeni bir proje oluştur.
3. "APIs & Services" → "Library" üzerinden **Google Sheets API** ve
   **Google Drive API**'yi etkinleştir.
4. "APIs & Services" → "Credentials" → "Create Credentials" → **Service Account**
   oluştur.
5. Oluşturduğun servis hesabına tıkla → "Keys" → "Add Key" → "Create new key"
   → **JSON** seç → indir.
6. İndirilen JSON dosyasını proje köküne `service_account.json` adıyla koy
   (veya başka bir yere koyup yolunu `.env` dosyasında belirt).
7. JSON dosyasındaki `client_email` alanındaki adresi kopyala.
8. Hedef Google Sheets dosyasını aç → sağ üst **"Paylaş"** → bu e-postayı
   **Düzenleyen (Editor)** olarak ekle.
9. `.env.example` dosyasını `.env` olarak kopyala ve doldur:

```env
GOOGLE_SERVICE_ACCOUNT_JSON=service_account.json
GOOGLE_SHEETS_URL=https://docs.google.com/spreadsheets/d/XXXXXXXXXXXXXXXXXXXXXXXXXXXX/edit
```

`.env` ve `service_account.json` dosyaları `.gitignore` içinde olduğu için
asla repoya gitmez.

---

## 1) Web arayüzü ile kullanım

```bash
python app.py
```

Tarayıcıda **http://127.0.0.1:5000** adresini aç:

- **Banka Adı** — Google Sheets'te açılacak sekmenin adı (ör. "T-Bank")
- **Sözleşmeler ve Formlar Sayfası URL'si** — bankanın ilgili sayfa linki
- **Tarayıcı ile aç (JS)** — ilk denemede belge bulunamazsa işaretleyip tekrar dene

Gönderince:
1. Sayfa indirilir (gerekirse Playwright ile JS render edilerek),
2. Belgeler ayıklanıp Sözleşme/Form olarak kategorilendirilir,
3. `GOOGLE_SHEETS_URL` ile belirtilen Sheets dosyasında **banka adıyla** yeni bir
   sekme açılır (aynı isimde sekme varsa mevcut gruplar korunarak güncellenir),
4. Ekranda sonuç özeti ve sekmeye giden link gösterilir.

Aynı bankayı farklı sayfalarından (ör. önce "Sözleşmeler", sonra "Formlar")
art arda çekmek, önceki grubu silmez — sadece ilgili kategori güncellenir,
diğerleri korunur.

## 2) Komut satırı ile kullanım (yerel Excel)

```bash
# Otomatik dosya adıyla
python main.py "https://www.tbank.com.tr/hakkimizda/detay/Sozlesmeler-ve-Formlar/188/275/0/"

# Belirli bir çıktı dosyası adıyla
python main.py "<URL>" -o sonuc.xlsx
```

---

## Çıktı düzeni (hem Sheets hem Excel için ortak)

Belgeler kategoriye göre gruplanır: önce **Formlar**, sonra **Sözleşmeler**,
varsa en sonda **Diğer**. Her grubun tek sütunu vardır — **Başlık** — ve bu
hücrenin görünen metni belge başlığıdır, tıklandığında ilgili dosyanın
bağlantısına gider (URL, hücrenin kendisine gömülüdür).

---

## Kendi Sunucuna (VPS) Deploy

Proje tamamen **Dockerize** — Docker ve Docker Compose kurulu herhangi bir
Linux sunucuda (DigitalOcean, Hetzner, kendi VPS'in vb.) çalıştırılabilir.

Yapı iki dosyaya ayrılmıştır:

| Dosya | İçerik | Repoya gider mi? |
|-------|--------|-------------------|
| [docker-compose.yml](docker-compose.yml) | Sabit yapı: build talimatı, imaj adı, restart politikası | ✅ Evet |
| `docker-compose.override.yml` | Ortama özgü değerler: dışa açılan port, `.env` dosyası | ❌ Hayır (`.gitignore`'da) |

Bu ayrım sayesinde `docker-compose.yml` her sunucuda aynı kalır; port veya
ortam değişkeni gibi sunucuya özgü ayarlar sadece senin sunucunda duran
`docker-compose.override.yml` içinde tutulur ve asla repoya karışmaz.

### 1. Sunucuda Docker kurulu olduğundan emin ol

```bash
docker --version
docker compose version
```

Kurulu değilse: https://docs.docker.com/engine/install/ adresindeki resmi
kurulum adımlarını izle (Ubuntu/Debian için `apt` üzerinden kurulabilir).

### 2. Projeyi sunucuya çek

```bash
git clone <repo-url>
cd Dokumantasyon-otomasyon
```

### 3. Servis hesabı ve Sheets bilgilerini `.env` dosyasına yaz

`.env.example` dosyasını `.env` olarak kopyala:

```bash
cp .env.example .env
```

Ve doldur:

```env
GOOGLE_SHEETS_URL=https://docs.google.com/spreadsheets/d/XXXXXXXXXXXXXXXXXXXXXXXXXXXX/edit
GOOGLE_SERVICE_ACCOUNT_JSON={"type":"service_account","project_id":"...", ...}
```

**Dikkat:** `GOOGLE_SERVICE_ACCOUNT_JSON` burada bir dosya yolu değil,
**JSON içeriğinin kendisi** (tek satır) olmalı. Sebebi: `service_account.json`
dosyası `.dockerignore` ile bilerek imaja dahil edilmiyor (gizli bilgi
imaja gömülmesin diye); bunun yerine container içine ortam değişkeni
üzerinden aktarılıyor. JSON dosyasının içeriğini olduğu gibi kopyalayıp
`.env`'e yapıştırman yeterli — kod, değerin `{` ile başladığını görünce
bunu otomatik olarak kimlik bilgisi olarak yorumlar.

### 4. Override dosyasını oluştur

```bash
cp docker-compose.override.yml.example docker-compose.override.yml
```

Gerekirse [docker-compose.override.yml.example](docker-compose.override.yml.example)
içindeki portu (`"5000:5000"`) sunucunda kullanmak istediğin porta göre
düzenle (ör. `"8080:5000"` dersen dışarıya 8080 portundan açılır).

### 5. Build edip başlat

```bash
docker compose up -d --build
```

Birkaç dakika içinde (ilk build'de Chromium indirileceği için biraz uzun
sürebilir) `http://<sunucu-ip>:5000` adresinde web arayüzü ayakta olur.

### Yönetim komutları

```bash
docker compose logs -f        # canlı logları izle
docker compose down           # durdur
docker compose up -d --build  # kod güncellemesi sonrası yeniden build+başlat
```

İsteğe bağlı olarak bir domain bağlayıp HTTPS (nginx + Let's Encrypt)
eklemek istersen, bu adım bu projenin kapsamı dışındadır ama container
5000 portunda normal bir HTTP servisi olarak çalıştığı için herhangi bir
reverse proxy önüne rahatlıkla konabilir.

---

## Proje yapısı

| Dosya | Sorumluluk |
|-------|------------|
| [app.py](app.py) | Flask web arayüzü — form ve akış yönetimi |
| [templates/index.html](templates/index.html) | Web arayüzü şablonu |
| [main.py](main.py) | Komut satırı arayüzü (CLI) — yerel Excel akışı |
| [scraper.py](scraper.py) | Sayfayı indirir (statik veya Playwright ile), doküman bağlantılarını ayıklar, kategorilendirir |
| [sheets_export.py](sheets_export.py) | Belgeleri Google Sheets'e, banka adıyla sekme açarak yazar (tıklanabilir `HYPERLINK` formülüyle) |
| [excel_export.py](excel_export.py) | Belge listesini biçimlendirilmiş yerel Excel'e yazar |
| [Dockerfile](Dockerfile) | Docker imajı — Playwright'ın Chromium'u dahil tüm bağımlılıklar |
| [docker-compose.yml](docker-compose.yml) | Sabit Docker Compose yapısı |
| [docker-compose.override.yml.example](docker-compose.override.yml.example) | Örnek sunucuya özgü ayarlar (port, `.env`) — kopyalanıp `docker-compose.override.yml` yapılır |
| [.dockerignore](.dockerignore) | Docker imajına dahil edilmeyecek dosyalar |
| [.env.example](.env.example) | Örnek ortam değişkenleri şablonu |
| [requirements.txt](requirements.txt) | Bağımlılıklar (Playwright dahil) |

## Notlar ve sınırlamalar

- **Karakter kodlaması:** Türkçe karakterlerin bozulmaması için kodlama
  HTTP başlığı → `<meta charset>` → tahmin → UTF-8 sırasıyla belirlenir.
  Playwright yolu zaten doğru decode edilmiş HTML döndürür.
- **JavaScript ile yüklenen sayfalar:** Önce hızlı statik istek denenir;
  hiç belge bulunamazsa otomatik olarak Playwright (headless Chromium) ile
  sayfa gerçek bir tarayıcıda açılıp yeniden denenir. Web arayüzünde
  "Tarayıcı ile aç (JS)" kutusunu işaretleyerek bunu manuel olarak da
  zorlayabilirsin.
- **Docker imaj/Playwright sürüm eşleşmesi:** [Dockerfile](Dockerfile)'daki
  `mcr.microsoft.com/playwright/python:vX.Y.Z-jammy` imaj etiketi ile
  [requirements.txt](requirements.txt)'deki `playwright==X.Y.Z` sürümü
  **birebir aynı olmalı**. Farklıysa, pip farklı bir Chromium build'i bekler
  ve imajdaki önceden kurulu tarayıcı bulunamaz hatası alınır
  (`BrowserType.launch: Executable doesn't exist`). İkisini birlikte güncelle.
- **Uzantısız/CMS-özel doküman linkleri:** Bazı bankalar (ör. DenizBank)
  belgeleri `.pdf` yerine kendi CMS'lerine özgü bir medya endpoint'i
  üzerinden sunar (`.vsf` gibi). Bu durumda link metnindeki "İndir"/"Download"
  gibi ifadelere bakılarak doküman tespit edilir (bkz. `scraper.py`
  `INDIRME_ANAHTAR_KELIMELERI`).
- **Doküman türleri:** `.pdf, .doc, .docx, .xls, .xlsx, .rtf, .txt` uzantıları
  doküman olarak kabul edilir. `scraper.py` içindeki `DOCUMENT_EXTENSIONS`
  listesinden değiştirilebilir.
- **Sekme adları:** Google Sheets sekme adlarında geçersiz karakterler
  (`: \ / ? * [ ]`) otomatik olarak `-` ile değiştirilir, 100 karakterle sınırlanır.
- **Google Sheets kimlik bilgisi:** `GOOGLE_SERVICE_ACCOUNT_JSON` değeri hem bir
  dosya yolu (`service_account.json`) hem de doğrudan JSON içeriği olabilir —
  hangisinin verildiği otomatik algılanır (`{` ile başlıyorsa JSON içeriği).
