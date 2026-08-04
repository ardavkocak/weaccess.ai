'use strict';

/**
 * Excel (.xlsx) yemek listesi okuyucu.
 *
 * Dosya YALNIZCA yükleme anında okunur. Buradan çıkan satırlar
 * `mealMenu.service.saveRows()` ile veritabanına yazılır; sistem sonrasında hep
 * veritabanını kullanır, dosyayı bir daha açmaz.
 *
 * İKİ FARKLI DOSYA BİÇİMİ DESTEKLENİR
 * ===================================
 * Catering firmaları menüyü iki ayrı düzende hazırlar. Okuyucu önce daha özgün
 * olan blok düzenini dener, tutmazsa düz tabloya düşer. Hangi biçimin okunduğu
 * sonuçta `columns.format` olarak bildirilir ve panelde gösterilir.
 *
 * 1) HAFTALIK BLOK  (`format: 'block'`)
 * -------------------------------------
 * "Tarih" diye bir sütun YOKTUR; tarihler sütun başlıklarındadır ve sayfa
 * hafta hafta tekrar eder:
 *
 *        │   B          C      │   D        E      │   F          G      │
 *   R4   │ PAZARTESİ  ENERJİ   │ SALI     ENERJİ   │ ÇARŞAMBA   ENERJİ   │  ← gün başlığı
 *   R5   │ 06.07.2026   1385   │ 07.07.26   1263   │ 08.07.2026   1250   │  ← tarih satırı
 *   R6   │ TARHANA ÇORBA 194   │ TAVUK ÇORBA 189   │ EZOGELİN     162    │  ┐
 *   R7   │ KÖRİ TAVUK    384   │ KURU FASULYE 315  │ BODRUM KÖFTE 310    │  │ yemekler
 *   ...  │ ...                 │ ...               │ ...                 │  ┘
 *   R11  │ PAZARTESİ  ENERJİ   │ SALI     ENERJİ   │ ÇARŞAMBA   ENERJİ   │  ← YENİ HAFTA
 *
 * Okuma kuralları:
 *   • Gün başlığı satırı = en az iki hücresi TAM olarak bir hafta gününe eşit
 *     olan satır. Bu satırlar bloklara ayırma noktalarıdır; yeni hafta başladığında
 *     okuma kendiliğinden devam eder.
 *   • Gün sütunu = başlığı hafta günü olan sütun. ENERJİ (kalori) sütunları
 *     başlıkları gün olmadığı için hiç okunmaz — tamamen yok sayılır.
 *   • Tarih satırı = başlıktan sonraki, gün sütunlarında tarih ÇÖZÜLEBİLEN ilk
 *     satır. (Ayın ilk haftasında Pazartesi/Salı boş olabilir; o günler atlanır.)
 *   • Yemekler = tarih satırının altından, gün sütunlarının TAMAMI boşalana veya
 *     bir sonraki gün başlığına gelene kadar. Böylece sayfa sonundaki imza
 *     satırları ("GIDA MÜHENDİSİ") yemek sanılmaz.
 *
 * 2) DÜZ TABLO  (`format: 'table'`)
 * ---------------------------------
 * Her satır bir gün; başlıklar serbesttir:
 *
 *   Tarih       │ Gün       │ Çorba     │ Ana Yemek │ Salata
 *   23.07.2026  │ Perşembe  │ Mercimek  │ Tavuk Sote│ Mevsim
 *
 *   • Başlık satırı ilk 15 satırda aranır (üstteki logo satırları sorun değil).
 *   • Tarih ve Gün sütunları eş anlamlı sözlüğüyle tanınır.
 *   • Kalan TÜM sütunlar yemek sayılır; tek "Menü" sütunu da yayılmış tablo da
 *     aynı kodla okunur.
 *
 * SÜTUN EŞLEŞTİRME ALTYAPISI
 * ==========================
 * `parseBuffer(buffer, { mapping })` düz tablo algılamasını ezer:
 *
 *   mapping = { headerRow: 3, date: 2, day: 3, items: [4, 5, 6] }  // 1 tabanlı
 *
 * Dönen `columns` alanı hangi sütunun neye eşlendiğini bildirir; panel bunu
 * rapor olarak gösterir. "Sütunları elle eşleştir" ekranı eklenmek istenirse
 * kullanıcının seçimini aynı `mapping` nesnesi olarak geçirmek yeterlidir.
 */

