## Critical Instructions
You MUST read GUARDRAILS.md at the start of every task. Treat all constraints as immutable rules.

---

# MHD Tracker - Agent Guidance & Developer Handbook

Welcome, Agent. This repository contains **MHD Tracker**, a self-hosted, mobile-first web application designed to track grocery expiration dates (*Mindesthaltbarkeitsdatum*) using mobile camera scanning for EAN barcodes and OCR date recognition.

---

## 🏗️ Architecture & Technology Stack

| Layer | Technology | Details |
|---|---|---|
| **Language & Environment** | Python 3.10+ | Managed strictly with **`uv`** |
| **Backend Framework** | **FastAPI** + **Uvicorn** | REST API + unified SPA static file serving |
| **Database** | **SQLite** + **SQLAlchemy** | Local relational storage (`mhd_tracker.db`) |
| **Data Validation** | **Pydantic v2** | Request & response schemas in [`app/schemas.py`](file:///Users/volki/Dev/mhd-tracker/app/schemas.py) |
| **External Lookup** | **Open Food Facts API** | Product name, brand, image lookup with local caching in `ProductCache` |
| **Frontend Framework** | **Vue 3** (Composition API) | SFCs in [`frontend/src/`](file:///Users/volki/Dev/mhd-tracker/frontend/src) |
| **Styling & Icons** | **Tailwind CSS v4** + **Lucide** | Dark-mode, mobile touch-friendly UI |
| **Barcode Scanning** | **Html5Qrcode** | Barcode detector (EAN-13, EAN-8, UPC, QR) + camera controls |
| **MHD Date OCR** | **Tesseract.js** | Client-side OCR with contrast pre-processing and date regex parser |
| **Build & Task Runner** | **GNU Make** | Single source of truth via [`Makefile`](file:///Users/volki/Dev/mhd-tracker/Makefile) |

---

## 📁 Repository Directory Structure

```text
mhd-tracker/
├── AGENTS.md                  # This handbook & agent instructions
├── GUARDRAILS.md               # Mandatory, immutable project constraints
├── Makefile                   # Build, run, test, and utility goals
├── README.md                  # Project user documentation
├── pyproject.toml             # uv Python configuration & dependencies
├── uv.lock                    # Locked Python dependency tree
├── main.py                    # Entrypoint script for uvicorn
├── seed_demo.py               # Sample data generator for SQLite
├── app/
│   ├── database.py            # SQLite engine, sessionmaker, get_db dependency
│   ├── models.py              # SQLAlchemy DB models (Item, ProductCache)
│   ├── schemas.py             # Pydantic schemas (ItemCreate, ItemResponse, etc.)
│   ├── main.py                # FastAPI app instance, CORS, SPA static mounting
│   ├── routers/
│   │   ├── items.py           # CRUD endpoints and stats calculation
│   │   └── lookup.py          # Barcode lookup (Cache + Open Food Facts)
│   └── services/
│       └── openfoodfacts.py   # HTTP client fetching product info
├── frontend/
│   ├── package.json           # Frontend dependencies & scripts
│   ├── vite.config.js         # Vite configuration with Vue and Tailwind v4 plugins
│   ├── index.html             # Mobile web app viewport meta tags & root div
│   └── src/
│       ├── main.js            # Vue app bootstrap
│       ├── style.css          # Tailwind CSS root imports
│       ├── App.vue            # Main reactive dashboard, urgency badges, filter tabs
│       ├── utils/
│       │   └── dateParser.js  # Heuristic date parsing (European, text months, MM/YY) & beep sound
│       └── components/
│           ├── BarcodeScannerModal.vue # Live camera & photo barcode detection
│           ├── DateOcrScannerModal.vue # Live viewfinder & OCR date stamp parsing
│           └── ItemFormModal.vue       # Unified form to review, edit, and save items
└── tests/
    └── test_api.py            # Automated pytest integration & unit tests
```

---

## 🛠️ Essential Development Workflows

All tasks should be executed through the [`Makefile`](file:///Users/volki/Dev/mhd-tracker/Makefile):

| Task | Command | Notes |
|---|---|---|
| **Run Tests** | `make test` | Runs `uv run pytest` (must pass 100%) |
| **Build Frontend** | `make build` | Builds Vite assets into `frontend/dist/` |
| **Run App (HTTP)** | `make run` | Runs `app.main:app` on port 8000 (serves API + SPA) |
| **Run App (HTTPS)** | `make run-ssl` | Generates SSL cert & starts HTTPS server (required for mobile live camera) |
| **Backend Dev** | `make dev-backend` | Starts FastAPI with auto-reload |
| **Frontend Dev** | `make dev-frontend` | Starts Vite HMR server on port 5173 |
| **Seed Database** | `make seed` | Populates sample grocery items |
| **Clean Artifacts** | `make clean` | Cleans `frontend/dist`, `__pycache__`, `.pytest_cache` |
| **Reset Database** | `make clean-db` | Removes `mhd_tracker.db` |

---

## 🧠 Rules for Modifying the Codebase

### 1. Backend (`app/`)
- **Use async where appropriate:** Heavy I/O (like calling Open Food Facts via `httpx`) must be asynchronous. Database endpoints using synchronous SQLAlchemy sessions run with standard def endpoints (FastAPI automatically handles them in a worker thread pool).
- **Timezone Awareness:** Use `datetime.now(timezone.utc)` instead of deprecated `datetime.utcnow()`.
- **Field Constraints:** `quantity` can be `0` when an item is consumed. Ensure Pydantic models use `ge=0`.
- **Open Food Facts Caching:** Always check and update `ProductCache` when looking up or creating items with an EAN barcode to minimize external network requests.

### 2. Frontend (`frontend/src/`)
- **Keep it Mobile-First:** Use touch-friendly padding, minimum 44px tap targets, and safe area insets.
- **Always preserve dual scanning modes:**
  1. Live WebRTC video (active in secure contexts / HTTPS).
  2. Native camera snapshot (`<input type="file" accept="image/*" capture="environment">`) as a fallback that works anywhere.
- **Audio & Haptic Feedback:** Call `playBeepSound()` from `frontend/src/utils/dateParser.js` when a barcode or date is recognized.
- **Component Communication:** Use Vue 3 `defineEmits` (`detected`, `close`, `save`) and `defineExpose` where parents trigger child actions.

### 3. Testing (`tests/`)
- In [`tests/test_api.py`](file:///Users/volki/Dev/mhd-tracker/tests/test_api.py), SQLite in-memory databases must use `poolclass=StaticPool` so that connections share the same memory instance.
- Always run `make test` after backend alterations.

---

## ⚠️ Known Pitfalls & Solutions

1. **Mobile Camera Not Opening:**
   - **Reason:** Insecure context on plain HTTP (`http://192.168.x.x:8000`).
   - **Solution:** Instruct user to run `make run-ssl` or use the "Take Photo" button.
2. **`Html5Qrcode.getCameras()` Crash:**
   - **Reason:** Calling `getCameras()` before permission is granted fails on iOS.
   - **Solution:** Pass `{ facingMode: 'environment' }` directly to `html5QrCode.start()`.
3. **Pydantic Validation on Consumed Items:**
   - **Reason:** Setting quantity to 0 failed when `ge=1` was configured.
   - **Solution:** Use `ge=0` in [`app/schemas.py`](file:///Users/volki/Dev/mhd-tracker/app/schemas.py).
