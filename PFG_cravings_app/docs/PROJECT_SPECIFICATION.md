# CODEX MASTER DEVELOPMENT PROMPT
# PROJECT: PFG CRAVINGS
## Complete Full-Stack Staff Refreshment Ordering and Management System

### 1. ROLE AND OBJECTIVE

Act as a senior full-stack software engineer, application architect, UI/UX designer, database engineer, and quality-assurance engineer.

Your assignment is to design, implement, test, document, and prepare a complete, production-ready internal web application named **PFG Cravings**.

**Application tagline:** Order. Pay. Enjoy.

PFG Cravings is a lightweight office refreshment ordering system allowing employees to purchase drinks, snacks, and biscuits through a simple browser interface.

The application must have two interconnected portals:

1. **Buyer Portal:** Staff select products, choose quantities, submit orders, and declare whether payment has been made.
2. **Seller/Admin Portal:** The administrator manages products, prices, staff PINs, incoming orders, payment verification, ordering sessions, reporting, and application configuration.

The system must work across desktop computers, laptops, tablets, and mobile phones connected to the same office local-area network.

The office uses Starlink for internet connectivity. The application must operate over the LAN without depending on an external cloud service or an active internet connection.

This is a real business application, not an illustrative dashboard or static prototype.

All buttons, forms, database transactions, navigation, authentication, calculations, notifications, and PDF downloads must actually work.

Do not deliver mock functionality or incomplete placeholders.

---

### 2. CURRENT WORKSPACE INSTRUCTIONS

You are operating inside the currently opened VS Code project directory.

Follow these rules:

1. Inspect the entire existing directory before modifying anything.
2. Determine whether an application, configuration, or useful source code already exists.
3. Preserve existing useful files and code.
4. If the directory is empty, build the application from scratch.
5. Work directly inside the current directory.
6. Do not create an unnecessary nested project directory.
7. Do not initialize a new Git repository.
8. Do not commit, push, pull, merge, rebase, reset, or change Git branches or remotes.
9. Do not modify files outside the current project directory.
10. Use npm for dependency management.
11. Create clean, modular, maintainable source code.
12. Avoid unnecessarily complex microservices or distributed infrastructure.

Do not ask me to manually create individual source files. Implement the entire application directly.

Do not stop after creating the frontend. Complete the backend, database, security, reporting, configuration, and integration.

---

### 3. PRODUCT IDENTITY AND VISUAL DESIGN

**Application name:** PFG Cravings

**Tagline:** Order. Pay. Enjoy.

**Primary corporate colour:** `#181F63`

Use a professional corporate design based on the following palette:

| Purpose | Colour |
|---|---|
| Primary | #181F63 |
| Main background | #F5F6FA |
| Cards | #FFFFFF |
| Borders | #E2E5ED |
| Primary text | #252B39 |
| Secondary text | #667085 |
| Success | #16803D |
| Warning | #B76A0B |
| Error | #C62828 |

**VERY IMPORTANT DESIGN RESTRICTION:**

Do not use AI-style futuristic gradients.

Avoid:
- Gradient backgrounds, gradient buttons, or gradient cards.
- Neon lighting or glowing borders.
- Glassmorphism.
- Oversized decorative illustrations.
- Unnecessary animations.
- Excessive shadows.
- Futuristic science-fiction dashboards.
- Generic AI-generated-looking website styling.
- Unnecessary emoji icons throughout the interface.

Use:
- Solid corporate colours.
- Clean typography.
- Professional spacing.
- Subtle borders.
- Simple Lucide icons.
- Well-structured forms.
- Clearly labelled buttons.
- Flat professional dashboard cards.
- Consistent alignment.
- Accessible contrast.
- Subtle, purposeful hover and focus states.

Use Inter or another suitable professional sans-serif font.

If an official company logo exists within the project assets, inspect and integrate it appropriately.

Do not invent or recreate an inaccurate company logo. If no suitable logo exists, use a simple text-based PFG Cravings identity with a restrained shopping-basket icon.

Support light and dark themes if practical, with light mode as the default. Both must remain consistent with the corporate colour.

---

### 4. RECOMMENDED TECHNOLOGY STACK

Prioritize lightweight deployment, maintainability, security, and Windows compatibility.

Recommended architecture:

**Frontend**
- React.
- TypeScript.
- Vite.
- Tailwind CSS.
- Lucide React.
- React Router.
- Appropriate lightweight form validation.

**Backend**
- Node.js.
- Express.
- TypeScript.
- Zod validation.
- REST APIs.

**Database**
- SQLite.
- A lightweight SQLite driver such as better-sqlite3.
- Drizzle ORM or a similarly lightweight database abstraction.
- Proper schema migrations.