const ExcelJS = require('exceljs');
const { todayISO } = require('../utils/date');
const { normalizeTr } = require('../utils/text');

/** Başlık satırı bu kadar satır içinde aranır. */
const HEADER_SEARCH_ROWS = 15;

/** Tek bir yüklemede kabul edilen en fazla satır (kazara dev dosya koruması). */
const MAX_ROWS = 1000;

/**
 * Başlık eş anlamlıları. Normalize edilmiş (ASCII, küçük harf) hâlleriyle
 * karşılaştırılır; başlığın İÇİNDE geçmesi yeterlidir ("yemek menusu" → menü).
 */
const HEADER_ALIASES = {
  date: ['tarih', 'date', 'gun tarihi'],
  day: ['gun', 'day', 'haftanin gunu', 'gunu'],
};

/** Yemek sütunu olduğu kesin olan başlıklar (algılama güvenini artırır). */
const MEAL_HINTS = [
  'menu', 'yemek', 'corba', 'ana', 'yan', 'salata', 'tatli', 'icecek',
  'ogun', 'ogle', 'aksam', 'kahvalti', 'icerik', 'liste',
];

/**
 * Hafta günleri: normalize edilmiş anahtar → görünen ad.
 *
 * Eşleştirme TAM EŞİTLİKLE yapılır, `includes` ile DEĞİL: "cumartesi" metni
 * "cuma" içerdiği için kısmi eşleştirme Cumartesi'yi Cuma sanardı.
 */
const WEEKDAYS = {
  pazartesi: 'Pazartesi',
  sali: 'Salı',
  carsamba: 'Çarşamba',
  persembe: 'Perşembe',
  cuma: 'Cuma',
  cumartesi: 'Cumartesi',
  pazar: 'Pazar',
};

/** Bir hücre metni hafta günü mü? Öyleyse görünen adını döner. */
function weekdayOf(text) {
  return WEEKDAYS[normalize(text)] ?? null;
}

/** Blok düzeninde bir satırın gün başlığı sayılması için gereken en az gün sayısı. */
const MIN_WEEKDAYS_IN_HEADER = 2;

/**
 * Türkçe karakterleri sadeleştirip küçük harfe indirir.
 * "Yemek Menüsü" -> "yemek menusu"
 *
 * Ortak yardımcıdan gelir (bkz. utils/text.js): aynı katlama kuralı yemek ikonu
 * seçiminde de kullanılıyor, iki yerde ayrı ayrı durmasın.
 */
const normalize = normalizeTr;

/** Hücrenin görünen metnini güvenle alır (formül, zengin metin, tarih dahil). */
function cellText(cell) {
  if (cell == null) return '';
  const value = cell.value;

  if (value == null) return '';
  if (value instanceof Date) return value.toISOString();
  if (typeof value === 'object') {
    // Formül hücresi: hesaplanmış sonucu kullan. Zengin metin: parçaları birleştir.
    if (value.result != null) return String(value.result);
    if (Array.isArray(value.richText)) return value.richText.map((part) => part.text).join('');
    if (value.text != null) return String(value.text);
    return '';
  }
  return String(value).trim();
}

/**
 * Bir hücreyi "YYYY-MM-DD" tarihine çevirir; çevrilemezse null.
 *
 * Desteklenenler:
 *   - Gerçek Excel tarih hücresi (exceljs bunu Date verir)
 *   - Excel seri numarası (1900 tabanlı)
 *   - "17.07.2026", "17/07/2026", "17-07-2026", "2026-07-17"
 */
