# -*- coding: utf-8 -*-
"""
Sözleşme ve Form kazıyıcı (scraper).

Bir bankanın "Sözleşmeler ve Formlar" sayfasının URL'sini alır,
sayfadaki tüm doküman (PDF vb.) bağlantılarını başlıklarıyla birlikte çıkarır.

Belirli bir bankaya bağımlı değildir: sayfadaki tüm <a> etiketlerini tarayıp
doküman uzantısına (.pdf, .doc, .docx, .xls, .xlsx) sahip olanları toplar.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from urllib.parse import urljoin, urlparse, unquote

import requests
from bs4 import BeautifulSoup, Comment

# İndirilebilir doküman olarak kabul edilen uzantılar.
# ".vsf" bazı bankaların (DenizBank, Odeabank) kullandığı CMS'e özgü bir
# medya/doküman endpoint uzantısıdır (ör. "/medium/document-file-1425.vsf").
DOCUMENT_EXTENSIONS = (".pdf", ".doc", ".docx", ".xls", ".xlsx", ".rtf", ".txt", ".vsf")

# Mobil uygulama indirme / analitik yönlendirme servisleri. Bazı bankalar
# "Uygulamayı İndir" gibi butonları bu servislere yönlendirir; link metninde
# "indir" geçtiği için bunlar yanlışlıkla doküman sanılabilir.
HARICI_YONLENDIRME_DOMAINLERI = (
    "adjust.com", "onelink.me", "app.link", "branch.io",
    "apps.apple.com", "play.google.com", "itunes.apple.com",
)

# Bankanın KENDİ sitesinde de olsa, mobil uygulama indirme sayfasına giden
# yol kalıpları (ör. Alternatifbank'ta "/mobil-indir"). Link metninde "indir"
# geçtiği için bunlar da yanlışlıkla doküman sanılabilir.
MOBIL_UYGULAMA_YOL_KALIPLARI = ("mobil-indir", "mobil-uygulama", "app-indir")

# Bazı bankalar (ör. DenizBank) belgeleri ".pdf" yerine kendi CMS'lerine özgü
# uzantısız/özel uzantılı bir medya endpoint'i üzerinden sunar
# (örn. "/medium/document-file-11615.vsf"). Bu durumda uzantı yerine link
# metnindeki "indirme niyeti" ifadelerine bakılır.
INDIRME_ANAHTAR_KELIMELERI = (
    "dokümanı indir", "dokumani indir", "dökümanı indir", "belgeyi indir",
    "dosyayı indir", "download",
)

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0 Safari/537.36"
    ),
    "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
}


@dataclass
class Belge:
    """Tek bir sözleşme/form kaydı."""

    baslik: str          # Doküman başlığı (link metni)
    url: str             # Dokümanın tam (mutlak) URL'si
    tur: str             # "PDF", "DOC", "XLS" ...
    kategori: str        # "Sözleşme", "Form" veya "Diğer"

    def dict(self) -> dict:
        return asdict(self)


def _temizle(metin: str) -> str:
    """Fazla boşlukları ve satır sonlarını temizler."""
    return re.sub(r"\s+", " ", metin or "").strip()


# Bazı tarayıcı eklentileri (ör. Chrome'un yerleşik PDF görüntüleyicisi),
# yakaladıkları PDF linklerinin önüne kendi eklenti önekini ekler:
# "chrome-extension://efaidnbmnnnibpcajpcglclefindmkaj/https://site.com/x.pdf".
# Bu durumda gerçek hedef URL, önekten sonraki kısımdır.
_TARAYICI_EKLENTI_ONEKI_DESENI = re.compile(r"^chrome-extension://[a-z]+/(https?://.+)$", re.IGNORECASE)


def _eklenti_onekini_temizle(url: str) -> str:
    """URL'nin başındaki tarayıcı eklentisi önekini (varsa) kaldırıp gerçek hedefi döndürür."""
    eslesme = _TARAYICI_EKLENTI_ONEKI_DESENI.match(url)
    return eslesme.group(1) if eslesme else url


def _uzanti_turu(url: str) -> str | None:
    """URL'nin doküman uzantısını (büyük harf, noktasız) döndürür; doküman değilse None."""
    yol = urlparse(url).path.lower()
    for ext in DOCUMENT_EXTENSIONS:
        if yol.endswith(ext):
            return ext.lstrip(".").upper()
    return None