**PDF generation**
- PDFKit, pdf-lib, or another maintained Node.js PDF generator supporting A4 reports, tables, pagination, and embedded branding.

**Authentication**
- Secure server-side administrator sessions.
- Four-digit staff order PIN verification.
- Modern password/PIN hashing.
- Rate limiting and server-side access controls.

**Live updates**
- Server-Sent Events where appropriate.
- Lightweight polling fallback if necessary.

Avoid cloud databases, Firebase, Supabase, paid APIs, or unnecessary external services.

The finished application should run as a single manageable Node.js server process.

In development, Vite and Express may run separately. In production, the backend should serve the compiled frontend and APIs from one origin.

You may choose more suitable maintained libraries where technically justified, but avoid unnecessary architectural complexity.

---

### 5. APPLICATION ROUTES

The application must expose the following logical routes.

**Buyer Portal**

`/`

Main staff ordering page.

`/order/:reference`

Individual order receipt and status page, protected against unauthorized access.

`/my-orders`

Staff order lookup and history using their assigned name and four-digit PIN.

**Seller Portal**

`/admin/login`

Administrator authentication.

`/admin`

Main seller dashboard.

`/admin/orders`

Order management.

`/admin/products`

Products and pricing management.

`/admin/staff`

Staff registry and PIN management.

`/admin/payments`

Payment verification.

`/admin/reports`

PDF reporting.

`/admin/history`

Historical order records.

`/admin/settings`

Application and ordering configuration.

The admin pages must all be protected using server-side authentication and authorization.

Do not rely on hiding frontend navigation elements as a security mechanism.

Use shared application components where appropriate.

---

### 6. BUYER PORTAL

The buyer portal is intended for ordinary employees and must be extremely simple to use.

The primary user workflow is:

**Select Name → Enter PIN → Select Products → Choose Quantities → Review Total → Declare Payment → Submit Order**

#### 6.1 Main buyer interface

Display:

- PFG Cravings branding.
- A short welcome message.
- Current ordering status.
- Current ordering deadline, if configured.
- Staff selection.
- Four-digit PIN input.
- Product categories.
- Product prices.
- Quantity controls.
- Shopping basket.
- Total payable amount.
- Payment declaration checkbox.
- Optional order notes.
- Submit Order button.

The form must work comfortably on mobile devices.

#### 6.2 Staff selection

Staff must select their name from a searchable dropdown populated from the administrator-managed staff registry.

Do not allow buyers to create arbitrary identities during checkout.

Display only active staff accounts.

#### 6.3 Four-digit staff PIN

Each staff member is assigned a personal four-digit numeric PIN by the administrator.

Requirements:

- Exactly four digits.
- Preserve leading zeros.
- Mask the PIN while typing.
- Support numeric mobile keyboards.
- Validate the PIN on the backend.
- Never include the PIN in a PDF, public API response, server log, or order receipt.
- Reject incorrect PIN submissions.
- Provide clear but non-revealing authentication errors.

The staff identity associated with an order must come from validated backend staff records, not an untrusted name supplied by the browser.

Do not build a heavyweight staff registration or email authentication system.

#### 6.4 Product selection

Organize products into three categories:

1. Drinks.
2. Snacks.
3. Biscuits.

Products must display:
- Product name.
- Price in Nigerian naira.
- Availability.
- Quantity controls.

Provide plus and minus buttons.

Prevent negative quantities.

Allow multiple products in the same order.

Unavailable products must not be selectable.

#### 6.5 Shopping basket

The shopping basket must automatically calculate:

- Selected products.
- Unit prices.
- Quantities.
- Line totals.
- Overall order total.

Use the admin-configured prices.

All financial calculations must be validated on the backend.

Do not trust frontend-supplied prices or totals.

Use integer minor currency units or another safe decimal representation to prevent floating-point financial errors.

#### 6.6 Payment declaration

Provide the checkbox:

**I have made payment.**

If checked, the system records that the buyer claims payment has been made.

If unchecked, the order may still be submitted as unpaid.

Important: Buyer-declared payment must never automatically become administrator-verified payment.

#### 6.7 Order submission

When a valid order is submitted:

1. Verify the staff PIN.
2. Verify the ordering session is open.
3. Verify products and availability.
4. Retrieve authoritative prices from the database.
5. Calculate the order total.
6. Save the order transactionally.
7. Generate a unique order reference.
8. Record the server-side date and time.
9. Set the correct payment status.
10. Return an order confirmation.

Display a receipt containing:
- Order reference.
- Staff name.
- Items ordered.
- Quantities.
- Total amount.
- Payment status.
- Date and time.
- Order fulfilment status.

Prevent accidental duplicate submission from repeated clicks or network retries.

