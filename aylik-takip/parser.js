// Dosyalardan veri cikaran parser fonksiyonlari.
// - PDF (Muafiyet Raporu): koordinat bazli okuma ile her personelin
//   Ad Soyad + Toplam Sure (Saat) bilgisini cikarir.
// - Word (docx): ham metinden personel + saat cikarmayi dener (yedek yol).
// - Gorsel (png/jpeg/webp): OCR ile izin kayitlarini (isim + tarih araligi) okur.

const mammoth = require('mammoth');
const Tesseract = require('tesseract.js');

// Personel satirindaki alan degerleri / baslik gurultusu (isim degil).
const AD_GURULTU =
  /^(Evet|Hayır|Gönderilmedi|Reddedildi|Onaylandı|Araştırmacı|Destek|İşlemler|Proje|Ar-?Ge)\b|-\s*20\d{2}|Personel|Toplam|Süre/i;

/**
 * Turkce ondalikli sayiyi (virgullu) js sayisina cevirir. "108,85" -> 108.85
 * @param {string} s
 * @returns {number}
 */
function sayiya(s) {
  if (s == null) return 0;
  const n = parseFloat(String(s).replace(/\./g, '').replace(',', '.'));
  return isNaN(n) ? 0 : n;
}

/**
 * Muafiyet Raporu PDF'inden personel listesini koordinat bazli cikarir.
 *
 * Rapor tablosu sabit sutun x-konumlarina sahiptir:
 *   x~47  : Sira No
 *   x~70  : TC Kimlik No (11 hane)
 *   x~107 : Adi Soyadi (bazen 2 satira bolunur)
 *   x~762 : Toplam Sure (Saat)  <- calisilan saat olarak bunu aliriz
 *
 * Gercek personel satiri = ayni y bandinda hem Sira No hem 11 haneli TC olmasi.
 * Boylece ay-listesi / ozet satirlari elenir.
 *
 * @param {Buffer} buffer
 * @returns {Promise<Array<{sira:number, tc:string, isim:string, toplamSaat:number}>>}
 */
async function pdfPersonelCikar(buffer) {
  const pdfjs = await import('pdfjs-dist/legacy/build/pdf.mjs');
  const data = new Uint8Array(buffer);
  const doc = await pdfjs.getDocument({ data, useSystemFonts: true }).promise;

  const personeller = [];

  for (let p = 1; p <= doc.numPages; p++) {
    const page = await doc.getPage(p);
    const tc = await page.getTextContent();
    const items = tc.items
      .map((it) => ({
        s: it.str.trim(),
        x: Math.round(it.transform[4]),
        y: Math.round(it.transform[5]),
      }))
      .filter((it) => it.s);

    // Gercek personel satirlari: 11 haneli TC (x 60-90) ve yaninda sira no.
    const tcTokenlar = items.filter(
      (i) => i.x >= 60 && i.x <= 95 && /^\d{11}$/.test(i.s)
    );

    for (const tcT of tcTokenlar) {
      const siraTok = items.find(
        (i) =>
          i.x >= 38 &&
          i.x <= 60 &&
          /^\d{1,3}$/.test(i.s) &&
          Math.abs(i.y - tcT.y) < 6
      );
      if (!siraTok) continue;

      // Ad Soyad tokenlari: x 100-132, TC'nin y bandina yakin, gurultu haric.
      // Her isim tokenini EN YAKIN TC'ye atamak icin, bu TC gercekten en
      // yakin mi diye kontrol ederiz (baska personelin ismini kapmamak icin).
      const isimTok = items
        .filter(
          (i) =>
            i.x >= 100 &&
            i.x <= 132 &&
            /[A-Za-zÇĞİÖŞÜçğıöşü]/.test(i.s) &&
            !AD_GURULTU.test(i.s) &&
            i.y <= tcT.y + 12 &&
            i.y >= tcT.y - 3
        )
        // Bu token bu TC'ye en yakin mi? Degilse (baska TC daha yakinsa) atla.
        .filter((i) => {
          const enYakin = tcTokenlar.reduce((a, b) =>
            Math.abs(b.y - i.y) < Math.abs(a.y - i.y) ? b : a
          );
          return enYakin === tcT;
        })
        .sort((a, b) => b.y - a.y || a.x - b.x); // ustten alta

      // Belli bir x sutunundaki (tcT ile ayni y bandinda) sayi degerini alir.
      // Sutun x-merkezleri sabit oldugu icin +-24px pencere yeterli.
      const sutunSaat = (xMin, xMax) => {
        const tok = items.filter(
          (i) =>
            i.x >= xMin &&
            i.x <= xMax &&
            /^[\d.,]+$/.test(i.s) &&
            Math.abs(i.y - tcT.y) < 6
        );
        return tok.length ? sayiya(tok[tok.length - 1].s) : 0;
      };

      // Saat sutunlari (Muafiyet Raporu tablosu):
      //   x~576 Bolgede Bulundugu Sure + Resmi Tatil + Yillik Izin
      //   x~628 Muafiyete Konu Saat
      //   x~762 Toplam Sure  <- fiili calisilan saat
      const bolgedeSaat = sutunSaat(560, 600);
      const muafiyetSaat = sutunSaat(612, 652);
      const toplamSaat = sutunSaat(745, 795);

      const toplamTokVar = items.some(
        (i) =>
          i.x >= 745 &&
          i.x <= 795 &&
          /^[\d.,]+$/.test(i.s) &&
          Math.abs(i.y - tcT.y) < 6
      );
      if (!isimTok.length || !toplamTokVar) continue;

      const isim = isimTok
        .map((t) => t.s)
        .join(' ')
        .replace(/\s+/g, ' ')
        .trim();

      personeller.push({
        sira: parseInt(siraTok.s, 10),
        tc: tcT.s,
        isim,
        toplamSaat,
        bolgedeSaat,
        muafiyetSaat,
      });
    }
  }

  personeller.sort((a, b) => a.sira - b.sira);
  return personeller;
}

