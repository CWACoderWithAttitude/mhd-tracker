// Helper functions for parsing expiration dates from OCR text with heuristic error recovery

const MONTH_NAMES = {
  // German
  jan: 1,
  janar: 1,
  januar: 1,
  feb: 2,
  febr: 2,
  februar: 2,
  mrz: 3,
  mär: 3,
  märz: 3,
  maerz: 3,
  mar: 3,
  march: 3,
  apr: 4,
  april: 4,
  avr: 4, // French avril
  mai: 5,
  may: 5,
  jun: 6,
  juni: 6,
  june: 6,
  juin: 6, // French juin
  jul: 7,
  juli: 7,
  july: 7,
  juil: 7, // French juillet
  aug: 8,
  august: 8,
  aout: 8, // French août
  ago: 8, // Spanish/Italian agosto
  sep: 9,
  sept: 9,
  september: 9,
  set: 9,
  okt: 10,
  oct: 10,
  oktober: 10,
  october: 10,
  ott: 10, // Italian ottobre
  nov: 11,
  november: 11,
  dez: 12,
  dec: 12,
  dezember: 12,
  december: 12,
  dic: 12, // Spanish/Italian diciembre
};

function padZero(num) {
  return String(num).padStart(2, "0");
}

function normalizeYear(yearStr) {
  let yr = parseInt(yearStr, 10);
  if (yr < 100) {
    // 2-digit year: assume 2000s
    yr = 2000 + yr;
  }
  return yr;
}

function getLastDayOfMonth(year, month) {
  // day 0 of month+1 gives last day of month
  return new Date(year, month, 0).getDate();
}

/**
 * Replace OCR visual confusion characters in numeric segments.
 */
function fixOcrNumericSubstitutions(str) {
  return str
    .replace(/[OoDQ]/g, "0")
    .replace(/[Il|!]/g, "1")
    .replace(/[Zz]/g, "2")
    .replace(/[$Ss]/g, "5")
    .replace(/[B]/g, "8");
}

function isValidDate(year, month, day) {
  const currentYear = new Date().getFullYear();
  if (year < currentYear - 3 || year > currentYear + 15) return false;
  if (month < 1 || month > 12) return false;
  const maxDay = getLastDayOfMonth(year, month);
  if (day < 1 || day > maxDay) return false;
  return true;
}

