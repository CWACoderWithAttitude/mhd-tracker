<template>
  <div
    class="fixed inset-0 z-40 bg-black/80 flex items-end sm:items-center justify-center p-0 sm:p-4 backdrop-blur-sm"
  >
    <div
      class="bg-slate-900 border border-slate-800 w-full max-w-lg rounded-t-3xl sm:rounded-2xl max-h-[92vh] flex flex-col shadow-2xl overflow-hidden animate-in slide-in-from-bottom duration-200"
    >
      <!-- Header -->
      <div
        class="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/90 sticky top-0 z-10"
      >
        <div class="flex items-center gap-2">
          <div
            class="w-8 h-8 rounded-lg bg-emerald-500/20 text-emerald-400 flex items-center justify-center font-bold"
          >
            <PackagePlus v-if="!itemData.id" class="w-5 h-5" />
            <Edit3 v-else class="w-5 h-5" />
          </div>
          <div>
            <h2 class="text-lg font-bold text-white leading-tight">
              {{ itemData.id ? "Edit Item" : "Add to Inventory" }}
            </h2>
            <p class="text-xs text-slate-400">
              Track best-before date and location
            </p>
          </div>
        </div>
        <button
          @click="$emit('close')"
          class="p-2 rounded-full text-slate-400 hover:text-white hover:bg-slate-800 transition"
        >
          <X class="w-5 h-5" />
        </button>
      </div>

      <!-- Quick Action Scanning Bar -->
      <div
        class="p-3 bg-slate-950/60 border-b border-slate-800/80 grid grid-cols-2 gap-2"
      >
        <button
          type="button"
          @click="openBarcodeScanner"
          class="flex items-center justify-center gap-2 py-2 px-3 rounded-xl bg-emerald-950/60 border border-emerald-600/40 text-emerald-300 hover:bg-emerald-900/40 text-xs font-semibold transition active:scale-95"
        >
          <Barcode class="w-4 h-4 text-emerald-400" />
          <span>{{
            itemData.ean ? "Re-scan Barcode" : "Scan Barcode (EAN)"
          }}</span>
        </button>

        <button
          type="button"
          @click="openDateScanner"
          class="flex items-center justify-center gap-2 py-2 px-3 rounded-xl bg-sky-950/60 border border-sky-600/40 text-sky-300 hover:bg-sky-900/40 text-xs font-semibold transition active:scale-95"
        >
          <Calendar class="w-4 h-4 text-sky-400" />
          <span>{{
            itemData.expiration_date ? "Re-scan MHD" : "Scan Date (OCR)"
          }}</span>
        </button>
      </div>

      <!-- Scrollable Form Body -->
      <div class="p-4 overflow-y-auto space-y-4 flex-1">
        <!-- Scanned Product Preview Card if Image/EAN is available -->
        <div
          v-if="itemData.image_url || isLookingUpEan"
          class="p-3 rounded-xl bg-slate-950 border border-slate-800 flex items-center gap-3"
        >
          <div
            class="w-14 h-14 rounded-lg bg-slate-800 flex items-center justify-center overflow-hidden flex-shrink-0"
          >
            <img
              v-if="itemData.image_url"
              :src="itemData.image_url"
              alt="Product"
              class="w-full h-full object-contain"
            />
            <Loader2
              v-else-if="isLookingUpEan"
              class="w-6 h-6 animate-spin text-emerald-400"
            />
            <Package v-else class="w-6 h-6 text-slate-500" />
          </div>
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-1.5">
              <span
                class="text-xs px-2 py-0.5 rounded-full bg-emerald-950 text-emerald-400 border border-emerald-800/60 font-mono text-[10px]"
              >
                EAN: {{ itemData.ean || "None" }}
              </span>
              <span v-if="lookupSource" class="text-[10px] text-slate-400"
                >({{ lookupSource }})</span
              >
            </div>
            <p class="text-sm font-semibold text-white truncate mt-0.5">
              {{ itemData.name || "Lookup in progress..." }}
            </p>
            <p class="text-xs text-slate-400 truncate">
              {{ itemData.brand || "No brand specified" }}
            </p>
          </div>
        </div>

        <!-- Product Name -->
        <div>
          <label class="block text-xs font-medium text-slate-300 mb-1">
            Product Name <span class="text-rose-400">*</span>
          </label>
          <input
            v-model="itemData.name"
            type="text"
            required
            placeholder="e.g. Organic Oat Milk 1L"
            class="w-full bg-slate-950 border border-slate-700 rounded-xl px-3.5 py-2.5 text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 text-sm"
          />
        </div>

        <!-- Brand & Barcode Grid -->
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-xs font-medium text-slate-300 mb-1"
              >Brand</label
            >
            <input
              v-model="itemData.brand"
              type="text"
              placeholder="e.g. Oatly"
              class="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 text-sm"
            />
          </div>
          <div>
            <label class="block text-xs font-medium text-slate-300 mb-1"
              >EAN Barcode</label
            >
            <div class="relative">
              <input
                v-model="itemData.ean"
                type="text"
                placeholder="Barcode"
                class="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 text-sm font-mono"
                @change="triggerLookupIfEanEntered"
              />
              <button
                type="button"
                @click="openBarcodeScanner"
                class="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 hover:text-emerald-400"
              >
                <Barcode class="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>

        <!-- Expiration Date (MHD) & Quantity Grid -->
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-xs font-medium text-slate-300 mb-1">
              Expiration Date (MHD) <span class="text-rose-400">*</span>
            </label>
            <div class="relative">
              <input
                v-model="itemData.expiration_date"
                type="date"
                required
                class="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-emerald-500 text-sm font-mono"
              />
            </div>
          </div>

          <div>
            <label class="block text-xs font-medium text-slate-300 mb-1"
              >Quantity</label
            >
            <div
              class="flex items-center bg-slate-950 border border-slate-700 rounded-xl overflow-hidden"
            >
              <button
                type="button"
                @click="decrementQuantity"
                class="px-3 py-2 text-slate-400 hover:text-white hover:bg-slate-800 transition"
              >
                <Minus class="w-4 h-4" />
              </button>
              <input
                v-model.number="itemData.quantity"
                type="number"
                min="1"
                class="w-full text-center bg-transparent py-2 text-white font-bold text-sm focus:outline-none"
              />
              <button
                type="button"
                @click="incrementQuantity"
                class="px-3 py-2 text-slate-400 hover:text-white hover:bg-slate-800 transition"
              >
                <Plus class="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>

        <!-- Category & Storage Location -->
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-xs font-medium text-slate-300 mb-1"
              >Category</label
            >
            <select
              v-model="itemData.category"
              class="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-white text-sm focus:outline-none focus:border-emerald-500"
            >
              <option value="Dairy">🥛 Dairy & Cheese</option>
              <option value="Pantry">🥫 Pantry & Dry</option>
              <option value="Produce">🥦 Fresh Produce</option>
              <option value="Meat">🥩 Meat & Fish</option>
              <option value="Drinks">🧃 Drinks</option>
              <option value="Frozen">❄️ Frozen</option>
              <option value="Snacks">🍫 Snacks</option>
              <option value="Other">📦 Other</option>
            </select>
          </div>

          <div>
            <label class="block text-xs font-medium text-slate-300 mb-1"
              >Location</label
            >
            <select
              v-model="itemData.location"
              class="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-white text-sm focus:outline-none focus:border-emerald-500"
            >
              <option v-for="loc in locations" :key="loc" :value="loc">
                {{ loc }}
              </option>
            </select>
          </div>
        </div>

        <!-- Optional Notes -->
        <div>
          <label class="block text-xs font-medium text-slate-300 mb-1"
            >Notes (Optional)</label
          >
          <input
            v-model="itemData.notes"
            type="text"
            placeholder="e.g. opened 2 days ago, top shelf"
            class="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 text-sm"
          />
        </div>
      </div>

      <!-- Action Buttons Footer -->
      <div
        class="p-4 border-t border-slate-800 bg-slate-900/95 flex items-center gap-3"
      >
        <button
          type="button"
          @click="$emit('close')"
          class="flex-1 py-3 px-4 rounded-xl border border-slate-700 text-slate-300 hover:bg-slate-800 font-semibold text-sm transition"
        >
          Cancel
        </button>
        <button
          type="button"
          @click="submitForm"
          :disabled="isSubmitting || !isFormValid"
          class="flex-1 py-3 px-4 rounded-xl bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white font-bold text-sm shadow-lg shadow-emerald-950/40 transition active:scale-95 flex items-center justify-center gap-2"
        >
          <Loader2 v-if="isSubmitting" class="w-4 h-4 animate-spin" />
          <span>{{ itemData.id ? "Save Changes" : "Store in Pantry" }}</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, reactive } from "vue";
