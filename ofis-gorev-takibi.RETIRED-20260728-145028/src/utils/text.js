'use strict';

/**
 * Metin yardımcıları.
 *
 * TÜRKÇE BÜYÜK/KÜÇÜK HARF TUZAĞI
 * ------------------------------
 * JavaScript'in `i` bayraklı düzenli ifadeleri Türkçe'ye göre çalışmaz:
 *
 *   /mercimek/i.test('MERCİMEK')  →  false   (!)
 *   /pilav/i.test('PİLAVI')       →  false   (!)
 *
 * Sebebi noktalı büyük İ (U+0130): standart harf katlaması bunu ASCII "i" ile
 * eşleştirmez. Catering menüleri genelde TAMAMI BÜYÜK HARF geldiği için bu,
 * sessizce yanlış sonuç veren cinsten bir hatadır — kod doğru görünür, eşleşme
 * olmaz.
 *
 * Çözüm: karşılaştırmadan önce metni Türkçe'ye duyarlı biçimde küçültüp ASCII'ye
 * sadeleştirmek ve kalıpları da ASCII yazmak. Aynı ihtiyaç hem Excel başlığı
 * tanımada hem yemek ikonu seçiminde olduğu için tek yerde durur.
 */

/**
 * Türkçe metni karşılaştırmaya hazır hâle getirir:
 * küçük harfe indirir, Türkçe karakterleri ASCII karşılıklarına çevirir,
 * fazla boşlukları temizler.
 *
 *   "Yemek Menüsü"  -> "yemek menusu"
 *   "MERCİMEK ÇORBA" -> "mercimek corba"
 *   "PİRİNÇ PİLAVI"  -> "pirinc pilavi"
 *
 * @param {*} value
 * @returns {string}
 */
function normalizeTr(value) {
  return String(value ?? '')
    // tr-TR yerelinde İ→i ve I→ı doğru biçimde eşlenir; sıralama önemlidir,
    // ı/İ dönüşümü buradan sonra sadeleştirilir.
    .toLocaleLowerCase('tr-TR')
    .replace(/ı/g, 'i')
    .replace(/ş/g, 's')
    .replace(/ğ/g, 'g')
    .replace(/ü/g, 'u')
    .replace(/ö/g, 'o')
    .replace(/ç/g, 'c')
    .replace(/\s+/g, ' ')
    .trim();
}

module.exports = { normalizeTr };
