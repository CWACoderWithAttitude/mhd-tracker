/**
 * Computer Vision preprocessing pipeline for OCR recognition of packaging date stamps.
 *
 * Optimizes packaging images for Tesseract:
 * 1. Contrast stretching & normalization (enhances faint ink on plastic/foil)
 * 2. Otsu dynamic binarization (calculates optimal threshold per image)
 * 3. Dot-matrix morphological bridge (connects inkjet printer dots into solid letters)
 * 4. Auto-inversion (ensures white text on dark backgrounds becomes black-on-white)
 * 5. High-resolution bicubic upscaling for small text crops
 */

/**
 * Compute optimal binarization threshold using Otsu's method.
 */
export function computeOtsuThreshold(histogram, totalPixels) {
  let sum = 0;
  for (let i = 0; i < 256; i++) {
    sum += i * histogram[i];
  }

  let sumB = 0;
  let weightB = 0;
  let maximumVariance = 0;
  let optimalThreshold = 128;

  for (let t = 0; t < 256; t++) {
    weightB += histogram[t];
    if (weightB === 0) continue;

    const weightF = totalPixels - weightB;
    if (weightF === 0) break;

    sumB += t * histogram[t];
    const meanB = sumB / weightB;
    const meanF = (sum - sumB) / weightF;

    const varianceBetween =
      weightB * weightF * (meanB - meanF) * (meanB - meanF);

    if (varianceBetween > maximumVariance) {
      maximumVariance = varianceBetween;
      optimalThreshold = t;
    }
  }

  return optimalThreshold;
}

/**
 * Detect if an image has an overall dark background (e.g. white text on black bottle lid).
 */
export function isImageDark(data) {
  let totalLuminance = 0;
  const numPixels = data.length / 4;
  for (let i = 0; i < data.length; i += 4) {
    const lum = data[i] * 0.299 + data[i + 1] * 0.587 + data[i + 2] * 0.114;
    totalLuminance += lum;
  }
  const avgLuminance = totalLuminance / numPixels;
  return avgLuminance < 120;
}

/**
 * Morphological dilation (min-filter for black pixels on white background).
 * Bridges 1-2px gaps between dot-matrix inkjet dots so characters form solid lines.
 */
export function applyDilationToImageData(data, width, height) {
  const output = new Uint8ClampedArray(data);

  // For each pixel (excluding 1px borders)
  for (let y = 1; y < height - 1; y++) {
    for (let x = 1; x < width - 1; x++) {
      const idx = (y * width + x) * 4;

      // If current pixel is already dark (0), keep it
      if (data[idx] === 0) continue;

      // Check 3x3 neighborhood. If any neighbor is black (0), make this pixel black
      let hasBlackNeighbor = false;
      for (let dy = -1; dy <= 1; dy++) {
        for (let dx = -1; dx <= 1; dx++) {
          const neighborIdx = ((y + dy) * width + (x + dx)) * 4;
          if (data[neighborIdx] === 0) {
            hasBlackNeighbor = true;
            break;
          }
        }
        if (hasBlackNeighbor) break;
      }

      if (hasBlackNeighbor) {
        output[idx] = 0;
        output[idx + 1] = 0;
        output[idx + 2] = 0;
      }
    }
  }

  return output;
}

/**
 * Preprocess raw image data for OCR.
 */
export function preprocessImageDataForOcr(data, width, height, options = {}) {
  const {
    contrastStretch = true,
    invert = "auto",
    binarize = true,
    connectDots = true,
  } = options;

  const totalPixels = width * height;
  const grayscale = new Float32Array(totalPixels);

  let minVal = 255;
  let maxVal = 0;

  // 1. Grayscale conversion and min/max detection
  for (let i = 0, p = 0; i < data.length; i += 4, p++) {
    const lum = data[i] * 0.299 + data[i + 1] * 0.587 + data[i + 2] * 0.114;
    grayscale[p] = lum;
    if (lum < minVal) minVal = lum;
    if (lum > maxVal) maxVal = lum;
  }

  // 2. Contrast stretching (normalize dynamic range to [0, 255])
  const range = maxVal - minVal;
  const histogram = new Array(256).fill(0);

  for (let p = 0; p < totalPixels; p++) {
    let normalized = grayscale[p];
    if (contrastStretch && range > 10) {
      normalized = ((normalized - minVal) / range) * 255;
    }
    const val = Math.min(255, Math.max(0, Math.round(normalized)));
    grayscale[p] = val;
    histogram[val]++;
  }

  // 3. Determine inversion (dark background with light text)
  let shouldInvert = false;
  if (invert === true) {
    shouldInvert = true;
  } else if (invert === "auto") {
    // If mean luminance is low, it's light text on dark background
    let sum = 0;
    for (let p = 0; p < totalPixels; p++) sum += grayscale[p];
    shouldInvert = sum / totalPixels < 128;
  }

  if (shouldInvert) {
    for (let p = 0; p < totalPixels; p++) {
      grayscale[p] = 255 - grayscale[p];
    }
    // Recompute histogram after inversion
    histogram.fill(0);
    for (let p = 0; p < totalPixels; p++) {
      histogram[Math.round(grayscale[p])]++;
    }
  }

  // 4. Binarization via Otsu's thresholding
  let threshold = 128;
  if (binarize) {
    threshold = computeOtsuThreshold(histogram, totalPixels);
  }

  const output = new Uint8ClampedArray(data.length);
  for (let p = 0, i = 0; p < totalPixels; p++, i += 4) {
    const val = binarize
      ? grayscale[p] > threshold
        ? 255
        : 0
      : Math.round(grayscale[p]);
    output[i] = val;
    output[i + 1] = val;
    output[i + 2] = val;
    output[i + 3] = 255;
  }

  // 5. Morphological dot-matrix dilation (thickens text dots)
  if (binarize && connectDots) {
    return applyDilationToImageData(output, width, height);
  }

  return output;
}

/**
 * Crop source image/video and upscale onto a canvas with OCR preprocessing applied.
 */
export function prepareOcrCanvas(source, cropRect, scale = 2, options = {}) {
  const canvas = document.createElement("canvas");
  const targetWidth = Math.round(cropRect.width * scale);
  const targetHeight = Math.round(cropRect.height * scale);

  canvas.width = targetWidth;
  canvas.height = targetHeight;

  const ctx = canvas.getContext("2d", { willReadFrequently: true });
  ctx.imageSmoothingEnabled = true;
  ctx.imageSmoothingQuality = "high";

  // Draw scaled crop
  ctx.drawImage(
    source,
    cropRect.x,
    cropRect.y,
    cropRect.width,
    cropRect.height,
    0,
    0,
    targetWidth,
    targetHeight,
  );

  const imgData = ctx.getImageData(0, 0, targetWidth, targetHeight);
  const processedData = preprocessImageDataForOcr(
    imgData.data,
    targetWidth,
    targetHeight,
    options,
  );

  imgData.data.set(processedData);
  ctx.putImageData(imgData, 0, 0);

  return canvas;
}
