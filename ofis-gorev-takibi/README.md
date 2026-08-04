# ☕ Ofis Görev Takip Sistemi

Ofis içindeki günlük çay görevini dijital olarak takip eden, Discord entegrasyonlu yönetim paneli.

Sistem çalıştığı sürece her şey **otomatik** ilerler: sabah görevli bildirilir, gün içinde hatırlatmalar gider, sıra kendiliğinden bir sonraki kişiye geçer. Kullanıcı müdahalesi gerekmez. Sisteme yalnızca admin giriş yapar; çalışanların hesap açmasına gerek yoktur.

### Günlük otomatik akış

| Saat | Mesaj | Nereye gider? | Sıraya etkisi |
|---|---|---|---|
| **08:05** | "Sıradaki kişi X, bugün ofiste mi?" (butonlu onay) | 📢 Görev kanalı | ✅ "Evet" alınınca görevli kesinleşir, sıra hak edilmişse ilerler |
| _onay anında_ | ☀️ Günaydın! Bugünkü ofis görevi sende. | 📩 Görevlinin DM'i | — |
| **10:30** | ☕ Çay kontrol zamanı. | 📩 Görevlinin DM'i | — |
| **15:00** | ☕ İkinci çay kontrolü zamanı. | 📩 Görevlinin DM'i | — |
| **17:20** | 🧹 Gün sonu: çöp + bulaşık makinesi | 📩 Görevlinin DM'i | — |

**Görev kanalı yalnızca sabahki onay sorusu için kullanılır.** Günün görevlisi kesinleştikten sonra hiçbir hatırlatma kanala düşmez; tüm mesajlar yalnızca o kişinin özel mesaj kutusuna gider. DM gönderimi çalışan kaydındaki **Discord ID** üzerinden yapılır (Çalışanlar sayfasından girilir).

Saatlerin tamamı **Ayarlar** sayfasından değiştirilebilir; değişiklik anında geçerli olur, sunucuyu yeniden başlatmak gerekmez.

```
📢 Görev kanalı (08:05)
☕ Günaydın. Bugünkü sıradaki kişi @Beril. Beril bugün ofiste mi?
   [✅ Evet]  [❌ Hayır]

📩 Beril'in özel mesaj kutusu ("Evet" denince)
☀️ Günaydın! Bugünkü ofis görevi sende. İyi çalışmalar.
```

---

## İçindekiler

