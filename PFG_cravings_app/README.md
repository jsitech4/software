# PFG Cravings

**Order. Pay. Enjoy.** — An internal office refreshment ordering application.

PFG Cravings contains a real buyer portal, a protected seller dashboard, a local SQLite database and on-demand A4 PDF exports. It is designed for phones, tablets and desktops, and runs on the office LAN without relying on a cloud provider.

## First start (Windows 11)

Install **Python 3.11 or newer**, then open PowerShell or Git Bash in this extracted folder. The simplest way is to double-click **`START_WINDOWS.bat`**. That installs Python dependencies (internet needed the first time) and starts the local server. For the initial administrator setup, leave the server running and open a second terminal.

Manual method (PowerShell):

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m app.manage setup-admin
.\.venv\Scripts\python.exe run.py
```

Create your own administrator username and password (12+ characters). **There is no default administrator password.**

Open:

- **Buyer:** http://localhost:8000/
- **Seller:** http://localhost:8000/admin
- **Seller login:** http://localhost:8000/admin/login

From another device on the same accessible Wi-Fi, replace `localhost` with the IP address of the Windows PC running the application, e.g. `http://192.168.1.50:8000/`. That example is not your actual IP. Run `ipconfig` on Windows to identify the server's IPv4 address. Allow inbound TCP 8000 in Windows Defender Firewall **only on your trusted Private network profile**, and ensure Wi-Fi client isolation is not preventing LAN traffic. **The hosting PC must remain powered on.**

### Initial configuration

1. Open `/admin/login` and sign in with the credentials created by `setup-admin`.
2. In **Products & prices**, set actual selling prices for the preloaded 19 items. Products have no invented prices.
3. In **Staff & PINs**, register staff names and privately issue a four-digit PIN per employee (leading zeros are supported). PINs are displayed _once_ at creation/reset.
4. In **Settings**, add payment details if desired. These are shown to buyers, not automatically charged.
5. In **Dashboard**, click **New session** to open ordering. You can optionally set a closing deadline. There is no open session before administrator setup.
6. Staff visit `/`, select their names and enter their PINs at the buyer sign-in screen. The catalogue opens only after the server verifies the PIN; they can then choose refreshments and submit.
7. The seller reviews the submitted orders in **Orders/Payments**, confirms payments separately and marks the collection status.
8. Download **Staff orders PDF** or **Shopping list PDF** in **Reports**. Both use actual persisted orders.

### Staff order editing

A staff member can open **My Orders**, verify their PIN, view receipts and edit or cancel an eligible submitted order before ordering closes. A previously verified payment cannot be modified by staff without the seller handling it. Only one active order per employee per session is allowed.

### Prices, payments and historical integrity

The server recalculates all amounts using current server-side prices and stores **snapshots** of product name and price on every order item. Changing today's price does not alter yesterday's order. Payment states are `unpaid`, `claimed`, and `verified`; the staff checkbox never automatically verifies payment. Purchase-list exports exclude cancelled orders.

### Staff debts and payment reconciliation

Outstanding debt is calculated from active order totals less administrator-confirmed payment allocations; it is never stored as an editable running balance. It therefore carries across sessions without duplication. A buyer selecting **I have made payment** creates only a payment claim and does not reduce their debt.

After a staff member verifies their PIN, they can check their own balance on the buyer portal. The seller uses **Staff Debts** to review balances, see orders and payment history, record full or partial payments, settle an account, and download individual statements. Payments are allocated to the oldest outstanding orders first unless the seller explicitly chooses one order. Each confirmed payment is transactionally recorded in a ledger with its allocations and administrator audit entry.

Cancelled orders are excluded from debt calculations. Orders with confirmed payment allocations cannot be cancelled or reduced below their confirmed payment total; this prevents orphaned payments and negative balances.

## Official production domain

The official public deployment URLs are:

- **Buyer:** `https://pfgcravings.com`
- **Seller:** `https://pfgcravings.com/admin`

The application does not register domains, create DNS records, provision a hosting account, or issue certificates by itself. Production uses the exact `PFG_PUBLIC_ORIGIN` value to generate receipt links and browser-visible application URLs; it must be `https://pfgcravings.com`. The deployment process and an example Caddy TLS reverse-proxy configuration are in [`deploy/README.md`](deploy/README.md).

### Local Starlink address

The local `.env` can enable the optional mDNS alias `http://pfgcravings.local` with `PFG_MDNS_ENABLED=1`. It is advertised only while the PFG Cravings server is running and works only on the same local network for devices that support mDNS. It does not change the Windows computer name (`pfg-electrical.local`) and does not expose the application to the internet. Keep `http://192.168.1.104` as the direct local fallback; reserve that address in the Starlink router if possible.

### Start automatically after Windows boots

On the server PC, run `scripts\install-autostart.ps1` once. It requests Windows administrator approval, creates the **PFG Cravings Server** startup task, starts it as the local system account after boot, and retries up to three times if the process exits unexpectedly. The task starts the application hidden and keeps the local `.env` configuration, including port 80 and the optional mDNS alias.