#### 6.8 Editing orders

Allow staff to edit or cancel their own orders before ordering closes, after verifying their name and PIN.

To keep the system simple, prefer one active order per staff member per ordering session, with amendments to that order rather than accidental duplicate orders.

If an order has already been payment-verified, changes affecting its total must require administrator handling or an explicit controlled re-verification process.

Preserve an audit history of meaningful changes.

Once an order is closed or collected, prevent unauthorized modifications.

---

### 7. INITIAL PRODUCT CATALOGUE

Seed the database with the following 19 products.

**DRINKS — 10 products**

1. Pepsi
2. 7Up
3. Teem
4. Fanta
5. Coca-Cola
6. American Cola
7. Maltina
8. Zobo
9. Nutrimilk
10. Table Water

**SNACKS — 4 products**

1. Buns
2. Egg Buns
3. Chin Chin
4. Plantain

**BISCUITS — 5 products**

1. Fab
2. Coaster
3. Top
4. Shortbread
5. Munchit

These are the initial products only.

The administrator must be able to modify the catalogue without changing application source code.

Do not invent actual selling prices.

Products should initially require price configuration before they can become orderable.

---

### 8. SELLER / ADMIN DASHBOARD

The seller dashboard is the application's operational control centre.

It must be password-protected.

The administrator should be able to access it from a desktop, tablet, or mobile phone.

#### 8.1 Dashboard summary

Display:

- Total orders.
- Total items ordered.
- Total expected sales.
- Total verified payments.
- Total outstanding payments.
- Number of pending payments.
- Number of payment declarations awaiting verification.
- Number of completed orders.
- Current ordering status.
- Current date.
- Ordering deadline.

Use clean professional summary cards.

Do not clutter the dashboard with unnecessary analytics.

#### 8.2 Recent orders

Show submitted orders in real time or near real time.

Each order record must display:

- Order reference.
- Staff name.
- Products ordered.
- Quantities.
- Total amount.
- Payment status.
- Fulfilment status.
- Submission date and time.

Allow the admin to open an order and inspect its complete details.

Provide filters for:
- Staff.
- Date.
- Payment status.
- Order status.

Include search and pagination.

Do not implement infinite scrolling.

#### 8.3 Order management

The seller can:

- View orders.
- Edit orders.
- Cancel orders.
- Mark orders as preparing.
- Mark orders as ready.
- Mark orders as collected.
- Review order history.
- Verify payment.
- Reopen orders where authorized.
- Correct genuine mistakes.

Preserve useful audit information.

Cancelled orders must not contribute to active purchasing totals.

---

### 9. PRODUCT AND PRICE MANAGEMENT

Create a complete administrator product-management page.

The admin must be able to:

- View all products.
- Add products.
- Edit product names.
- Assign categories.
- Set unit prices.
- Change existing prices.
- Enable or disable products.
- Mark products out of stock.
- Search products.
- Reorder products for display.
- Remove products safely, preferably using archival or soft deletion where historical orders reference them.

Use NGN currency formatting.

Display prices using the naira symbol: ₦.

Validate all prices on the backend.

Prevent negative prices.

Do not show fake prices in the production application.

**Critical financial requirement:**

Each submitted order item must store the actual product name and unit price at the time of purchase.

If an administrator changes a product's current price, historical orders must retain their original prices.

Example:

Monday: Pepsi costs ₦400.

Tuesday: Admin changes Pepsi to ₦500.

Monday's existing orders must still show ₦400.

Implement this using immutable order-item price snapshots.

---

### 10. STAFF REGISTRY AND FOUR-DIGIT PIN MANAGEMENT

Create a lightweight staff-management page.

The administrator must be able to:

- Register a staff member.
- Assign a four-digit PIN.
- Generate a random four-digit PIN.
- Reset a PIN.
- Deactivate a staff member.
- Reactivate a staff member.
- View staff order history.
- Search staff members.

Store:
- Unique staff ID.
- Staff full name.
- Active/inactive status.
- Secure PIN hash.
- Creation timestamp.
- Last update timestamp.

Do not store plaintext PINs.

If automatically generating PINs, use cryptographically secure randomness rather than Math.random().

Avoid duplicate assigned PINs when provisioning staff, without exposing stored PINs in plaintext.

Display a new or reset PIN only during the authorized issuance process.

Implement sensible protection against repeated incorrect PIN attempts.

For example:
- Five failed attempts within a configured window.
- Temporary cooldown.
- Per-staff throttling.
- Additional origin-based abuse protection where appropriate.
- Admin-controlled recovery.

Avoid permanent lockout that another employee could maliciously trigger.

Use appropriately strong PIN hashing and access controls. A four-digit PIN remains inherently limited, so it must be protected by rate limiting and should not be presented as equivalent to enterprise-grade authentication.