function parseDate(cell) {
  if (cell == null) return null;
  const value = cell.value;

  // 1) Gerçek tarih hücresi. exceljs tarihi UTC olarak verir; gün kaymasını
  //    önlemek için UTC bileşenlerini olduğu gibi kullanırız.
  if (value instanceof Date) {
    return `${value.getUTCFullYear()}-${pad(value.getUTCMonth() + 1)}-${pad(value.getUTCDate())}`;
  }

  const text = cellText(cell).trim();
  if (!text) return null;

  // 2) ISO biçimi (yükleme sırasında ürettiğimiz metin de buraya düşer).
  const iso = text.match(/^(\d{4})-(\d{2})-(\d{2})/);
  if (iso) return `${iso[1]}-${iso[2]}-${iso[3]}`;

  // 3) Gün önce biçimleri: 17.07.2026 / 17-7-26 / 17/07/2026
  const dmy = text.match(/^(\d{1,2})[./-](\d{1,2})[./-](\d{2,4})$/);
  if (dmy) {
    const day = Number(dmy[1]);
    const month = Number(dmy[2]);
    let year = Number(dmy[3]);
    if (year < 100) year += 2000;
    if (month < 1 || month > 12 || day < 1 || day > 31) return null;
    return `${year}-${pad(month)}-${pad(day)}`;
  }

  // 4) Excel seri numarası (hücre tarih olarak biçimlenmemişse sayı gelir).
  const serial = Number(text);
  if (Number.isFinite(serial) && serial > 1 && serial < 100_000) {
    // Excel'in 1900 epoch'u + meşhur "1900 artık yıl" hatası telafisi.
    const ms = Math.round((serial - 25_569) * 86_400 * 1000);
    const date = new Date(ms);
    if (!Number.isNaN(date.getTime())) {
      return `${date.getUTCFullYear()}-${pad(date.getUTCMonth() + 1)}-${pad(date.getUTCDate())}`;
    }
  }

  return null;
}

function pad(number) {
  return String(number).padStart(2, '0');
}

/** Bir başlık metni verilen eş anlamlılardan birine uyuyor mu? */
function matchesAlias(header, aliases) {
  const normalized = normalize(header);
  if (!normalized) return false;
  return aliases.some((alias) => normalized === alias || normalized.includes(alias));
}

/**
 * Başlık satırını ve sütun eşlemesini bulur.
 *
 * @returns {{ headerRow: number, columns: object }|null}
 *   columns = { date: number|null, day: number|null, items: number[], labels: object }
 */
function detectColumns(worksheet) {
  const lastRow = Math.min(worksheet.rowCount, HEADER_SEARCH_ROWS);

  for (let rowNumber = 1; rowNumber <= lastRow; rowNumber += 1) {
    const row = worksheet.getRow(rowNumber);
    const headers = [];

    row.eachCell({ includeEmpty: false }, (cell, colNumber) => {
      const text = cellText(cell).trim();
      if (text) headers.push({ col: colNumber, text });
    });

    if (headers.length < 2) continue; // Başlık satırı en az iki sütun içermeli.

    const dateColumn = headers.find((h) => matchesAlias(h.text, HEADER_ALIASES.date));
    if (!dateColumn) continue; // Tarih sütunu olmadan satırları güne bağlayamayız.

    // "Gün" başlığı "gun tarihi" ile karışmasın diye tarih sütunu hariç tutulur.
    const dayColumn = headers.find(
      (h) => h.col !== dateColumn.col && matchesAlias(h.text, HEADER_ALIASES.day)
    );

    // Kalan her sütun yemek sütunudur. Başlığı tanıdıksa (MEAL_HINTS) bu yalnızca
    // güveni artırır; tanınmayan başlıklar da yemek olarak alınır ki
    // "Çorba/Ana Yemek/Tatlı" gibi serbest başlıklar kaybolmasın.
    const itemColumns = headers
      .filter((h) => h.col !== dateColumn.col && h.col !== dayColumn?.col)
      .map((h) => h.col);

    if (itemColumns.length === 0) continue;

    const labels = {};
    for (const header of headers) labels[header.col] = header.text;

    return {
      headerRow: rowNumber,
      columns: {
        date: dateColumn.col,
        day: dayColumn?.col ?? null,
        items: itemColumns,
        labels,
        // Panelde "şu sütunlar yemek olarak okundu" bilgisini göstermek için.
        recognizedMealHeaders: itemColumns.filter((col) =>
          MEAL_HINTS.some((hint) => normalize(labels[col]).includes(hint))
        ),
      },
    };
  }

  return null;
}

/**
 * Bir yemek hücresini tek tek yemeklere böler.
 *
 * Aynı hücrede birden fazla yemek olması çok yaygındır:
 *   "Mercimek Çorbası\nTavuk Sote\nPirinç Pilavı"
 *   "Mercimek Çorbası, Tavuk Sote"
 * Satır sonu ve noktalı virgül kesin ayraçtır; virgül de ayraç sayılır ama
 * "Etli Nohut, Pilav" gibi kullanımlarda doğru sonucu verir.
 */
function splitDishes(text) {
  return String(text ?? '')
    .split(/[\n\r;]+|,(?=\s)/)
    .map((part) => part.trim().replace(/\s+/g, ' '))
    .filter((part) => part.length > 0);
}