def _harici_yonlendirme_mi(url: str) -> bool:
    """URL'nin bilinen bir mobil uygulama/analitik yönlendirme servisine
    (ör. adjust.com, play.google.com) ya da bankanın kendi sitesindeki bir
    mobil uygulama indirme sayfasına (ör. "/mobil-indir") gidip gitmediğini
    kontrol eder."""
    parcalanmis = urlparse(url)
    host = parcalanmis.netloc.lower()
    if any(domain in host for domain in HARICI_YONLENDIRME_DOMAINLERI):
        return True
    yol = parcalanmis.path.lower()
    return any(kalip in yol for kalip in MOBIL_UYGULAMA_YOL_KALIPLARI)


def _kategori_bul(baslik: str, url: str) -> str:
    """Başlık/URL'den kabaca kategori tahmini yapar (Türkçe anahtar kelimelerle).

    Önce sadece BAŞLIĞA bakılır; URL'ye yalnızca başlıkta hiçbir ipucu yoksa
    başvurulur. Sebep: sayfanın/klasörün URL'si genelde "sozlesme-ve-formlar"
    gibi her iki kelimeyi de içerir (ör. Fibabanka), bu da başlık ne olursa
    olsun URL'den yanlış/sabit bir kategori çıkmasına yol açar.
    """
    baslik_metni = _tr_kucult(baslik)
    if "form" in baslik_metni:
        return "Form"
    if "sözleşme" in baslik_metni or "sozlesme" in baslik_metni:
        return "Sözleşme"

    url_metni = _tr_kucult(unquote(url))
    if "form" in url_metni:
        return "Form"
    if "sözleşme" in url_metni or "sozlesme" in url_metni:
        return "Sözleşme"
    return "Diğer"


def _tr_kucult(metin: str) -> str:
    """Türkçe kurallarına göre küçük harfe çevirir.

    Python'ın varsayılan str.lower() metodu 'İ' harfini Unicode kurallarına göre
    'i̇' (düz i + combining dot, \\u0307) yapar, 'I' harfini de düz 'i' yapar —
    ikisi de Türkçe "indir" gibi sabit string'lerle eşleşmez. Bu yüzden 'İ'/'I'
    karakterlerini önce elle normalize ediyoruz.
    """
    return metin.replace("İ", "i").replace("I", "ı").lower()


def _indirme_linki_mi(metin: str) -> bool:
    """Link metninin (kendi başlığı olmayan) genel bir 'indir' ifadesi olup olmadığını kontrol eder.

    Önce tam kalıp listesiyle (INDIRME_ANAHTAR_KELIMELERI) karşılaştırılır.
    Bunlardan biriyle eşleşmezse, KISA metinlerde (en fazla 3 kelime) tek
    başına "indir" kelimesi de yeterli sayılır — ör. ING'de "PDF İndir",
    Ziraat'te "PDF Görüntüle" gibi kısa link metinleri gerçek başlık değil,
    genel bir eylem ifadesidir. Uzun başlıklarda (ör. "...İndirimli Kredi
    Sözleşmesi") yanlış pozitif olmaması için bu gevşetme sadece kısa
    metinlerde uygulanır.
    """
    normalize = _tr_kucult(_temizle(metin))
    if any(kelime in normalize for kelime in INDIRME_ANAHTAR_KELIMELERI):
        return True
    # "indir" kelime sınırıyla (\b) aranır — aksi halde "indirim", "indirimli"
    # gibi alakasız kelimeler (ör. "Fuudy Restoran İndirimleri" kampanya linki)
    # yanlışlıkla eşleşir.
    if len(normalize.split()) <= 3 and re.search(r"\bindir\b", normalize):
        return True
    return False


# Başlık taşıyabilecek, ama kendisi doküman linki olmayan "düz metin" etiketleri.
_INLINE_METIN_ETIKETLERI = ("strong", "b", "em", "span", "p", "h1", "h2", "h3", "h4", "h5", "h6")