/**
 * Word (docx) yedek yolu: ham metinden "Ad Soyad ... 108,85" satirlarini dener.
 * PDF koordinat yontemi kadar guvenilir degildir; ana format PDF'tir.
 * @param {Buffer} buffer
 * @returns {Promise<Array<{isim:string, toplamSaat:number}>>}
 */
async function wordPersonelCikar(buffer) {
  const result = await mammoth.extractRawText({ buffer });
  const satirlar = (result.value || '').split(/\r?\n/);
  const personeller = [];
  for (const satir of satirlar) {
    // "Melih ERÜNAL ... 108,85" - isim + satirdaki son ondalikli sayi.
    const isimM = satir.match(
      /([A-ZÇĞİÖŞÜ][a-zçğıöşü]+(?:\s+[A-ZÇĞİÖŞÜ][A-Za-zÇĞİÖŞÜçğıöşü]+)+)/
    );
    const sayilar = satir.match(/\d+(?:,\d+)?/g);
    if (isimM && sayilar && sayilar.length) {
      personeller.push({
        isim: isimM[1].trim(),
        toplamSaat: sayiya(sayilar[sayilar.length - 1]),
      });
    }
  }
  return personeller;
}

/**
 * Gorselden OCR ile ham metin okur (Turkce + Ingilizce).
 * @param {Buffer} buffer
 * @returns {Promise<string>}
 */
async function gorselOcr(buffer) {
  const {
    data: { text },
  } = await Tesseract.recognize(buffer, 'tur+eng');
  return text || '';
}

/**
 * "GG.AA.YYYY" tarihini Date'e cevirir.
 * @param {string} s
 * @returns {Date|null}
 */
function tarihParse(s) {
  const m = s.match(/(\d{1,2})[.\/-](\d{1,2})[.\/-](\d{4})/);
  if (!m) return null;
  const d = new Date(
    parseInt(m[3], 10),
    parseInt(m[2], 10) - 1,
    parseInt(m[1], 10)
  );
  return isNaN(d.getTime()) ? null : d;
}

/**
 * Bir Date'i 'YYYY-MM-DD' string'ine cevirir (yerel saat).
 * @param {Date} d
 * @returns {string}
 */
function isoTarih(d) {
  return (
    d.getFullYear() +
    '-' +
    String(d.getMonth() + 1).padStart(2, '0') +
    '-' +
    String(d.getDate()).padStart(2, '0')
  );
}

/**
 * Izne cikis ve donus tarihleri arasindaki NET izin gun sayisi.
 *
 * - bas = izne cikilan gun (dahil)
 * - bit = geri donulen gun (HARIC — o gun calisilir)
 * - Hafta sonlari (Cmt/Pazar) sayilmaz.
 * - Resmi tatile denk gelen hafta ici gunler izinden DUSULUR; cunku o gunler
 *   zaten resmi tatil olarak ayri sayilir ve mesaiden muaftir (cift saymayi onler).
 *
 * @param {Date} bas
 * @param {Date} bit
 * @param {Set<string>} [resmiSet] 'YYYY-MM-DD' formatinda resmi tatil gunleri
 * @returns {number}
 */
function aralikIsGunu(bas, bit, resmiSet) {
  let g = 0;
  const d = new Date(bas.getTime());
  while (d < bit) {
    // bitis HARIC: donus gununde calisilir
    const w = d.getDay();
    const haftaIci = w !== 0 && w !== 6;
    const resmiMi = resmiSet ? resmiSet.has(isoTarih(d)) : false;
    if (haftaIci && !resmiMi) g++;
    d.setDate(d.getDate() + 1);
  }
  return g;
}

/**
 * Izin gorselinin OCR metninden izin kayitlarini cikarir.
 *
 * Beklenen satir yapisi (izin listesi ekran goruntusu):
 *   <talep tarihi> <saat> <email> <Ad Soyad> <izin baslangic> <izin bitis> <tip> <sistem>
 * Ornek:
 *   06.07.2026 11:20:22 mlhrnl00@gmail.com Melih ERÜNAL 13.07.2026 20.07.2026 Yıllık İzin Nevisoft
 *
 * Her satirda 3 tam tarih olur: [0]=talep, [1]=izne cikis, [2]=geri donus.
 * Izin gun sayisi = cikis..donus arasi hafta ici gun (donus HARIC, resmi tatil dusuk).
 * Isim = email ile ilk izin tarihi arasindaki metin.
 *
 * @param {string} metin
 * @param {Set<string>} [resmiSet] 'YYYY-MM-DD' resmi tatil gunleri (izinden dusulur)
 * @returns {Array<{isim:string, baslangic:string, bitis:string, isGunu:number, tip:string}>}
 */
