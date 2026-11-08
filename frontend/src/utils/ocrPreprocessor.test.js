import { describe, it, expect } from "vitest";
import {
  computeOtsuThreshold,
  isImageDark,
  preprocessImageDataForOcr,
  applyDilationToImageData,
} from "./ocrPreprocessor";

describe("ocrPreprocessor", () => {
  describe("computeOtsuThreshold", () => {
    it("computes reasonable threshold for bimodal histogram", () => {
      // 256-bucket histogram with peaks at 50 (dark background) and 200 (light text)
      const hist = new Array(256).fill(0);
      for (let i = 40; i <= 60; i++) hist[i] = 100;
      for (let i = 190; i <= 210; i++) hist[i] = 100;
      const threshold = computeOtsuThreshold(hist, 4200);
      expect(threshold).toBeGreaterThanOrEqual(60);
      expect(threshold).toBeLessThan(190);
    });
  });

  describe("isImageDark", () => {
    it("detects dark background requiring inversion", () => {
      // 10x10 black image with a few white pixels (dark background)
      const data = new Uint8ClampedArray(10 * 10 * 4);
      for (let i = 0; i < data.length; i += 4) {
        data[i] = 30; // R
        data[i + 1] = 30; // G
        data[i + 2] = 30; // B
        data[i + 3] = 255;
      }
      expect(isImageDark(data)).toBe(true);
    });

    it("detects light background", () => {
      const data = new Uint8ClampedArray(10 * 10 * 4);
      for (let i = 0; i < data.length; i += 4) {
        data[i] = 220;
        data[i + 1] = 220;
        data[i + 2] = 220;
        data[i + 3] = 255;
      }
      expect(isImageDark(data)).toBe(false);
    });
  });

  describe("applyDilationToImageData (Dot Matrix Bridge)", () => {
    it("dilates dark text pixels into adjacent pixels to connect dots", () => {
      // 5x5 image, white (255) with single black pixel (0) at center (2,2)
      const width = 5;
      const height = 5;
      const data = new Uint8ClampedArray(width * height * 4).fill(255);

      // Set center pixel (x=2, y=2) to black (0)
      const centerIdx = (2 * width + 2) * 4;
      data[centerIdx] = 0;
      data[centerIdx + 1] = 0;
      data[centerIdx + 2] = 0;

      const dilated = applyDilationToImageData(data, width, height);

      // In 3x3 neighborhood around center, neighbor pixels should now be black (0)
      const rightNeighborIdx = (2 * width + 3) * 4;
      expect(dilated[rightNeighborIdx]).toBe(0);
    });
  });

  describe("preprocessImageDataForOcr", () => {
    it("converts color image to normalized high-contrast grayscale with dark text on white", () => {
      const width = 4;
      const height = 4;
      const data = new Uint8ClampedArray(width * height * 4);
      // Dark text on white background
      for (let i = 0; i < data.length; i += 4) {
        data[i] = 240;
        data[i + 1] = 240;
        data[i + 2] = 240;
        data[i + 3] = 255;
      }
      // Put a dark pixel at (1,1)
      const textIdx = (1 * width + 1) * 4;
      data[textIdx] = 20;
      data[textIdx + 1] = 20;
      data[textIdx + 2] = 20;

      const result = preprocessImageDataForOcr(data, width, height, {
        contrastStretch: true,
        binarize: true,
        connectDots: false,
      });

      // Background should be pure white (255)
      expect(result[0]).toBe(255);
      // Text pixel should be pure black (0)
      expect(result[textIdx]).toBe(0);
    });
  });
});