def _dogrudan_metin(el) -> str:
    """Bir elemanın kendi doğrudan metnini (alt elemanların İÇİNDEKİ linkli
    kısımları hariç tutarak) birleştirip döndürür.

    Bazı sitelerde başlık, elemanın doğrudan text node'unda durur (ör.
    Fibabanka'da <li>Başlık metni <div><a>...</a></div></li>); bazılarında
    ise <strong>/<span>/<p> gibi küçük bir inline etiketin içinde durur (ör.
    ING'de <div><strong>Başlık</strong><p><a>PDF İndir</a></p></div>). Normal
    .get_text() linkli/linksiz her şeyi birleştirir; bu fonksiyon sadece
    LİNK İÇERMEYEN kısımları izole eder.

    HTML yorumları (<!-- ... -->) BeautifulSoup'ta NavigableString'in bir alt
    sınıfı (Comment) olduğu için string=True filtresine takılır; bazı sitelerde
    (ör. VakıfBank) sayfanın herhangi bir yerinde debug/log amaçlı yorumlar
    bulunabilir ve bunlar yanlışlıkla "doğrudan metin" sanılabilir.
    """
    parcalar = []
    for cocuk in el.contents:
        if isinstance(cocuk, Comment):
            continue
        if isinstance(cocuk, str):
            parcalar.append(str(cocuk))
        elif cocuk.name in _INLINE_METIN_ETIKETLERI and not cocuk.find("a", href=True):
            parcalar.append(cocuk.get_text(" "))
    return _temizle(" ".join(parcalar))


def _kardes_baslik_ara(a_tag) -> str:
    """Link boş/simge metinliyse (ör. sadece indirme ikonu), başlığı linki
    saran en yakın anlamlı kapsayıcının KARDEŞ elemanlarında arar.

    Bazı sitelerde (ör. Fibabanka) her belge satırı, biri başlığı taşıyan
    (düz metin, <li>/<div>), diğeri ikon-linki taşıyan (görünür metni yok)
    kardeş elemanlardan oluşur — başlık linkin atası değil, kardeşidir.
    """
    for ata in a_tag.parents:
        if ata is None or ata.name in ("body", "html"):
            break
        if ata.name not in ("li", "div", "tr", "td", "span"):
            continue
        for kardes in ata.find_next_siblings(limit=3):
            temiz = _temizle(kardes.get_text())
            if temiz and not _indirme_linki_mi(temiz) and not kardes.find("a", href=True):
                return temiz
        for kardes in ata.find_previous_siblings(limit=3):
            temiz = _temizle(kardes.get_text())
            if temiz and not _indirme_linki_mi(temiz) and not kardes.find("a", href=True):
                return temiz
    return ""


def _yakin_baslik_ara(a_tag) -> str:
    """Link metni sadece 'İndir' gibi genel bir ifadeyse, gerçek başlığı sırasıyla
    şu yollarla arar: (1) atalardan birinin KENDİ doğrudan metni (2) atalardan
    birinin içindeki h1-h6/'.title' elemanı (3) kardeş elemanlar.

    (1) önce denenir çünkü daha spesifiktir — bir üst sekme/sayfa başlığını
    değil, doğrudan o belge satırının kendi metnini yakalar (ör. Fibabanka'da
    <li>Başlık <div><a>ikon</a></div></li> yapısı). (2) daha üstteki genel bir
    başlık (ör. DenizBank'ta <h4 class="title">) bulmak için ikinci sırada
    denenir; sadece (1) hiçbir seviyede sonuç vermezse denenir, aksi halde
    (ör. Fibabanka'daki sekme başlığı "Sözleşmeler" gibi) yanlış/genel bir
    başlık yakalama riski taşır.
    """
    # Atalar zincirinde çok yukarı çıkmak, sayfanın alakasız bir bölümünden
    # (ör. genel bir sekme başlığı, footer, script/log içeriği) metin
    # yakalama riskini artırır — bu yüzden derinlik 6 seviyeyle sınırlanır.
    _MAX_DERINLIK = 6

    for derinlik, ata in enumerate(a_tag.parents):
        if derinlik >= _MAX_DERINLIK or ata is None or ata.name in ("body", "html"):
            break
        dogrudan = _dogrudan_metin(ata)
        if dogrudan and not _indirme_linki_mi(dogrudan):
            return dogrudan

    # h1-h6/'.title' aramasından önce kardeş arama denenir: kardeş arama daha
    # spesifiktir (linkin doğrudan yanındaki elemanı hedefler), h1-h6/'.title'
    # ise atalar zincirinde çok daha üstteki genel bir kart/accordion başlığını
    # (ör. Burgan'da "Yürürlükte Olan Versiyonlar") yanlışlıkla bulabilir.
    kardes = _kardes_baslik_ara(a_tag)
    if kardes:
        return kardes

    for derinlik, ata in enumerate(a_tag.parents):
        if derinlik >= _MAX_DERINLIK or ata is None or ata.name in ("body", "html"):
            break
        baslik_el = ata.find(["h1", "h2", "h3", "h4", "h5", "h6"]) or ata.find(class_=re.compile("title", re.I))
        if baslik_el:
            temiz = _temizle(baslik_el.get_text())
            if temiz and not _indirme_linki_mi(temiz):
                return temiz

    return ""


