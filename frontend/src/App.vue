<template>
  <div class="min-h-screen bg-slate-950 text-slate-100 pb-28">
    <!-- Top App Bar -->
    <header
      class="sticky top-0 z-30 bg-slate-900/90 backdrop-blur-md border-b border-slate-800 px-4 py-3"
    >
      <div class="max-w-2xl mx-auto flex items-center justify-between">
        <div class="flex items-center gap-2.5">
          <div
            class="w-9 h-9 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-400 flex items-center justify-center text-slate-950 font-black shadow-lg shadow-emerald-900/30"
          >
            <ScanBarcode class="w-5 h-5 text-slate-950" />
          </div>
          <div>
            <h1
              class="font-bold text-base sm:text-lg leading-tight tracking-tight text-white flex items-center gap-1.5"
            >
              MHD Tracker
              <span
                class="text-[10px] font-mono px-1.5 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800/60 font-normal"
                >v1.0</span
              >
            </h1>
            <p class="text-[11px] text-slate-400">
              Home Expiration & Barcode Manager
            </p>
          </div>
        </div>

        <div class="flex items-center gap-2">
          <button
            @click="loadItems"
            :disabled="isLoading"
            class="p-2 rounded-xl bg-slate-800/80 hover:bg-slate-700 text-slate-300 hover:text-white transition active:scale-95"
            title="Refresh"
          >
            <RefreshCw
              :class="['w-4 h-4', isLoading && 'animate-spin text-emerald-400']"
            />
          </button>
        </div>
      </div>
    </header>

    <main class="max-w-2xl mx-auto px-4 py-4 space-y-4">
      <!-- HTTP Mobile Notice Banner -->
      <div
        v-if="showHttpNotice"
        class="p-3 rounded-2xl bg-amber-950/40 border border-amber-600/40 text-amber-200 text-xs flex items-start justify-between gap-3"
      >
        <div class="flex items-start gap-2.5">
          <AlertTriangle class="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
          <div class="space-y-1">
            <p class="font-bold text-amber-300">Connected via HTTP</p>
            <p class="text-[11px] text-slate-300 leading-relaxed">
              Mobile browsers block live video streams on HTTP. You can still
              scan by tapping <strong>Take Photo</strong> in the scanner, or
              launch the server with
              <code
                class="text-amber-300 bg-black/40 px-1 py-0.5 rounded font-mono"
                >make run-ssl</code
              >
              for live camera!
            </p>
          </div>
        </div>
        <button
          @click="showHttpNotice = false"
          class="p-1 rounded text-slate-400 hover:text-white"
        >
          <X class="w-4 h-4" />
        </button>
      </div>

      <!-- Dashboard Stats Cards -->
      <div class="grid grid-cols-3 gap-2.5">
        <!-- Expired -->
        <button
          @click="setQuickFilter('expired')"
          :class="[
            'p-3 rounded-2xl border text-left transition-all active:scale-95',
            activeFilter === 'expired'
              ? 'bg-rose-950/70 border-rose-500 shadow-lg shadow-rose-950/50'
              : 'bg-slate-900/60 border-slate-800/80 hover:border-rose-900/60',
          ]"
        >
          <div
            class="flex items-center justify-between text-xs text-rose-400 font-medium mb-1"
          >
            <span>Expired</span>
            <AlertTriangle class="w-4 h-4" />
          </div>
          <div class="text-2xl font-black text-white font-mono">
            {{ stats.expired_count }}
          </div>
        </button>

        <!-- Expiring Soon -->
        <button
          @click="setQuickFilter('soon')"
          :class="[
            'p-3 rounded-2xl border text-left transition-all active:scale-95',
            activeFilter === 'soon'
              ? 'bg-amber-950/70 border-amber-500 shadow-lg shadow-amber-950/50'
              : 'bg-slate-900/60 border-slate-800/80 hover:border-amber-900/60',
          ]"
        >
          <div
            class="flex items-center justify-between text-xs text-amber-400 font-medium mb-1"
          >
            <span>≤ 3 Days</span>
            <Clock class="w-4 h-4" />
          </div>
          <div class="text-2xl font-black text-white font-mono">
            {{ stats.expiring_soon_count }}
          </div>
        </button>

        <!-- Total Fresh -->
        <button
          @click="setQuickFilter('active')"
          :class="[
            'p-3 rounded-2xl border text-left transition-all active:scale-95',
            activeFilter === 'active'
              ? 'bg-emerald-950/70 border-emerald-500 shadow-lg shadow-emerald-950/50'
              : 'bg-slate-900/60 border-slate-800/80 hover:border-emerald-900/60',
          ]"
        >
          <div
            class="flex items-center justify-between text-xs text-emerald-400 font-medium mb-1"
          >
            <span>In Pantry</span>
            <CheckCircle2 class="w-4 h-4" />
          </div>
          <div class="text-2xl font-black text-white font-mono">
            {{ stats.total_active }}
          </div>
        </button>
      </div>

      <!-- Search & Filters -->
      <div class="space-y-2.5">
        <div class="relative">
          <Search
            class="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500"
          />
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Search groceries, brands, barcodes..."
            class="w-full bg-slate-900/80 border border-slate-800 rounded-xl pl-10 pr-9 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 transition"
          />
          <button
            v-if="searchQuery"
            @click="searchQuery = ''"
            class="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white"
          >
            <X class="w-4 h-4" />
          </button>
        </div>

        <!-- Filter Pills Scroll -->
        <div
          class="flex items-center gap-1.5 overflow-x-auto pb-1 no-scrollbar text-xs"
        >
          <button
            v-for="pill in filterPills"
            :key="pill.id"
            @click="activeFilter = pill.id"
            :class="[
              'px-3 py-1.5 rounded-full whitespace-nowrap transition-all font-medium',
              activeFilter === pill.id
                ? 'bg-emerald-500 text-slate-950 font-bold shadow-md shadow-emerald-950'
                : 'bg-slate-900 text-slate-300 border border-slate-800 hover:bg-slate-800',
            ]"
          >
            {{ pill.label }}
          </button>
        </div>
      </div>

      <!-- Items List -->
      <div
        v-if="isLoading && items.length === 0"
        class="py-12 flex flex-col items-center justify-center text-slate-400"
      >
        <Loader2 class="w-8 h-8 animate-spin text-emerald-400 mb-2" />
        <span class="text-sm">Loading your groceries...</span>
      </div>

      <div
        v-else-if="filteredItems.length === 0"
        class="py-12 px-4 rounded-3xl border border-dashed border-slate-800 text-center bg-slate-900/20"
      >
        <div
          class="w-14 h-14 rounded-2xl bg-slate-800/80 text-slate-400 flex items-center justify-center mx-auto mb-3"
        >
          <ShoppingBag class="w-7 h-7" />
        </div>
        <h3 class="text-base font-semibold text-white mb-1">No items found</h3>
        <p class="text-xs text-slate-400 max-w-xs mx-auto mb-4">
          {{
            searchQuery
              ? "Try adjusting your search query or filters."
              : "Your pantry list is empty. Scan barcodes or MHD dates to start tracking!"
          }}
        </p>
        <button
          @click="openAddModal"
          class="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold transition shadow"
        >
          <Plus class="w-4 h-4" />
          <span>Add First Grocery</span>
        </button>
      </div>

      <div v-else class="space-y-2.5">
        <div
          v-for="item in filteredItems"
          :key="item.id"
          :class="[
            'p-3.5 rounded-2xl border transition-all bg-slate-900/80 hover:bg-slate-900 flex flex-col gap-2.5 relative overflow-hidden',
            getUrgencyBorder(item.days_left, item.status),
          ]"
        >
          <!-- Urgency Accent Indicator Bar -->
          <div
            :class="[
              'absolute left-0 inset-y-0 w-1.5',
              getUrgencyBg(item.days_left, item.status),
            ]"
          ></div>

          <div class="flex items-start justify-between gap-3 pl-1">
            <!-- Product Image / Icon & Info -->
            <div class="flex items-center gap-3 min-w-0 flex-1">
              <div
                class="w-13 h-13 rounded-xl bg-slate-800 border border-slate-700/60 overflow-hidden flex items-center justify-center flex-shrink-0"
              >
                <img
                  v-if="item.image_url"
                  :src="item.image_url"
                  :alt="item.name"
                  class="w-full h-full object-contain p-1"
                  loading="lazy"
                  @error="item.image_url = null"
                />
                <span v-else class="text-2xl">{{
                  getCategoryEmoji(item.category)
                }}</span>
              </div>

              <div class="min-w-0 flex-1">
                <div class="flex items-center gap-1.5 flex-wrap">
                  <h4 class="font-bold text-sm text-white truncate">
                    {{ item.name }}
                  </h4>
                  <span
                    v-if="item.quantity > 1"
                    class="text-xs px-1.5 py-0.2 rounded bg-slate-800 text-slate-300 font-mono font-semibold"
                  >
                    ×{{ item.quantity }}
                  </span>
                </div>

                <div
                  class="flex items-center gap-2 text-xs text-slate-400 mt-0.5 truncate"
                >
                  <span
                    v-if="item.brand"
                    class="truncate font-medium text-slate-300"
                    >{{ item.brand }}</span
                  >
                  <span v-if="item.brand && item.location">•</span>
                  <span class="text-slate-400">{{ item.location }}</span>
                  <span
                    v-if="item.ean"
                    class="text-[10px] font-mono text-slate-500"
                    >#{{ item.ean }}</span
                  >
                </div>
              </div>
            </div>

            <!-- Expiration Badge -->
            <div class="flex flex-col items-end flex-shrink-0">
              <span
                :class="[
                  'text-xs px-2.5 py-1 rounded-full font-bold flex items-center gap-1 whitespace-nowrap',
                  getUrgencyBadgeClass(item.days_left, item.status),
                ]"
              >
                {{ formatDaysLeft(item.days_left, item.status) }}
              </span>
              <span class="text-[10px] text-slate-400 font-mono mt-1">
                MHD: {{ formatDate(item.expiration_date) }}
              </span>
            </div>
          </div>

          <!-- Card Actions Row -->
          <div
            class="flex items-center justify-between pt-2 border-t border-slate-800/80 text-xs pl-1"
          >
            <span
              class="text-[11px] text-slate-400 italic truncate max-w-[180px]"
            >
              {{ item.notes || item.category }}
            </span>

            <div class="flex items-center gap-1.5">
              <button
                v-if="item.status === 'active'"
                @click="consumeItem(item)"
                class="px-2.5 py-1 rounded-lg bg-emerald-950/80 hover:bg-emerald-900 border border-emerald-700/50 text-emerald-300 font-semibold text-xs flex items-center gap-1 transition active:scale-95"
                title="Consume one"
              >
                <Check class="w-3.5 h-3.5 text-emerald-400" />
                <span>Consume</span>
              </button>

              <button
                @click="editItem(item)"
                class="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition"
                title="Edit item"
              >
                <Pencil class="w-3.5 h-3.5" />
              </button>

              <button
                @click="deleteItem(item)"
                class="p-1.5 rounded-lg bg-slate-800 hover:bg-rose-950/80 hover:text-rose-400 text-slate-400 transition"
                title="Delete"
              >
                <Trash2 class="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </main>

    <!-- Bottom Navigation / Floating Action Bar -->
    <nav
      class="fixed bottom-0 inset-x-0 z-30 bg-slate-900/95 backdrop-blur-lg border-t border-slate-800 p-3"
    >
      <div class="max-w-md mx-auto flex items-center justify-around gap-2">
        <!-- Quick Barcode Scan -->
        <button
          @click="startScanWorkflow('barcode')"
          class="flex flex-col items-center gap-1 text-slate-300 hover:text-emerald-400 transition px-3 py-1"
        >
          <Barcode class="w-5 h-5" />
          <span class="text-[10px] font-medium">Scan EAN</span>
        </button>

        <!-- Big Center "Add / Scan" Button -->
        <button
          @click="openAddModal"
          class="flex items-center justify-center gap-2 py-3 px-6 rounded-2xl bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-400 hover:to-teal-400 text-slate-950 font-black text-sm shadow-xl shadow-emerald-950/80 active:scale-95 transition"
        >
          <Plus class="w-5 h-5 stroke-[2.5]" />
          <span>Add Grocery</span>
        </button>

        <!-- Quick MHD Date OCR Scan -->
        <button
          @click="startScanWorkflow('date')"
          class="flex flex-col items-center gap-1 text-slate-300 hover:text-sky-400 transition px-3 py-1"
        >
          <Calendar class="w-5 h-5" />
          <span class="text-[10px] font-medium">Scan MHD</span>
        </button>
      </div>
    </nav>

    <!-- Modals -->
    <!-- 1. Barcode Scanner Modal -->
    <BarcodeScannerModal
      v-if="isBarcodeModalOpen"
      @detected="onBarcodeDetected"
      @close="isBarcodeModalOpen = false"
    />

    <!-- 2. Date OCR Scanner Modal -->
    <DateOcrScannerModal
      v-if="isDateModalOpen"
      @detected="onDateDetected"
      @close="isDateModalOpen = false"
    />

    <!-- 3. Item Form / Review Modal -->
    <ItemFormModal
      v-if="isItemFormOpen"
      ref="itemFormRef"
      :initial-data="editingItemData"
      :locations="locations"
      @save="onSaveItem"
      @close="isItemFormOpen = false"
      @open-barcode-scanner="isBarcodeModalOpen = true"
      @open-date-scanner="isDateModalOpen = true"
    />

    <!-- Toast message -->
    <div
      v-if="toastMessage"
      class="fixed top-5 inset-x-4 max-w-sm mx-auto z-50 bg-emerald-500 text-slate-950 px-4 py-2.5 rounded-xl font-bold text-sm shadow-2xl flex items-center justify-center gap-2 animate-in slide-in-from-top duration-200"
    >
      <CheckCircle2 class="w-4 h-4 text-slate-950" />
      <span>{{ toastMessage }}</span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import {
  ScanBarcode,
  Barcode,
  Calendar,
  Plus,
  Search,
  X,
  RefreshCw,
  AlertTriangle,
  Clock,
  CheckCircle2,
  Trash2,
  Pencil,
  Check,
  ShoppingBag,
  Loader2,
} from "lucide-vue-next";