import {
  PackagePlus,
  Edit3,
  X,
  Barcode,
  Calendar,
  Plus,
  Minus,
  Loader2,
  Package,
} from "lucide-vue-next";

const props = defineProps({
  initialData: {
    type: Object,
    default: () => ({}),
  },
  locations: {
    type: Array,
    default: () => [],
  },
});

const emit = defineEmits([
  "save",
  "close",
  "openBarcodeScanner",
  "openDateScanner",
]);

const itemData = reactive({
  id: props.initialData.id || null,
  ean: props.initialData.ean || "",
  name: props.initialData.name || "",
  brand: props.initialData.brand || "",
  expiration_date: props.initialData.expiration_date || "",
  quantity: props.initialData.quantity || 1,
  category: props.initialData.category || "Pantry",
  location: props.initialData.location || props.locations[0] || "",
  notes: props.initialData.notes || "",
  image_url: props.initialData.image_url || "",
});

const isLookingUpEan = ref(false);
const lookupSource = ref("");
const isSubmitting = ref(false);

const isFormValid = computed(() => {
  return (
    itemData.name.trim().length > 0 &&
    itemData.expiration_date &&
    itemData.quantity >= 1
  );
});

function incrementQuantity() {
  itemData.quantity++;
}

function decrementQuantity() {
  if (itemData.quantity > 1) {
    itemData.quantity--;
  }
}

