<template>
  <div class="fixed inset-0 z-50 bg-black/95 flex flex-col justify-between backdrop-blur-md">
    <!-- Header -->
    <div class="flex items-center justify-between p-4 bg-slate-900/80 border-b border-slate-800 text-white z-10">
      <div class="flex items-center gap-2">
        <Calendar class="w-6 h-6 text-sky-400" />
        <div>
          <h3 class="font-semibold text-lg leading-tight">Scan MHD / Expiration Date</h3>
          <p class="text-xs text-slate-400">OCR recognition for packaging date</p>
        </div>
      </div>
      <button
        @click="closeModal"
        class="p-2 rounded-full bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition"
      >
        <X class="w-6 h-6" />
      </button>
    </div>

    <!-- Scanner Viewport Area -->
    <div class="relative flex-1 flex flex-col items-center justify-center overflow-hidden">
      <!-- Live Video element -->
      <video
        ref="videoEl"
        autoplay
        playsinline
        muted
        class="w-full h-full object-cover"
      ></video>

      <!-- Reticle Box for Date Crop -->
      <div class="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
        <div
          ref="reticleEl"
          class="w-72 h-28 border-2 border-sky-400/90 rounded-xl relative shadow-[0_0_0_9999px_rgba(0,0,0,0.65)] flex items-center justify-center"
        >
          <!-- Corner brackets -->
          <div class="absolute -top-1 -left-1 w-4 h-4 border-t-2 border-l-2 border-sky-300"></div>
          <div class="absolute -top-1 -right-1 w-4 h-4 border-t-2 border-r-2 border-sky-300"></div>
          <div class="absolute -bottom-1 -left-1 w-4 h-4 border-b-2 border-l-2 border-sky-300"></div>
          <div class="absolute -bottom-1 -right-1 w-4 h-4 border-b-2 border-r-2 border-sky-300"></div>

          <div v-if="isProcessing" class="flex items-center gap-2 bg-black/70 px-3 py-1.5 rounded-full text-xs text-sky-200">
            <Loader2 class="w-3.5 h-3.5 animate-spin text-sky-400" />
            <span>Reading date...</span>
          </div>
          <div v-else class="text-center text-xs text-sky-200/90 font-medium px-2">
            Center date stamp here
          </div>
        </div>

        <p class="mt-4 text-xs text-slate-300 text-center max-w-xs px-4">
          e.g. <span class="text-sky-300 font-mono">15.08.2025</span>, <span class="text-sky-300 font-mono">24/11/26</span> or <span class="text-sky-300 font-mono">09/2026</span>
        </p>
      </div>

      <!-- Live OCR Result Preview Toast -->
      <div
        v-if="detectedDate"
        class="absolute bottom-6 inset-x-4 bg-emerald-950/95 border border-emerald-500 rounded-xl p-3 shadow-2xl z-20 flex items-center justify-between animate-bounce"
      >
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-lg bg-emerald-600/30 text-emerald-400 flex items-center justify-center font-bold text-lg">
            ✓
          </div>
          <div>
            <div class="text-xs text-emerald-300 font-semibold uppercase tracking-wider">Date Detected</div>
            <div class="text-lg font-bold text-white font-mono">{{ detectedDate }}</div>
          </div>
        </div>

        <button
          @click="confirmDate(detectedDate)"
          class="px-4 py-2 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-sm rounded-lg shadow transition"
        >
          Use Date
        </button>
      </div>

      <!-- Raw text debug preview (collapsible) -->
      <div
        v-if="rawOcrText && !detectedDate"
        class="absolute top-4 inset-x-4 bg-slate-950/80 border border-slate-700 rounded-lg p-2 text-xs text-slate-300 font-mono truncate text-center z-10"
      >
        OCR reading: "{{ rawOcrText }}"
      </div>

      <!-- Camera error -->
      <div v-if="cameraError" class="absolute inset-0 bg-slate-950/95 flex flex-col items-center justify-center p-6 text-center z-20">
        <AlertCircle class="w-12 h-12 text-rose-500 mb-3" />
        <h4 class="text-white font-medium text-lg mb-1">Camera Issue</h4>
        <p class="text-slate-400 text-sm max-w-xs mb-4">{{ cameraError }}</p>
        <button
          @click="startCamera"
          class="px-4 py-2 bg-sky-600 hover:bg-sky-500 text-white rounded-lg font-medium text-sm transition"
        >
          Try Again
        </button>
      </div>
    </div>

    <!-- Hidden canvas for image capture and cropping -->
    <canvas ref="canvasEl" class="hidden"></canvas>

    <!-- Bottom Controls -->
    <div class="p-4 bg-slate-900/90 border-t border-slate-800 flex flex-col gap-3 z-10 max-w-md mx-auto w-full">
      <div class="flex items-center gap-3">
        <!-- Manual Capture Button -->
        <button
          @click="captureAndOcr"
          :disabled="isProcessing"
          class="flex-1 py-3 px-4 bg-sky-600 hover:bg-sky-500 active:scale-95 disabled:opacity-50 text-white font-semibold rounded-xl flex items-center justify-center gap-2 shadow-lg transition"
        >
          <Camera class="w-5 h-5" />
          <span>{{ isProcessing ? 'Scanning...' : 'Capture & Scan Date' }}</span>
        </button>

        <!-- Upload from gallery / file -->
        <label class="p-3 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl cursor-pointer transition">
          <UploadCloud class="w-5 h-5" />
          <input type="file" accept="image/*" class="hidden" @change="onFileSelected" />
        </label>
      </div>

      <!-- Manual Date Picker Fallback -->
      <div class="flex items-center gap-2 pt-1 border-t border-slate-800/60">
        <span class="text-xs text-slate-400 whitespace-nowrap">Or pick date:</span>
        <input
          v-model="manualInputDate"
          type="date"
          class="flex-1 bg-slate-950 border border-slate-700 rounded-lg px-2.5 py-1.5 text-sm text-white focus:outline-none focus:border-sky-500"
        />
        <button
          @click="confirmDate(manualInputDate)"
          :disabled="!manualInputDate"
          class="px-3 py-1.5 bg-sky-600 hover:bg-sky-500 disabled:opacity-50 text-white rounded-lg text-xs font-semibold transition"
        >
          OK
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { createWorker } from 'tesseract.js'
import { Calendar, X, Camera, AlertCircle, UploadCloud, Loader2 } from 'lucide-vue-next'
import { parseExpirationDate, playBeepSound } from '../utils/dateParser'