import BarcodeScannerModal from "./components/BarcodeScannerModal.vue";
import DateOcrScannerModal from "./components/DateOcrScannerModal.vue";
import ItemFormModal from "./components/ItemFormModal.vue";

const items = ref([]);
const isLoading = ref(false);
const searchQuery = ref("");
const activeFilter = ref("active");
const toastMessage = ref("");
const locations = ref([]);
const showHttpNotice = ref(
  !window.isSecureContext &&
    window.location.hostname !== "localhost" &&
    window.location.hostname !== "127.0.0.1",
);

const isBarcodeModalOpen = ref(false);
const isDateModalOpen = ref(false);
const isItemFormOpen = ref(false);
const editingItemData = ref({});
const itemFormRef = ref(null);

const stats = ref({
  total_active: 0,
  expired_count: 0,
  expiring_soon_count: 0,
  ok_count: 0,
});

const filterPills = computed(() => [
  { id: "active", label: "All Pantry" },
  { id: "soon", label: "Expiring Soon (≤3d)" },
  { id: "expired", label: "Expired" },
  ...locations.value.map((loc) => ({ id: loc, label: loc })),
  { id: "consumed", label: "Consumed" },
]);

onMounted(async () => {
  await loadLocations();
  await loadItems();
  await loadStats();
});

