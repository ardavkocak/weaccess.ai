# İK Otomasyon

## Kurulum

```bash
cp .env.example .env
npm install
npm run dev
```

`http://localhost:3002` adresinden Excel dosyasını yükleyin. Başlıklar `Ad Soyad`, `Doğum Tarihi` ve `İşe Giriş Tarihi` olmalıdır.

## Otomasyon kuralları

- Her ayın son cuma kutlanacak doğum günleri için, iki gün önce İK'ya toplu e-posta gider.
- 3 yıl ve katlarındaki işe giriş yıl dönümlerinde, iki gün önce plaket e-postası gider.
- Hesaplanan gönderim Cumartesi/Pazar ise önceki Cuma gününe çekilir.
- Cron, iş günlerinde 09:00'da çalışır. Aynı hatırlatma iki kez gönderilmez.
- Paneldeki **İK e-postasını test et** düğmesi ise her tıklamada iki ayrı `[TEST]` e-postası gönderir; bu işlem otomatik gönderim kaydını etkilemez.
