# Aylık Çalışma & İzin Takip Ajanı

Haftanın 5 günü, günde 9 saat çalışan bir kişinin aylık çalışma saatini ve izin durumunu; yüklenen bir **çalışma dosyası** (PDF/Word) ve bir **izin görseli** (PNG/JPEG/WebP) üzerinden kontrol eden web uygulaması. Resmi tatiller gömülü olarak kontrol edilir.

## Ne yapar?

- **Input 1 — Çalışma dosyası (Muafiyet Raporu, PDF/Word):** Koordinat bazlı okuma ile tablodaki her personelin **Ad Soyad** ve **Toplam Süre (Saat)** değerini çıkarır (fiili çalışılan saat).
- **Input 2 — İzin görseli (PNG / JPEG / WebP):** OCR ile izin kayıtları listesini okur. Her satırdaki **başlangıç–bitiş tarihi** aralığından izin iş günü hesaplanır, personel adıyla eşleştirilir.
- **Resmi tatiller:** [resmiTatiller.js](resmiTatiller.js) içinde gömülüdür (2025–2026). Yalnızca hafta içine denk gelenler düşülür.

## Hesaplama

```
Çalışması gereken saat = (ayın iş günü − resmi tatil günü − izin günü) × 9
```

Günlük mesai **9 saat** kabul edilir. İzin, görseldeki tarih aralığının hafta içi (Pzt–Cuma) gün sayısıdır (örn. 13.07 → 20.07 = 6 gün × 9 = 54 saat).

## Çıktı (output)

Hesapla butonuna basınca, her personel için tablo halinde:

- **Kaç saat çalışmış** (PDF Toplam Süre)
- **Kaç gün izin almış** — saat karşılığıyla (6 gün × 9 = 54 saat)
- **Resmi izin kaç gün** — saat karşılığıyla
- **Çalışması gereken saat** ve fark (fazla/eksik/tam) durumu

## Kurulum

```bash
npm install
npm start
```

Ardından tarayıcıda: http://localhost:3000

## Yapı

| Dosya | Görev |
|-------|-------|
| [server.js](server.js) | Express backend, `/hesapla` endpoint'i, dosya yükleme |
| [parser.js](parser.js) | PDF koordinat bazlı personel çıkarma (pdfjs-dist), görsel OCR, izin kaydı ayrıştırma, isim eşleştirme |
| [hesaplama.js](hesaplama.js) | Aylık özet iş mantığı (iş günü, izin/resmi saat, çalışması gereken, fark) |
| [resmiTatiller.js](resmiTatiller.js) | Gömülü Türkiye resmi tatilleri |
| [public/index.html](public/index.html) | Arayüz: 2 input + Hesapla butonu + kişi bazlı sonuç tablosu |

## Notlar

- PDF, Nevisoft/ATAP **Muafiyet Raporu** formatında beklenir; tablo sütunları koordinatla okunur (bitişik sayı sorunu yaşanmaz).
- İzin görseli, her satırda `... Ad Soyad <başlangıç tarihi> <bitiş tarihi> <izin tipi> ...` içeren bir izin listesi ekran görüntüsü olmalıdır.
- İzin görselindeki isim, PDF'teki personel adıyla gevşek eşleştirilir (büyük/küçük harf, Türkçe karakter, sıra farkına toleranslı). Eşleşmeyen izinler uyarı olarak gösterilir.
- OCR (tesseract.js) ilk çalıştırmada dil verisini indirdiği için biraz sürebilir.
