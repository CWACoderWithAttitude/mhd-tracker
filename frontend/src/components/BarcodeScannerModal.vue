<template>
  <div class="fixed inset-0 z-50 bg-black/90 flex flex-col justify-between backdrop-blur-sm">
    <!-- Header -->
    <div class="flex items-center justify-between p-4 bg-slate-900/80 border-b border-slate-800 text-white z-10">
      <div class="flex items-center gap-2">
        <Barcode class="w-6 h-6 text-emerald-400" />
        <h3 class="font-semibold text-lg">Scan EAN Barcode</h3>
      </div>
      <button
        @click="closeScanner"
        class="p-2 rounded-full bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition"
      >
        <X class="w-6 h-6" />
      </button>
    </div>

    <!-- Scanner Viewport Area -->
    <div class="relative flex-1 flex flex-col items-center justify-center overflow-hidden">
      <!-- Camera container -->
      <div id="barcode-reader" class="w-full max-w-md h-full max-h-[460px] overflow-hidden rounded-xl bg-black relative"></div>

      <!-- Overlay Reticle Guidelines -->
      <div class="pointer-events-none absolute inset-0 flex items-center justify-center">
        <div class="w-72 h-44 border-2 border-emerald-400/80 rounded-2xl relative shadow-[0_0_0_9999px_rgba(0,0,0,0.5)]">
          <!-- Animated laser scanner bar -->
          <div class="absolute inset-x-2 h-0.5 bg-gradient-to-r from-transparent via-emerald-400 to-transparent animate-pulse shadow-[0_0_8px_#34d399] top-1/2 -translate-y-1/2"></div>
          <span class="absolute -bottom-8 inset-x-0 text-center text-xs text-emerald-300 font-medium tracking-wide">
            Align barcode inside frame
          </span>
        </div>
      </div>

      <!-- Loading / Camera Error -->
      <div v-if="cameraError" class="absolute inset-0 bg-slate-950/95 flex flex-col items-center justify-center p-6 text-center z-20">
        <AlertCircle class="w-12 h-12 text-rose-500 mb-3" />
        <h4 class="text-white font-medium text-lg mb-1">Camera Access Issue</h4>
        <p class="text-slate-400 text-sm max-w-xs mb-4">{{ cameraError }}</p>
        <button
          @click="startScanning"
          class="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg font-medium text-sm transition"
        >
          Try Again
        </button>
      </div>
    </div>

    <!-- Bottom Controls & Fallbacks -->
    <div class="p-4 bg-slate-900/90 border-t border-slate-800 flex flex-col gap-3 z-10 max-w-md mx-auto w-full">
      <!-- Camera switch & Torch -->
      <div class="flex items-center justify-center gap-4">
        <button
          v-if="hasMultipleCameras"
          @click="switchCamera"
          class="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800 text-slate-200 text-xs font-medium hover:bg-slate-700 transition"
        >
          <SwitchCamera class="w-4 h-4" />
          Switch Camera
        </button>

        <label class="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800 text-slate-200 text-xs font-medium hover:bg-slate-700 cursor-pointer transition">
          <UploadCloud class="w-4 h-4" />
          <span>Upload Image</span>
          <input type="file" accept="image/*" class="hidden" @change="onFileSelected" />
        </label>
      </div>

      <!-- Manual Test Code Entry -->
      <div class="flex items-center gap-2">
        <input
          v-model="manualBarcode"
          type="text"
          placeholder="Or enter barcode manually..."
          class="flex-1 bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500"
          @keyup.enter="submitManualBarcode"
        />
        <button
          @click="submitManualBarcode"
          :disabled="!manualBarcode.trim()"
          class="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white rounded-lg text-sm font-medium transition"
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
import { Barcode, X, AlertCircle, SwitchCamera, UploadCloud } from 'lucide-vue-next'
import { playBeepSound } from '../utils/dateParser'

const emit = defineEmits(['detected', 'close'])

let html5QrCode = null
const cameraError = ref(null)
const manualBarcode = ref('')
const hasMultipleCameras = ref(false)
const cameras = ref([])
const currentCameraIndex = ref(0)

onMounted(async () => {
  await initScanner()
})

onUnmounted(async () => {
  await stopScanner()
})

async function initScanner() {
  cameraError.value = null
  try {
    const devices = await Html5Qrcode.getCameras()
    if (devices && devices.length > 0) {
      cameras.value = devices
      hasMultipleCameras.value = devices.length > 1
      // Prefer back camera if found
      const backIndex = devices.findIndex(d => d.label.toLowerCase().includes('back') || d.label.toLowerCase().includes('rear'))
      currentCameraIndex.value = backIndex !== -1 ? backIndex : 0
      await startScanning()
    } else {
      cameraError.value = 'No camera found on this device.'
    }
  } catch (err) {
    cameraError.value = 'Camera permission was denied or camera is unavailable.'
    console.error(err)
  }
}

async function startScanning() {
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

    const cameraId = cameras.value[currentCameraIndex.value]?.id || { facingMode: 'environment' }

    await html5QrCode.start(
      cameraId,
      {
        fps: 15,
        qrbox: { width: 280, height: 180 },
        aspectRatio: 1.0,
      },
      (decodedText) => {
        handleBarcodeFound(decodedText)
      },
      () => {
        // scan failure / frame skip, normal
      }
    )
  } catch (err) {
    console.error('Failed to start html5QrCode:', err)
    cameraError.value = 'Failed to start camera preview. Please check camera permissions.'
  }
}

async function stopScanner() {
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

async function switchCamera() {
  if (cameras.value.length < 2) return
  await stopScanner()
  currentCameraIndex.value = (currentCameraIndex.value + 1) % cameras.value.length
  await startScanning()
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

async function onFileSelected(e) {
  const file = e.target.files?.[0]
  if (!file) return

  try {
    if (!html5QrCode) {
      html5QrCode = new Html5Qrcode('barcode-reader')
    }
    const result = await html5QrCode.scanFile(file, true)
    handleBarcodeFound(result)
  } catch (err) {
    alert('Could not find a valid barcode in this image. Try another picture.')
  }
}

function closeScanner() {
  stopScanner()
  emit('close')
}
</script>
