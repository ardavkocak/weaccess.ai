'use strict';

/**
 * Yemek menüsü duyuru metni.
 *
 * Örnek çıktı:
 *
 *   🍽️ **Yarının Yemek Menüsü**
 *
 *   📅 23 Temmuz 2026 Perşembe
 *
 *   🥣 Mercimek Çorbası
 *   🍗 Tavuk Sote
 *   🍚 Pirinç Pilavı
 *   🥗 Mevsim Salata
 *
 *   Yarın yemek yiyecek misiniz? Lütfen aşağıdaki butonlardan birini seçiniz.
 *
 *   ✅ Yiyeceğim: 18   •   ❌ Yemeyeceğim: 5
 *
 * Katılım satırı her oy değişiminde yeniden üretilip mesaja yazılır; sayılar
 * böylece gerçek zamanlı görünür.
 */

const { formatLongTR } = require('../utils/date');
const { normalizeTr } = require('../utils/text');
const { dayLabel } = require('./messages');

/**
 * Yemek adına göre ikon seçer.
 *
 * KALIPLAR ASCII YAZILIR. Menüler çoğunlukla TAMAMI BÜYÜK HARF gelir ve
 * JavaScript'in `i` bayrağı Türkçe'de çalışmaz: `/mercimek/i` metni "MERCİMEK"
 * ile EŞLEŞMEZ (noktalı İ sorunu). Bu yüzden yemek adı önce `normalizeTr` ile
 * ASCII'ye sadeleştirilir, kalıplar da ona göre yazılır — "PİRİNÇ PİLAVI" da
 * "Pirinç Pilavı" da aynı sonucu verir. Ayrıntı: utils/text.js
 *
 * Sıra ÖNEMLİDİR: ilk eşleşen kural kazanır. Örneğin "Tavuk Çorbası" çorba
 * sayılmalıdır, bu yüzden çorba kuralı tavuktan önce gelir. Hiçbiri tutmazsa
 * nötr bir tabak ikonu kullanılır — bilinmeyen yemek yine düzgün görünür.
 */
const ICON_RULES = [
  [/corba/, '🥣'],
  [/salata|sogus|piyaz/, '🥗'],
  [/pilav|bulgur|makarna|eriste|spagetti|spaghetti|penne|noodle/, '🍚'],
  // "pasta" Türkçe'de kektir, makarna değil — bu yüzden tatlı grubundadır.
  [/tatli|balli|pasta|baklava|sutlac|kek|puding|helva|revani|magnolia|supangle|trilece|browni|muhallebi|panna|asure|kunefe|profiterol/, '🍰'],
  [/meyve|elma|portakal|karpuz|uzum|muz|kavun/, '🍎'],
  [/ayran|yogurt|cacik|kefir|sut(?!lac)/, '🥛'],
  [/tavuk|pilic|hindi|shnitzel|sniztel/, '🍗'],
  [/balik|hamsi|somon|levrek|palamut/, '🐟'],
  [/kofte|\bet\b|etli|kebap|kebabi|biftek|kavurma|sote|tava|sarma|kilis|bahcivan/, '🥩'],
  // "böreği" → normalize sonrası "boregi" olur (ğ→g); hem k hem g kabul edilir.
  [/bore[kg]|pogaca|pide|lahmacun|manti|gozleme/, '🥧'],
  [/pizza|burger|sandvic|tost/, '🍔'],
  [/fasulye|nohut|mercimek|bakla|turlu|sebze|dolma|musakka|ispanak|bezelye|patlican|begendi/, '🥘'],
  [/patates|kizartma/, '🍟'],
  [/mesrubat|cay|kahve|icecek|limonata|komposto|soda|kola/, '🥤'],
];

/** Bir yemek adı için uygun ikonu döner. */
function iconFor(dish) {
  const text = normalizeTr(dish);
  for (const [pattern, icon] of ICON_RULES) {
    if (pattern.test(text)) return icon;
  }
  return '🍽️';
}

/**
 * Katılım bloğunun başlığı.
 *
 * Menü kaydı silinmişse mesajın tamamı yeniden üretilemez; o durumda mevcut
 * metnin yalnızca bu başlıktan sonrası tazelenir (bkz.
 * mealNotifier.service.refreshCountsBlock). Bu yüzden sabit ve tekildir —
 * mesajın en üstündeki "🍽️ Yarının Yemek Menüsü" başlığıyla karışmaz.
 */
const COUNTS_HEADING = '🍽️ **Katılım Durumu**';

/**
 * Katılım özeti.
 *
 * YALNIZCA SAYI — İSİM YOK. Kanalda kimin ne yediğini listelemek hem mesajı
 * şişirir hem gereksiz bir görünürlük yaratır. İsim bazlı ayrıntı (yiyecekler /
 * yemeyecekler / cevap vermeyenler) yalnızca admin panelindedir.
 *
 * Oy yokken de gösterilir ki kullanıcı sayaçların çalıştığını görsün.
 */
function renderCounts({ yes = 0, no = 0 } = {}) {
  return [
    COUNTS_HEADING,
    '',
    `✅ Yiyeceğim (${yes})`,
    `❌ Yemeyeceğim (${no})`,
  ].join('\n');
}

/**
 * Duyuru mesajının tam metni.
 *
 * @param {object} p
 * @param {object} p.menu   mealMenu.service kaydı (items, menu_date, dayName).
 * @param {object} p.counts { yes, no }
 * @returns {string}
 */
function renderAnnouncement({ menu, counts }) {
  // formatLongTR zaten "23 Temmuz 2026 Perşembe" üretir; Excel'den gelen gün adı
  // farklıysa (örn. kısaltma) tarihin kendisi esas alınır, tutarlılık bozulmasın.
  const dateLine = formatLongTR(menu.menu_date);

  // Gün etiketi: hafta içi "Yarın", Cuma günü Pazartesi menüsü için "Pazartesi".
  const day = dayLabel(menu.menu_date);

  // Her yemek: ikon + ad + (varsa) kalori. Kalori bilgisi olmayan eski/kalorisiz
  // kayıtlarda parantez hiç yazılmaz.
  const dishes = menu.items
    .map((item) => {
      const kcal = item.kcal != null ? ` (${item.kcal} kcal)` : '';
      return `${iconFor(item.name)} ${item.name}${kcal}`;
    })
    .join('\n');

  return [
    `🍽️ **${day.genitive} Yemek Menüsü**`,
    '',
    `📅 ${dateLine}`,
    '',
    dishes,
    '',
    `${day.plain} yemek yiyecek misiniz? Lütfen aşağıdaki butonlardan birini seçiniz.`,
    '',
    renderCounts(counts),
  ].join('\n');
}

module.exports = { renderAnnouncement, renderCounts, iconFor, COUNTS_HEADING };
