<template>
  <div class="fixed inset-0 z-50 bg-black/95 flex flex-col justify-between backdrop-blur-md">
    <!-- Header -->
    <div class="flex items-center justify-between p-4 bg-slate-900/90 border-b border-slate-800 text-white z-10">
      <div class="flex items-center gap-2">
        <Barcode class="w-6 h-6 text-emerald-400" />
        <div>
          <h3 class="font-semibold text-lg leading-tight">Scan EAN Barcode</h3>
          <p class="text-xs text-slate-400">Point at product barcode or take a photo</p>
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
      <div id="barcode-reader" class="w-full h-full max-h-[500px] overflow-hidden relative"></div>

      <!-- Live Overlay Reticle Guidelines (only shown when live camera is running) -->
      <div v-if="isScanningLive" class="pointer-events-none absolute inset-0 flex items-center justify-center">
        <div class="w-72 h-44 border-2 border-emerald-400/90 rounded-2xl relative shadow-[0_0_0_9999px_rgba(0,0,0,0.6)]">
          <!-- Animated laser scan line -->
          <div class="absolute inset-x-2 h-0.5 bg-gradient-to-r from-transparent via-emerald-400 to-transparent animate-pulse shadow-[0_0_8px_#34d399] top-1/2 -translate-y-1/2"></div>
          <span class="absolute -bottom-8 inset-x-0 text-center text-xs text-emerald-300 font-medium tracking-wide">
            Align barcode inside frame
          </span>
        </div>
      </div>

      <!-- Processing indicator -->
      <div v-if="isProcessingFile" class="absolute inset-0 bg-slate-950/80 flex flex-col items-center justify-center p-6 text-center z-20">
        <Loader2 class="w-10 h-10 animate-spin text-emerald-400 mb-3" />
        <p class="text-white font-medium text-sm">Decoding barcode from photo...</p>
      </div>

      <!-- Insecure Context / Camera Access Fallback UI -->
      <div v-if="cameraError" class="absolute inset-0 bg-slate-950/95 flex flex-col items-center justify-center p-6 text-center z-20">
        <div class="w-16 h-16 rounded-2xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400 mb-3">
          <Camera class="w-8 h-8" />
        </div>

        <h4 class="text-white font-bold text-lg mb-1">
          {{ isHttpNonLocal ? 'Live Camera Requires HTTPS' : 'Camera Access Unavailable' }}
        </h4>

        <p class="text-slate-300 text-xs max-w-sm mb-4 leading-relaxed">
          <span v-if="isHttpNonLocal">
            Mobile browsers (iOS Safari & Android Chrome) block live WebRTC video streams over plain HTTP.
            <br /><br />
            <strong>Good news:</strong> You can snap a photo directly using your phone's native camera below!
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
          Tip: Run <code class="text-emerald-400 bg-slate-900 px-1.5 py-0.5 rounded">make run-ssl</code> on your server to enable live video on mobile!
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
          class="flex items-center justify-center gap-2 py-2.5 px-3 rounded-xl bg-emerald-600 hover:bg-emerald-500 active:scale-95 text-white font-bold text-xs transition shadow"
        >
          <Camera class="w-4 h-4" />
          <span>Take Photo</span>
        </button>

        <!-- Choose from Gallery / Files -->
        <button
          @click="openFilePicker"
          class="flex items-center justify-center gap-2 py-2.5 px-3 rounded-xl bg-slate-800 hover:bg-slate-700 active:scale-95 text-slate-200 font-semibold text-xs transition border border-slate-700"
        >
          <UploadCloud class="w-4 h-4" />
          <span>Photo Gallery</span>
        </button>
      </div>

      <!-- Manual Test Code Entry -->
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
import { Barcode, X, Camera, UploadCloud, Loader2 } from 'lucide-vue-next'
import { playBeepSound } from '../utils/dateParser'

const emit = defineEmits(['detected', 'close'])

let html5QrCode = null
const isScanningLive = ref(false)
const isProcessingFile = ref(false)
const cameraError = ref(null)
const manualBarcode = ref('')
const isHttpNonLocal = ref(false)

const nativeCameraInputRef = ref(null)
const filePickerRef = ref(null)

onMounted(async () => {
  checkEnvironmentAndStart()
})

onUnmounted(async () => {
  await stopScanner()
})

function checkEnvironmentAndStart() {
  const isSecure = window.isSecureContext || window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
  const hasMediaDevices = !!(navigator?.mediaDevices?.getUserMedia)

  if (!isSecure || !hasMediaDevices) {
    isHttpNonLocal.value = true
    cameraError.value = 'Live video camera is disabled by your mobile browser because this connection is not HTTPS.'
    return
  }

  startLiveScanner()
}

async function startLiveScanner() {
  cameraError.value = null
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
        verbose: false,
      })
    }

    // Pass facingMode: 'environment' directly to request rear camera without getCameras()
    await html5QrCode.start(
      { facingMode: 'environment' },
      {
        fps: 10,
        qrbox: { width: 280, height: 180 },
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
  } catch (err) {
    console.warn('Live scanner start error:', err)
    isScanningLive.value = false
    cameraError.value = 'Could not access the live camera stream. You can snap a photo with your camera instead!'
  }
}

async function stopScanner() {
  isScanningLive.value = false
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
  playBeepSound()
  stopScanner()
  emit('detected', barcode.trim())
}

function submitManualBarcode() {
  if (manualBarcode.value.trim()) {
    playBeepSound()
    stopScanner()
    emit('detected', manualBarcode.value.trim())
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
        verbose: false,
      })
    }
    const result = await html5QrCode.scanFile(file, true)
    handleBarcodeFound(result)
  } catch (err) {
    alert('No barcode detected in the photo. Please ensure the barcode is sharp, well-lit, and try again.')
  } finally {
    isProcessingFile.value = false
    // reset input so the same file can be selected again
    e.target.value = ''
  }
}

function closeScanner() {
  stopScanner()
  emit('close')
}
</script>
