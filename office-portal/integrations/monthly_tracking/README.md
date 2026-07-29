# monthly_tracking — Aylık Takip Entegrasyonu

**Kaynak proje:** `aylik-takip/` · Node.js + Express + tesseract.js (OCR) + pdfjs-dist
**Durum:** Bağlanmadı (placeholder)

## Kaynak projenin özeti

- PDF/Word mesai raporu + izin görselini OCR ile okuyup aylık çalışma
  saati/izin uyuşmazlığını hesaplayan **tek seferlik** araç
- Kalıcı veri/veritabanı yok; her istek bağımsız (stateless)
- Varsayılan port 3000 — **`ofis-gorev-takibi` ile çakışıyor**, birlikte
  çalıştırılacaksa portlardan biri değiştirilmeli

## Planlanan bağlantı şekli: değerlendirilecek (tbd)

Bu araç stateless olduğu için iki makul seçenek var:

1. **Basit proxy/embed**: Portal sadece dosya yükleme formunu gösterir,
   `POST /hesapla` isteğini arka planda `aylik-takip` sunucusuna iletir,
   sonucu kendi şablonunda render eder — kullanıcı hiç ayrı sekme görmez.
2. **Fonksiyon taşıma**: `parser.js`/`hesaplama.js` mantığı ileride
   Python'a çevrilip doğrudan portale gömülebilir (OCR bağımlılığı
   nedeniyle bu seçenek daha maliyetli).

İlk fazda seçenek 1 (proxy/embed) öneriliyor çünkü kaynak kodun mantığına
dokunmadan "tek uygulama hissi" sağlar.

## Bilinen riskler

- Port çakışması (bkz. yukarı) — entegrasyon öncesi çözülmeli.
- OCR ilk çalıştırmada dil verisi indirir; portala embed edilirken bu
  gecikmenin kullanıcıya nasıl gösterileceği (yükleniyor durumu) planlanmalı.