# "[Başlık] Görüntülemek/Sesli dinlemek/İşaret diliyle görmek için tıklayınız"
# gibi eylem ifadesiyle BİTEN metinlerde başlığı ayıklamak için kullanılır.
_EYLEM_SONEKI_DESENI = re.compile(
    r"\s*(görüntülemek|(sesli\s+)?dinlemek|işaret\s+diliyle\s+(gör(mek)?|izlemek))"
    r"\s+için\s+tıklayınız\.?\s*$",
    re.IGNORECASE,
)


def _indirme_onekini_ayikla(metin: str) -> str:
    """Link/aria-label metninde genel bir eylem ifadesiyle karışık olarak
    duran asıl başlığı ayıklar. İki desteklenen desen:

    1. ÖNEK + ayraç (- veya :) + başlık, ör. Garanti BBVA'da
       "Dokümanı İndir - Çek İşlemleri Ürün Hizmet Bilgi Formu"
    2. Başlık + SONEK (eylem ifadesi), ör. Ziraat Bankası'nda
       "Avantajlı Vadeli Hesap Ek Sözleşmesi Görüntülemek için tıklayınız."
    """
    for ayrac in (" - ", ": "):
        if ayrac in metin:
            onek, sonrasi = metin.split(ayrac, 1)
            if _indirme_linki_mi(onek) and _temizle(sonrasi):
                return _temizle(sonrasi)

    sonek_temizlenmis = _EYLEM_SONEKI_DESENI.sub("", metin)
    if sonek_temizlenmis != metin and _temizle(sonek_temizlenmis):
        return _temizle(sonek_temizlenmis)

    return ""


def _link_basligi(a_tag, url: str) -> str:
    """Bağlantının en anlamlı başlığını üretir."""
    kendi_metni = _temizle(a_tag.get_text())
    aria_label = _temizle(a_tag.get("aria-label") or "")

    # "İndir - Gerçek Başlık" gibi birleşik aria-label varsa, gerçek başlığı
    # ayrıştırıp öncelikli olarak kullan (ör. Garanti BBVA).
    if aria_label:
        ayiklanan = _indirme_onekini_ayikla(aria_label)
        if ayiklanan:
            return ayiklanan

    # Link metni sadece "İndir" gibi genel bir ifadeyse, gerçek başlığı
    # yakındaki bir başlık etiketinden (h1-h6, .title) bulmayı dene.
    if not kendi_metni or _indirme_linki_mi(kendi_metni):
        yakin = _yakin_baslik_ara(a_tag)
        if yakin:
            return yakin

    for kaynak in (kendi_metni, a_tag.get("title"), aria_label):
        temiz = _temizle(kaynak or "")
        if temiz:
            return temiz
    # Metin yoksa dosya adından üret
    dosya = unquote(urlparse(url).path.rsplit("/", 1)[-1])
    return _temizle(re.sub(r"\.[a-z0-9]+$", "", dosya, flags=re.I).replace("_", " ").replace("-", " "))


def _kodlama_bul(yanit: requests.Response) -> str:
    """Yanıt için en güvenilir karakter kodlamasını belirler.

    Sıra: HTTP başlığındaki charset -> HTML <meta charset> -> chardet tahmini -> UTF-8.
    requests, charset belirtilmeyen text/* yanıtlar için ISO-8859-1 varsayar; bu da
    Türkçe karakterlerde bozulmaya (mojibake) yol açar. Bu yüzden özel mantık gerekir.
    """
    icerik_tipi = yanit.headers.get("Content-Type", "").lower()
    if "charset=" in icerik_tipi:
        return icerik_tipi.split("charset=")[-1].split(";")[0].strip()

    # HTML meta etiketinden charset ara (ham baytlar üzerinde)
    ham = yanit.content[:4096].decode("ascii", errors="ignore").lower()
    m = re.search(r'<meta[^>]+charset=["\']?\s*([a-z0-9\-_]+)', ham)
    if m:
        return m.group(1)

    return yanit.apparent_encoding or "utf-8"


