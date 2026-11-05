<template>
  <div class="fixed inset-0 z-50 bg-black/95 flex flex-col justify-between backdrop-blur-md select-none">
    <!-- Header -->
    <div class="flex items-center justify-between p-4 bg-slate-900/90 border-b border-slate-800 text-white z-10">
      <div class="flex items-center gap-2">
        <Barcode class="w-6 h-6 text-emerald-400" />
        <div>
          <h3 class="font-semibold text-lg leading-tight">Scan EAN Barcode</h3>
          <p class="text-xs text-slate-400">High-speed hardware barcode scanner</p>
        </div>
      </div>
      <button
        @click="closeScanner"
        class="p-2 rounded-full bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition"
      >
        <X class="w-6 h-6" />
      </button>
    </div>

    <!-- Scanner Viewport Area -->
    <div class="relative flex-1 flex flex-col items-center justify-center overflow-hidden bg-black">
      <!-- Live Video element container for Html5Qrcode -->
      <div id="barcode-reader" class="w-full h-full max-h-[560px] overflow-hidden relative"></div>

      <!-- Live Overlay Reticle & Dynamic Guide Lines -->
      <div v-if="isScanningLive" class="pointer-events-none absolute inset-0 flex items-center justify-center">
        <!-- Reticle bounding box matching scanner active region -->
        <div class="w-[85vw] max-w-[360px] h-[45vw] max-h-[220px] min-h-[140px] border-2 border-emerald-400/90 rounded-2xl relative shadow-[0_0_0_9999px_rgba(0,0,0,0.65)] flex items-center justify-center">
          <!-- Laser animation bar -->
          <div class="absolute inset-x-2 h-0.5 bg-gradient-to-r from-transparent via-emerald-400 to-transparent animate-pulse shadow-[0_0_10px_#34d399] top-1/2 -translate-y-1/2"></div>
          
          <!-- Corner brackets for clear target acquisition -->
          <div class="absolute -top-1 -left-1 w-4 h-4 border-t-2 border-l-2 border-emerald-300"></div>
          <div class="absolute -top-1 -right-1 w-4 h-4 border-t-2 border-r-2 border-emerald-300"></div>
          <div class="absolute -bottom-1 -left-1 w-4 h-4 border-b-2 border-l-2 border-emerald-300"></div>
          <div class="absolute -bottom-1 -right-1 w-4 h-4 border-b-2 border-r-2 border-emerald-300"></div>

          <span class="absolute -bottom-8 inset-x-0 text-center text-xs text-emerald-300 font-medium tracking-wide">
            Hold barcode horizontally inside frame
          </span>
        </div>
      </div>

      <!-- Camera Quick Controls Overlay (Torch & Zoom) -->
      <div
        v-if="isScanningLive && (isTorchSupported || isZoomSupported)"
        class="absolute top-4 inset-x-4 flex items-center justify-center gap-3 z-20 pointer-events-auto"
      >
        <!-- Torch / Flashlight Toggle Button -->
        <button
          v-if="isTorchSupported"
          @click="toggleTorch"
          :class="[
            'flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-xs font-bold transition shadow-lg backdrop-blur-md',
            isTorchOn
              ? 'bg-amber-400 text-slate-950 shadow-amber-400/40 ring-2 ring-amber-300'
              : 'bg-slate-900/80 text-slate-200 border border-slate-700/80 hover:bg-slate-800'
          ]"
        >
          <Zap v-if="isTorchOn" class="w-3.5 h-3.5 fill-current" />
          <ZapOff v-else class="w-3.5 h-3.5 text-slate-400" />
          <span>{{ isTorchOn ? 'Flash On' : 'Flashlight' }}</span>
        </button>

        <!-- 1x / 2x Zoom Toggle Button (helps scanning small grocery items) -->
        <button
          v-if="isZoomSupported"
          @click="toggleZoom"
          class="flex items-center gap-1 px-3 py-1.5 rounded-full text-xs font-bold bg-slate-900/80 text-emerald-300 border border-emerald-600/40 hover:bg-slate-800 transition shadow-lg backdrop-blur-md"
        >
          <ZoomIn class="w-3.5 h-3.5" />
          <span>{{ currentZoom > 1 ? `${currentZoom}x Zoom` : '1x Zoom' }}</span>
        </button>
      </div>

      <!-- Processing photo indicator -->
      <div v-if="isProcessingFile" class="absolute inset-0 bg-slate-950/85 flex flex-col items-center justify-center p-6 text-center z-20">
        <Loader2 class="w-10 h-10 animate-spin text-emerald-400 mb-3" />
        <p class="text-white font-medium text-sm">Optimizing & decoding barcode...</p>
        <p class="text-slate-400 text-xs mt-1">Multi-pass analysis</p>
      </div>

      <!-- Insecure Context / Camera Access Fallback UI -->
      <div v-if="cameraError" class="absolute inset-0 bg-slate-950/95 flex flex-col items-center justify-center p-6 text-center z-20">
        <div class="w-16 h-16 rounded-2xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400 mb-3">
          <Camera class="w-8 h-8" />
        </div>

        <h4 class="text-white font-bold text-lg mb-1">
          {{ isHttpNonLocal ? 'Live Camera Requires HTTPS' : 'Camera Access Issue' }}
        </h4>

        <p class="text-slate-300 text-xs max-w-sm mb-4 leading-relaxed">
          <span v-if="isHttpNonLocal">
            Mobile browsers (iOS Safari & Android Chrome) block live WebRTC video streams over plain HTTP.
            <br /><br />
            <strong>You can take a photo of the barcode directly using your camera!</strong>
          </span>
          <span v-else>
            {{ cameraError }}
          </span>
        </p>

        <!-- Primary Native Camera Button (works 100% on iOS & Android over HTTP & HTTPS) -->
        <button
          @click="openNativeCamera"
          class="w-full max-w-xs py-3.5 px-6 bg-emerald-600 hover:bg-emerald-500 active:scale-95 text-white font-bold text-sm rounded-xl shadow-lg shadow-emerald-950/50 flex items-center justify-center gap-2 mb-3 transition"
        >
          <Camera class="w-5 h-5" />
          <span>Snap Barcode Photo</span>
        </button>

        <p v-if="isHttpNonLocal" class="text-[11px] text-slate-500 max-w-xs">
          Tip: Run <code class="text-emerald-400 bg-slate-900 px-1.5 py-0.5 rounded">make run-ssl</code> on your server for live video on mobile!
        </p>
      </div>
    </div>

    <!-- Hidden native camera input (capture="environment" directly triggers mobile camera app!) -->
    <input
      ref="nativeCameraInputRef"
      type="file"
      accept="image/*"
      capture="environment"
      class="hidden"
      @change="onFileSelected"
    />

    <!-- Hidden regular file picker for gallery / desktop -->
    <input
      ref="filePickerRef"
      type="file"
      accept="image/*"
      class="hidden"
      @change="onFileSelected"
    />

    <!-- Bottom Controls & Fallbacks -->
    <div class="p-4 bg-slate-900/90 border-t border-slate-800 flex flex-col gap-3 z-10 max-w-md mx-auto w-full">
      <!-- Action buttons -->
      <div class="grid grid-cols-2 gap-2">
        <!-- Native Camera Snap Button -->
        <button
          @click="openNativeCamera"
          :disabled="isProcessingFile"
          class="flex items-center justify-center gap-2 py-2.5 px-3 rounded-xl bg-emerald-600 hover:bg-emerald-500 active:scale-95 disabled:opacity-50 text-white font-bold text-xs transition shadow"
        >
          <Camera class="w-4 h-4" />
          <span>Take Photo</span>
        </button>

        <!-- Choose from Gallery / Files -->
        <button
          @click="openFilePicker"
          :disabled="isProcessingFile"
          class="flex items-center justify-center gap-2 py-2.5 px-3 rounded-xl bg-slate-800 hover:bg-slate-700 active:scale-95 disabled:opacity-50 text-slate-200 font-semibold text-xs transition border border-slate-700"
        >
          <UploadCloud class="w-4 h-4" />
          <span>Photo Gallery</span>
        </button>
      </div>

      <!-- Manual Code Entry Fallback -->
      <div class="flex items-center gap-2 pt-1 border-t border-slate-800/80">
        <input
          v-model="manualBarcode"
          type="text"
          placeholder="Or type barcode manually..."
          class="flex-1 bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 font-mono"
          @keyup.enter="submitManualBarcode"
        />
        <button
          @click="submitManualBarcode"
          :disabled="!manualBarcode.trim()"
          class="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white rounded-lg text-xs font-bold transition"
        >
          Submit
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { Html5Qrcode, Html5QrcodeSupportedFormats } from 'html5-qrcode'
import {
  Barcode,
  X,
  Camera,
  UploadCloud,
  Loader2,
  Zap,
  ZapOff,
  ZoomIn,
} from 'lucide-vue-next'
import { playBeepSound } from '../utils/dateParser'
import {
  cleanBarcode,
  getOptimalQrboxDimensions,
  optimizeImageForBarcode,
} from '../utils/barcodeHelper'

