# Project Guardrails & Immutable Constraints

> **CRITICAL NOTICE FOR AI AGENTS & DEVELOPERS:**  
> All rules in this document are **mandatory and immutable**. Do not bypass, disable, or violate these constraints under any circumstances.

---

## 0. # Guardrails: Secret Management

1. **Credentials:**
   - **CRITICAL:** Do NOT write, hardcode, or commit plain-text API keys, passwords, bearer tokens, or secret credentials under any circumstances.
   - **Enforcement:** Always use environment variables (`.env`) or a secure keychain system.
   - **Action Blocked:** If code changes introduce string literals resembling keys (e.g., `sk_live_...`, `AIzaSy...`), reject the file modification and alert the user.

## 1. Tooling & Package Management

1. **Python / Backend:**
   - **MUST** use `uv` exclusively for all Python operations: `uv run`, `uv add`, `uv sync`.
   - **NEVER** run bare `pip install` or create alternative virtual environments manually.
   - Keep dependencies locked via `uv.lock`.
   - Target Python version: `Python >= 3.10`.

2. **Frontend:**
   - All frontend code resides inside [`frontend/`](file:///Users/volki/Dev/mhd-tracker/frontend).
   - Use `npm` inside [`frontend/`](file:///Users/volki/Dev/mhd-tracker/frontend) for JavaScript package management.
   - **NEVER** mix frontend dependencies with root project root `package.json`.

3. **Makefile as Single Source of Truth:**
   - Standard actions (`install`, `build`, `run`, `run-ssl`, `test`, `seed`, `clean`) **MUST** be maintained in the [`Makefile`](file:///Users/volki/Dev/mhd-tracker/Makefile).
   - Whenever introducing new scripts or major workflows, add corresponding Makefile targets.

---

## 2. Architecture & File Boundaries

1. **Unified Static Serving:**
   - FastAPI in [`app/main.py`](file:///Users/volki/Dev/mhd-tracker/app/main.py) serves the compiled frontend assets from `frontend/dist`.
   - Any modifications to the frontend **must compile cleanly** with `make build` (`npm run build`) so that `make run` and `make run-ssl` work out of the box.

2. **Clean Backend Modularization:**
   - [`app/models.py`](file:///Users/volki/Dev/mhd-tracker/app/models.py): Database schema and SQLAlchemy ORM models.
   - [`app/schemas.py`](file:///Users/volki/Dev/mhd-tracker/app/schemas.py): Pydantic request/response validation.
   - [`app/routers/`](file:///Users/volki/Dev/mhd-tracker/app/routers/): API route definitions. Business/lookup logic belongs in services or router handlers.
   - [`app/services/`](file:///Users/volki/Dev/mhd-tracker/app/services/): External APIs (Open Food Facts) and caching logic.

3. **Single Database Source:**
   - SQLite file: `mhd_tracker.db` at project root.
   - **NEVER** commit `.db` or `.sqlite3` files to git (enforced in `.gitignore`).

---

## 3. Mobile Camera & Web Security Guardrails

1. **Secure Context & HTTPS Awareness:**
   - Mobile browsers (iOS Safari/WebKit, Android Chrome, Android Firefox) **strictly require HTTPS** (`window.isSecureContext === true`) for live camera streams (`navigator.mediaDevices.getUserMedia`).
   - Plain HTTP over local IP (e.g. `http://192.168.x.x:8000`) completely disables WebRTC cameras on mobile devices.

2. **Mandatory Native Camera Fallback:**
   - The native camera snapshot input:
     ```html
     <input type="file" accept="image/*" capture="environment">
     ```
     **MUST ALWAYS be preserved** in both [`BarcodeScannerModal.vue`](file:///Users/volki/Dev/mhd-tracker/frontend/src/components/BarcodeScannerModal.vue) and [`DateOcrScannerModal.vue`](file:///Users/volki/Dev/mhd-tracker/frontend/src/components/DateOcrScannerModal.vue).
   - This ensures full camera scanning functionality even when running over plain HTTP without HTTPS certificates.

3. **Live Camera Startup Rule:**
   - Do **NOT** call `Html5Qrcode.getCameras()` before starting the scanner; on mobile browsers, this causes permission exceptions. Pass `{ facingMode: 'environment' }` directly to `html5QrCode.start()`.

4. **Secrets & Certificates:**
   - Self-signed SSL certificates belong in `certs/` and **MUST NEVER** be committed to version control.

---

## 4. Quality & Testing Standards

1. **Automated Testing:**
   - All tests live in [`tests/test_api.py`](file:///Users/volki/Dev/mhd-tracker/tests/test_api.py).
   - Run tests using `make test` (`uv run pytest`).
   - Every pull request or modification **must maintain 100% passing tests**.
   - For in-memory SQLite testing, always use `StaticPool` (`from sqlalchemy.pool import StaticPool`) to share memory across threads.

2. **Data Consistency & Validation:**
   - Expiration dates must always normalize to ISO `YYYY-MM-DD`.
   - Quantity values must allow `0` (indicating consumed items) without validation errors.
   - All OCR and barcode operations must provide user confirmation before persisting to the database.