/**
 * Bir ENERJİ hücresini kaloriye (tam sayı) çevirir; çözülemezse null.
 *
 * "194", "194 kcal", "1.385" (binlik ayraç) gibi biçimleri kabul eder; içindeki
 * ilk sayı grubu alınır. Toplam enerji satırları (günlük ~1385) tek yemekten
 * çok büyüktür ama biz onu YEMEK satırlarıyla eşlemeyiz — yalnızca yemek
 * satırının hizasındaki hücreyi okuruz (bkz. parseBlockLayout).
 */
function parseKcal(cell) {
  const text = cellText(cell).trim();
  if (!text) return null;
  const digits = text.replace(/[.\s]/g, ''); // "1.385" -> "1385"
  const match = digits.match(/\d+/);
  if (!match) return null;
  const value = Number(match[0]);
  return Number.isFinite(value) && value > 0 ? value : null;
}

/**
 * Bir yemek satırından `{ name, kcal }` nesneleri üretir.
 *
 * Kalori YALNIZCA hücrede TEK yemek varsa eşlenir: bir hücrede birden fazla
 * yemek (satır sonuyla ayrılmış) varken tek bir kalori değeri hangisine aitmiş
 * belirsizdir; yanlış eşleme yapmaktansa o yemekleri kalorisiz bırakırız.
 *
 * @param {string} dishText Gün sütunundaki yemek hücresinin metni.
 * @param {number|null} kcal Aynı satırdaki ENERJİ hücresinden okunan değer.
 * @returns {Array<{ name: string, kcal: number|null }>}
 */
function toDishEntries(dishText, kcal) {
  const dishes = splitDishes(dishText);
  if (dishes.length === 1) return [{ name: dishes[0], kcal: kcal ?? null }];
  return dishes.map((name) => ({ name, kcal: null }));
}

/* ─────────────────────── Haftalık blok düzeni ─────────────────────── */

/**
 * Bir satır "gün başlığı" satırı mı? (PAZARTESİ | ENERJİ | SALI | ENERJİ ...)
 *
 * @returns {Array<{ col: number, dayName: string }>|null}
 *   Gün sütunları; gün başlığı satırı değilse null.
 */
function readDayHeaderRow(worksheet, rowNumber) {
  const row = worksheet.getRow(rowNumber);
  const dayColumns = [];

  row.eachCell({ includeEmpty: false }, (cell, colNumber) => {
    const dayName = weekdayOf(cellText(cell));
    if (dayName) dayColumns.push({ col: colNumber, dayName });
  });

  return dayColumns.length >= MIN_WEEKDAYS_IN_HEADER ? dayColumns : null;
}

/**
 * Bir hücre yemek adı olarak kabul edilir mi?
 *
 * ENERJİ sütunlarını zaten hiç okumuyoruz; bu kontrol, birleştirilmiş hücre ya
 * da kayık bir kalori değeri gün sütununa düşerse onu elemek içindir. Ayrıca
 * blok içinde tekrar eden gün/ENERJİ başlıkları yemek sayılmaz.
 */
function isDishText(text) {
  const trimmed = String(text ?? '').trim();
  if (!trimmed) return false;
  if (/^[\d.,\s]+$/.test(trimmed)) return false;        // yalnızca sayı (kalori)
  if (weekdayOf(trimmed)) return false;                 // tekrar eden gün başlığı
  if (normalize(trimmed) === 'enerji') return false;
  return true;
}

/**
 * Haftalık blok düzenini okur.
 *
 * @returns {{ rows: object[], skipped: number, warnings: string[], columns: object }|null}
 *   Düzen tanınmazsa null (çağıran düz tablo okuyucusuna düşer).
 */