const emit = defineEmits(['detected', 'close'])

const videoEl = ref(null)
const canvasEl = ref(null)
const reticleEl = ref(null)

const isProcessing = ref(false)
const cameraError = ref(null)
const detectedDate = ref(null)
const rawOcrText = ref('')
const manualInputDate = ref('')

let stream = null
let tesseractWorker = null
let autoScanInterval = null

onMounted(async () => {
  await startCamera()
  await initWorker()
  // Start gentle auto-scan every 2.5 seconds
  autoScanInterval = setInterval(() => {
    if (!isProcessing.value && !detectedDate.value) {
      captureAndOcr()
    }
  }, 2500)
})

onUnmounted(async () => {
  if (autoScanInterval) clearInterval(autoScanInterval)
  stopCamera()
  if (tesseractWorker) {
    try {
      await tesseractWorker.terminate()
    } catch (e) {
      console.warn('Worker terminate error:', e)
    }
  }
})

async function initWorker() {
  try {
    tesseractWorker = await createWorker('deu+eng', 1, {
      logger: (m) => {},
    })
    // Whitelist digits and common date separators/letters
    await tesseractWorker.setParameters({
      tessedit_char_whitelist: '0123456789./- :MHDBEXPBbestbeforeMhdExpJanFebMarAprMaiJunJulAugSepOktNovDez',
    })
  } catch (err) {
    console.error('Failed to init Tesseract worker:', err)
  }
}

async function startCamera() {
  cameraError.value = null
  try {
    const constraints = {
      video: {
        facingMode: { ideal: 'environment' },
        width: { ideal: 1280 },
        height: { ideal: 720 },
      },
    }
    stream = await navigator.mediaDevices.getUserMedia(constraints)
    if (videoEl.value) {
      videoEl.value.srcObject = stream
    }
  } catch (err) {
    console.error('Camera stream error:', err)
    cameraError.value = 'Could not access camera. Please allow camera permissions or upload an image.'
  }
}

function stopCamera() {
  if (stream) {
    stream.getTracks().forEach((track) => track.stop())
    stream = null
  }
}

async function captureAndOcr() {
  if (!videoEl.value || !tesseractWorker || isProcessing.value) return
  if (videoEl.value.videoWidth === 0) return

  isProcessing.value = true
  try {
    const video = videoEl.value
    const canvas = canvasEl.value
    const ctx = canvas.getContext('2d', { willReadFrequently: true })

    // Calculate crop coordinates based on center reticle
    const vw = video.videoWidth
    const vh = video.videoHeight

    // Reticle is roughly 65% width and 25% height in center
    const cropW = Math.floor(vw * 0.65)
    const cropH = Math.floor(vh * 0.28)
    const cropX = Math.floor((vw - cropW) / 2)
    const cropY = Math.floor((vh - cropH) / 2)

    canvas.width = cropW
    canvas.height = cropH

    // Draw cropped region
    ctx.drawImage(video, cropX, cropY, cropW, cropH, 0, 0, cropW, cropH)

    // Image preprocessing: Grayscale + high contrast to enhance laser dot matrix prints
    const imgData = ctx.getImageData(0, 0, cropW, cropH)
    const data = imgData.data
    for (let i = 0; i < data.length; i += 4) {
      const avg = (data[i] * 0.299 + data[i + 1] * 0.587 + data[i + 2] * 0.114)
      // High contrast curve
      const adjusted = avg > 120 ? 255 : (avg < 80 ? 0 : avg)
      data[i] = adjusted
      data[i + 1] = adjusted
      data[i + 2] = adjusted
    }
    ctx.putImageData(imgData, 0, 0)

    // Run Tesseract
    const { data: result } = await tesseractWorker.recognize(canvas)
    const text = result.text.trim()
    rawOcrText.value = text

    const parsed = parseExpirationDate(text)
    if (parsed) {
      detectedDate.value = parsed
      playBeepSound()
    }
  } catch (err) {
    console.error('OCR processing error:', err)
  } finally {
    isProcessing.value = false
  }
}

async function onFileSelected(e) {
  const file = e.target.files?.[0]
  if (!file) return

  isProcessing.value = true
  try {
    if (!tesseractWorker) await initWorker()
    const { data: result } = await tesseractWorker.recognize(file)
    const parsed = parseExpirationDate(result.text)
    if (parsed) {
      detectedDate.value = parsed
      playBeepSound()
    } else {
      alert(`Could not extract expiration date from image. Text found: "${result.text.slice(0, 80)}"`)
    }
  } catch (err) {
    alert('Error reading image file for OCR.')
  } finally {
    isProcessing.value = false
  }
}

function confirmDate(dateStr) {
  if (dateStr) {
    playBeepSound()
    stopCamera()
    emit('detected', dateStr)
  }
}

function closeModal() {
  stopCamera()
  emit('close')
}
</script>
