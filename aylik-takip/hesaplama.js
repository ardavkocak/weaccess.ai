// Aylik calisma/izin ozetini hesaplayan is mantigi.

const { ayinResmiTatilleri } = require('./resmiTatiller');

const GUNLUK_SAAT = 9; // gunluk mesai 9 saat kabul edilir

/**
 * Verilen yil/ay icin hafta ici (Pzt-Cuma) is gunu sayisini bulur.
 * @param {number} yil
 * @param {number} ay 1-12
 * @returns {number}
 */
function ayinIsGunuSayisi(yil, ay) {
  const gunSayisi = new Date(yil, ay, 0).getDate();
  let is = 0;
  for (let g = 1; g <= gunSayisi; g++) {
    const gun = new Date(yil, ay - 1, g).getDay(); // 0=Pazar,6=Cumartesi
    if (gun !== 0 && gun !== 6) is++;
  }
  return is;
}

/**
 * Tek bir personel icin aylik ozet hesaplar.
 *
 * Calismasi gereken saat = (ayin is gunu - resmi tatil) x 9
 * Izin suresi calismasi gereken saate dahildir (dusulmez); fark hesaplanirken
 * izinli gecirilen saatler fiili calisma saatine eklenir.
 *
 * @param {Object} p
 * @param {string} p.isim
 * @param {number} p.calismaSaat  PDF Toplam Sure (fiili calisilan saat)
 * @param {number} p.izinGun      Gorselden okunan izin gun sayisi (hafta ici)
 * @param {number} p.isGunu       Ayin toplam is gunu (Pzt-Cuma)
 * @param {number} p.resmiGun     Aydaki hafta ici resmi tatil gunu
 * @returns {Object}
 */
function personelOzet({ isim, calismaSaat, izinGun, isGunu, resmiGun }) {
  const izinSaat = izinGun * GUNLUK_SAAT;
  const resmiSaat = resmiGun * GUNLUK_SAAT;

  // Calismasi gereken gun = is gunu - resmi tatil (izin dusulmez).
  const calismaGerekliGun = Math.max(0, isGunu - resmiGun);
  const gerekliSaat = calismaGerekliGun * GUNLUK_SAAT;

  // Izinli gecirilen saatler fiili calisilmis gibi sayilir.
  const fark = Math.round((calismaSaat + izinSaat - gerekliSaat) * 100) / 100;

  return {
    isim,
    calismaSaat: Math.round(calismaSaat * 100) / 100,
    izinGun,
    izinSaat,
    resmiGun,
    resmiSaat,
    calismaGerekliGun,
    gerekliSaat: Math.round(gerekliSaat * 100) / 100,
    fark,
    durum: Math.abs(fark) < 0.01 ? 'tam' : fark > 0 ? 'fazla' : 'eksik',
  };
}

/**
 * Tum personel + izin kayitlarindan aylik ozet tablosu uretir.
 *
 * @param {Object} p
 * @param {Array<{isim:string,toplamSaat:number}>} p.personeller  PDF'ten
 * @param {Array<{isim:string,isGunu:number}>} p.izinler           Gorselden
 * @param {Function} p.isimEslesir  (a,b)=>bool isim karsilastirici
 * @param {number} p.yil
 * @param {number} p.ay 1-12
 * @returns {Object}
 */
function aylikOzet({ personeller, izinler, isimEslesir, yil, ay }) {
  const isGunu = ayinIsGunuSayisi(yil, ay);
  const resmiTatiller = ayinResmiTatilleri(yil, ay);
  const resmiHaftaIci = resmiTatiller.filter((t) => t.haftaIci);
  const resmiGun = resmiHaftaIci.length;

  const satirlar = personeller.map((per) => {
    // Bu personele ait izin kayitlarini isimle eslesir topla.
    const kendiIzinleri = izinler.filter((iz) => isimEslesir(per.isim, iz.isim));
    const izinGun = kendiIzinleri.reduce((t, iz) => t + (iz.isGunu || 0), 0);
    return {
      ...personelOzet({
        isim: per.isim,
        calismaSaat: per.toplamSaat,
        izinGun,
        isGunu,
        resmiGun,
      }),
      // PDF'ten gelen ek detaylar (saat kirilimlari).
      sira: per.sira,
      bolgedeSaat: per.bolgedeSaat,
      muafiyetSaat: per.muafiyetSaat,
      // Gorselden gelen izin kayitlari (tarih araligi + tip dahil).
      izinKayitlari: kendiIzinleri,
    };
  });

  // Izin kaydi olup PDF'te personeli bulunamayanlar (uyari icin).
  const eslesmeyenIzinler = izinler.filter(
    (iz) => !personeller.some((per) => isimEslesir(per.isim, iz.isim))
  );

  return {
    yil,
    ay,
    gunlukSaat: GUNLUK_SAAT,
    ayinIsGunu: isGunu,
    resmiGun,
    resmiSaat: resmiGun * GUNLUK_SAAT,
    resmiTatiller: resmiHaftaIci,
    resmiTatillerTum: resmiTatiller,
    personeller: satirlar,
    eslesmeyenIzinler,
  };
}

module.exports = { aylikOzet, personelOzet, ayinIsGunuSayisi, GUNLUK_SAAT };