function parseBlockLayout(worksheet) {
  // 1) Sayfadaki tüm gün başlığı satırlarını bul; bunlar blok sınırlarıdır.
  const headers = [];
  for (let rowNumber = 1; rowNumber <= worksheet.rowCount; rowNumber += 1) {
    const dayColumns = readDayHeaderRow(worksheet, rowNumber);
    if (dayColumns) headers.push({ rowNumber, dayColumns });
  }

  if (headers.length === 0) return null; // Blok düzeni değil.

  const rows = [];
  const seen = new Map();
  const warnings = [];
  const ignoredColumns = new Map();
  let skipped = 0;

  headers.forEach((header, index) => {
    // Blok, bir sonraki gün başlığına (ya da sayfa sonuna) kadar sürer.
    const blockEnd = index + 1 < headers.length
      ? headers[index + 1].rowNumber - 1
      : worksheet.rowCount;

    const dayCols = new Set(header.dayColumns.map((d) => d.col));

    // Gün olmayan başlıklar (ENERJİ vb.) not edilir. ENERJİ sütunları kalori
    // için OKUNUR; diğer tanınmayan sütunlar yalnızca rapora yazılır.
    const energyCols = [];
    worksheet.getRow(header.rowNumber).eachCell({ includeEmpty: false }, (cell, colNumber) => {
      const text = cellText(cell).trim();
      if (!text || dayCols.has(colNumber)) return;
      ignoredColumns.set(colNumber, text);
      if (normalize(text) === 'enerji') energyCols.push(colNumber);
    });

    // Her gün sütununu, SAĞINDAKİ ilk ENERJİ sütunuyla eşle (düzen:
    // PAZARTESİ | ENERJİ | SALI | ENERJİ ...). Bulunamazsa kalori okunmaz.
    const energyColFor = (dayColNumber) => {
      const candidates = energyCols.filter((col) => col > dayColNumber).sort((a, b) => a - b);
      return candidates.length > 0 ? candidates[0] : null;
    };

    // 2) Tarih satırı: gün sütunlarında tarih çözülebilen ilk satır.
    let dateRow = null;
    for (let rowNumber = header.rowNumber + 1; rowNumber <= blockEnd; rowNumber += 1) {
      const row = worksheet.getRow(rowNumber);
      if (header.dayColumns.some((day) => parseDate(row.getCell(day.col)))) {
        dateRow = rowNumber;
        break;
      }
    }

    if (dateRow === null) {
      warnings.push(`${header.rowNumber}. satırdaki gün başlığının altında tarih bulunamadı; blok atlandı.`);
      return;
    }

    // 3) Yemek satırları: tarih satırının altından, gün sütunlarının TAMAMI
    //    boşalana kadar. Sayfa sonundaki imza/dipnot satırları böyle elenir.
    const dishRows = [];
    for (let rowNumber = dateRow + 1; rowNumber <= blockEnd; rowNumber += 1) {
      const row = worksheet.getRow(rowNumber);
      const hasAny = header.dayColumns.some((day) => cellText(row.getCell(day.col)).trim());
      if (!hasAny) break;
      dishRows.push(rowNumber);
    }

    // 4) Her gün sütununu tek tek topla.
    for (const day of header.dayColumns) {
      const menuDate = parseDate(worksheet.getRow(dateRow).getCell(day.col));

      // Ayın ilk/son haftasında bazı günler boştur (henüz ay başlamamış ya da
      // bitmiştir). Tarihi olmayan sütun sessizce atlanır.
      if (!menuDate) continue;

      const energyCol = energyColFor(day.col);
      const items = [];
      for (const rowNumber of dishRows) {
        const dishCell = worksheet.getRow(rowNumber).getCell(day.col);
        const text = cellText(dishCell);
        if (!isDishText(text)) continue;
        // Yemekle aynı satırdaki ENERJİ hücresini oku (varsa).
        const kcal = energyCol ? parseKcal(worksheet.getRow(rowNumber).getCell(energyCol)) : null;
        items.push(...toDishEntries(text, kcal));
      }

      if (items.length === 0) {
        skipped += 1; // Tarih var, yemek yok (hafta sonu / tatil).
        continue;
      }

      if (seen.has(menuDate)) {
        warnings.push(`${menuDate} tarihi dosyada birden fazla kez var; ilk blok kullanıldı.`);
        continue;
      }
      seen.set(menuDate, true);

      rows.push({ menu_date: menuDate, day_name: day.dayName, items });
    }
  });

  if (rows.length === 0) return null; // Başlıklar vardı ama veri çıkmadı.

  return {
    rows,
    skipped,
    warnings,
    columns: {
      format: 'block',
      blockCount: headers.length,
      headerRows: headers.map((h) => h.rowNumber),
      dayColumns: headers[0].dayColumns,
      ignoredColumns: [...ignoredColumns.entries()].map(([col, label]) => ({ col, label })),
    },
  };
}