const emit = defineEmits(['detected', 'close'])

let html5QrCode = null
const isScanningLive = ref(false)
const isProcessingFile = ref(false)
const cameraError = ref(null)
const manualBarcode = ref('')
const isHttpNonLocal = ref(false)

const isTorchSupported = ref(false)
const isTorchOn = ref(false)
const isZoomSupported = ref(false)
const currentZoom = ref(1)

const nativeCameraInputRef = ref(null)
const filePickerRef = ref(null)

onMounted(async () => {
  checkEnvironmentAndStart()
})

onUnmounted(async () => {
  await stopScanner()
})

function checkEnvironmentAndStart() {
  const isSecure =
    window.isSecureContext ||
    window.location.hostname === 'localhost' ||
    window.location.hostname === '127.0.0.1'
  const hasMediaDevices = !!navigator?.mediaDevices?.getUserMedia

  if (!isSecure || !hasMediaDevices) {
    isHttpNonLocal.value = true
    cameraError.value =
      'Live video camera is disabled by your mobile browser because this connection is not HTTPS.'
    return
  }

  startLiveScanner()
}

function getActiveVideoTrack() {
  const videoEl = document.querySelector('#barcode-reader video')
  if (videoEl && videoEl.srcObject) {
    return videoEl.srcObject.getVideoTracks()[0] || null
  }
  return null
}

