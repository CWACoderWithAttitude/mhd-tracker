<template>
  <div class="fixed inset-0 z-50 bg-black/95 flex flex-col justify-between backdrop-blur-md">
    <!-- Header -->
    <div class="flex items-center justify-between p-4 bg-slate-900/90 border-b border-slate-800 text-white z-10">
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
    <div class="relative flex-1 flex flex-col items-center justify-center overflow-hidden bg-black">
      <!-- Live Video element -->
      <video
        v-if="isScanningLive"
        ref="videoEl"
        autoplay
        playsinline
        muted
        class="w-full h-full object-cover"
      ></video>

      <!-- Reticle Box for Date Crop (shown during live scanning) -->
      <div v-if="isScanningLive" class="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
        <div
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

      <!-- Insecure Context / Camera Access Fallback UI -->
      <div v-if="cameraError" class="absolute inset-0 bg-slate-950/95 flex flex-col items-center justify-center p-6 text-center z-20">
        <div class="w-16 h-16 rounded-2xl bg-sky-500/10 border border-sky-500/30 flex items-center justify-center text-sky-400 mb-3">
          <Calendar class="w-8 h-8" />
        </div>

        <h4 class="text-white font-bold text-lg mb-1">
          {{ isHttpNonLocal ? 'Live Camera Requires HTTPS' : 'Camera Access Issue' }}
        </h4>

        <p class="text-slate-300 text-xs max-w-sm mb-4 leading-relaxed">
          <span v-if="isHttpNonLocal">
            Mobile browsers disable live video over HTTP.
            <br /><br />
            <strong>You can take a photo of the date stamp directly using your phone's camera!</strong>
          </span>
          <span v-else>
            {{ cameraError }}
          </span>
        </p>

        <!-- Native Camera Snap Button -->
        <button
          @click="openNativeCamera"
          class="w-full max-w-xs py-3.5 px-6 bg-sky-600 hover:bg-sky-500 active:scale-95 text-white font-bold text-sm rounded-xl shadow-lg shadow-sky-950/50 flex items-center justify-center gap-2 mb-3 transition"
        >
          <Camera class="w-5 h-5" />
          <span>Snap Date Stamp Photo</span>
        </button>

        <p v-if="isHttpNonLocal" class="text-[11px] text-slate-500 max-w-xs">
          Tip: Run <code class="text-sky-400 bg-slate-900 px-1.5 py-0.5 rounded">make run-ssl</code> for live video scanning on your mobile!
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

      <!-- Raw text debug preview -->
      <div
        v-if="rawOcrText && !detectedDate"
        class="absolute top-4 inset-x-4 bg-slate-950/80 border border-slate-700 rounded-lg p-2 text-xs text-slate-300 font-mono truncate text-center z-10"
      >
        OCR reading: "{{ rawOcrText }}"
      </div>
    </div>

    <!-- Hidden canvas for image capture and cropping -->
    <canvas ref="canvasEl" class="hidden"></canvas>

    <!-- Hidden native camera input (capture="environment") -->
    <input
      ref="nativeCameraInputRef"
      type="file"
      accept="image/*"
      capture="environment"
      class="hidden"
      @change="onFileSelected"
    />

    <!-- Hidden regular file picker -->
    <input
      ref="filePickerRef"
      type="file"
      accept="image/*"
      class="hidden"
      @change="onFileSelected"
    />

    <!-- Bottom Controls -->
    <div class="p-4 bg-slate-900/90 border-t border-slate-800 flex flex-col gap-3 z-10 max-w-md mx-auto w-full">
      <div class="grid grid-cols-2 gap-2">
        <!-- Native Camera Snap Button -->
        <button
          @click="openNativeCamera"
          :disabled="isProcessing"
          class="flex items-center justify-center gap-2 py-2.5 px-3 rounded-xl bg-sky-600 hover:bg-sky-500 active:scale-95 disabled:opacity-50 text-white font-bold text-xs transition shadow"
        >
          <Camera class="w-4 h-4" />
          <span>{{ isProcessing ? 'Scanning...' : 'Take Photo' }}</span>
        </button>

        <!-- Choose from Gallery -->
        <button
          @click="openFilePicker"
          class="flex items-center justify-center gap-2 py-2.5 px-3 rounded-xl bg-slate-800 hover:bg-slate-700 active:scale-95 text-slate-200 font-semibold text-xs transition border border-slate-700"
        >
          <UploadCloud class="w-4 h-4" />
          <span>Photo Gallery</span>
        </button>
      </div>

      <!-- Manual Date Picker Fallback -->
      <div class="flex items-center gap-2 pt-1 border-t border-slate-800/80">
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
import { Calendar, X, Camera, UploadCloud, Loader2 } from 'lucide-vue-next'
import { parseExpirationDate, playBeepSound } from '../utils/dateParser'
import { formatCameraErrorMessage } from '../utils/barcodeHelper'