Do not introduce Windows account inspection, PC-name harvesting, device fingerprinting, or invasive device tracking.

The aim is lightweight staff identity verification, not complex enterprise identity management.

---

### 11. PAYMENT MANAGEMENT

Implement three primary payment states:

1. **Unpaid**
2. **Payment Claimed — Awaiting Verification**
3. **Payment Verified**

Buyer declaration and seller verification must remain separate.

The administrator can:

- View unpaid orders.
- View payment claims.
- Confirm payments.
- Correct erroneous payment statuses.
- Record optional payment notes.
- Review payment verification history.

Store the administrator action and verification timestamp.

Only authorized administrators may mark payments as verified.

Do not automatically treat a staff checkbox as proof of payment.

Do not integrate a payment gateway in the initial implementation.

Allow the admin to configure payment instructions, such as:
- Bank name.
- Account name.
- Account number.
- Optional payment description.

These can be shown to staff when configured.

Do not invent banking information.

---

### 12. ORDERING SESSIONS AND DEADLINES

Implement an ordering-session system.

An ordering session represents a specific collection of staff refreshment orders, usually for one workday.

Each session should have:
- Unique session ID.
- Session date.
- Opening time.
- Closing time.
- Current status.
- Optional administrative notes.

The admin must be able to:

- Open ordering.
- Close ordering.
- Reopen ordering.
- Configure a closing time.
- Start a new session.
- View previous sessions.

When a session is closed:

- Staff cannot submit new orders.
- Staff cannot modify existing orders.
- Admin access remains available.
- PDF reports remain available.
- Historical records remain unchanged.

Display the ordering status clearly on the buyer page.

If automatic deadlines are configured, enforce them on the backend using the server time.

Use the **Africa/Lagos** timezone for business dates, session display, and reports.

Store machine timestamps in a consistent format, preferably UTC.

Avoid confusing date boundaries.

---

### 13. PDF REPORT GENERATION

PDF generation is one of the most important features.

Create a prominent, functional button in the seller dashboard:

**Generate PDF Report**

When clicked, the administrator must receive a properly generated, downloadable PDF.

The report must not be a screenshot of the dashboard.

It must be a professionally formatted document generated from authoritative database records.

#### 13.1 PDF branding

Use:
- PFG Cravings.
- Primary colour #181F63.
- Company logo if an authentic asset is available.
- Report title.
- Report date.
- Generation timestamp.
- Clean table formatting.
- Footer with page numbers.

Use A4 page size.

Support automatic page breaks.

Ensure long names, multiple order items, and long tables wrap correctly without clipping.

#### 13.2 Individual order report

Suggested title:

**PFG CRAVINGS — STAFF ORDER REPORT**

Include:

| Column | Content |
|---|---|
| S/N | Serial number |
| Staff Name | Employee name |
| Order | Purchased products |
| Quantity | Quantity per product |
| Amount | Total order amount |
| Payment | Payment status |
| Date / Time | Submission timestamp |

For multiple products, show clearly formatted item details under the corresponding employee.

Include summary information:

- Number of staff who ordered.
- Total active orders.
- Total quantity of items.
- Total expected sales.
- Total verified payments.
- Total unpaid/outstanding amount.
- Number of unverified payment claims.

Use precise labels so payment claims are not misrepresented as verified revenue.

#### 13.3 Consolidated shopping report

Create a second PDF report:

**PFG CRAVINGS — SHOPPING LIST**

Aggregate identical items across all active orders.

Example:

| Product | Total quantity |
|---|---:|
| Pepsi | 8 |
| Buns | 12 |
| Maltina | 5 |
| Fab | 3 |

The shopping list should make it easy for the seller to purchase everything without manually counting individual orders.

Optionally include expected cost totals.

Exclude cancelled orders.

#### 13.4 Report filtering

Allow reports to be generated by:
- Selected ordering session.
- Individual date.
- Date range.

Reports must reflect the selected filters.

Use predictable filenames, for example:

`PFG_Cravings_Orders_2026-10-19.pdf`

`PFG_Cravings_Shopping_List_2026-10-19.pdf`

Create a local archive of generated reports organized by date, if practical.

Ensure reports contain actual database records rather than hardcoded example entries.

---

### 14. ORDER HISTORY

Implement a history page for the seller.

Features:
- View historical ordering sessions.
- Search staff orders.
- Filter by date range.
- Filter by payment status.
- Inspect past orders.
- Export historical PDF reports.
- Use pagination where necessary.

Do not combine all historical orders into an endlessly growing page.

Historical data must remain available after a new daily ordering session begins.

Do not automatically erase previous orders.

---