function checkTrackCapabilities() {
  setTimeout(() => {
    const track = getActiveVideoTrack()
    if (!track) return

    const capabilities = track.getCapabilities ? track.getCapabilities() : {}
    if (capabilities.torch) {
      isTorchSupported.value = true
    }
    if (capabilities.zoom) {
      isZoomSupported.value = true
      currentZoom.value = track.getSettings ? track.getSettings().zoom || 1 : 1
    }
  }, 400)
}

async function toggleTorch() {
  const track = getActiveVideoTrack()
  if (!track) return

  try {
    isTorchOn.value = !isTorchOn.value
    await track.applyConstraints({
      advanced: [{ torch: isTorchOn.value }],
    })
  } catch (err) {
    console.warn('Torch toggle failed:', err)
  }
}

async function toggleZoom() {
  const track = getActiveVideoTrack()
  if (!track) return

  try {
    const capabilities = track.getCapabilities ? track.getCapabilities() : {}
    const maxZoom = capabilities.zoom?.max || 2
    currentZoom.value = currentZoom.value > 1 ? 1 : Math.min(2, maxZoom)
    await track.applyConstraints({
      advanced: [{ zoom: currentZoom.value }],
    })
  } catch (err) {
    console.warn('Zoom toggle failed:', err)
  }
}

