'use strict';

const XLSX = require('xlsx');

const HEADER_ALIASES = {
  fullName: ['ad soyad', 'adsoyad', 'çalışan adı', 'personel adı', 'isim soyisim', 'isim', 'ad', 'soyad', 'adı'],
  birthDate: ['doğum tarihi', 'doğumtarihi', 'dogum tarihi', 'dogumtarihi', 'doğum', 'dogum', 'birth', 'birthdate', 'doğum günü'],
  hireDate: ['işe giriş tarihi', 'işegiriş tarihi', 'ise giris tarihi', 'işe başlama tarihi', 'işebaşlama tarihi', 'işe giriş', 'başlangıç tarihi', 'başlangıç', 'hire', 'start date'],
};

function normalize(value) {
  return String(value ?? '').trim().toLocaleLowerCase('tr-TR').replace(/\s+/g, ' ');
}

function findColumn(headers, aliases) {
  // Try exact alias match first
  const normalized = headers.map(normalize);
  for (const alias of aliases) {
    const idx = normalized.findIndex((h) => h === normalize(alias));
    if (idx >= 0) return idx;
  }
  // Otherwise try substring/keyword matching
  for (const alias of aliases) {
    const key = normalize(alias);
    const idx = normalized.findIndex((h) => h.includes(key));
    if (idx >= 0) return idx;
  }
  return -1;
}

function findColumnByKeywords(headers, keywords) {
  const normalized = headers.map(normalize);
  for (const key of keywords) {
    const k = normalize(key);
    const idx = normalized.findIndex((h) => h.includes(k));
    if (idx >= 0) return idx;
  }
  return -1;
}

function parseExcelDate(value) {
  if (!value) return null;
  if (value instanceof Date && !Number.isNaN(value.valueOf())) return value;
  if (typeof value === 'number') {
    const parts = XLSX.SSF.parse_date_code(value);
    return parts ? new Date(parts.y, parts.m - 1, parts.d, 12) : null;
  }
  const text = String(value).trim();
  const tr = text.match(/^(\d{1,2})[./-](\d{1,2})[./-](\d{4})$/);
  if (tr) return new Date(Number(tr[3]), Number(tr[2]) - 1, Number(tr[1]), 12);
  const parsed = new Date(text);
  return Number.isNaN(parsed.valueOf()) ? null : parsed;
}

/** Excel satırlarını değiştirmeden tablo için ham veri + otomasyon alanları döndürür. */
function readEmployees(buffer) {
  const workbook = XLSX.read(buffer, { type: 'buffer', cellDates: true, cellNF: true });
  const sheet = workbook.Sheets[workbook.SheetNames[0]];
  if (!sheet) throw new Error('Excel dosyasında okunabilir bir sayfa yok.');

  const matrix = XLSX.utils.sheet_to_json(sheet, { header: 1, defval: '', raw: true });
  const headers = (matrix[0] || []).map((value) => String(value ?? '').trim());
  const fullNameColumn = findColumn(headers, HEADER_ALIASES.fullName);
  const birthDateColumn = findColumn(headers, HEADER_ALIASES.birthDate);
  const hireDateColumn = findColumn(headers, HEADER_ALIASES.hireDate);

  // Try to detect split name columns (e.g., 'Ad' + 'Soyad') if fullName not found
  let adColumn = -1;
  let soyadColumn = -1;
  if (fullNameColumn < 0) {
    adColumn = findColumnByKeywords(headers, ['ad', 'isim', 'adı']);
    soyadColumn = findColumnByKeywords(headers, ['soyad', 'soyadı', 'soy isim']);
  }

  const rows = matrix.slice(1).filter((row) => row.some((value) => String(value ?? '').trim() !== ''));
  const employees = rows.map((row, index) => {
    let fullName = '';
    if (fullNameColumn >= 0) fullName = String(row[fullNameColumn] ?? '').trim();
    else if (adColumn >= 0 || soyadColumn >= 0) {
      const a = String(row[adColumn] ?? '').trim();
      const s = String(row[soyadColumn] ?? '').trim();
      fullName = [a, s].filter(Boolean).join(' ').trim();
    } else {
      // fallback to first non-empty cell in the row
      const first = row.find((c) => String(c ?? '').trim() !== '');
      fullName = String(first ?? '').trim();
    }

    return {
      rowNumber: index + 2,
      values: headers.map((_, column) => row[column] ?? ''),
      fullName,
      birthDate: parseExcelDate(row[birthDateColumn]),
      hireDate: parseExcelDate(row[hireDateColumn]),
    };
  }).filter((employee) => employee.fullName);

  const missing = [];
  if (fullNameColumn < 0 && adColumn < 0 && soyadColumn < 0) missing.push('Ad Soyad');
  if (birthDateColumn < 0) missing.push('Doğum Tarihi');
  if (hireDateColumn < 0) missing.push('İşe Giriş Tarihi');

  return { headers, employees, missing };
}

module.exports = { readEmployees };