async function loadItems() {
  isLoading.value = true;
  try {
    const statusParam =
      activeFilter.value === "consumed"
        ? "consumed"
        : activeFilter.value === "all"
          ? "all"
          : "active";
    const res = await fetch(`/api/items?status=${statusParam}`);
    if (res.ok) {
      items.value = await res.json();
    }
  } catch (err) {
    console.error("Failed to load items:", err);
  } finally {
    isLoading.value = false;
  }
}

async function loadStats() {
  try {
    const res = await fetch("/api/items/stats");
    if (res.ok) {
      stats.value = await res.json();
    }
  } catch (err) {
    console.error("Failed to load stats:", err);
  }
}

async function loadLocations() {
  try {
    const res = await fetch("/api/locations");
    if (res.ok) {
      locations.value = await res.json();
    }
  } catch (err) {
    console.error("Failed to load locations:", err);
  }
}

function setQuickFilter(f) {
  activeFilter.value = f;
  if (f === "consumed") loadItems();
  else if (
    items.value.some((i) => i.status === "consumed") &&
    f !== "consumed"
  ) {
    loadItems();
  }
}

const filteredItems = computed(() => {
  return items.value.filter((item) => {
    // Quick filter check
    if (activeFilter.value === "soon") {
      if (item.days_left < 0 || item.days_left > 3 || item.status !== "active")
        return false;
    } else if (activeFilter.value === "expired") {
      if (item.days_left >= 0 || item.status !== "active") return false;
    } else if (locations.value.includes(activeFilter.value)) {
      // Filter by any location from the DB
      if (item.location !== activeFilter.value) return false;
    }

    // Search query check
    if (!searchQuery.value.trim()) return true;
    const q = searchQuery.value.toLowerCase().trim();
    return (
      (item.name && item.name.toLowerCase().includes(q)) ||
      (item.brand && item.brand.toLowerCase().includes(q)) ||
      (item.ean && item.ean.includes(q)) ||
      (item.category && item.category.toLowerCase().includes(q)) ||
      (item.notes && item.notes.toLowerCase().includes(q))
    );
  });
});