function openBarcodeScanner() {
  emit("openBarcodeScanner");
}

function openDateScanner() {
  emit("openDateScanner");
}

async function triggerLookupIfEanEntered() {
  if (!itemData.ean || itemData.ean.trim().length < 6) return;
  await lookupBarcode(itemData.ean.trim());
}

async function lookupBarcode(barcode) {
  isLookingUpEan.value = true;
  lookupSource.value = "";
  try {
    const res = await fetch(`/api/lookup/ean/${encodeURIComponent(barcode)}`);
    if (res.ok) {
      const data = await res.json();
      if (data.found) {
        if (data.name) itemData.name = data.name;
        if (data.brand) itemData.brand = data.brand;
        if (data.category) itemData.category = data.category;
        if (data.image_url) itemData.image_url = data.image_url;
        lookupSource.value =
          data.source === "openfoodfacts" ? "Open Food Facts" : "Local History";
      }
    }
  } catch (e) {
    console.error("Barcode lookup failed:", e);
  } finally {
    isLookingUpEan.value = false;
  }
}

// Method exposed to parent to inject detected barcode or date
function setBarcode(barcode) {
  itemData.ean = barcode;
  lookupBarcode(barcode);
}

function setDate(dateStr) {
  itemData.expiration_date = dateStr;
}

defineExpose({
  setBarcode,
  setDate,
});

async function submitForm() {
  if (!isFormValid.value) return;
  isSubmitting.value = true;
  try {
    emit("save", { ...itemData });
  } finally {
    isSubmitting.value = false;
  }
}
</script>