### 15. NEW ORDER NOTIFICATIONS

Implement lightweight new-order notifications for the admin.

When a staff member submits an order:

- Update the seller dashboard.
- Show a subtle new-order indicator.
- Optionally play a short, discreet notification sound.
- Provide a mute/unmute control.

Keep sounds disabled until the user explicitly enables them, respecting browser autoplay restrictions.

Avoid continuous buzzing or disruptive alert loops.

Do not depend on third-party push-notification services.

Prefer Server-Sent Events or an appropriately lightweight alternative.

If the seller dashboard is not running, orders must still be stored reliably in the database.

---

### 16. RESPONSIVE DESIGN — CRITICAL REQUIREMENT

The entire application must be genuinely responsive.

Do not simply shrink desktop elements to fit mobile screens.

Design mobile-first and adapt layouts according to available space.

Test at minimum:

| Viewport | Expected behaviour |
|---|---|
| 320px | Very small mobile |
| 360px | Small Android phone |
| 375px | Standard mobile |
| 390px | Modern phone |
| 430px | Large phone |
| 768px | Tablet |
| 1024px | Small laptop |
| 1366px | Laptop |
| 1440px | Desktop |
| 1920px | Large desktop |

Requirements:

- No unwanted horizontal scrolling.
- No clipped text.
- No overlapping buttons.
- No overflowing cards.
- No unusable dropdowns.
- No broken modals.
- No hidden submit buttons.
- No excessively small touch targets.
- No dashboard elements extending beyond their containers.
- No misaligned tables.
- No oversized unused whitespace.

Use accessible touch targets of approximately 44px or larger where appropriate.

On mobile:
- Stack content vertically.
- Use comfortable spacing.
- Make the ordering form easy to complete.
- Keep the basket accessible.
- Avoid excessively large sticky elements.
- Convert large desktop tables into readable mobile cards.
- Use suitable dropdowns and numeric keypads.
- Keep navigation minimal.

On desktop:
- Use a professional admin sidebar.
- Display summary cards in a clean grid.
- Use tables where appropriate.
- Provide clear filters and action controls.

The admin sidebar should collapse appropriately on smaller screens.

Use CSS Grid, Flexbox, responsive typography, and appropriate breakpoints.

Test actual interaction, not merely visual appearance.

Support current versions of Chrome, Edge, Firefox, and Safari where feasible.

---

### 17. DATABASE DESIGN

Create a normalized and maintainable SQLite schema.

Suggested entities:

**AdminUsers**
- id
- username
- password_hash
- active
- created_at
- updated_at

**Staff**
- id
- full_name
- pin_hash
- pin_fingerprint where needed for duplicate checking
- active
- created_at
- updated_at

**Categories**
- id
- name
- display_order
- active

**Products**
- id
- category_id
- name
- price
- available
- display_order
- created_at
- updated_at
- archived_at

**OrderingSessions**
- id
- session_date
- opens_at
- closes_at
- status
- notes
- created_at
- updated_at

**Orders**
- id
- order_reference
- session_id
- staff_id
- total_amount
- payment_status
- fulfilment_status
- submitted_at
- updated_at
- cancelled_at
- notes

**OrderItems**
- id
- order_id
- product_id
- product_name_snapshot
- unit_price_snapshot
- quantity
- line_total

**PaymentVerification**
- id
- order_id
- verification_status
- verified_by
- verified_at
- notes

**AppSettings**
- key
- value
- updated_at

**AuditLogs**
- id
- actor_type
- actor_id
- action
- entity_type
- entity_id
- timestamp
- relevant_change_details

Adapt the schema where technically appropriate.

Ensure:
- Primary keys.
- Foreign keys.
- Useful indexes.
- Database constraints.
- Transactions.
- Safe migrations.
- Consistent timestamps.
- Reliable persistence.

Use SQLite WAL mode where appropriate.

Database records must survive application restarts and machine reboots.

Avoid duplicating business logic in frontend and backend code.

---

### 18. LOCAL DATA STORAGE AND BACKUPS

Create a configurable persistent data directory.

Suggested structure:

PFG_CRAVINGS_DATA/
- database/
- backups/
- reports/
- logs/

Organize archived PDF reports into date-based folders when appropriate.

Use proper filesystem access controls.

Exclude database contents, secrets, credentials, and private operational files from version control.

Implement a simple backup process for SQLite.

Backups must be consistent even when the database is active.

Use a SQLite-supported backup mechanism rather than blindly copying a live database file.

Provide:
- Manual backup command.
- Backup storage directory.
- Restore instructions.
- Configurable retention where practical.

Do not delete production records during application updates.

---

### 19. SECURITY REQUIREMENTS

Implement sensible security for a small internal business application.

