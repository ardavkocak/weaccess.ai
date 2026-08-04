// Turkiye resmi tatilleri (gomulu).
// Dini bayramlar her yil degistigi icin yila gore tarihler burada tanimlidir.
// Tarih formati: 'YYYY-MM-DD'

const RESMI_TATILLER = {
  2025: [
    { tarih: '2025-01-01', ad: 'Yilbasi' },
    { tarih: '2025-03-30', ad: 'Ramazan Bayrami 1. Gun' },
    { tarih: '2025-03-31', ad: 'Ramazan Bayrami 2. Gun' },
    { tarih: '2025-04-01', ad: 'Ramazan Bayrami 3. Gun' },
    { tarih: '2025-04-23', ad: 'Ulusal Egemenlik ve Cocuk Bayrami' },
    { tarih: '2025-05-01', ad: 'Emek ve Dayanisma Gunu' },
    { tarih: '2025-05-19', ad: 'Ataturku Anma, Genclik ve Spor Bayrami' },
    { tarih: '2025-06-06', ad: 'Kurban Bayrami 1. Gun' },
    { tarih: '2025-06-07', ad: 'Kurban Bayrami 2. Gun' },
    { tarih: '2025-06-08', ad: 'Kurban Bayrami 3. Gun' },
    { tarih: '2025-06-09', ad: 'Kurban Bayrami 4. Gun' },
    { tarih: '2025-07-15', ad: 'Demokrasi ve Milli Birlik Gunu' },
    { tarih: '2025-08-30', ad: 'Zafer Bayrami' },
    { tarih: '2025-10-29', ad: 'Cumhuriyet Bayrami' },
  ],
  2026: [
    { tarih: '2026-01-01', ad: 'Yilbasi' },
    { tarih: '2026-03-20', ad: 'Ramazan Bayrami 1. Gun' },
    { tarih: '2026-03-21', ad: 'Ramazan Bayrami 2. Gun' },
    { tarih: '2026-03-22', ad: 'Ramazan Bayrami 3. Gun' },
    { tarih: '2026-04-23', ad: 'Ulusal Egemenlik ve Cocuk Bayrami' },
    { tarih: '2026-05-01', ad: 'Emek ve Dayanisma Gunu' },
    { tarih: '2026-05-19', ad: 'Ataturku Anma, Genclik ve Spor Bayrami' },
    { tarih: '2026-05-27', ad: 'Kurban Bayrami 1. Gun' },
    { tarih: '2026-05-28', ad: 'Kurban Bayrami 2. Gun' },
    { tarih: '2026-05-29', ad: 'Kurban Bayrami 3. Gun' },
    { tarih: '2026-05-30', ad: 'Kurban Bayrami 4. Gun' },
    { tarih: '2026-07-15', ad: 'Demokrasi ve Milli Birlik Gunu' },
    { tarih: '2026-08-30', ad: 'Zafer Bayrami' },
    { tarih: '2026-10-29', ad: 'Cumhuriyet Bayrami' },
  ],
  2027: [
    { tarih: '2027-01-01', ad: 'Yilbasi' },
    { tarih: '2027-03-09', ad: 'Ramazan Bayrami 1. Gun' },
    { tarih: '2027-03-10', ad: 'Ramazan Bayrami 2. Gun' },
    { tarih: '2027-03-11', ad: 'Ramazan Bayrami 3. Gun' },
    { tarih: '2027-04-23', ad: 'Ulusal Egemenlik ve Cocuk Bayrami' },
    { tarih: '2027-05-01', ad: 'Emek ve Dayanisma Gunu' },
    { tarih: '2027-05-16', ad: 'Kurban Bayrami 1. Gun' },
    { tarih: '2027-05-17', ad: 'Kurban Bayrami 2. Gun' },
    { tarih: '2027-05-18', ad: 'Kurban Bayrami 3. Gun' },
    { tarih: '2027-05-19', ad: 'Ataturku Anma, Genclik ve Spor Bayrami / Kurban Bayrami 4. Gun' },
    { tarih: '2027-07-15', ad: 'Demokrasi ve Milli Birlik Gunu' },
    { tarih: '2027-08-30', ad: 'Zafer Bayrami' },
    { tarih: '2027-10-29', ad: 'Cumhuriyet Bayrami' },
  ],
  2028: [
    { tarih: '2028-01-01', ad: 'Yilbasi' },
    { tarih: '2028-02-27', ad: 'Ramazan Bayrami 1. Gun' },
    { tarih: '2028-02-28', ad: 'Ramazan Bayrami 2. Gun' },
    { tarih: '2028-02-29', ad: 'Ramazan Bayrami 3. Gun' },
    { tarih: '2028-04-23', ad: 'Ulusal Egemenlik ve Cocuk Bayrami' },
    { tarih: '2028-05-01', ad: 'Emek ve Dayanisma Gunu' },
    { tarih: '2028-05-05', ad: 'Kurban Bayrami 1. Gun' },
    { tarih: '2028-05-06', ad: 'Kurban Bayrami 2. Gun' },
    { tarih: '2028-05-07', ad: 'Kurban Bayrami 3. Gun' },
    { tarih: '2028-05-08', ad: 'Kurban Bayrami 4. Gun' },
    { tarih: '2028-05-19', ad: 'Ataturku Anma, Genclik ve Spor Bayrami' },
    { tarih: '2028-07-15', ad: 'Demokrasi ve Milli Birlik Gunu' },
    { tarih: '2028-08-30', ad: 'Zafer Bayrami' },
    { tarih: '2028-10-29', ad: 'Cumhuriyet Bayrami' },
  ],
};

/**
 * Verilen yil ve ay icin resmi tatilleri dondurur.
 * Sadece hafta ici (Pazartesi-Cuma) gunlere denk gelen resmi tatiller
 * calisma gununden dusulur; hafta sonuna denk gelenler zaten calisma gunu degildir.
 * @param {number} yil
 * @param {number} ay  1-12
 * @returns {Array<{tarih: string, ad: string, haftaIci: boolean}>}
 */
function ayinResmiTatilleri(yil, ay) {
  const liste = RESMI_TATILLER[yil] || [];
  return liste
    .filter((t) => {
      const d = new Date(t.tarih + 'T00:00:00');
      return d.getFullYear() === yil && d.getMonth() + 1 === ay;
    })
    .map((t) => {
      const d = new Date(t.tarih + 'T00:00:00');
      const gun = d.getDay(); // 0=Pazar, 6=Cumartesi
      return { ...t, haftaIci: gun !== 0 && gun !== 6 };
    });
}

/**
 * Verilen yil(lar) icin tum resmi tatil tarihlerini 'YYYY-MM-DD' Set'i olarak
 * dondurur. Izin araligindaki resmi tatilleri dusmek icin kullanilir.
 * @param {...number} yillar
 * @returns {Set<string>}
 */
function resmiTatilSeti(...yillar) {
  const set = new Set();
  for (const yil of yillar) {
    (RESMI_TATILLER[yil] || []).forEach((t) => set.add(t.tarih));
  }
  return set;
}

module.exports = { RESMI_TATILLER, ayinResmiTatilleri, resmiTatilSeti };
