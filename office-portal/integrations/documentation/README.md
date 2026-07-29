# documentation — Dokümantasyon Otomasyonu Entegrasyonu

**Kaynak proje:** `dokumantasyon-otomasyon/` · Python + Flask + Playwright + Google Sheets API
**Durum:** Bağlanmadı (placeholder)

## Kaynak projenin özeti

- Banka "Sözleşmeler ve Formlar" sayfasını tarayıp bulduğu doküman
  linklerini Google Sheets'e (veya yerel Excel'e) aktarır
- Kalıcı veri yok; çıktı harici bir Google Sheets dosyasında tutulur
- Playwright/Chromium bağımlılığı nedeniyle imaj boyutu büyük

## Planlanan bağlantı şekli: API

Portal ile aynı dilde (Python) yazılmış olsa da farklı framework
(Flask). Kalıcı veri Google Sheets'te olduğu için veritabanı paylaşımı
anlamsız; bunun yerine:

1. `app.py` içindeki form akışına küçük bir JSON API eklenir
   (`POST /api/tara` → tarama sonucu JSON döner).
2. Portal, formu kendi şablonunda gösterir, isteği bu API'ye iletir,
   sonucu (kaç sözleşme/form bulundu, Sheets linki) kendi arayüzünde
   render eder.

## Bilinen riskler

- Playwright/Chromium indirme süresi ilk çalıştırmada uzun sürebilir —
  API çağrısının zaman aşımı (timeout) portalde yüksek tutulmalı.
- Google Service Account kimlik bilgisi hassas veri; portal bu API'yi
  çağırırken kendi tarafında ayrıca saklamamalı, yalnızca dokumantasyon
  servisine iletmeli.
