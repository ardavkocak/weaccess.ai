# Bot Bakım Rehberi (Docker bilmeyen biri için)

Bu bot, sunucu (VPS) her yeniden başladığında veya çökse bile **kendiliğinden**
tekrar ayağa kalkacak şekilde ayarlandı (`restart: unless-stopped`). Yani
normal koşullarda hiçbir şeye dokunmana gerek yok.

Aşağıdaki komutları anlamana gerek yok — olduğu gibi kopyala/yapıştır yeterli.
Terminalden VPS'e bağlandıktan sonra, projenin bulunduğu klasöre girip çalıştır.

## Bot çalışıyor mu, kontrol et
```bash
docker compose ps discord-satis-bot
```
"Up" yazıyorsa çalışıyordur.

## Son logları gör (bir sorun varsa buradan anlaşılır)
```bash
docker compose logs --tail 100 discord-satis-bot
```

## Botu yeniden başlat
```bash
docker compose restart discord-satis-bot
```

## Botu tamamen durdur
```bash
docker compose stop discord-satis-bot
```

## Tekrar başlat (durdurulduysa)
```bash
docker compose start discord-satis-bot
```

---

## Günlük kullanım — hiçbir komut gerekmez

Aşağıdaki değişiklikler artık **tamamen Discord üzerinden** yapılıyor,
dosya düzenlemeye veya botu yeniden başlatmaya gerek yok:

| Ne yapmak istiyorsun | Discord komutu |
|---|---|
| Hangi Google Sheet / sekme izlensin | `/ayar sheet spreadsheet_id:... sekme_adi:...` |
| Kontrol sıklığı (dakika) | `/ayar siklik dakika:...` |
| Kaç gün güncellenmeyen fırsat "eski" sayılsın | `/ayar eskime-esigi gun:...` |
| Sahipsiz bildirimlerin düşeceği kanal | `/ayar kanal kanal:#...` |
| Kişisel bildirim aboneliği ekle/sil | `/bildirim-ekle`, `/bildirim-sil` |

**Önemli:** Botu yeni bir Google Sheet'e yönlendirirken, o sheet'i Google
Sheets üzerinden botun servis hesabı e-postasına (credentials.json içindeki
`client_email`) **Görüntüleyici** olarak paylaşman gerekiyor — yoksa bot o
sheet'i okuyamaz. Bu da terminal gerektirmez, normal Google Sheets
"Paylaş" ekranından yapılır.

## Sadece şu durumlarda terminale ihtiyaç var
- Discord token'ı sızdı/değişti → `.env` dosyasındaki `DISCORD_TOKEN` güncellenip
  `docker compose up -d --build discord-satis-bot` çalıştırılır.
- Google servis hesabı anahtarı değişti → yeni `credentials.json` dosyası
  aynı isimle üzerine kopyalanıp `docker compose restart discord-satis-bot` çalıştırılır.
- Kodun kendisinde bir değişiklik/güncelleme yapıldıysa.

Bu üç durum dışında botu yönetmek tamamen Discord üzerinden yapılabiliyor.
