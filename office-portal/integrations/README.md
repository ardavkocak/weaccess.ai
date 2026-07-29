# Entegrasyon Katmanı

Bu klasör, Office Portal'ın `weaccess.ai` çalışma alanındaki bağımsız
projelerle (Zimmet Sistemi, Ofis Görev Takibi, İK Otomasyonu, Aylık
Takip, Dokümantasyon Otomasyonu) konuşacağı **tek nokta**dır.

## Neden bu katman var?

Portal'ın Sidebar/Header/Dashboard/View'ları hiçbir zaman doğrudan başka
bir projenin koduna veya veritabanına bağlanmaz. Bunun yerine burada
tanımlı bir **adapter** (`BaseIntegration` alt sınıfı) ile konuşur. Bu
sayede:

- Bir modül henüz bağlı değilken de portal sorunsuz çalışır (`base.py`
  içindeki varsayılanlar "henüz bağlanmadı" döner).
- Bir modül gerçek projeye bağlandığında yalnızca ilgili adapter'ın
  içi doldurulur; şablonlar, URL'ler, Sidebar hiç değişmez.
- Her entegrasyonun bağlantı şekli (paylaşılan veritabanı, REST API,
  reverse proxy) birbirinden bağımsız seçilebilir.

## Klasör yapısı

```
integrations/
├── base.py                # Ortak sözleşme: BaseIntegration, IntegrationStatus, IntegrationInfo
├── registry.py             # slug -> adapter eşlemesi (tek kayıt noktası)
├── inventory/               # Zimmet Sistemi (zimmet-sistemi)
├── office_bot/               # Ofis Görev Takibi (ofis-gorev-takibi) — görev + yemek modülleri
├── hr/                        # İK Otomasyonu (ik-otomasyon)
├── monthly_tracking/           # Aylık Takip (aylik-takip)
└── documentation/                # Dokümantasyon Otomasyonu (dokumantasyon-otomasyon)
```

Her alt klasör aynı üçlüyü içerir:

| Dosya | Görev |
|---|---|
| `adapter.py` | `BaseIntegration`'dan türeyen sınıf + `IntegrationInfo` meta verisi |
| `config.py` | Bu entegrasyona özgü ortam değişkeni tanımları (henüz kullanılmıyor, ileride bağlanınca devreye girer) |
| `README.md` | Kaynak projenin özeti ve o modüle özel entegrasyon notları/riskleri |

## Şu an neredeyiz?

Hiçbir adapter gerçek bir bağlantı kurmuyor. `portal/views.py` içindeki
`ModulePlaceholderView`, ilgili adapter'ın `health_check()` sonucunu
placeholder sayfasında gösteriyor — bugün hepsi "bağlantı kurulmadı"
yazıyor. Bu, altyapının uçtan uca doğru bağlandığının kanıtı; bir sonraki
adım tek tek adapter'ları gerçek projelerle konuşacak şekilde doldurmak.
