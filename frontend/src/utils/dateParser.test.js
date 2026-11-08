import { describe, it, expect } from "vitest";
import { parseExpirationDate } from "./dateParser";

describe("dateParser", () => {
  describe("Standard European Formats", () => {
    it("parses standard DD.MM.YYYY and DD.MM.YY", () => {
      expect(parseExpirationDate("15.08.2026")).toBe("2026-08-15");
      expect(parseExpirationDate("15.08.26")).toBe("2026-08-15");
      expect(parseExpirationDate("01.01.27")).toBe("2027-01-01");
      expect(parseExpirationDate("31.12.2025")).toBe("2025-12-31");
    });

    it("parses slash and dash separated dates", () => {
      expect(parseExpirationDate("15/08/2026")).toBe("2026-08-15");
      expect(parseExpirationDate("15/08/26")).toBe("2026-08-15");
      expect(parseExpirationDate("15-08-2026")).toBe("2026-08-15");
      expect(parseExpirationDate("15-08-26")).toBe("2026-08-15");
    });

    it("parses space-separated dates (common on dairy and egg cartons)", () => {
      expect(parseExpirationDate("15 08 2026")).toBe("2026-08-15");
      expect(parseExpirationDate("24 11 26")).toBe("2026-11-24");
      expect(parseExpirationDate("05 06 27")).toBe("2027-06-05");
    });
  });

  describe("OCR Noise and Punctuation Tolerance", () => {
    it("tolerates spaces around dots and slashes", () => {
      expect(parseExpirationDate("15 . 08 . 2026")).toBe("2026-08-15");
      expect(parseExpirationDate("15 . 08 . 26")).toBe("2026-08-15");
      expect(parseExpirationDate("15 / 08 / 26")).toBe("2026-08-15");
    });

    it("handles colons commonly misread from dot-matrix dots", () => {
      expect(parseExpirationDate("15:08:2026")).toBe("2026-08-15");
      expect(parseExpirationDate("15:08:26")).toBe("2026-08-15");
      expect(parseExpirationDate("15 : 08 : 26")).toBe("2026-08-15");
    });

    it("recovers from common OCR character substitutions (O/0, I/1, l/1)", () => {
      expect(parseExpirationDate("15.O8.2026")).toBe("2026-08-15");
      expect(parseExpirationDate("15.08.2O26")).toBe("2026-08-15");
      expect(parseExpirationDate("I5.08.26")).toBe("2026-08-15");
      expect(parseExpirationDate("l5.08.26")).toBe("2026-08-15");
    });
  });

  describe("Text Months and Multi-Language Support", () => {
    it("parses German text months including MRZ (standard DIN abbreviation)", () => {
      expect(parseExpirationDate("15 MRZ 2026")).toBe("2026-03-15");
      expect(parseExpirationDate("15.MRZ.26")).toBe("2026-03-15");
      expect(parseExpirationDate("15 März 2026")).toBe("2026-03-15");
      expect(parseExpirationDate("15 OKT 2026")).toBe("2026-10-15");
      expect(parseExpirationDate("15 DEZ 2026")).toBe("2026-12-15");
      expect(parseExpirationDate("15 MAI 2026")).toBe("2026-05-15");
    });

    it("parses English and international text months", () => {
      expect(parseExpirationDate("15 AUG 2026")).toBe("2026-08-15");
      expect(parseExpirationDate("15-AUG-26")).toBe("2026-08-15");
      expect(parseExpirationDate("15 SEP 2026")).toBe("2026-09-15");
      expect(parseExpirationDate("15 APR 2026")).toBe("2026-04-15");
      expect(parseExpirationDate("15 AVR 2026")).toBe("2026-04-15"); // French Avril
    });
  });

  describe("Packaging Keywords and Compact Formats", () => {
    it("extracts dates with packaging prefixes like MHD, EXP, BB", () => {
      expect(parseExpirationDate("MHD 15.08.2026")).toBe("2026-08-15");
      expect(parseExpirationDate("EXP: 15/08/26")).toBe("2026-08-15");
      expect(parseExpirationDate("BEST BEFORE 15-08-2026")).toBe("2026-08-15");
      expect(parseExpirationDate("BBE 15.08.26 L1234")).toBe("2026-08-15");
      expect(parseExpirationDate("Mindestens haltbar bis: 15.08.2026")).toBe(
        "2026-08-15",
      );
    });

    it("parses compact 6-digit dates following keyword (e.g. MHD 150826)", () => {
      expect(parseExpirationDate("MHD 150826")).toBe("2026-08-15");
      expect(parseExpirationDate("EXP 150826")).toBe("2026-08-15");
      expect(parseExpirationDate("BB: 150826")).toBe("2026-08-15");
    });

    it("parses Month/Year format (common for canned / dry goods)", () => {
      expect(parseExpirationDate("08/2026")).toBe("2026-08-31");
      expect(parseExpirationDate("08/26")).toBe("2026-08-31");
      expect(parseExpirationDate("02/2028")).toBe("2028-02-29"); // Leap year
      expect(parseExpirationDate("MHD 08.2026")).toBe("2026-08-31");
    });

    it("parses ISO format YYYY-MM-DD", () => {
      expect(parseExpirationDate("2026-08-15")).toBe("2026-08-15");
      expect(parseExpirationDate("EXP 2026.08.15")).toBe("2026-08-15");
    });
  });

  describe("Validation and Edge Cases", () => {
    it("rejects invalid dates and pure non-date numbers", () => {
      expect(parseExpirationDate("")).toBeNull();
      expect(parseExpirationDate(null)).toBeNull();
      expect(parseExpirationDate("32.08.2026")).toBeNull(); // Day 32
      expect(parseExpirationDate("15.13.2026")).toBeNull(); // Month 13
      expect(parseExpirationDate("Batch: 9876543210")).toBeNull();
      expect(parseExpirationDate("Ingredients: Water, Sugar, Salt")).toBeNull();
    });
  });
});