Requirements:

1. Secure administrator login.
2. Hashed administrator passwords.
3. Hashed four-digit staff PINs.
4. Server-side authorization.
5. Session expiration.
6. HTTP-only authentication cookies.
7. Appropriate SameSite cookie settings.
8. Secure cookies when HTTPS is configured.
9. Rate limiting.
10. Request validation.
11. Safe database queries.
12. Output encoding.
13. Protection against common XSS and injection vulnerabilities.
14. CSRF protection for authenticated state-changing requests where applicable.
15. Avoid exposing private operational records to unauthenticated visitors.
16. Never expose the database directly through the web server.
17. Never store passwords or PINs in frontend source code.
18. Do not expose stack traces or secrets in production responses.

Administrator credentials must be created through a secure first-run setup command or equivalent secure setup process.

Do not ship a hardcoded public default admin password.

Keep configuration secrets in environment variables.

Provide a safe `.env.example` file without actual credentials.

Internal LAN access is not a substitute for authentication.

Avoid collecting unnecessary staff personal information or device identifiers.

---

### 20. LOCAL NETWORK HOSTING

PFG Cravings will initially run on an office Windows PC.

Design the application so it can later be moved to a Raspberry Pi or Linux mini PC without major changes.

Everyone in the office connects through the same Starlink Wi-Fi network.

The application must be accessible using the server's actual local IP address.

For example:

Buyer Portal:

`http://192.168.1.50/`

Seller Portal:

`http://192.168.1.50/admin`

The IP is illustrative and must not be hardcoded.

The desired local hostname is:

**Buyer:** `http://cravings`

**Seller:** `http://cravings/admin`

Important implementation requirements:

- Listen on the appropriate LAN interface.
- Support configurable host and port.
- Support a stable private IP through appropriate network configuration.
- Allow deployment behind a lightweight reverse proxy.
- Do not assume the Starlink router automatically provides custom local DNS.
- Document how to configure local DNS for the hostname `cravings`.
- Explain alternatives where the existing router does not provide suitable DNS or DHCP controls.
- Explain that local device isolation must be disabled or appropriately configured for LAN communication.
- Support optional HTTPS through a correctly configured trusted certificate and reverse proxy.
- Document the security implications of using plain HTTP for authentication.
- Do not pretend that HTTPS is automatically active without valid certificate configuration.

Do not make external internet connectivity a requirement for placing orders once the system is deployed.

Do not expose the application to the public internet by default.

---

### 21. APPLICATION SETTINGS

Implement an admin settings page.

Include:

**General**
- Application name.
- Optional subtitle.
- Timezone.
- Theme preference.

**Ordering**
- Open/close ordering.
- Deadline.
- Default session behaviour.
- Order editing policy.

**Payment**
- Bank name.
- Account name.
- Account number.
- Payment instructions.

**Notifications**
- Enable/disable new-order sounds.
- Notification preferences.

**Administration**
- Change admin password.
- Manage current sessions.
- Backup and restore instructions.

Settings must be persisted in the database or appropriate configuration storage.

Do not require source-code editing for everyday administrative changes.

---

### 22. USER EXPERIENCE AND FEEDBACK

Every significant user action must provide meaningful feedback.

Examples:

- Order successfully submitted.
- Incorrect PIN.
- Too many incorrect PIN attempts.
- Product unavailable.
- Ordering currently closed.
- Product price not configured.
- Order successfully updated.
- Payment successfully verified.
- PDF generated.
- Network connection unavailable.
- Server error.

Use proper loading states.

Prevent repeated submissions.

Handle network failures without misleading success messages.

Do not display fake success notifications when no backend operation has occurred.

Use concise, professional wording.

Do not expose technical stack traces to ordinary users.

---

### 23. PROJECT ARCHITECTURE AND MODULARITY

Organize the project clearly.

Suggested structure:

```text
PFG_CRAVINGS/
├── client/
│   └── src/
│       ├── app/
│       ├── components/
│       ├── pages/
│       │   ├── buyer/
│       │   └── admin/
│       ├── layouts/
│       ├── hooks/
│       ├── services/
│       ├── styles/
│       └── utils/
├── server/
│   └── src/
│       ├── config/
│       ├── database/
│       ├── middleware/
│       ├── modules/
│       │   ├── auth/
│       │   ├── staff/
│       │   ├── products/
│       │   ├── orders/
│       │   ├── payments/
│       │   ├── sessions/
│       │   ├── reports/
│       │   └── settings/
│       ├── services/
│       └── utils/
├── shared/
├── scripts/
├── tests/
├── public/
├── PFG_CRAVINGS_DATA/
├── .env.example
├── .gitignore
├── README.md
└── package.json
```

