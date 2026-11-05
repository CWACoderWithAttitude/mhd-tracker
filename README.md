# MHD Tracker (Mindesthaltbarkeitsdatum Tracker)

A modern, responsive, mobile-first web application to track household grocery inventory, scan EAN barcodes, and recognize expiration dates (MHD) directly using your smartphone's camera.

---

## 🌟 Key Features

1. **EAN Barcode Scanning & Auto-Lookup**
   - Live camera barcode scanner (EAN-13, EAN-8, UPC, Code 128, QR).
   - Integrated with **Open Food Facts API** & local cache: instantly fetches product title, brand, category, and packaging photos upon barcode detection.
   - Camera switcher, flashlight support, and image upload fallback.

2. **MHD / Expiration Date OCR Scanner**
   - High-contrast camera reticle tailored for food packaging date stamps.
   - Client-side OCR powered by **Tesseract.js** (no cloud latency, runs privately on device).
   - Smart parser supporting European (`DD.MM.YYYY`, `DD/MM/YY`), text-month (`15 MAI 2025`), and month/year (`MM/YYYY`) date formats.

3. **Reactive Mobile Interface**
   - Mobile-first PWA-ready design optimized for touch and handheld scanning.
   - Urgency color-coding:
     - 🔴 **Expired** (with days elapsed counter)
     - 🟠 **Expiring Soon** (≤ 3 days countdown)
     - 🟢 **Fresh**
   - Quick one-tap "Consume" button to decrement quantity or mark item consumed.
   - Filter by location (Fridge, Pantry, Freezer, Spice Rack) or category.

4. **Fast Backend with `uv`, FastAPI & SQLite**
   - Modern Python project management with `uv`.
   - SQLite persistence with SQLAlchemy models and Pydantic schemas.
   - Static single-page application bundling: FastAPI serves both the API and frontend simultaneously.

---

## 🚀 Quick Start (via Makefile)

A [`Makefile`](file:///Users/volki/Dev/mhd-tracker/Makefile) is provided with all common targets:

| Command | Action |
|---|---|
| `make help` | Display available targets |
| `make install` | Install backend (`uv`) and frontend (`npm`) dependencies |
| `make build` | Compile Vue 3 frontend assets to `frontend/dist` |
| `make run` | Build frontend and run HTTP server on `http://0.0.0.0:8000` |
| `make run-ssl` | **Recommended for mobile:** Run HTTPS server on `https://0.0.0.0:8000` (enables live camera) |
| `make dev-backend` | Run FastAPI with auto-reload on `http://localhost:8000` |
| `make dev-frontend` | Run Vite frontend development server with HMR on `http://localhost:5173` |
| `make test` | Run pytest test suite |
| `make seed` | Populate SQLite database with sample groceries |
| `make clean` | Clean build artifacts and temporary cache files |
| `make clean-db` | Reset SQLite database |

### Running on Mobile Devices

Mobile browsers (iOS Safari, Android Chrome, and Firefox) strictly enforce **Secure Contexts (HTTPS)** for live video camera streams:

1. **Option A: Live Video Scanning (Recommended)**
   Launch with SSL:
   ```bash
   make run-ssl
   ```
   Open `https://<your-ip>:8000` on your iPhone or Xiaomi device. Accept the self-signed certificate warning once, and live camera scanning will work directly.

2. **Option B: Native Camera Snapshot (Works over plain HTTP or HTTPS)**
   If running over plain HTTP (`make run`), tap the **Take Photo** button inside the scanner modal. This triggers your phone's native camera app directly to capture and decode the barcode or date stamp without needing HTTPS.


---

## 🧪 Demo Data

To populate your pantry with sample groceries (with varied expiration dates):

```bash
uv run python seed_demo.py
```

---

## 🛠️ Project Structure

```text
mhd-tracker/
├── app/
│   ├── database.py             # SQLite connection and session maker
│   ├── models.py               # SQLAlchemy models (Item, ProductCache)
│   ├── schemas.py              # Pydantic schemas for validation
│   ├── services/
│   │   └── openfoodfacts.py    # Open Food Facts API lookup integration
│   ├── routers/
│   │   ├── items.py            # CRUD operations and dashboard stats
│   │   └── lookup.py           # Barcode lookup endpoint
│   └── main.py                 # FastAPI application and SPA static serving
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── BarcodeScannerModal.vue  # Camera barcode scanning
│   │   │   ├── DateOcrScannerModal.vue  # Camera OCR expiration date scanning
│   │   │   └── ItemFormModal.vue        # Item review, edit, and storage form
│   │   ├── utils/
│   │   │   └── dateParser.js            # European date normalization & audio feedback
│   │   ├── App.vue                      # Reactive dashboard & pantry list
│   │   └── main.js
│   ├── package.json
│   └── vite.config.js
├── main.py                     # App entrypoint (runs uvicorn)
├── pyproject.toml              # uv dependencies
└── seed_demo.py                # Sample grocery items generator
```

---

## 💻 Frontend Development (Optional)

If you wish to edit frontend components with hot-module replacement (HMR):

```bash
cd frontend
npm run dev
```

And to build production assets into `frontend/dist`:

```bash
npm run build
```
