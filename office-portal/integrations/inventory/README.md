# inventory — Zimmet Sistemi Entegrasyonu

**Kaynak proje:** `zimmet-sistemi/` · Django 5 + PostgreSQL
**Durum:** Bağlanmadı (placeholder)

## Kaynak projenin özeti

- Rol tabanlı auth: `apps.accounts.User` (özel model, e-posta ile giriş)
- İş mantığı: `apps.inventory` (Cihaz/Zimmet/Şirket/Çalışan CRUD, PDF/Excel)
- Aynı tasarım dilini paylaşıyoruz zaten (bkz. `static/css/theme.css` —
  Zimmet'in `style.css`'inden birebir uyarlandı).

## Neden diğer 4 modülden farklı ele alınmalı?

Portal da Zimmet de Django. Diğer modüller (Node.js) için API/reverse-proxy
gerekirken, Zimmet için **aynı Django projesine dahil etme (shared_db /
app transplant)** seçeneği var — bu, gerçek "tek uygulama" hissini en
sorunsuz veren yoldur. Ayrıntılı adım adım plan için ana konuşmadaki
"Zimmet Entegrasyon Planı" bölümüne bakın.

## Bilinen riskler (özet)

- `AUTH_USER_MODEL` projede bir kez belirlenir ve sonradan değiştirilemez.
  Portal şu an Django'nun varsayılan `User` modelini kullanıyor; Zimmet'in
  `accounts.User` modeline geçiş kararı **gerçek kullanıcı verisi
  oluşmadan önce** verilmeli.
- Statik dosya isim çakışması: `main.js`, `style.css` iki tarafta da var.
- Zimmet'in kendi `base.html`/sidebar/navbar'ı, portalinkiyle çakışabilir;
  şablonlar portalin `base.html`'ini kullanacak şekilde uyarlanmalı.
