# hr — İK Otomasyonu Entegrasyonu

**Kaynak proje:** `ik-otomasyon/` · Node.js + Express + EJS + JSON dosya deposu
**Durum:** Bağlanmadı (placeholder)

## Kaynak projenin özeti

- Excel'den çalışan listesi yükleme, doğum günü / iş yıldönümü hatırlatma
  e-postaları (`src/services/reminder.service.js`, `mail.service.js`)
- Veri kalıcılığı: `data/employees.json`, `data/settings.json` — veritabanı yok
- Ayarlar sayfası **sabit kodlu `admin123` şifresi** ile korunuyor (URL
  query string üzerinden gönderiliyor)

## Entegrasyon öncesi kapatılması gereken borç

Bu proje portale bağlanmadan önce mutlaka:

1. Sabit kodlu şifre ortam değişkenine taşınmalı, query string yerine
   POST body + session tabanlı korumaya geçilmeli.
2. JSON dosya deposu yerine (portal ile ortak) bir veritabanına geçiş
   değerlendirilmeli — aksi halde eşzamanlı yazmalarda veri kaybı riski var.

## Planlanan bağlantı şekli: API

`office_bot` ile aynı mantık: küçük bir salt-okunur API eklenip
(`/api/reminders/upcoming` gibi) Dashboard'da "yaklaşan doğum günleri /
yıldönümleri" kartı gösterilir. Yazma işlemleri (Excel yükleme, ayarlar)
ilk fazda ik-otomasyon'un kendi arayüzünde kalır.