def sayfayi_getir(url: str, timeout: int = 30) -> str:
    """Verilen URL'nin HTML içeriğini doğru kodlama ile indirir (statik istek)."""
    yanit = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout)
    yanit.raise_for_status()
    yanit.encoding = _kodlama_bul(yanit)
    return yanit.text


def sayfayi_tarayiciyla_getir(url: str, timeout: int = 30) -> str:
    """Sayfayı gerçek bir (headless) tarayıcıda açıp JS çalıştıktan sonraki HTML'i döndürür.

    Statik istekle belge bulunamayan sayfalar için kullanılır (belgeler JavaScript
    ile sonradan yükleniyorsa). Playwright'ın Chromium tarayıcısını kullanır.
    """
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        tarayici = p.chromium.launch(headless=True)
        try:
            sayfa = tarayici.new_page(
                user_agent=DEFAULT_HEADERS["User-Agent"],
                locale="tr-TR",
            )
            sayfa.goto(url, timeout=timeout * 1000, wait_until="networkidle")
            # Bazı sayfalar accordion/tab içinde gizli link render eder; kısa bir
            # ekstra bekleme, geç yüklenen içeriklerin de DOM'a girmesini sağlar.
            sayfa.wait_for_timeout(1500)
            return sayfa.content()
        finally:
            tarayici.close()


def belgeleri_ayikla(html: str, taban_url: str) -> list[Belge]:
    """HTML içinden tüm doküman bağlantılarını çıkarır (tekrarları eler)."""
    corba = BeautifulSoup(html, "lxml")
    belgeler: list[Belge] = []
    gorulen: set[str] = set()

    for a in corba.find_all("a", href=True):
        ham_url = a["href"].strip()
        if not ham_url or ham_url.startswith(("#", "javascript:", "mailto:", "tel:")):
            continue

        tam_url = _eklenti_onekini_temizle(urljoin(taban_url, ham_url))
        tur = _uzanti_turu(tam_url)
        if tur is None:
            # Uzantıdan doküman türü belirlenemedi; bazı bankalar (ör. DenizBank)
            # belgeleri özel bir CMS medya endpoint'i üzerinden ".pdf" uzantısı
            # olmadan sunar. Link metni "İndir" gibi bir ifadeyse yine de
            # doküman olarak kabul et — ANCAK link, bilinen bir mobil
            # uygulama/analitik yönlendirme servisine (ör. "Uygulamayı İndir"
            # butonları genelde adjust.com/app store gibi servislere gider)
            # gitmiyorsa. Aksi halde banka uygulaması indirme linkleri de
            # yanlışlıkla "doküman" sayılır (bkz. Akbank/Yapı Kredi "Geri").
            if _indirme_linki_mi(a.get_text()) and not _harici_yonlendirme_mi(tam_url):
                tur = "DOSYA"
            else:
                continue  # Doküman değil, atla

        if tam_url in gorulen:
            continue
        gorulen.add(tam_url)

        baslik = _link_basligi(a, tam_url)
        belgeler.append(
            Belge(
                baslik=baslik,
                url=tam_url,
                tur=tur,
                kategori=_kategori_bul(baslik, tam_url),
            )
        )

    return belgeler


# Statik istekle bu sayıdan az belge bulunursa, sayfa muhtemelen JS ile
# yükleniyordur ve tarayıcı (Playwright) yöntemine geçilir.
MIN_STATIK_BELGE_ESIGI = 1


def kaz(url: str, timeout: int = 30, zorla_tarayici: bool = False) -> list[Belge]:
    """URL'yi indirip belgeleri döndüren üst seviye yardımcı.

    Önce hızlı statik istek denenir. Hiç belge bulunamazsa (veya
    zorla_tarayici=True ise) otomatik olarak Playwright ile JS-render edilmiş
    sayfa üzerinden tekrar denenir.
    """
    if not zorla_tarayici:
        try:
            html = sayfayi_getir(url, timeout=timeout)
            belgeler = belgeleri_ayikla(html, taban_url=url)
            if len(belgeler) >= MIN_STATIK_BELGE_ESIGI:
                return belgeler
        except requests.RequestException:
            pass  # Statik istek başarısız oldu, tarayıcıya düş

    html = sayfayi_tarayiciyla_getir(url, timeout=timeout)
    return belgeleri_ayikla(html, taban_url=url)