const emit = defineEmits(['detected', 'close'])

const videoEl = ref(null)
const canvasEl = ref(null)
const nativeCameraInputRef = ref(null)
const filePickerRef = ref(null)

const isScanningLive = ref(false)
const isProcessing = ref(false)
const cameraError = ref(null)
const isHttpNonLocal = ref(false)
const detectedDate = ref(null)
const rawOcrText = ref('')
const manualInputDate = ref('')

let stream = null
let tesseractWorker = null
let autoScanInterval = null

onMounted(async () => {
  checkEnvironmentAndStart()
  await initWorker()
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

function checkEnvironmentAndStart() {
  const isSecure = window.isSecureContext || window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
  const hasMediaDevices = !!(navigator?.mediaDevices?.getUserMedia)

  if (!isSecure || !hasMediaDevices) {
    isHttpNonLocal.value = true
    cameraError.value = 'Live video is disabled by your browser because connection is not HTTPS.'
    return
  }

  startLiveCamera()
}

async function initWorker() {
  try {
    tesseractWorker = await createWorker('deu+eng', 1, {
      logger: (m) => {},
    })
    await tesseractWorker.setParameters({
      tessedit_char_whitelist: '0123456789./- :MHDBEXPBbestbeforeMhdExpJanFebMarAprMaiJunJulAugSepOktNovDez',
    })
  } catch (err) {
    console.error('Failed to init Tesseract worker:', err)
  }
}

async function startLiveCamera() {
  cameraError.value = null
  stopCamera()

  function attachStreamAndScan(activeStream) {
    stream = activeStream
    isScanningLive.value = true
    if (videoEl.value) {
      videoEl.value.srcObject = stream
    }

    if (autoScanInterval) clearInterval(autoScanInterval)
    autoScanInterval = setInterval(() => {
      if (!isProcessing.value && !detectedDate.value) {
        captureAndOcr()
      }
    }, 2500)
  }

  // Tier 1: HD environment camera
  try {
    const s = await navigator.mediaDevices.getUserMedia({
      video: {
        facingMode: { ideal: 'environment' },
        width: { ideal: 1920, min: 1280 },
        height: { ideal: 1080, min: 720 },
      },
    })
    attachStreamAndScan(s)
    return
  } catch (tier1Err) {
    console.warn('OCR camera tier 1 failed, trying tier 2:', tier1Err)
  }

  // Tier 2: Basic environment camera
  try {
    const s = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: 'environment' },
    })
    attachStreamAndScan(s)
    return
  } catch (tier2Err) {
    console.warn('OCR camera tier 2 failed, trying tier 3:', tier2Err)
  }

  // Tier 3: Any video device
  try {
    const s = await navigator.mediaDevices.getUserMedia({
      video: true,
    })
    attachStreamAndScan(s)
    return
  } catch (tier3Err) {
    console.error('All OCR camera tiers failed:', tier3Err)
    isScanningLive.value = false
    cameraError.value = formatCameraErrorMessage(tier3Err)
  }
}


function stopCamera() {
  isScanningLive.value = false
  if (stream) {
    stream.getTracks().forEach((track) => track.stop())
    stream = null
  }
}

function openNativeCamera() {
  if (nativeCameraInputRef.value) {
    nativeCameraInputRef.value.click()
  }
}

function openFilePicker() {
  if (filePickerRef.value) {
    filePickerRef.value.click()
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

    const vw = video.videoWidth
    const vh = video.videoHeight

    const cropW = Math.floor(vw * 0.65)
    const cropH = Math.floor(vh * 0.28)
    const cropX = Math.floor((vw - cropW) / 2)
    const cropY = Math.floor((vh - cropH) / 2)

    canvas.width = cropW
    canvas.height = cropH

    ctx.drawImage(video, cropX, cropY, cropW, cropH, 0, 0, cropW, cropH)

    // Preprocessing: High contrast grayscale
    const imgData = ctx.getImageData(0, 0, cropW, cropH)
    const data = imgData.data
    for (let i = 0; i < data.length; i += 4) {
      const avg = data[i] * 0.299 + data[i + 1] * 0.587 + data[i + 2] * 0.114
      const adjusted = avg > 120 ? 255 : avg < 80 ? 0 : avg
      data[i] = adjusted
      data[i + 1] = adjusted
      data[i + 2] = adjusted
    }
    ctx.putImageData(imgData, 0, 0)

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
      alert(`Could not extract date from photo. Text found: "${result.text.slice(0, 80)}"`)
    }
  } catch (err) {
    alert('Error reading image file for OCR.')
  } finally {
    isProcessing.value = false
    e.target.value = ''
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