/**
 * Yükleme raporunda gösterilecek "ne nasıl okundu" özeti.
 *
 * Biçime özgü ayrıntıyı görünümden uzak tutar: yeni bir dosya biçimi eklendiğinde
 * yalnızca burası genişler, meal.ejs değişmez.
 *
 * @returns {Array<{ label: string, value: string }>}
 */
function describeColumns(columns) {
  if (!columns) return [];

  if (columns.format === 'block') {
    return [
      { label: 'Biçim', value: `Haftalık blok (${columns.blockCount} hafta)` },
      { label: 'Gün başlığı satırları', value: columns.headerRows.join(', ') },
      { label: 'Gün sütunları', value: columns.dayColumns.map((d) => d.dayName).join(', ') },
      {
        label: 'Yok sayılan sütunlar',
        value: columns.ignoredColumns.length > 0
          ? [...new Set(columns.ignoredColumns.map((c) => c.label))].join(', ')
          : '—',
      },
    ];
  }

  const labels = columns.labels ?? {};
  return [
    { label: 'Biçim', value: 'Düz tablo' },
    { label: 'Tarih sütunu', value: String(labels[columns.date] ?? `Sütun ${columns.date}`) },
    { label: 'Gün sütunu', value: columns.day ? String(labels[columns.day] ?? `Sütun ${columns.day}`) : '—' },
    { label: 'Yemek sütunları', value: columns.items.map((col) => labels[col] ?? `Sütun ${col}`).join(', ') },
  ];
}

/* ─────────────────────────── Düz tablo düzeni ─────────────────────────── */

/**
 * Her satırı bir gün olan klasik tabloyu okur.
 *
 * @param {object} worksheet
 * @param {object} columns  detectColumns() çıktısı ya da elle eşleştirme.
 * @param {number} headerRow
 * @returns {{ rows: object[], skipped: number, warnings: string[], columns: object }}
 */
function parseTableLayout(worksheet, columns, headerRow) {
  const rows = [];
  const seen = new Set();
  const warnings = [];
  let skipped = 0;

  for (let rowNumber = headerRow + 1; rowNumber <= worksheet.rowCount; rowNumber += 1) {
    if (rows.length >= MAX_ROWS) {
      warnings.push(`Dosyada ${MAX_ROWS} satırdan fazlası var; fazlası okunmadı.`);
      break;
    }

    const row = worksheet.getRow(rowNumber);
    const menuDate = parseDate(row.getCell(columns.date));

    // Tarihi olmayan satır: boş satır, ara başlık veya dipnot olabilir; atlanır.
    if (!menuDate) {
      const hasContent = columns.items.some((col) => cellText(row.getCell(col)).trim());
      if (hasContent) skipped += 1;
      continue;
    }

    // Düz tabloda ayrı bir kalori sütunu düzeni yoktur; yemekler kalorisiz
    // alınır. (Kalori bilgisi haftalık blok düzenindeki ENERJİ sütunlarından
    // gelir; bkz. parseBlockLayout.)
    const items = [];
    for (const col of columns.items) {
      for (const name of splitDishes(cellText(row.getCell(col)))) {
        items.push({ name, kcal: null });
      }
    }

    if (items.length === 0) {
      skipped += 1;
      continue; // Tarih var ama yemek yok (tatil/izin satırı olabilir).
    }

    // Aynı tarih iki kez geçerse ilk satır geçerlidir; ikincisi bildirilir.
    if (seen.has(menuDate)) {
      warnings.push(`${menuDate} tarihi dosyada birden fazla kez var; ilk satır kullanıldı.`);
      continue;
    }
    seen.add(menuDate);

    rows.push({
      menu_date: menuDate,
      day_name: columns.day ? cellText(row.getCell(columns.day)).trim() : '',
      items,
    });
  }

  return { rows, skipped, warnings, columns: { ...columns, format: 'table' }, headerRow };
}

/* ─────────────────────────────── Giriş noktası ─────────────────────────────── */

/**
 * Excel dosyasını okur ve menü satırlarını üretir.
 *
 * Biçim otomatik seçilir: önce haftalık blok denenir (daha özgün desen), tutmazsa
 * düz tabloya düşülür. `mapping` verilirse doğrudan düz tablo okunur.
 *
 * @param {Buffer} buffer Yüklenen dosyanın içeriği.
 * @param {object} [options]
 * @param {object} [options.mapping] Düz tablo algılamasını ezen sütun eşlemesi:
 *   `{ headerRow: 3, date: 1, day: 2, items: [3, 4] }` (1 tabanlı sütun numaraları).
 * @param {string} [options.sheetName] Belirli bir sayfa; yoksa ilk sayfa.
 * @returns {Promise<{
 *   ok: boolean, message?: string,
 *   rows: Array<{ menu_date: string, day_name: string, items: string[] }>,
 *   columns?: object, details?: Array<{label: string, value: string}>,
 *   headerRow?: number, sheetName?: string,
 *   skipped: number, warnings: string[]
 * }>}
 */
