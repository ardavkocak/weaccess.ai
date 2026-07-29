# office_bot — Ofis Görev Takibi Entegrasyonu

**Kaynak proje:** `ofis-gorev-takibi/` · Node.js + Express + SQLite + discord.js
**Durum:** Bağlanmadı (placeholder)
**Portaldeki karşılığı:** İki Sidebar öğesi — *Görev Takibi* ve *Yemek Sistemi*
(ikisi de aynı kaynak projeden, aynı adapter'dan beslenir).

## Kaynak projenin özeti

- Görev sırası, Discord bot onay akışı, günlük hatırlatmalar (`src/services/rotation.service.js`, `duty.service.js`)
- Yemek menüsü modülü — görev takibinden bağımsız (`mealMenu`, `mealVote` servisleri)
- Veri: SQLite dosyası (`data/ofis.sqlite`), tek süreçte cron çalışıyor

## Planlanan bağlantı şekli: API

Django ile Node.js farklı runtime'lar olduğu için paylaşılan veritabanı
(shared_db) önerilmez — SQLite zaten tek sürece kilitli, eşzamanlı çift
erişim veri bozulmasına yol açabilir. Bunun yerine:

1. `ofis-gorev-takibi` içine küçük bir **salt-okunur REST API** eklenir
   (`/api/duty/today`, `/api/meal/today` gibi) — mevcut servis katmanı
   zaten HTTP'den bağımsız yazılmış, sadece yeni route'lar eklenir.
2. `OfficeBotIntegration.get_dashboard_summary()` bu endpoint'lere
   `requests` ile istek atar, portalin Dashboard'unda "bugünkü görevli",
   "yarının menüsü" gibi kartlar gösterir.
3. Yazma işlemleri (görev sırasını değiştirme, Discord ayarları) ilk
   fazda hâlâ `ofis-gorev-takibi`'nin kendi panelinde kalabilir; portal
   yalnızca özet gösterir. Tam "tek uygulama" hissi için ikinci fazda
   iframe veya proxy ile panel sayfaları da portale taşınabilir.

## Bilinen riskler

- Kimlik doğrulama iki ayrı sistemde (portal: Django session, bot: kendi
  admin/şifre) — API çağrıları için bir servis anahtarı (API key) veya
  dahili ağ kısıtlaması gerekir.
- Cron tek süreçte çalıştığı için API eklense bile veri "gerçek zamanlı"
  değil, en fazla saniyeler mertebesinde gecikmeli olur (kabul edilebilir).