- [Özellikler](#özellikler)
- [Ekranlar](#ekranlar)
- [Hızlı Başlangıç](#hızlı-başlangıç)
- [Ortam Değişkenleri (.env)](#ortam-değişkenleri-env)
- [Discord Bot Kurulumu](#discord-bot-kurulumu)
- [Sistem Nasıl Çalışır?](#sistem-nasıl-çalışır)
- [Yemek Menüsü Modülü](#yemek-menüsü-modülü)
- [Proje Yapısı](#proje-yapısı)
- [Genişletme: Yeni Görev ve Mesaj Ekleme](#genişletme-yeni-görev-ve-mesaj-ekleme)
- [Loglar](#loglar)
- [Sık Karşılaşılan Sorunlar](#sık-karşılaşılan-sorunlar)
- [Üretim Notları](#üretim-notları)

---

## Özellikler

| Özellik | Açıklama |
|---|---|
| **Tam otomatik** | Bot açılışta bağlanır, zamanlanmış mesajlar kendiliğinden gider, sıra otomatik ilerler. |
| **Tek admin girişi** | Çalışanlar giriş yapmaz; kimlik bilgileri `.env` dosyasında tutulur. |
| **Personel yönetimi** | Ad soyad, Discord ID ve aktif/pasif durumu ile ekleme, düzenleme, silme. |
| **Otomatik sıra** | Yeni çalışan sıranın sonuna eklenir; sıra sona gelince başa döner. |
| **Pasif atlama** | Pasif (veya izinli) çalışanlar sıradan tamamen çıkarılır. |
| **4 zamanlanmış mesaj** | Sabah bildirimi + üç hatırlatma. Saatleri panelden ayarlanır, açılıp kapatılabilir. |
| **Görev geçmişi** | Hangi gün görevin kimde olduğu, tarih filtresi ve kişi bazlı dağılımla. |
| **Manuel müdahale** | "Sırayı Geç" ile görev anında bir sonraki aktif çalışana aktarılır. |
| **Discord ayarları** | Bot Token, Sunucu (Guild) ID, **ayrı görev ve yemek kanalları** ve tüm mesaj saatleri arayüzden yönetilir. |
| **Yemek menüsü modülü** | Aylık menü Excel'den yüklenir; her gün 15:00'te yarının menüsü **kendi kanalında** butonlu katılım anketiyle duyurulur. Görev takibinden bağımsız çalışır. |
| **Log kayıtları** | Zaman damgalı, seviyeli loglar; isteğe bağlı dosyaya yazma. |
| **Genişletilebilir** | Kahve, çöp, mutfak düzeni gibi yeni görev türleri ve hatırlatmalar kod yazmadan eklenir. |

---

## Ekranlar

Sol menüden erişilen beş bölüm:

- **Dashboard** — Bugünkü görevli (büyük kart), sıradaki görevli, toplam/aktif çalışan sayısı, görev sırası, bugünün mesaj takvimi ve sistem durumu.
- **Personeller** — Çalışan ekleme/düzenleme/silme, aktif-pasif değiştirme.
- **Görev Sırası** — Sıranın tamamı, sırada yukarı/aşağı taşıma, mesaj şablonu önizlemesi.
- **Görev Geçmişi** — Tarihe göre filtrelenebilir kayıtlar ve kişi bazlı görev dağılımı.
- **Ayarlar** — Discord bağlantısı, otomatik mesaj saatleri, şirket adı, bağlantı testi.

Arayüz mobil uyumludur; dar ekranda sol menü açılır-kapanır panele dönüşür.

---

## Hızlı Başlangıç

### Gereksinimler

- **Node.js 18 veya üzeri** (`node -v` ile kontrol edin)
- npm

### Kurulum

```bash
# 1. Projeyi klonlayın
git clone <repo-adresi>
cd ofis-gorev-takibi

# 2. Paketleri yükleyin
npm install

# 3. Ortam dosyasını oluşturun
cp .env.example .env

# 4. Başlatın
npm start
```

Panel şu adreste açılır: **http://localhost:3000**

Varsayılan giriş bilgileri (`.env` dosyasından değiştirilir):

| | |
|---|---|
| Kullanıcı adı | `admin` |
| Parola | `admin123` |

> ⚠️ **İlk iş olarak `.env` içindeki `ADMIN_PASSWORD` ve `SESSION_SECRET` değerlerini değiştirin.**

Açılışta konsolda günlük takvimi görürsünüz:

```
  Günlük mesaj takvimi:
    ✓ 08:05  Sabah Görev Bildirimi → sırayı ilerletir
    ✓ 10:30  Birinci Çay Kontrol
    ✓ 15:00  İkinci Çay Kontrol
    ✓ 17:20  Gün Sonu Hatırlatması
```

### Geliştirme modu

Dosya değişikliklerinde sunucuyu otomatik yeniden başlatır:

```bash
npm run dev
```

### İlk kullanım adımları

1. Panele giriş yapın.
2. **Personeller** sayfasından çalışanları ekleyin (eklenme sırası görev sırasını belirler).
3. **Ayarlar** sayfasından Discord bot token, sunucu ID, **Görev Kanalı ID** ve **Yemek Kanalı ID**'sini girin.
4. **Bağlantıyı Test Et** ile doğrulayın.
5. Hazır. Bot her sabah 08:05'te görevliyi bildirir, gün içinde hatırlatmaları gönderir.

Discord'u yapılandırmadan da sistem çalışır; sıra ve geçmiş takibi yapılır, yalnızca mesaj gönderilmez.

---

## Ortam Değişkenleri (.env)

`.env.example` dosyasını `.env` olarak kopyalayıp düzenleyin. `.env` dosyası git'e gönderilmez.

### Sunucu

| Değişken | Varsayılan | Açıklama |
|---|---|---|
| `PORT` | `3000` | Panelin çalışacağı port. |
| `TZ` | `Europe/Istanbul` | Saat dilimi. Cron ve "bugün" hesabı buna göre yapılır. |
| `DATABASE_FILE` | `data/ofis.sqlite` | SQLite dosyasının yolu. Klasör otomatik oluşturulur. |

### Yönetici girişi

| Değişken | Varsayılan | Açıklama |
|---|---|---|
| `ADMIN_USERNAME` | `admin` | Yönetici kullanıcı adı. |
| `ADMIN_PASSWORD` | `admin123` | Yönetici parolası. **Mutlaka değiştirin.** |

### Oturum

| Değişken | Varsayılan | Açıklama |
|---|---|---|
| `SESSION_SECRET` | — | Oturum çerezlerini imzalar. **Mutlaka değiştirin.** |
| `SESSION_SECURE` | `false` | HTTPS arkasındaysanız `true` yapın. |

Güçlü bir secret üretmek için:

```bash
node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"
```

### Kayıt (log)

| Değişken | Varsayılan | Açıklama |
|---|---|---|
| `LOG_LEVEL` | `info` | `debug` \| `info` \| `warn` \| `error` |
| `LOG_FILE` | — | Tanımlanırsa loglar bu dosyaya da yazılır (örn. `logs/app.log`). |

### Discord ve mesaj saatleri

> Aşağıdakiler **yalnızca ilk çalıştırmada** veritabanına yazılır. Sonrasında panelin **Ayarlar** sayfasından yönetilir; `.env`'i düzenlemek mevcut ayarları değiştirmez.

| Değişken | Varsayılan | Açıklama |
|---|---|---|
| `DISCORD_BOT_TOKEN` | boş | Bot token'ı. Panelden de girilebilir. |
| `DISCORD_GUILD_ID` | boş | Ofis sunucunuzun ID'si. İsteğe bağlı ama önerilir. |
| `DISCORD_DUTY_CHANNEL_ID` | boş | **Görev kanalı**: sabahki Evet/Hayır onay sorusu buraya gider. (Gün içi hatırlatmalar kanala değil, görevliye DM olarak gider.) |
| `DISCORD_MEAL_CHANNEL_ID` | boş | **Yemek kanalı**: yarının menüsü ve katılım anketi buraya gider. |
| `DISCORD_CHANNEL_ID` | boş | _Eski kurulumlar için._ Girilirse iki kanala da tohum değeri olur. |
| `COMPANY_NAME` | `Şirketiniz` | Panelde ve `{company}` değişkeninde görünen ad. |
| `NOTIFY_TIME` | `08:05` | Sabah görev bildirimi. **Sırayı ilerleten mesaj budur.** |
| `TEA_CHECK_1_TIME` | `10:30` | Birinci çay kontrol hatırlatması. |
| `TEA_CHECK_2_TIME` | `15:00` | İkinci çay kontrol hatırlatması. |
| `END_OF_DAY_TIME` | `17:20` | Gün sonu hatırlatması. |
| `MEAL_NOTIFY_TIME` | `15:00` | Yarının yemek menüsü duyurusu. Yemek Menüsü sayfasından da değiştirilir. |

---

## Discord Bot Kurulumu

### 1. Bot oluşturun

1. [Discord Developer Portal](https://discord.com/developers/applications) → **New Application**
2. Uygulamaya bir isim verin (örn. "Ofis Görev Botu") → **Create**
3. Sol menüden **Bot** → **Add Bot** → onaylayın.
4. **Reset Token** → **Copy** ile token'ı kopyalayın.

> 🔒 Token bir paroladır. Kimseyle paylaşmayın, ekran görüntüsüne almayın, git'e commit etmeyin. Sızdıysa aynı ekrandan **Reset Token** ile iptal edin.

> Bu bot yalnızca mesaj **gönderir**, okumaz. Bu nedenle *Privileged Gateway Intents* (Message Content vb.) açmanıza **gerek yoktur**.

### 2. Botu sunucunuza ekleyin

1. Sol menüden **OAuth2** → **URL Generator**
2. **Scopes**: `bot` işaretleyin.
3. **Bot Permissions**: `Send Messages` (kanal özelse ayrıca `View Channel`)
4. Sayfanın altındaki **Generated URL**'i kopyalayıp tarayıcıda açın, ofis sunucunuzu seçin ve yetkilendirin.

### 3. Sunucu ve Kanal ID'sini alın

Önce Geliştirici Modu'nu açın:

**Discord → Kullanıcı Ayarları (⚙️) → Gelişmiş → Geliştirici Modu** → açık konuma getirin.

Ardından:

| Ne | Nasıl |
|---|---|
| **Sunucu (Guild) ID** | Sol taraftaki sunucu simgesine sağ tıklayın → **Sunucu ID'sini Kopyala** |
| **Görev Kanalı ID** | Onay sorusunun gideceği kanala sağ tıklayın → **Kanal ID'sini Kopyala** |
| **Yemek Kanalı ID** | Yemek menüsünün gideceği kanala sağ tıklayın → **Kanal ID'sini Kopyala** |
| **Kullanıcı ID** (isteğe bağlı) | Kişiye sağ tıklayın → **Kullanıcı ID'sini Kopyala** |

Bu ID'ler 17-20 haneli sayılardır (örn. `123456789012345678`).

### 4. Panele girin

**Ayarlar** sayfasına token, sunucu ID ve kanal ID'sini yazıp kaydedin, ardından **Bağlantıyı Test Et** deyin. Başarılıysa bot adı, sunucu adı ve kanal adı görünür:

```
Bağlantı başarılı. Bot: OfisBot#1234 — Sunucu: Ofis — Kanal: #genel
```

Ayarlar sayfasındaki **Zamanlayıcı** kutusundan her mesajın yanındaki ✈️ simgesine basarak saati beklemeden test mesajı gönderebilirsiniz.

### Çalışan Discord ID'si (isteğe bağlı)

Mesajda kişiyi etiketlemek (`@Beril`) isterseniz çalışanın Discord kullanıcı ID'sini girin ve şablonda `{name}` yerine `{mention}` kullanın.

ID girilmezse `{mention}` düz isme düşer — sistem yine sorunsuz çalışır.

---

## Sistem Nasıl Çalışır?

### İki tür mesaj

Bu ayrım sistemin temelidir:

| Tür | Örnek | Ne yapar |
|---|---|---|
| **Görev mesajı** (`duty`) | 08:05 sabah bildirimi | **Etkileşimli onay akışı** başlatır: **kanala** butonlu "ofiste mi?" sorusu sorar, "Evet" alınca görevliyi kesinleştirir, geçmişe kaydeder ve **sırayı ilerletir**. |
| **Hatırlatma** (`reminder`) | 10:30 / 15:00 / 17:20 | Metni **yalnızca o günün görevlisine özel mesaj (DM)** olarak gönderir. Sıraya ve geçmişe **dokunmaz**. |

Hatırlatmalar bilerek sıraya dokunmaz — aksi halde günde bir kişi yerine dört kişinin sırası yanardı.

### Hatırlatmalar kime gider?

Hatırlatmanın tek adresi **o günün kesinleşmiş görevlisidir** (`duty_history` kaydı). Buna bağlı üç davranış vardır:

- **Görevli henüz belli değilse** (sabahki onay sonuçlanmadıysa) hiçbir mesaj gönderilmez; log'a bilgi satırı yazılır ve cron normal çalışmaya devam eder.
- **Görevlinin Discord ID'si yoksa** mesaj atlanır; sistem hata vermez, kanala da düşmez.
- **DM gönderilemezse** (kişi DM'leri kapatmış, botu engellemiş veya başka bir Discord hatası) yalnızca log'a yazılır:

```
2026-07-22 10:30:00 WARN  [dm] DM gönderilemedi: Beril Kahramanca - Cannot send messages to this user.
```

> DM gönderebilmek için botun kişiyle **ortak bir sunucuda** olması ve kişinin sunucu üyelerinden özel mesaj almaya açık olması gerekir (Discord → Gizlilik Ayarları).

### Çalışma günleri (hafta sonu kontrolü)

Otomatik görevler yalnızca **Pazartesi–Cuma** çalışır. Cumartesi ve Pazar günleri:

- Hiçbir otomatik Discord mesajı gönderilmez.
- Görev sırası ilerlemez, kimseye otomatik görev atanmaz.
- Dashboard'da "Bugün hafta sonu — otomatik görevler çalışmıyor" bilgisi görünür.

Pazartesi sistem **kaldığı yerden** devam eder: hafta sonu hiçbir şey olmadığı için sıra Cuma'daki yerinden ilerler, ekstra kişi atlanmaz.

**Manuel gönderim hafta sonu da çalışır.** "Gün kontrolü" yalnızca otomatik (cron) çalışmayı durdurur; panelin **Gönder** / **Onayı Başlat** butonları her gün çalışmaya devam eder.

Karar tek bir yerdedir: [`src/services/calendar.service.js`](src/services/calendar.service.js) → `isWorkingDay()`. Tüm zamanlanmış görevler bu kontrolü kullanır (cron işlerinin ortak giriş noktası olan `scheduler.runJob` içinde). **Resmi tatil desteği** eklemek için yalnızca aynı dosyadaki `isHoliday()` fonksiyonunu doldurmak yeterlidir; başka hiçbir yeri değiştirmek gerekmez.

> Cron ifadeleri değişmedi (hâlâ her gün tetiklenir); hafta sonu çalışması `runJob` içindeki tek kapı ile engellenir. Bu, `1-5` gibi bir cron ifadesinin aksine ileride tatilleri de kapsayabilir.

### Etkileşimli sabah görev onayı

Sabah görev mesajı artık doğrudan "Bugünkü görevli Beril" demez. Bunun yerine Discord'da **butonlu bir onay akışı** yürütür:

**1. Bot sorar** (görev sırası: Beril → Doğa → Ahmet → Ayşe):

> ☕ Günaydın. Bugünkü sıradaki kişi Beril Kahramanca. Beril bugün ofiste mi?
> [ ✅ Evet ] [ ❌ Hayır ]

**2a. Biri "✅ Evet" derse** — aynı mesaj güncellenir, görev kesinleşir:

> ✅ Beril bugün ofiste. ☕ Bugünkü görevli Beril Kahramanca. İyi çalışmalar.

**2b. Biri "❌ Hayır" derse** — *aynı mesaj* düzenlenir, sıradaki kişi sorulur (yeni mesaj oluşmaz):

> Beril bugün ofiste değil.
> Sıradaki kişi Doğa Uslu.
> Doğa bugün ofiste mi?
> [ ✅ Evet ] [ ❌ Hayır ]

**3. İlk "Evet" alınana kadar** böyle devam eder. Örneğin Beril ve Doğa için "Hayır", Ahmet için "Evet" denirse:

> ☕ Bugünkü görev kesinleşti.
> Bugünkü görevli: Ahmet Yılmaz.
> İyi çalışmalar.

Kesinleşince Ahmet'e "☀️ Günaydın! Bugünkü ofis görevi sende." özel mesajı gider; günün geri kalanındaki çay kontrol ve gün sonu hatırlatmaları da yalnızca **Ahmet'in DM kutusuna** düşer. Sıra ise Ahmet'ten değil, sıranın sahibinden (Beril) hesaplanmaya devam eder.

**Kurallar:**
- **Herkes basabilir** — herhangi bir çalışan "Beril gelmedi" diyebilir.
- **Tek mesaj** — akış boyunca aynı mesaj düzenlenir; kanal temiz kalır.
- **Spam koruması** — bir soru yanıtlandıktan sonra o adımın butonları geçersizleşir; aynı kişi art arda basıp sistemi bozamaz (ilk tıklama kazanır, sonrakiler "bu soru zaten yanıtlandı" uyarısı alır).
- **Kendini toparlar** — cevap beklemeyen bir butona basılırsa (görev zaten sonuçlanmış ya da mesaj başka bir veritabanıyla çalışan bir örnekten kalmış) kullanıcıya teknik hata gösterilmez: mesajın butonları kaldırılır ve yerine tek satır `☕ Bugünkü görevli: X.` yazılır. Böylece eski mesajlar kanalda tıklanabilir çıkmaz olarak kalmaz.
- **Kalıcı** — her soru ve cevap `duty_confirmations` / `duty_confirmation_events` tablolarına yazılır: hangi gün kime soruldu, kim "Evet/Hayır" dedi, görev kime kesinleşti. Sunucu yeniden başlasa bile mevcut mesajdaki butonlar çalışmaya devam eder (durum bellekte değil, veritabanındadır).
- Kimse "Evet" demez ve sıra başa dönerse, mesaj "bugün uygun kişi bulunamadı" olarak güncellenir.

Bu akışı saatini beklemeden başlatmak için: **Dashboard → Görev Onayını Başlat** veya **Ayarlar → (görev mesajı) → Onayı Başlat**.

### "Bugünkü görevli" nasıl belirlenir?

Mesaj gönderildikten sonra sıra hemen ilerlediği için, `rotation_state.current` değeri artık **yarının** görevlisini gösterir. Panelin bugünü doğru göstermesi için sistem şu kuralı uygular:

| Durum | Bugünkü görevli | Sıradaki |
|---|---|---|
| Bugün mesaj **gönderilmiş** | Bugünün geçmiş kaydı | `current` (yarın) |
| Bugün mesaj **gönderilmemiş** | `current` | `current`'tan sonraki aktif |

### Pasif ve izinli çalışanlar

Çalışan modeli **aktif/pasif** durumu tutar. İzinli bir çalışan için de aynı mekanizma kullanılır: çalışanı **pasife alın**, sıra onu otomatik atlar; döndüğünde tekrar aktif yapın.

Sıradaki kişi pasife alınırsa sistem panel her açıldığında bunu fark eder ve sırayı bir sonraki aktif kişiye kaydırır.

### Güvenlik önlemleri

- Parola karşılaştırması `crypto.timingSafeEqual` ile sabit sürede yapılır (timing attack koruması).
- Giriş sonrası oturum kimliği yenilenir (session fixation koruması).
- Tüm POST formları CSRF token ile korunur; çerezler `httpOnly` + `sameSite=lax`.
- Form yönlendirmeleri yalnızca uygulama içi yollara izin verir (açık yönlendirme koruması).
- Discord token veritabanında saklanır ve arayüze **asla** tam gönderilmez (yalnızca `••••••••••••5XYZ` biçiminde maskeli).

### Dayanıklılık

- **Discord hatası:** Mesaj gönderilemese bile görev o güne kaydedilir ve sıra ilerler (kayıt `notified = 0`, geçmişte kırmızı ünlemle görünür). Böylece geçici bir arıza rotasyonu takvimden kaydırmaz. **Dashboard → Mesajı Şimdi Gönder** ile tekrar gönderebilirsiniz.
- **Çift tetikleme:** Görev mesajı aynı gün ikinci kez çalışırsa sıra **ikinci kez ilerletilmez**; yalnızca mesaj yeniden gönderilir. Bir günde iki kişinin sırası yanmaz.
- **Bir mesajın hatası diğerlerini etkilemez:** Her cron işi bağımsız çalışır ve hataları yakalanır.
- **Çalışan silme:** Geçmiş kayıtları silinmez. İsim, kayıt anında kopyalandığı için geçmiş okunabilir kalır ("Silinmiş çalışan" etiketiyle).

---

## Yemek Menüsü Modülü

Görev takibinden **bağımsız** bir modüldür: kendi tabloları (`meal_menus`, `meal_votes`),
kendi zamanlayıcısı ve kendi Discord mesajı vardır. Görev tablolarıyla hiçbir yabancı
anahtar ilişkisi yoktur; modül devre dışı bırakılsa görev sistemi aynen çalışır.

### Aylık menüyü yükleme

**Yemek Menüsü → Aylık Menüyü Yükle** ile `.xlsx` dosyası seçilir. Excel **yalnızca yükleme
anında** okunur; satırlar veritabanına aktarılır ve sistem bundan sonra hep veritabanını
kullanır — dosya bir daha açılmaz, sunucuda saklanmaz.

**İki farklı dosya düzeni desteklenir.** Okuyucu önce haftalık bloğu dener, tutmazsa düz
tabloya düşer; hangisinin okunduğu yükleme raporunda yazar. "Tarih" adlı bir sütun bulunma
zorunluluğu **yoktur**.

#### 1. Haftalık blok (catering firmalarının yaygın formatı)

Tarihler sütun başlıklarındadır ve sayfa hafta hafta tekrar eder:

```
      │ B          C     │ D          E     │ F           G     │
 R4   │ PAZARTESİ  ENERJİ│ SALI     ENERJİ  │ ÇARŞAMBA   ENERJİ │  ← gün başlığı
 R5   │ 06.07.2026  1385 │ 07.07.2026 1263  │ 08.07.2026  1250  │  ← tarih satırı
 R6   │ TARHANA ÇORBA 194│ TAVUK ÇORBA 189  │ EZOGELİN     162  │  ┐
 R7   │ KÖRİ TAVUK    384│ KURU FASULYE 315 │ BODRUM KÖFTE 310  │  │ yemekler
 ...  │                  │                  │                   │  ┘
 R11  │ PAZARTESİ  ENERJİ│ SALI     ENERJİ  │ ÇARŞAMBA   ENERJİ │  ← YENİ HAFTA
```

- **Gün başlığı satırı** = en az iki hücresi tam olarak bir hafta gününe eşit olan satır.
  Yeni hafta başlığı geldiğinde okuma kendiliğinden bir sonraki bloğa geçer.
- **ENERJİ (kalori) sütunları tamamen yok sayılır** — başlıkları hafta günü olmadığı için
  hiç okunmazlar.
- **Tarih satırı** = başlığın altındaki, gün sütunlarında tarih çözülebilen ilk satır.
  Ayın ilk/son haftasında boş kalan günler sessizce atlanır.
- **Yemekler**, gün sütunlarının tamamı boşalana kadar okunur; böylece sayfa sonundaki
  imza satırları ("GIDA MÜHENDİSİ") yemek sanılmaz.
- Menüsü olmayan günler (hafta sonu) kaydedilmez.

#### 2. Düz tablo

Her satır bir gündür; başlıklar serbesttir:

| Tarih | Gün | Çorba | Ana Yemek | Salata |
|---|---|---|---|---|
| 23.07.2026 | Perşembe | Mercimek | Tavuk Sote | Mevsim |

- Başlık satırı ilk 15 satırda aranır (üstteki logo satırları sorun olmaz).
- **Tarih** ve **Gün** sütunları eş anlamlı sözlüğüyle tanınır.
- **Geri kalan tüm sütunlar yemek sayılır** — tek `Menü` sütunu da yayılmış tablo da aynı
  kodla okunur.

#### Ortak davranışlar

Desteklenen tarih biçimleri: gerçek Excel tarih hücresi, Excel seri numarası,
`23.07.2026`, `23/07/2026`, `2026-07-23`. Bir hücrede satır sonu, `;` veya `, ` ile
ayrılmış birden fazla yemek varsa ayrı yemekler olarak kaydedilir (`/` ile ayrılanlar
bölünmez: "PİLİÇ SHNİTZEL / KETÇAP MAYONEZ" tek yemektir).

Yükleme sonrası panelde **rapor** gösterilir: biçim, kaç hafta bloğu bulundu, hangi
sütunlar okundu, hangileri yok sayıldı, kaç gün okundu/atlandı. Düz tablo için sütun
eşleştirme altyapısı hazırdır — `mealImport.parseBuffer(buffer, { mapping })` algılamayı ezer:

```js
parseBuffer(buffer, { mapping: { headerRow: 3, date: 1, day: 2, items: [3, 4, 5] } })
```

Aynı tarih yeniden yüklenirse satır **güncellenir**, çoğalmaz. "Mevcut tüm menüleri sil"
kutusu işaretlenirse önce eski kayıtlar temizlenir.

> **Türkçe büyük harf notu:** Menüler genelde TAMAMI BÜYÜK HARF gelir. JavaScript'in
> `i` bayrağı Türkçe'de çalışmaz — `/mercimek/i` metni `MERCİMEK` ile eşleşmez (noktalı İ
> sorunu). Bu yüzden hem başlık tanıma hem yemek ikonu seçimi, karşılaştırmadan önce metni
> `utils/text.js → normalizeTr()` ile ASCII'ye sadeleştirir.

### Günlük duyuru (varsayılan 15:00)

Her gün belirlenen saatte yarının tarihi hesaplanır ve veritabanından o günün menüsü
aranır:

- **Menü varsa** → Discord kanalına butonlu duyuru gönderilir.
- **Menü yoksa** → **hiçbir mesaj gönderilmez.** Log'a yalnızca
  `Yarın için yemek menüsü bulunamadı.` yazılır ve uygulama normal çalışmaya devam eder.

Saat, modülün kendi sayfasından değiştirilir (`settings.meal_notify_time`); kaydedildiğinde
zamanlayıcı anında yenilenir. Aynı gün ikinci kez tetiklenirse menü tekrar duyurulmaz
(`meal_menus.announced_at`); **Yarının Menüsünü Şimdi Gönder** test butonu bu kontrolü atlar.

```
🍽️ **Yarının Yemek Menüsü**

📅 23 Temmuz 2026 Perşembe

🥣 Mercimek Çorbası
🍗 Tavuk Sote
🍚 Pirinç Pilavı
🥗 Mevsim Salata

Yarın yemek yiyecek misiniz? Lütfen aşağıdaki butonlardan birini seçiniz.

✅ **Yiyeceğim:** 18    ❌ **Yemeyeceğim:** 5
   [ 🟢 Yiyeceğim ]  [ 🔴 Yemeyeceğim ]
```

Yemek adının başındaki ikon içeriğe göre seçilir (çorba → 🥣, salata → 🥗, tatlı → 🍰…);
tanınmayan yemekler nötr 🍽️ ile gösterilir.

### Katılım oylaması

- **Tek oy, değiştirilebilir.** Bir kişi bir gün için tek oy kullanır. "Yiyeceğim" deyip
  sonra "Yemeyeceğim" seçerse eski oy **silinmez, güncellenir** — sonuç aynıdır, iki oy
  asla oluşmaz. Bu kural `UNIQUE (menu_date, discord_user_id)` ile **veritabanı düzeyinde**
  garantidir, koda bağlı değildir.
- **Sayaçlar gerçek zamanlı.** Her tıklamada mesaj güncel sayılarla yeniden yazılır.
- **Kişiye özel geri bildirim.** Oy veren, yalnızca kendisinin gördüğü bir onay alır
  ("Tercihiniz 🟢 Yiyeceğim → 🔴 Yemeyeceğim olarak güncellendi").
- **Dayanıklı.** Buton `customId`'si satır id'si değil **tarih** taşır; menü yeniden
  yüklense veya sunucu yeniden başlasa bile eski mesajın butonları çalışmaya devam eder.

### Discord'da sayı, panelde isim

Discord mesajında **yalnızca sayılar** görünür — isim listesi kanala düşmez:

```
🍽️ **Katılım Durumu**

✅ Yiyeceğim (18)
❌ Yemeyeceğim (5)
   [ 🟢 Yiyeceğim ]  [ 🔴 Yemeyeceğim ]
```

Ayrıntılı döküm **yalnızca admin panelindedir**: sayfanın üstünde dört istatistik kartı
(🍽️ Toplam Personel · ✅ Yiyeceğim · ❌ Yemeyeceğim · ⏳ Cevap Vermeyen) ve altında üç
liste — *Yiyecekler*, *Yemeyecekler*, *Henüz cevap vermeyenler*.

Kartlar ve listeler **canlı güncellenir**: sayfa, `/yemek-menusu/katilim.json` uç noktasını
10 saniyede bir yoklar; Discord'da butona basıldığında panel kendini yeniler (sekme arka
plandayken yoklama durur). Sayfayı besleyen servis ile JSON uç noktası aynıdır, iki farklı
doğruluk kaynağı oluşmaz.

İsimler **personel kaydından** gelir (Discord takma adı değişse bile panel tutarlı kalır).
Personel listesinde olmayan biri oy verirse "personel listesinde yok" etiketiyle görünür.
**Cevap vermeyenler** listesi oy kullanmamış *aktif* personeldir; pasif (izinli) çalışanlar
beklenen katılımcı sayılmaz.

> Discord ID'si girilmemiş personel butonlara basamaz; panelde "Discord ID yok" etiketiyle
> cevap vermeyenler arasında görünür. Anketin çalışması için **Personeller** sayfasından
> Discord ID'lerinin doldurulması gerekir.

---

## Proje Yapısı

```
ofis-gorev-takibi/
├── src/
│   ├── server.js              # Giriş noktası: DB + bot + cron + HTTP başlatır
│   ├── app.js                 # Express kurulumu (middleware zinciri)
│   │
│   ├── config/                # .env okuma ve doğrulama
│   ├── database/
│   │   ├── connection.js      # SQLite bağlantısı (better-sqlite3)
│   │   └── schema.js          # Tablolar, göçler, varsayılan veriler
│   │
│   ├── routes/                # URL → controller eşlemesi
│   ├── controllers/           # HTTP isteklerini karşılar, servisleri çağırır
│   ├── services/              # İş mantığı (HTTP'den bağımsız)
│   │   ├── employee.service.js
│   │   ├── rotation.service.js         # ← sıra mantığının kalbi
│   │   ├── duty.service.js             # ← mesaj yürütme: duty vs reminder
│   │   ├── dutyNotifier.service.js     # ← görevliye DM gönderiminin tek noktası
│   │   ├── scheduledMessage.service.js # ← "ne zaman ne gönderilecek?"
│   │   ├── mealMenu.service.js         # ← yemek menüsü kayıtları
│   │   ├── mealImport.service.js       # ← Excel okuma (blok + düz tablo)
│   │   ├── mealVote.service.js         # ← katılım oyları + panel dökümü
│   │   ├── mealNotifier.service.js     # ← yemek kanalına duyuru + buton işleme
│   │   ├── dutyType.service.js         # ← "sıra kimde?" (çay, kahve...)
│   │   ├── history.service.js
│   │   └── settings.service.js
│   │
│   ├── discord/
│   │   ├── bot.js             # discord.js istemcisi, guild/kanal çözümleme, DM gönderimi
│   │   ├── directMessages.js  # Görevliye DM olarak giden metinler
│   │   ├── mealComponents.js  # Yemek katılım butonları ("mv" öneki)
│   │   ├── mealMessages.js    # Yemek duyuru metni ve ikon seçimi
│   │   └── messages.js        # Şablon değişkenlerinin işlenmesi
│   │
│   ├── cron/
│   │   ├── scheduler.js       # node-cron: her görev mesajı için ayrı iş
│   │   └── mealScheduler.js   # yemek duyurusu (bağımsız tek iş)
│   ├── middleware/            # auth, csrf, flash, upload, hata yakalama
│   ├── utils/                 # tarih, metin (Türkçe katlama), görünüm, log
│   └── views/                 # EJS şablonları
│       ├── partials/          # layout, sidebar, flash
│       └── pages/             # dashboard, employees, queue, history, settings
│
├── public/                    # Statik dosyalar (css, js)
├── data/                      # SQLite dosyası (git'e gönderilmez)
├── .env.example
└── package.json
```

### Katman kuralları

Sorumluluklar bilerek ayrılmıştır:

- **Controller** HTTP bilir (`req`, `res`), iş kuralı bilmez.
- **Service** iş kuralı bilir, HTTP bilmez — bu sayede cron da aynı servisleri çağırabilir.
- **View** yalnızca kendisine verilen veriyi gösterir, sorgu yapmaz.
- **Discord, cron ve sıra yönetimi** birbirinden bağımsız dosyalardadır: cron "ne zaman"ı, duty servisi "ne olacağını", rotation servisi "sıra kimde"yi, bot ise "nasıl gönderileceğini" bilir.

### Veri modeli

| Tablo | Sorumluluk |
|---|---|
| `employees` | Çalışanlar ve sıradaki yerleri (`position`). |
| `duty_types` | Görev türleri (çay, kahve...). "Sıra kimde?" sorusunun sahibi. |
| `rotation_state` | Her görev türü için sıradaki kişi. |
| `scheduled_messages` | "Ne zaman ne gönderilecek?" — saat, şablon, tür (`duty`/`reminder`). |
| `duty_history` | Günlük görev kayıtları (isim kopyalanır). |
| `duty_confirmations` | Etkileşimli onay akışının durumu (gün başına bir akış + Discord mesaj kimliği). |
| `duty_confirmation_events` | Onaydaki her cevabın denetim kaydı (kime, ne cevap, kim verdi). |
| `sessions` | Oturum deposu (yeniden başlatmaya dayanıklı). |
| `settings` | Panelden yönetilen anahtar/değer ayarları. |

### Kullanılan teknolojiler

| Katman | Teknoloji |
|---|---|
| Sunucu | Node.js + Express 4 |
| Veritabanı | SQLite (better-sqlite3) |
| Görünüm | EJS + Tailwind CSS |
| Discord | discord.js v14 |
| Zamanlama | node-cron |

---

## Genişletme: Yeni Görev ve Mesaj Ekleme

Sistem tek bir "çay görevi"ne gömülü değildir. **Kod değişikliği gerekmez.**

### Yeni görev türü (kendi sırası olan)

Kahve görevi ekleyelim — kendi bağımsız sırası ve kendi sabah bildirimi olsun:

```bash
node -e "
require('./src/services/dutyType.service').create({
  key: 'coffee',
  name: 'Kahve',
  emoji: '☕',
  sendTime: '09:00',
});
"
```

Bu tek çağrı şunları birlikte kurar: görev türü + rotasyon satırı + 09:00'da çalışıp **kendi sırasını ilerleten** bir sabah bildirimi. Çay sırası ile kahve sırası birbirinden tamamen bağımsızdır.

Sunucuyu yeniden başlattığınızda **Görev Sırası** ve **Görev Geçmişi** sayfalarında tür sekmeleri belirir.

### Yeni hatırlatma (sıraya dokunmayan)

```bash
node -e "
require('./src/services/scheduledMessage.service').create({
  key: 'kitchen_check',
  name: 'Mutfak Düzeni',
  send_time: '16:45',
  message_template: '🍽️ **Mutfak Düzeni**\n\nMutfağı toplamayı unutmayalım.',
  kind: 'reminder',
});
"
```

Yeniden başlatınca cron bunu da zamanlar; Ayarlar sayfasında saati düzenlenebilir hale gelir.

### Şablon değişkenleri

| Değişken | Çıktı |
|---|---|
| `{name}` | Beril Kahramanca |
| `{mention}` | `<@123...>` (Discord ID yoksa isme düşer) |
| `{emoji}` | ☕ |
| `{duty}` | Çay |
| `{company}` | Ayarlardaki şirket adı |
| `{date}` | 17 Temmuz 2026 Cuma |

Şablonlarda `\n` satır sonu, `**kalın**` ise Discord'da kalın yazı üretir.

---

## Loglar

Loglar zaman damgalı, seviyeli ve kaynak etiketlidir:

```
2026-07-17 08:05:00 INFO  [cron]    Çalıştırılıyor: "Sabah Görev Bildirimi" (08:05, duty)
2026-07-17 08:05:01 INFO  [confirm] Onay akışı başladı (akış 42, Çay): Beril Kahramanca soruluyor.
2026-07-17 08:07:12 INFO  [confirm] Onay kesinleşti (akış 42): görevli Beril Kahramanca sırasını kullandı, sıra → Doğa Uslu.
2026-07-17 08:07:12 INFO  [dm]      DM gönderildi: Beril Kahramanca - Günaydın mesajı
2026-07-17 10:30:00 INFO  [dm]      DM gönderildi: Beril Kahramanca - Birinci Çay Kontrol
2026-07-17 15:00:00 WARN  [dm]      DM gönderilemedi: Doğa Uslu - Cannot send messages to this user.
```

Seviyeler: `debug` < `info` < `warn` < `error`. Uyarı ve hatalar `stderr`'e gider.

```bash
LOG_LEVEL=debug npm start          # ayrıntılı (yığın izleriyle)
LOG_FILE=logs/app.log npm start    # dosyaya da yaz
npm start 2> hatalar.log           # yalnızca hataları ayır
```

---

## Sık Karşılaşılan Sorunlar

**`npm install` sırasında better-sqlite3 hatası**
better-sqlite3 yerel (native) bir modüldür. npm 11 kurulum betiklerini varsayılan olarak engeller; bu projede gerekli izin `package.json` içindeki `allowScripts` alanında kayıtlıdır. Yine de sorun yaşarsanız:
```bash
npm rebuild better-sqlite3
```

**Bot "Yapılandırılmadı" görünüyor**
Ayarlar sayfasına bot token'ı girilmemiştir. Token girip kaydedin.

**"Unknown Guild" / "Girdiğiniz Guild ID ... bu bota ait bir sunucu değil"**

Bu hatanın tek bir anlamı vardır: **bot, girdiğiniz ID'ye sahip sunucuda değil.** `guilds.fetch(id)` yalnızca botun üye olduğu sunucuları getirebilir; üye değilse Discord `Unknown Guild` (kod 10004) döner. Bot başarıyla giriş yapmış olması bunu değiştirmez — giriş yapmak ile sunucuya davet edilmiş olmak farklı şeylerdir.

İki olası neden var:

1. **Yanlış ID girilmiş** — en sık: kanal ID'si Guild alanına yazılmış ya da başka bir sunucunun ID'si kullanılmış.
2. **Bot sunucuya davet edilmemiş** — token doğru, uygulama var, ama bot sunucuya eklenmemiş.

Hangisi olduğunu görmek için:

```bash
npm run discord:teshis
```

Bu komut bağlanır ve botun **gerçekte hangi sunucularda olduğunu** ID'leriyle listeler, girdiğiniz ID ile karşılaştırır, doğru olanı söyler. Hiçbir mesaj göndermez.

Aynı bilgi **Ayarlar** sayfasında da görünür: "Botun bulunduğu sunucular" listesinden doğru ID'yi kopyalayabilirsiniz. Sunucu listesi boşsa bot hiçbir yere davet edilmemiştir → OAuth2 bağlantısıyla ekleyin.

> Guild ID isteğe bağlıdır. Alanı **boş bırakırsanız** kanal doğrudan ID ile çözülür ve sistem sorunsuz çalışır.

**"Kanal bulunamadı" / "Kanal şu sunucuda bulunamadı"**
Kanal ID yanlış olabilir veya kanal, girdiğiniz Guild ID'ye ait değildir. `npm run discord:teshis` çalıştırın; kanalın bulunup bulunmadığını ve bot izinlerini raporlar.

**"Botun bu kanala mesaj gönderme yetkisi yok"**
Kanal özel ise botun rolüne **View Channel** ve **Send Messages** izinlerini verin.

**Butona basınca "Bu onay kaydı bulunamadı" çıkıyor / butonlar kalkmıyor**
Mesaj, **başka bir veritabanıyla** çalışan bir örnek tarafından gönderilmiştir. En sık sebep aynı bot token'ının hem Docker'da hem yerelde çalıştırılmasıdır: `docker-compose.yml` içindeki veri hacmi ile yereldeki `data/ofis.sqlite` **ayrı dosyalardır**, ikisi de aynı Discord kanalına yazar ama birbirinin onay kayıtlarını göremez. Butonun `flowId`'si diğer veritabanına aittir ve `AUTOINCREMENT` yüzünden bir daha asla eşleşmez.

Güncel sürümde bu tıklama artık hata göstermez; mesajın butonları kaldırılıp yerine günün görevlisi yazılır. Kalıcı çözüm için **aynı anda tek bir örnek** çalıştırın (ya Docker ya yerel) veya her ortama ayrı bir bot token/kanal verin.

**Hatırlatma DM'i gitmiyor**
Sırasıyla kontrol edin:
1. **Günün görevlisi kesinleşti mi?** Sabahki onayda kimse "Evet" demediyse gönderilecek adres yoktur; log'da `Hatırlatma atlandı ... bugünkü görevli henüz kesinleşmedi` satırı görünür.
2. **Çalışanın Discord ID'si girili mi?** Çalışanlar sayfasından ekleyin — log: `DM gönderilemedi: <isim> - Discord ID tanımlı değil.`
3. **Kişi DM'lere açık mı?** Discord → Gizlilik Ayarları → "Sunucu üyelerinden özel mesaj al" kapalıysa veya botu engellemişse Discord `Cannot send messages to this user.` döner. Bot ile kişinin **ortak bir sunucuda** olması da gerekir.

Bu durumların hiçbiri uygulamayı durdurmaz; log'a bilgi satırı yazılır ve zamanlayıcı normal çalışmaya devam eder.

**Mesaj yanlış saatte gidiyor**
`.env` dosyasındaki `TZ` değerini kontrol edin (varsayılan `Europe/Istanbul`). Ayarlar sayfasındaki "Zamanlayıcı" kutusu geçerli saat dilimini ve kurulu saatleri gösterir.

**Mesaj hiç gitmiyor**
Ayarlar → Zamanlayıcı kutusunda mesajın yanında yeşil "● zamanlandı" yazmalı. Yazmıyorsa mesaj kapalıdır — "Etkin" kutusunu işaretleyip kaydedin.

**Giriş yaparken "Oturum doğrulaması başarısız" (403)**
Giriş sayfası uzun süre açık kaldıysa güvenlik anahtarı eskimiş olabilir. Sistem bunu otomatik onarır: giriş denemeniz sizi temiz bir giriş sayfasına döndürür, "Oturum süreniz yenilendi" mesajını görürsünüz ve tekrar giriş yaptığınızda çalışır. Görürseniz sadece bilgileri yeniden girin.

**Port 3000 kullanımda**
`.env` içindeki `PORT` değerini değiştirin.

**Sıra beklenmedik kişide**
Görev Sırası sayfasında pasif çalışanlar "Pasif · atlanır" etiketiyle görünür. Sıra yalnızca aktif çalışanlar üzerinde döner.

---

## Üretim Notları

Bu proje bir **iç ağ (intranet) uygulaması** olarak tasarlanmıştır. Herkese açık bir sunucuda çalıştıracaksanız:

1. `ADMIN_PASSWORD` ve `SESSION_SECRET` değerlerini mutlaka değiştirin.
2. HTTPS kullanın ve `SESSION_SECURE=true` yapın.
3. Süreci `pm2`, `systemd` veya Docker ile yönetin:
   ```bash
   npx pm2 start src/server.js --name ofis-gorev
   ```
4. `data/` klasörünü düzenli yedekleyin — tüm veri o dosyadadır.

### Bilinen sınırlar

- **Oturumlar:** SQLite'ta (`sessions` tablosu) saklanır; sunucu yeniden başlasa bile oturumunuz açık kalır ve CSRF anahtarları geçerliliğini korur. `SESSION_SECRET` değerini değiştirirseniz mevcut tüm oturumlar geçersiz olur (tekrar giriş gerekir).
- **Tailwind Play CDN:** Arayüz, derleme adımı gerektirmemesi için Tailwind'i CDN'den yükler ve bu nedenle sayfa açılışında internet bağlantısı ister. Tamamen çevrimdışı kurulum için Tailwind CLI ile derleyip çıktıyı `public/css/` altına alabilir ve `src/views/partials/head.ejs` içindeki CDN etiketini kaldırabilirsiniz.
- **Tek süreç:** Cron tek süreçte çalışır. Uygulamayı birden fazla kopya (cluster) olarak çalıştırırsanız aynı gün birden fazla mesaj gönderilmesini önlemek için yalnızca bir kopyada zamanlayıcıyı etkin bırakın.
- **Sunucu kapalıysa mesaj gitmez:** Zamanlanmış mesajlar yalnızca süreç çalışırken gönderilir; kaçırılan saat sonradan telafi edilmez. Sürekli çalışması için pm2/systemd kullanın.

---

## Lisans

MIT