function showToast(msg) {
  toastMessage.value = msg;
  setTimeout(() => {
    toastMessage.value = "";
  }, 2500);
}

function openAddModal() {
  editingItemData.value = {
    quantity: 1,
    category: "Pantry",
    location: locations.value[0] || "",
    expiration_date: new Date(Date.now() + 7 * 86400000)
      .toISOString()
      .split("T")[0],
  };
  isItemFormOpen.value = true;
}

function editItem(item) {
  editingItemData.value = { ...item };
  isItemFormOpen.value = true;
}

function startScanWorkflow(type) {
  if (!isItemFormOpen.value) {
    openAddModal();
  }
  if (type === "barcode") {
    isBarcodeModalOpen.value = true;
  } else if (type === "date") {
    isDateModalOpen.value = true;
  }
}

function onBarcodeDetected(barcode) {
  isBarcodeModalOpen.value = false;
  if (!isItemFormOpen.value) {
    openAddModal();
  }
  setTimeout(() => {
    if (itemFormRef.value) {
      itemFormRef.value.setBarcode(barcode);
    }
  }, 100);
}

function onDateDetected(dateStr) {
  isDateModalOpen.value = false;
  if (!isItemFormOpen.value) {
    openAddModal();
  }
  setTimeout(() => {
    if (itemFormRef.value) {
      itemFormRef.value.setDate(dateStr);
    }
  }, 100);
}

