/**
 * Utility helpers for barcode cleaning, checksum validation,
 * responsive viewfinder sizing, and photo pre-processing.
 */

export function cleanBarcode(rawText) {
  if (!rawText) return ''
  // Strip whitespace and dashes/dots commonly found in barcodes
  return rawText.trim().replace(/[-\s.]/g, '')
}

/**
 * Standard GS1 Modulo-10 Checksum Algorithm for EAN-13, EAN-8, and UPC-A.
 */
export function isValidEanChecksum(barcode) {
  const clean = cleanBarcode(barcode)
  if (!/^\d+$/.test(clean)) return false
  if (clean.length !== 8 && clean.length !== 12 && clean.length !== 13) {
    // If not standard length, cannot verify checksum
    return true
  }

  const digits = clean.split('').map(Number)
  const checkDigit = digits.pop()

  // Weight alternate 3 and 1 from right to left
  let sum = 0
  for (let i = digits.length - 1, weight = 3; i >= 0; i--, weight = weight === 3 ? 1 : 3) {
    sum += digits[i] * weight
  }

  const calculatedCheckDigit = (10 - (sum % 10)) % 10
  return calculatedCheckDigit === checkDigit
}

/**
 * Responsive calculation for the scanner reticle box.
 * Adapts to mobile portrait and landscape viewports.
 */
export function getOptimalQrboxDimensions(viewfinderWidth, viewfinderHeight) {
  const width = Math.min(Math.floor(viewfinderWidth * 0.85), 360)
  const height = Math.min(Math.floor(viewfinderHeight * 0.55), 220)
  return {
    width: Math.max(width, 240),
    height: Math.max(height, 140),
  }
}

/**
 * Calculate proportional dimensions ensuring neither width nor height exceeds maxDimension.
 */
export function calculateDownscaleDimensions(origWidth, origHeight, maxDimension = 1600) {
  if (origWidth <= maxDimension && origHeight <= maxDimension) {
    return { width: origWidth, height: origHeight }
  }

  if (origWidth >= origHeight) {
    const ratio = origHeight / origWidth
    return {
      width: maxDimension,
      height: Math.round(maxDimension * ratio),
    }
  } else {
    const ratio = origWidth / origHeight
    return {
      width: Math.round(maxDimension * ratio),
      height: maxDimension,
    }
  }
}

/**
 * Downscale and optimize an image File for barcode recognition.
 * Avoids memory overflows and extreme line-width issues in ZXing when users
 * upload 12MP-48MP smartphone photos.
 */
export async function optimizeImageForBarcode(file, maxDimension = 1600) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onerror = () => reject(new Error('Failed to read image file'))
    reader.onload = (e) => {
      const img = new Image()
      img.onerror = () => reject(new Error('Failed to load image'))
      img.onload = () => {
        const { width, height } = calculateDownscaleDimensions(img.width, img.height, maxDimension)

        const canvas = document.createElement('canvas')
        canvas.width = width
        canvas.height = height

        const ctx = canvas.getContext('2d')
        // High quality bicubic scaling
        ctx.imageSmoothingEnabled = true
        ctx.imageSmoothingQuality = 'high'
        ctx.drawImage(img, 0, 0, width, height)

        canvas.toBlob(
          (blob) => {
            if (blob) {
              const optimizedFile = new File([blob], file.name || 'scanned.jpg', {
                type: 'image/jpeg',
                lastModified: Date.now(),
              })
              resolve(optimizedFile)
            } else {
              resolve(file)
            }
          },
          'image/jpeg',
          0.92
        )
      }
      img.src = e.target.result
    }
    reader.readAsDataURL(file)
  })
}
