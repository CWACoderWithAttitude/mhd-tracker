import { describe, it, expect } from 'vitest'
import {
  cleanBarcode,
  isValidEanChecksum,
  getOptimalQrboxDimensions,
  calculateDownscaleDimensions,
} from './barcodeHelper'

describe('barcodeHelper', () => {
  describe('cleanBarcode', () => {
    it('trims whitespace and removes invalid characters', () => {
      expect(cleanBarcode('  3017620422003 \n')).toBe('3017620422003')
      expect(cleanBarcode('400-8400-404127')).toBe('4008400404127')
    })
  })

  describe('isValidEanChecksum', () => {
    it('validates correct EAN-13 check digit', () => {
      // Nutella EAN-13: 3017620422003 (valid)
      expect(isValidEanChecksum('3017620422003')).toBe(true)
      // Milk EAN-13: 4008400404127 (valid)
      expect(isValidEanChecksum('4008400404127')).toBe(true)
    })

    it('validates correct EAN-8 check digit', () => {
      // Sample EAN-8: 96385074 (valid)
      expect(isValidEanChecksum('96385074')).toBe(true)
    })

    it('rejects invalid checksum', () => {
      // 3017620422009 has invalid check digit (expected 3)
      expect(isValidEanChecksum('3017620422009')).toBe(false)
    })
  })

  describe('getOptimalQrboxDimensions', () => {
    it('calculates responsive dimensions for mobile viewport', () => {
      const box = getOptimalQrboxDimensions(360, 640)
      expect(box.width).toBeGreaterThanOrEqual(250)
      expect(box.width).toBeLessThanOrEqual(360)
      expect(box.height).toBeGreaterThanOrEqual(140)
      expect(box.height).toBeLessThanOrEqual(240)
    })
  })

  describe('calculateDownscaleDimensions', () => {
    it('downscales large phone images to max 1600px while maintaining aspect ratio', () => {
      // 4000x3000 photo (4:3)
      const res = calculateDownscaleDimensions(4000, 3000, 1600)
      expect(res.width).toBe(1600)
      expect(res.height).toBe(1200)
    })

    it('does not upscale smaller images', () => {
      const res = calculateDownscaleDimensions(800, 600, 1600)
      expect(res.width).toBe(800)
      expect(res.height).toBe(600)
    })
  })
})