async function onSaveItem(formData) {
  try {
    let res;
    if (formData.id) {
      res = await fetch(`/api/items/${formData.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      });
    } else {
      res = await fetch("/api/items", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      });
    }

    if (res.ok) {
      isItemFormOpen.value = false;
      showToast(formData.id ? "Item updated!" : "Item stored in pantry!");
      await loadItems();
      await loadStats();
    } else {
      const err = await res.json();
      alert("Save failed: " + (err.detail || "Unknown error"));
    }
  } catch (e) {
    console.error("Failed to save item:", e);
    alert("Network error while saving.");
  }
}

async function consumeItem(item) {
  try {
    const res = await fetch(`/api/items/${item.id}/consume`, {
      method: "POST",
    });
    if (res.ok) {
      showToast(`Consumed: ${item.name}`);
      await loadItems();
      await loadStats();
    }
  } catch (e) {
    console.error(e);
  }
}

async function deleteItem(item) {
  if (!confirm(`Delete "${item.name}" from tracker?`)) return;
  try {
    const res = await fetch(`/api/items/${item.id}`, { method: "DELETE" });
    if (res.ok) {
      showToast("Item deleted");
      await loadItems();
      await loadStats();
    }
  } catch (e) {
    console.error(e);
  }
}

function getCategoryEmoji(cat) {
  switch (cat) {
    case "Dairy":
      return "🥛";
    case "Meat":
      return "🥩";
    case "Drinks":
      return "🧃";
    case "Produce":
      return "🥦";
    case "Frozen":
      return "❄️";
    case "Snacks":
      return "🍫";
    default:
      return "🥫";
  }
}

function getUrgencyBorder(days, status) {
  if (status === "consumed") return "border-slate-800 opacity-60";
  if (days < 0) return "border-rose-900/80 bg-rose-950/20";
  if (days <= 3) return "border-amber-900/80 bg-amber-950/20";
  return "border-slate-800/80";
}

function getUrgencyBg(days, status) {
  if (status === "consumed") return "bg-slate-600";
  if (days < 0) return "bg-rose-500";
  if (days <= 3) return "bg-amber-500";
  if (days <= 7) return "bg-yellow-500";
  return "bg-emerald-500";
}

function getUrgencyBadgeClass(days, status) {
  if (status === "consumed") return "bg-slate-800 text-slate-400";
  if (days < 0)
    return "bg-rose-500/20 text-rose-400 border border-rose-500/40 animate-pulse";
  if (days === 0)
    return "bg-rose-500/20 text-rose-300 border border-rose-500/40";
  if (days <= 3)
    return "bg-amber-500/20 text-amber-300 border border-amber-500/40";
  if (days <= 7)
    return "bg-yellow-500/10 text-yellow-300 border border-yellow-500/30";
  return "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20";
}

function formatDaysLeft(days, status) {
  if (status === "consumed") return "Consumed";
  if (days < 0) return `Expired ${Math.abs(days)}d ago`;
  if (days === 0) return "Expires TODAY";
  if (days === 1) return "Expires tomorrow";
  return `Expires in ${days}d`;
}

function formatDate(isoStr) {
  if (!isoStr) return "";
  const parts = isoStr.split("-");
  if (parts.length === 3) {
    return `${parts[2]}.${parts[1]}.${parts[0]}`;
  }
  return isoStr;
}
</script>