export function parseExpirationDate(text) {
  if (!text) return null;

  // Clean newlines and excess whitespace
  let clean = text.replace(/[\n\r]+/g, " ").trim();

  // 1. Check ISO format: YYYY-MM-DD or YYYY.MM.DD
  const isoMatch = clean.match(
    /\b(20\d{2})[\s]*[-./][\s]*(\d{1,2})[\s]*[-./][\s]*(\d{1,2})\b/,
  );
  if (isoMatch) {
    const y = parseInt(isoMatch[1], 10);
    const m = parseInt(isoMatch[2], 10);
    const d = parseInt(isoMatch[3], 10);
    if (isValidDate(y, m, d)) {
      return `${y}-${padZero(m)}-${padZero(d)}`;
    }
  }

  // 2. Check European standard: DD.MM.YYYY, DD.MM.YY (with dots, colons, slashes, dashes)
  // Supports spaces around separators and dot-matrix colons: "15 . 08 . 26", "15:08:26"
  // Also supports common OCR character confusion (e.g. 15.O8.26, I5.08.26)
  const euroRegex =
    /(?:^|[^\d/.-])([0-9OoIl|!ZzSsBb]{1,2})\s*[-./:]\s*([0-9OoIl|!ZzSsBb]{1,2})\s*[-./:]\s*([0-9OoIl|!ZzSsBb]{2,4})(?=[^\d/.-]|$)/;
  const euroMatch = clean.match(euroRegex);
  if (euroMatch) {
    const dRaw = fixOcrNumericSubstitutions(euroMatch[1]);
    const mRaw = fixOcrNumericSubstitutions(euroMatch[2]);
    const yRaw = fixOcrNumericSubstitutions(euroMatch[3]);

    const d = parseInt(dRaw, 10);
    const m = parseInt(mRaw, 10);
    const y = normalizeYear(yRaw);

    if (isValidDate(y, m, d)) {
      return `${y}-${padZero(m)}-${padZero(d)}`;
    }
  }

  // 3. Space-separated European date: DD MM YYYY or DD MM YY (very common on dairy / egg cartons)
  // Must avoid matching arbitrary number sequences like 9876543210
  const spaceSeparatedRegex =
    /(?:^|[^\d])(\d{1,2})\s+(\d{1,2})\s+((?:20)?\d{2})(?=[^\d]|$)/;
  const spaceMatch = clean.match(spaceSeparatedRegex);
  if (spaceMatch) {
    const d = parseInt(spaceMatch[1], 10);
    const m = parseInt(spaceMatch[2], 10);
    const y = normalizeYear(spaceMatch[3]);
    if (isValidDate(y, m, d)) {
      return `${y}-${padZero(m)}-${padZero(d)}`;
    }
  }

  // 4. Text Month: e.g. "15 MRZ 2026", "15. DEZ. 25", "15-AUG-26", "15 AVR 2026"
  const textMonthRegex =
    /(?:^|[^\d])(\d{1,2})[.\s-]+([A-Za-zäÄöÖüÜ]{3,9})[.\s-]+((?:20)?\d{2})(?=[^\d]|$)/;
  const textMonthMatch = clean.match(textMonthRegex);
  if (textMonthMatch) {
    const d = parseInt(textMonthMatch[1], 10);
    const monthRaw = textMonthMatch[2].toLowerCase();
    const monthKey = monthRaw.slice(0, 3);
    const y = normalizeYear(textMonthMatch[3]);
    const m = MONTH_NAMES[monthRaw] || MONTH_NAMES[monthKey];
    if (m && isValidDate(y, m, d)) {
      return `${y}-${padZero(m)}-${padZero(d)}`;
    }
  }

  // 5. Compact 6-digit or 8-digit date immediately after packaging keyword:
  // e.g. "MHD 150826", "EXP: 150826", "BB 15082026"
  const keywordCompactRegex =
    /(?:MHD|EXP|BBE|BB|BEST\s*BEFORE|MINDESTENS\s*HALTBAR\s*BIS)[\s.:]*([0-9OoIl|!]{6,8})(?=[^\d]|$)/i;
  const keywordMatch = clean.match(keywordCompactRegex);
  if (keywordMatch) {
    const digits = fixOcrNumericSubstitutions(keywordMatch[1]);
    let d, m, y;
    if (digits.length === 6) {
      d = parseInt(digits.slice(0, 2), 10);
      m = parseInt(digits.slice(2, 4), 10);
      y = normalizeYear(digits.slice(4, 6));
    } else if (digits.length === 8) {
      d = parseInt(digits.slice(0, 2), 10);
      m = parseInt(digits.slice(2, 4), 10);
      y = parseInt(digits.slice(4, 8), 10);
    }
    if (d && m && y && isValidDate(y, m, d)) {
      return `${y}-${padZero(m)}-${padZero(d)}`;
    }
  }

  // 6. Check Month/Year only: MM/YYYY or MM.YYYY or MM/YY (common for canned / dry goods)
  // Ensure it's not preceded or followed by another separator + number (which would mean a broken full date)
  const monthYearRegex =
    /(?:^|[^\d/.:-])(0?[1-9]|1[0-2])\s*[-./]\s*((?:20)?\d{2})(?=[^\d/.:-]|$)/;
  const monthYearMatch = clean.match(monthYearRegex);
  if (monthYearMatch) {
    const m = parseInt(monthYearMatch[1], 10);
    const y = normalizeYear(monthYearMatch[2]);
    const currentYear = new Date().getFullYear();
    if (y >= currentYear - 3 && y <= currentYear + 15 && m >= 1 && m <= 12) {
      const lastDay = getLastDayOfMonth(y, m);
      return `${y}-${padZero(m)}-${padZero(lastDay)}`;
    }
  }

  return null;
}

export function playBeepSound() {
  try {
    const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.type = "sine";
    osc.frequency.setValueAtTime(880, audioCtx.currentTime); // A5 note
    gain.gain.setValueAtTime(0.15, audioCtx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.15);
    osc.connect(gain);
    gain.connect(audioCtx.destination);
    osc.start();
    osc.stop(audioCtx.currentTime + 0.15);
  } catch {
    // Ignore audio context errors if not allowed yet
  }
}