This is a suggested structure, not a requirement to create unnecessary directories.

Use a practical modular architecture.

Separate:
- UI components.
- API handlers.
- Validation.
- Authentication.
- Business logic.
- Database access.
- PDF generation.
- Configuration.

Avoid oversized monolithic files.

Avoid excessive abstraction that makes a small application harder to maintain.

Prefer clarity and simplicity.

---

### 24. QUALITY ASSURANCE AND AUTOMATED TESTING

This is a complete implementation assignment.

Do not consider the project complete merely because the frontend renders.

Create and execute meaningful tests.

#### 24.1 Staff ordering tests

Verify:
- Valid four-digit PIN is accepted.
- Invalid PIN is rejected.
- Leading-zero PINs work.
- PIN throttling works.
- Inactive staff cannot submit.
- Unavailable products cannot be ordered.
- Unpriced products cannot be ordered.
- Quantities are validated.
- Totals are calculated correctly.
- Payment declaration is saved correctly.
- Orders persist in the database.
- Duplicate submissions are handled safely.
- Ordering cannot proceed after closing.
- Order editing follows the configured rules.

#### 24.2 Admin tests

Verify:
- Admin login.
- Invalid credentials.
- Protected routes.
- Staff creation.
- PIN generation and reset.
- Product creation.
- Product price updates.
- Availability changes.
- Order review.
- Payment verification.
- Session opening and closing.
- Application settings persistence.

#### 24.3 Financial integrity tests

Verify:
- Product price snapshots.
- Accurate order totals.
- Accurate payment summaries.
- Correct outstanding balances.
- Correct cancellation handling.
- No unexpected changes to historical transactions.

#### 24.4 PDF tests

Verify:
- PDF files are generated.
- Files are valid and readable.
- Correct report date.
- Correct staff names.
- Correct quantities.
- Correct amounts.
- Correct payment states.
- Correct aggregated shopping list.
- Correct page breaks for long reports.
- No missing records due to pagination.

#### 24.5 Responsive tests

Use browser automation such as Playwright if practical.

Test:
- Small phones.
- Standard phones.
- Tablets.
- Laptops.
- Desktop screens.

Check for:
- Horizontal overflow.
- Clipped controls.
- Broken dropdowns.
- Modal overflow.
- Unreachable buttons.
- Navigation problems.
- Layout regression.

Test both buyer and admin interfaces.

---

### 25. ERROR HANDLING AND RELIABILITY

Implement centralized error handling.

Requirements:

- Clear API error responses.
- Proper HTTP status codes.
- Useful internal server logs.
- No secret leakage.
- Database operation error handling.
- Transaction rollback.
- Startup configuration validation.
- Graceful application shutdown.
- Clear response when the server or database is unavailable.
- Proper handling of missing or deleted records.
- Predictable behaviour after restart.

Avoid excessive console logging.

Do not silently swallow exceptions.

---

### 26. REQUIRED NPM COMMANDS

Provide practical scripts such as:

```bash
npm install
npm run setup
npm run dev
npm run lint
npm run typecheck
npm test
npm run build
npm start
npm run backup
```

Adapt the actual scripts to the final architecture.

Ensure the documented commands genuinely exist.

Make development startup convenient on Windows 11.

The production startup process must be clearly explained.

If separate client and server development processes are required, coordinate them using npm scripts.

Do not require me to manually start many unrelated services.

---

### 27. DOCUMENTATION

Create a complete and professionally written README.md.

Document:

1. Project introduction.
2. Application features.
3. Technology stack.
4. Directory structure.
5. Prerequisites.
6. Installation.
7. First-time administrator setup.
8. Database initialization.
9. Starting the development server.
10. Creating staff records.
11. Assigning four-digit PINs.
12. Setting product prices.
13. Opening an ordering session.
14. Placing an order.
15. Verifying payment.
16. Generating PDF reports.
17. Starting the production server.
18. LAN access.
19. Configuring the `cravings` hostname.
20. Windows deployment.
21. Raspberry Pi/Linux deployment guidance.
22. Backup and restore.
23. Troubleshooting.
24. Security considerations.

Include actual working commands.

Use professional, naturally written technical documentation.

Avoid unnecessary AI-generated commentary.

---

### 28. IMPLEMENTATION WORKFLOW

Follow this development sequence:

**Phase 1 — Repository inspection and architecture**

Inspect existing files, identify reusable resources, finalize the lightweight full-stack structure, and establish the development environment.

**Phase 2 — Database and backend**

Implement the schema, migrations, product catalogue, staff management, authentication, orders, pricing, payment verification, and ordering-session logic.

**Phase 3 — Buyer portal**

Build the responsive ordering interface with functional product selection, PIN verification, basket calculations, submission, and receipts.