async function startLiveScanner() {
  cameraError.value = null
  try {
    if (!html5QrCode) {
      // Enable native hardware BarcodeDetector API if supported (GPU/Vision acceleration)
      html5QrCode = new Html5Qrcode('barcode-reader', {
        formatsToSupport: [
          Html5QrcodeSupportedFormats.EAN_13,
          Html5QrcodeSupportedFormats.EAN_8,
          Html5QrcodeSupportedFormats.UPC_A,
          Html5QrcodeSupportedFormats.UPC_E,
          Html5QrcodeSupportedFormats.CODE_128,
          Html5QrcodeSupportedFormats.QR_CODE,
        ],
        experimentalFeatures: {
          useBarCodeDetectorIfSupported: true,
        },
        verbose: false,
      })
    }

    // High definition 1080p stream with continuous autofocus for crisp 1D barcode lines
    const cameraConstraints = {
      facingMode: { ideal: 'environment' },
      width: { min: 1280, ideal: 1920 },
      height: { min: 720, ideal: 1080 },
      focusMode: { ideal: 'continuous' },
    }

    await html5QrCode.start(
      cameraConstraints,
      {
        fps: 20, // 20 frames per second catches sharp moments during natural hand tremors
        qrbox: (viewfinderWidth, viewfinderHeight) => {
          return getOptimalQrboxDimensions(viewfinderWidth, viewfinderHeight)
        },
        aspectRatio: 1.0,
      },
      (decodedText) => {
        handleBarcodeFound(decodedText)
      },
      () => {
        // Frame skipped without barcode - normal
      }
    )

    isScanningLive.value = true
    checkTrackCapabilities()
  } catch (err) {
    console.warn('Live scanner start error with HD constraints, attempting fallback:', err)
    // Fallback to simpler constraints if device rejects HD
    try {
      await html5QrCode.start(
        { facingMode: 'environment' },
        {
          fps: 15,
          qrbox: (viewfinderWidth, viewfinderHeight) => {
            return getOptimalQrboxDimensions(viewfinderWidth, viewfinderHeight)
          },
          aspectRatio: 1.0,
        },
        (decodedText) => {
          handleBarcodeFound(decodedText)
        },
        () => {}
      )
      isScanningLive.value = true
      checkTrackCapabilities()
    } catch (fallbackErr) {
      console.warn('Fallback scanner also failed:', fallbackErr)
      isScanningLive.value = false
      cameraError.value =
        'Could not access the live camera stream. You can snap a photo with your camera instead!'
    }
  }
}

async function stopScanner() {
  isScanningLive.value = false
  isTorchOn.value = false
  if (html5QrCode) {
    try {
      if (html5QrCode.isScanning) {
        await html5QrCode.stop()
      }
      html5QrCode.clear()
    } catch (e) {
      console.warn('Error stopping scanner:', e)
    }
    html5QrCode = null
  }
}

function handleBarcodeFound(barcode) {
  const cleaned = cleanBarcode(barcode)
  if (cleaned) {
    playBeepSound()
    stopScanner()
    emit('detected', cleaned)
  }
}

function submitManualBarcode() {
  const cleaned = cleanBarcode(manualBarcode.value)
  if (cleaned) {
    playBeepSound()
    stopScanner()
    emit('detected', cleaned)
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

async function onFileSelected(e) {
  const file = e.target.files?.[0]
  if (!file) return

  isProcessingFile.value = true
  try {
    if (!html5QrCode) {
      html5QrCode = new Html5Qrcode('barcode-reader', {
        formatsToSupport: [
          Html5QrcodeSupportedFormats.EAN_13,
          Html5QrcodeSupportedFormats.EAN_8,
          Html5QrcodeSupportedFormats.UPC_A,
          Html5QrcodeSupportedFormats.UPC_E,
          Html5QrcodeSupportedFormats.CODE_128,
          Html5QrcodeSupportedFormats.QR_CODE,
        ],
        experimentalFeatures: {
          useBarCodeDetectorIfSupported: true,
        },
        verbose: false,
      })
    }

    // Step 1: Optimize photo resolution (downscale from 12-48MP to max 1600px)
    const optimizedFile = await optimizeImageForBarcode(file, 1600)

    try {
      // First pass with optimized image
      const result = await html5QrCode.scanFile(optimizedFile, true)
      handleBarcodeFound(result)
      return
    } catch (firstPassErr) {
      console.warn('First pass barcode scan failed, attempting high-resolution pass:', firstPassErr)
    }

    // Step 2: Fallback attempt on original file in case barcode lines were tiny
    const directResult = await html5QrCode.scanFile(file, true)
    handleBarcodeFound(directResult)
  } catch (err) {
    alert(
      'No barcode detected in the photo. Please hold the camera steadily, ensure good lighting, and try again.'
    )
  } finally {
    isProcessingFile.value = false
    e.target.value = ''
  }
}

function closeScanner() {
  stopScanner()
  emit('close')
}
</script>
