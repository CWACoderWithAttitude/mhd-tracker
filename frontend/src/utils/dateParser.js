// Helper functions for parsing expiration dates from OCR text

const MONTH_NAMES = {
  jan: 1,
  janar: 1,
  januar: 1,
  january: 1,
  feb: 2,
  febr: 2,
  februar: 2,
  february: 2,
  mär: 3,
  mar: 3,
  märz: 3,
  maerz: 3,
  march: 3,
  apr: 4,
  april: 4,
  mai: 5,
  may: 5,
  jun: 6,
  juni: 6,
  june: 6,
  jul: 7,
  juli: 7,
  july: 7,
  aug: 8,
  august: 8,
  sep: 9,
  sept: 9,
  september: 9,
  okt: 10,
  oct: 10,
  oktober: 10,
  october: 10,
  nov: 11,
  november: 11,
  dez: 12,
  dec: 12,
  dezember: 12,
  december: 12,
};

function padZero(num) {
  return String(num).padStart(2, "0");
}

function normalizeYear(yearStr) {
  let yr = parseInt(yearStr, 10);
  if (yr < 100) {
    // 2-digit year: 20s or 30s
    yr = 2000 + yr;
  }
  return yr;
}

function getLastDayOfMonth(year, month) {
  // day 0 of month+1 gives last day of month
  return new Date(year, month, 0).getDate();
}

export function parseExpirationDate(text) {
  if (!text) return null;

  // Clean up noisy text (remove random OCR punctuation except dots, slashes, dashes, colons)
  const clean = text.replace(/[\n\r]+/g, " ").trim();

  // 1. Check ISO format: YYYY-MM-DD or YYYY.MM.DD
  const isoMatch = clean.match(/\b(20\d{2})[-./](\d{1,2})[-./](\d{1,2})\b/);
  if (isoMatch) {
    const y = parseInt(isoMatch[1], 10);
    const m = parseInt(isoMatch[2], 10);
    const d = parseInt(isoMatch[3], 10);
    if (m >= 1 && m <= 12 && d >= 1 && d <= 31) {
      return `${y}-${padZero(m)}-${padZero(d)}`;
    }
  }

  // 2. Check European standard: DD.MM.YYYY or DD.MM.YY (or with / or -)
  const euroFullMatch = clean.match(
    /\b(\d{1,2})[-./](\d{1,2})[-./]((?:20)?\d{2})\b/,
  );
  if (euroFullMatch) {
    const d = parseInt(euroFullMatch[1], 10);
    const m = parseInt(euroFullMatch[2], 10);
    const y = normalizeYear(euroFullMatch[3]);
    if (m >= 1 && m <= 12 && d >= 1 && d <= 31 && y >= 2024 && y <= 2045) {
      return `${y}-${padZero(m)}-${padZero(d)}`;
    }
  }

  // 3. Check with Text Month (e.g. "15 MAI 2025" or "15. DEZ. 25")
  const textMonthRegex =
    /\b(\d{1,2})[.\s-]+([A-Za-zäÄöÖüÜ]{3,9})[.\s-]+((?:20)?\d{2})\b/;
  const textMonthMatch = clean.match(textMonthRegex);
  if (textMonthMatch) {
    const d = parseInt(textMonthMatch[1], 10);
    const monthKey = textMonthMatch[2].toLowerCase().slice(0, 3);
    const y = normalizeYear(textMonthMatch[3]);
    const m = MONTH_NAMES[monthKey];
    if (m && d >= 1 && d <= 31 && y >= 2024 && y <= 2045) {
      return `${y}-${padZero(m)}-${padZero(d)}`;
    }
  }

  // 4. Check Month/Year only: MM/YYYY or MM.YYYY or MM/YY (common for canned goods, dry goods)
  // Look for keywords nearby like MHD, EXP, BB, BEST
  const monthYearMatch = clean.match(/\b(0?[1-9]|1[0-2])[-./]((?:20)?\d{2})\b/);
  if (monthYearMatch) {
    const m = parseInt(monthYearMatch[1], 10);
    const y = normalizeYear(monthYearMatch[2]);
    if (y >= 2024 && y <= 2045) {
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
  } catch (e) {
    // Ignore audio context errors if not allowed yet
  }
}