**Phase 4 — Seller portal**

Build the administrator login, dashboard, orders, pricing, staff management, payment verification, history, and settings.

**Phase 5 — PDF reporting**

Implement the dated staff-order report, shopping list, summaries, and download functionality.

**Phase 6 — Integration and reliability**

Connect all frontend and backend modules, implement notifications, validate authorization, and ensure database consistency.

**Phase 7 — Responsive design verification**

Inspect and fix layouts across the specified device sizes.

**Phase 8 — Testing and documentation**

Run linting, TypeScript checks, automated tests, production builds, and appropriate end-to-end checks.

**Phase 9 — Final production review**

Remove temporary debugging code, check configuration, validate deployment instructions, and resolve identified defects.

Complete each phase rather than leaving disconnected unfinished modules.

---

### 29. FINAL ACCEPTANCE CRITERIA

The application is only complete when all the following conditions are satisfied:

- [ ] PFG Cravings branding is implemented.
- [ ] The primary colour is #181F63.
- [ ] No futuristic or AI-style gradients exist.
- [ ] Buyer portal is fully functional.
- [ ] Seller/admin portal is fully functional.
- [ ] All 19 initial products are present.
- [ ] Admin can set and update product prices.
- [ ] Staff can select their names.
- [ ] Four-digit PIN verification works.
- [ ] Staff can select multiple products.
- [ ] Quantity controls work.
- [ ] Basket totals are correct.
- [ ] Buyer payment declaration works.
- [ ] Admin payment verification works.
- [ ] Orders are saved persistently.
- [ ] New orders appear in the admin dashboard.
- [ ] Ordering sessions can be opened and closed.
- [ ] Staff cannot submit after closing.
- [ ] Historical records retain their original prices.
- [ ] Order history works.
- [ ] PDF order reports download correctly.
- [ ] Consolidated shopping-list PDFs work.
- [ ] PDFs include names, orders, payment status, and dates.
- [ ] Admin authentication is protected.
- [ ] Staff PINs are never stored in plaintext.
- [ ] Important server-side validations work.
- [ ] Application is responsive across mobile and desktop.
- [ ] Local-network access works using the configured server address.
- [ ] The `cravings` local hostname setup is documented accurately.
- [ ] Application data survives restarts.
- [ ] Backup and restore procedures are documented and tested where feasible.
- [ ] No hardcoded production credentials exist.
- [ ] No fake orders or hardcoded sales numbers appear in production.
- [ ] All critical buttons perform actual operations.
- [ ] Linting passes.
- [ ] TypeScript checks pass.
- [ ] Automated tests pass.
- [ ] Production build succeeds.
- [ ] README documentation is complete.

Do not report a check as passed unless it was actually executed successfully.

If a particular environment-dependent check cannot be performed, document the limitation precisely and provide the necessary verification command.

---

### 30. IMPORTANT DEVELOPMENT PRINCIPLES

This project is intended for everyday use by staff in a real office.

It must remain:

- Lightweight.
- Reliable.
- Secure enough for the intended environment.
- Easy to deploy.
- Easy to operate.
- Easy to maintain.
- Professional in appearance.
- Fully responsive.
- Fast on ordinary mobile devices.
- Independent of unnecessary cloud infrastructure.

Do not add unnecessary enterprise-level complexity.

Do not introduce:
- AI integrations.
- Chatbots.
- Cloud authentication providers.
- Payment gateway dependencies.
- Windows username harvesting.
- Computer-name tracking.
- Device fingerprinting.
- Complex microservices.
- Unnecessary analytics platforms.
- Decorative animations.
- Unrelated features.

Use sound engineering judgment when making small implementation decisions not explicitly covered by this specification.

Preserve all critical business requirements.

### 31. FINAL INSTRUCTION

**Implement the complete PFG Cravings application directly in the currently opened VS Code directory.**

I expect a complete working system, not a frontend demonstration.

The buyer portal, admin dashboard, backend, SQLite database, staff PINs, product pricing, payment verification, reports, and local-network deployment must be integrated into one functional application.

Run the available validation commands and correct implementation errors before finishing.

At the end, provide:

1. A concise summary of what was implemented.
2. The final project architecture.
3. The installation commands.
4. The administrator setup procedure.
5. The commands to run the application in development.
6. The commands to build and run it in production.
7. The buyer and admin URLs.
8. Instructions for local network access.
9. Instructions for configuring the `cravings` hostname.
10. The exact status of linting, tests, and production build.
11. Any genuine remaining limitations.

Do not perform Git operations.

Do not leave critical functionality as TODO comments or fake implementation placeholders.

**Begin by inspecting the current directory, then proceed with the complete implementation and verification.**