function izinKayitlariCikar(metin, resmiSet) {
  const satirlar = metin.split(/\r?\n/).filter((s) => s.trim());
  const kayitlar = [];

  for (const satir of satirlar) {
    const tarihler = satir.match(/\d{1,2}[.\/-]\d{1,2}[.\/-]\d{4}/g);
    if (!tarihler || tarihler.length < 3) continue; // en az talep+bas+bitis

    // Son iki tam tarih = izin baslangic ve bitis.
    const bitisStr = tarihler[tarihler.length - 1];
    const baslangicStr = tarihler[tarihler.length - 2];
    const bas = tarihParse(baslangicStr);
    const bit = tarihParse(bitisStr);
    if (!bas || !bit) continue;

    // Isim: ilk izin (baslangic) tarihinden ONCEKI bolumden cikarilir.
    // Bu bolumde talep tarihi, saat, email ve ad soyad bulunur.
    // Email OCR'da bozuk okunabildigi icin ( or. "mlhrnl00(© gmail.com"),
    // email'e guvenmeyiz; bunun yerine ilk izin tarihinden geriye dogru
    // ardisik "kelime" (harf grubu) tokenlarini isim olarak aliriz.
    let isim = '';
    const izinIdx = satir.indexOf(baslangicStr);
    const onBolum = izinIdx >= 0 ? satir.slice(0, izinIdx) : satir;
    // Harf iceren, en az 2 harfli ve icinde '@'/rakam/nokta gecmeyen tokenlar.
    const kelimeler = onBolum
      .split(/\s+/)
      .filter(
        (w) =>
          /^[A-Za-zÇĞİÖŞÜçğıöşü]{2,}$/.test(w) &&
          !/gmail|hotmail|outlook|com|nevisoft/i.test(w)
      );
    // Sondan geriye dogru ardisik isim tokenlarini al (ad soyad genelde sonda).
    isim = kelimeler.slice(-3).join(' ').replace(/\s+/g, ' ').trim();

    // Izin tipi (Yıllık İzin, Mazeret vb.) - bitis tarihinden sonraki metin.
    const sonrasi = satir.slice(satir.lastIndexOf(bitisStr) + bitisStr.length);
    const tip = sonrasi
      .replace(/Nevisoft|nevisoft/g, '')
      .replace(/\s+/g, ' ')
      .trim();

    kayitlar.push({
      isim,
      baslangic: baslangicStr,
      bitis: bitisStr,
      isGunu: aralikIsGunu(bas, bit, resmiSet),
      tip: tip || 'İzin',
    });
  }

  return kayitlar;
}

// Turkce ozel karakterleri ASCII karsiligina indirger. OCR sik sik Ş/Ç/Ğ/Ö/Ü/İ
// gibi harfleri duz S/C/G/O/U/I olarak okur (or. "ŞEN" -> "SEN"); bu yuzden
// isim eslestirmede hem orijinal hem ASCII-sadelestirilmis hali denenir.
function asciiye(s) {
  return String(s)
    .replace(/ş/gi, 's')
    .replace(/ç/gi, 'c')
    .replace(/ğ/gi, 'g')
    .replace(/ö/gi, 'o')
    .replace(/ü/gi, 'u')
    .replace(/ı/g, 'i')
    .replace(/İ/g, 'i');
}

/**
 * Iki ismin ayni kisiye ait olup olmadigini gevsek karsilastirir.
 * Buyuk/kucuk harf, Turkce karakter (OCR'in Ş/Ç/Ğ gibi harfleri duz okumasi
 * dahil) ve token sirasi farklarina toleransli.
 * @param {string} a
 * @param {string} b
 * @returns {boolean}
 */
function isimEslesir(a, b) {
  const norm = (s) =>
    asciiye(String(s).toLocaleLowerCase('tr'))
      .replace(/[^a-z\s]/g, ' ')
      .replace(/\s+/g, ' ')
      .trim()
      .split(' ')
      .filter(Boolean)
      .sort();
  const ta = norm(a);
  const tb = norm(b);
  if (!ta.length || !tb.length) return false;
  // Kucuk kumeyi buyuk kume iceriyor mu? (en az 2 ortak token veya tam kapsama)
  const ortak = ta.filter((t) => tb.includes(t));
  return ortak.length >= Math.min(2, Math.min(ta.length, tb.length));
}

module.exports = {
  pdfPersonelCikar,
  wordPersonelCikar,
  gorselOcr,
  izinKayitlariCikar,
  isimEslesir,
  aralikIsGunu,
  tarihParse,
  isoTarih,
  sayiya,
};