Keep the Python service on `127.0.0.1:8000` behind the HTTPS proxy. Do not expose port 8000 directly. For local testing, leave `PFG_ENV=development` and `PFG_PUBLIC_ORIGIN` blank; `http://localhost:8000` remains supported.

## Configuration

Create `.env` from `.env.example` as needed. Values:

```text
PFG_HOST=0.0.0.0
PFG_PORT=8000
PFG_DATA_DIR=./PFG_CRAVINGS_DATA
PFG_ENV=development
PFG_SECURE_COOKIES=0
PFG_PUBLIC_ORIGIN=
PFG_CORS_ORIGINS=
```

For production, copy [`deploy/.env.production.example`](deploy/.env.production.example) to the server-side `.env`. Its fail-closed settings require the canonical HTTPS origin, exact CORS allowlist, and secure cookies. When deploying behind a proxy, keep the application on a protected loopback listener. Never port-forward the application port to the public internet.

## Database and backups

Local persistent data is automatically created in `PFG_CRAVINGS_DATA/` and is intentionally excluded from Git/ZIP packaging. It contains the SQLite database, a server-side secret, backups, and dated PDF reports. **Keep the server secret together with the database when migrating**; PIN and password verification depends on it. Do not publish these files.

```powershell
.\.venv\Scripts\python.exe -m app.manage check
.\.venv\Scripts\python.exe -m app.manage backup
```

The backup command uses the native SQLite backup API, producing a consistent timestamped database copy. To restore: **stop the server first**, make a safety copy of the data directory, replace `PFG_CRAVINGS_DATA/database/cravings.sqlite3` with the selected backup, preserve `PFG_CRAVINGS_DATA/.server_key`, and restart. Move/clear stale `-wal` and `-shm` files only while the server is stopped and the backup is restored correctly. Practice restoration on a test machine before relying on it.

## Linux / Raspberry Pi

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m app.manage setup-admin
.venv/bin/python run.py
```

Use a system service (e.g. systemd) with an appropriate dedicated unprivileged account and persistent data path for unattended operation. Linux packages for Python and SQLite may be needed depending on the distribution.

## Source layout

```text
app/
  config.py       environment configuration and local server secret
  security.py     PIN/password hashing and login throttling
  db.py           SQLite schema, migrations/bootstrap and catalogue
  main.py         buyer/admin REST endpoints, transactions, authorization
  reports.py      A4 PDF generation and archival
  manage.py       administrator setup, safe backups and integrity checks
web/
  index.html      application shell
  assets/app.js   mobile-first buyer and seller portals
  assets/styles.css responsive flat corporate UI
  assets/icon.svg  neutral PFG Cravings favicon (not an official company logo)
tests/            isolated API workflow checks
run.py            configurable single-server launcher
START_WINDOWS.bat Windows convenience launcher
deploy/          production environment, Caddy, DNS and TLS guidance
```

### Implementation choice

This initial release intentionally uses **FastAPI + SQLite + ReportLab + dependency-free browser JavaScript/CSS** instead of the originally suggested React/Vite/Node stack. The choice avoids a frontend build toolchain and makes starting the application from a ZIP substantially easier. All frontend/server source is editable; migration to React/TypeScript can be performed later in Codex if required. It is a live full-stack application, not a static mock-up.

## Validation

```bash
python -m compileall -q app
node --check web/assets/app.js      # only if Node is installed
python -m pip install -r requirements-dev.txt
python -m pytest tests -q
```

The integration tests cover the core order-to-PDF flow, login protection, staff PIN (including leading zero), prices and snapshots, idempotency, payment verification, controlled seller amendments, and closed sessions. Browser rendering was additionally inspected at 320px, 390px, 768px and 1440px viewport widths. The database and test admin accounts generated during testing are not included in the release archive.

## Important limitations and next improvements

- This is a **useful working v1 starter**, not a third-party-penetration-tested financial system. Perform security and real-device LAN acceptance testing before actual staff payments are recorded.
- Four-digit PINs are inherently weak against a determined attacker with network or device access. They discourage casual misuse only. Keep the office network trusted and restrict admin access.
- Seller-side order amendments are retained as immutable before-images. If an amendment changes a verified total, the seller must explicitly return the payment to “claimed” and verify it again.
- The app has the text PFG Cravings identity, not an invented PROFORCE GALAXIES corporate logo. Add your genuine company asset if licensed for this internal use.
- New-order notifications are dashboard-based polling (16 seconds), with a manually enabled sound toggle; browser tabs must stay open for sounds.
- The optional short hostname and trusted HTTPS are **network administration tasks**, not automatically configured by installing the ZIP.
- If you require simultaneous users at a large scale, daily order export retention policies, or externally accessible mobile payments, plan a separate deployment/security review.

## Further development with Codex

Open the extracted folder in VS Code and ask Codex to inspect the current code first. Preserve persistent database structure and the existing logic, implement refinements in small tested increments, and avoid Git operations unless you ask for them. The original project specification is included under `docs/PROJECT_SPECIFICATION.md` for context.