async function parseBuffer(buffer, { mapping = null, sheetName = null } = {}) {
  const workbook = new ExcelJS.Workbook();

  try {
    await workbook.xlsx.load(buffer);
  } catch (error) {
    return {
      ok: false,
      message: 'Dosya okunamadı. Geçerli bir .xlsx dosyası olduğundan emin olun.',
      rows: [],
      skipped: 0,
      warnings: [String(error.message ?? error)],
    };
  }

  const worksheet = sheetName
    ? workbook.getWorksheet(sheetName)
    : workbook.worksheets[0];

  if (!worksheet) {
    return { ok: false, message: 'Dosyada okunabilir bir sayfa bulunamadı.', rows: [], skipped: 0, warnings: [] };
  }

  const parsed = readWorksheet(worksheet, mapping);

  if (parsed.error) {
    return { ok: false, message: parsed.error, rows: [], skipped: 0, warnings: [], sheetName: worksheet.name };
  }

  const { rows, skipped, warnings, columns, headerRow = 0 } = parsed;

  if (rows.length === 0) {
    return {
      ok: false,
      message: 'Dosyada okunabilir menü satırı bulunamadı. Tarih ve yemek sütunlarını kontrol edin.',
      rows: [],
      columns,
      details: describeColumns(columns),
      headerRow,
      sheetName: worksheet.name,
      skipped,
      warnings,
    };
  }

  // Geçmiş tarihli satırlar sorun değildir (geçmiş ay yüklenebilir) ama admin'in
  // yanlış dosyayı seçtiğini fark etmesi için bilgi olarak bildirilir.
  const today = todayISO();
  const past = rows.filter((row) => row.menu_date < today).length;
  if (past > 0) warnings.push(`${past} gün geçmiş tarihli.`);

  return {
    ok: true,
    rows: rows.sort((a, b) => a.menu_date.localeCompare(b.menu_date)),
    columns,
    details: describeColumns(columns),
    headerRow,
    sheetName: worksheet.name,
    skipped,
    warnings,
  };
}

/**
 * Biçim seçimi: elle eşleştirme > haftalık blok > düz tablo.
 * @returns {{ rows, skipped, warnings, columns, headerRow }|{ error: string }}
 */
function readWorksheet(worksheet, mapping) {
  // 1) Elle eşleştirme verildiyse algılama tamamen atlanır.
  if (mapping?.date) {
    const columns = {
      date: Number(mapping.date),
      day: mapping.day ? Number(mapping.day) : null,
      items: (mapping.items ?? []).map(Number).filter(Boolean),
      labels: {},
      recognizedMealHeaders: [],
    };
    if (columns.items.length === 0) {
      return { error: 'Sütun eşleştirmesinde en az bir yemek sütunu seçilmelidir.' };
    }
    return parseTableLayout(worksheet, columns, Number(mapping.headerRow ?? 1));
  }

  // 2) Haftalık blok düzeni (tarihler sütun başlıklarında).
  const block = parseBlockLayout(worksheet);
  if (block) return block;

  // 3) Düz tablo (her satır bir gün).
  const detected = detectColumns(worksheet);
  if (detected) return parseTableLayout(worksheet, detected.columns, detected.headerRow);

  return {
    error:
      'Dosya biçimi tanınamadı. İki düzen desteklenir: (1) haftalık blok — gün adları ' +
      '(PAZARTESİ, SALI…) sütun başlığı, altında tarih ve yemek satırları; (2) düz tablo — ' +
      'bir "Tarih" sütunu ve yanında yemek sütunları.',
  };
}

module.exports = {
  parseBuffer,
  describeColumns,
  // Test edilebilirlik ve ileride eklenecek eşleştirme ekranı için dışa açılır.
  detectColumns,
  parseBlockLayout,
  parseTableLayout,
  weekdayOf,
  parseDate,
  splitDishes,
  normalize,
};
