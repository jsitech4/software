/* PFG Cravings | Dependency-free, LAN-ready application client. */
const app = document.querySelector("#app");
const N = "/api";
const state = {
  bootstrap: null,
  admin: null,
  adminData: null,
  adminProducts: [],
  adminEdit: null,
  buyer: null,
  debt: null,
  route: "",
  cat: "Drinks",
  cart: {},
  staffId: "",
  pin: "",
  notes: "",
  paid: false,
  editing: null,
  receipt: null,
  myOrders: [],
  issued: null,
  filters: { q: "", status: "", start: "", end: "", page: 1 },
  report: {
    start: "",
    end: "",
    session_id: "",
    payment_status: "",
    fulfilment_status: "active",
  },
  menuOpen: false,
  sound: false,
  knownOrders: null,
};
const escapeHTML = (v = "") =>
  String(v ?? "").replace(
    /[&<>"']/g,
    (m) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        m
      ],
  );
const money = (k) =>
  k == null
    ? "Price not set"
    : "₦" +
      (Number(k) / 100).toLocaleString("en-NG", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      });
const fmtDate = (s) =>
  s
    ? new Intl.DateTimeFormat("en-NG", {
        timeZone: "Africa/Lagos",
        dateStyle: "medium",
        timeStyle: "short",
      }).format(new Date(s))
    : "—";
const icon = (name, size = 18) => {
  let paths = {
    basket: '<path d="m5 12 4-8m10 8-4-8M3 12h18l-2 9H5l-2-9ZM9 15v3m6-3v3"/>',
    bag: '<path d="M4 8h16l-1 13H5L4 8Zm5 0V6a3 3 0 0 1 6 0v2"/>',
    grid: '<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>',
    box: '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 10h18M10 10v10"/>',
    users:
      '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2m12-9a4 4 0 1 0 0-8m8 17v-2a4 4 0 0 0-3-3.87"/><circle cx="9" cy="7" r="4"/>',
    credit:
      '<rect x="2" y="5" width="20" height="14" rx="2"/><path d="M2 10h20"/>',
    file: '<path d="M6 3h9l4 4v14H6zM14 3v5h5M9 13h7M9 17h7"/>',
    clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    settings:
      '<path d="M12 2l2 2 3-.1.7 3 2.5 1.6-1.2 2.8 1.2 2.8-2.5 1.6-.7 3-3-.1-2 2-2-2-3 .1-.7-3-2.5-1.6 1.2-2.8-1.2-2.8L6.3 7l.7-3 3 .1 2-2z"/><circle cx="12" cy="12" r="3"/>',
    logout: '<path d="M10 17l5-5-5-5m5 5H3m8-9h8v18h-8"/>',
    check: '<path d="m4 12 5 5L20 6"/>',
    plus: '<path d="M12 5v14M5 12h14"/>',
    minus: '<path d="M5 12h14"/>',
    arrow: '<path d="M5 12h14m-6-6 6 6-6 6"/>',
    menu: '<path d="M4 6h16M4 12h16M4 18h16"/>',
    download: '<path d="M12 3v13m-5-5 5 5 5-5M4 17v4h16v-4"/>',
    shield:
      '<path d="m12 2 9 4v6c0 5-4 8-9 10-5-2-9-5-9-10V6l9-4zM9 12l2 2 4-4"/>',
    history: '<path d="M3 12a9 9 0 1 0 3-7M3 3v5h5m4-1v5l4 2"/>',
    search: '<circle cx="10.5" cy="10.5" r="7"/><path d="m16 16 5 5"/>',
    bell: '<path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4"/>',
    close: '<path d="M5 5l14 14M19 5 5 19"/>',
  };
  return `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${paths[name] || paths.box}</svg>`;
};
const brand = () =>
  `<a class="brand" href="/" data-link><span class="brand-mark">${icon("basket", 23)}</span><span><h1>PFG Cravings</h1><p>ORDER. PAY. ENJOY.</p></span></a>`;
const badge = (text, variant = "") =>
  `<span class="badge ${variant}">${escapeHTML(text)}</span>`;
const payBadge = (p) =>
  badge(
    { unpaid: "Unpaid", claimed: "Payment claimed", verified: "Verified" }[p] ||
      p,
    { unpaid: "warn", claimed: "navy", verified: "success" }[p] || "",
  );
const orderBadge = (p) =>
  badge(
    p.charAt(0).toUpperCase() + p.slice(1),
    { collected: "success", cancelled: "danger", ready: "navy" }[p] || "",
  );
function toast(message, error = false) {
  const d = document.createElement("div");
  d.className = "toast-item" + (error ? " error" : "");
  d.textContent = message;
  document.querySelector("#toast").appendChild(d);
  setTimeout(() => d.remove(), 4700);
}
async function api(path, { method = "GET", body } = {}) {
  const headers = {};
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (state.admin && method !== "GET")
    headers["X-CSRF-Token"] = state.admin.csrf;
  let response;
  try {
    response = await fetch(N + path, {
      method,
      headers,
      credentials: "same-origin",
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch {
    throw Error(
      "Cannot reach the server. Check the office network connection.",
    );
  }
  const result = await response
    .json()
    .catch(() => ({ detail: "Unexpected server response." }));
  if (!response.ok) {
    if (
      response.status === 401 &&
      path.startsWith("/admin/") &&
      path !== "/admin/login"
    ) {
      state.admin = null;
    }
    const detail = Array.isArray(result.detail)
      ? result.detail.map((x) => x.msg).join("; ")
      : result.detail || "Request could not be completed.";
    throw Error(detail);
  }
  return result;
}
async function fetchBootstrap() {
  state.bootstrap = await api("/public/bootstrap");
}
function navigate(path) {
  if (location.pathname === "/my-orders" && path !== "/my-orders")
    state.myOrders = [];
  history.pushState({}, "", path);
  route();
}
function topbar() {
  return `<header class="topbar"><div class="topbar-inner">${brand()}<nav class="navlinks"><a href="/" data-link>Order</a><a href="/my-orders" data-link>My Orders</a>${state.buyer && !location.pathname.startsWith("/admin") ? `<button type="button" data-action="buyer-signout">${icon("logout", 15)} Logout</button>` : ""}</nav></div></header>`;
}
function buyerShell(html) {
  app.innerHTML = `${topbar()}<main class="container">${html}</main><footer class="footer">PFG Cravings · An internal office ordering service</footer>`;
}
function buyerAccess() {
  buyerShell(
    `<div class="auth-wrap"><form class="surface auth-card" data-form="buyer-access">${brand()}<h2>Buyer sign in</h2><p>Enter your registered staff name and personal PIN to open today's refreshments.</p><div class="form-stack"><div class="field"><label for="buyer-login-staff">Staff name</label>${publicStaffSelect("buyer-login-staff")}</div><div class="field"><label for="buyer-login-pin">4-digit PIN</label><input id="buyer-login-pin" name="pin" type="password" inputmode="numeric" pattern="[0-9]{4}" minlength="4" maxlength="4" autocomplete="current-password" placeholder="••••" required></div><button class="btn wide" type="submit">Open ordering portal ${icon("arrow", 17)}</button></div><div class="notice" style="margin-top:20px">Your staff PIN is verified before products and prices are shown.</div></form></div>`,
  );
}
function titleHead(overline, title, desc, right = "") {
  return `<div class="page-head"><div><div class="eyebrow">${overline}</div><h1 class="page-title">${title}</h1><p class="lead">${desc}</p></div>${right}</div>`;
}
function publicStaffSelect(id = "staff-select") {
  let list = state.bootstrap?.staff || [];
  return `<select id="${id}" ${id === "buyer-login-staff" ? 'name="staff_id"' : ""} required><option value="">Choose your name</option>${list.map((s) => `<option value="${s.id}" ${String(s.id) === String(state.staffId) ? "selected" : ""}>${escapeHTML(s.full_name)}</option>`).join("")}</select>`;
}
function pinInput(id = "staff-pin") {
  return `<input type="password" id="${id}" inputmode="numeric" pattern="[0-9]{4}" minlength="4" maxlength="4" autocomplete="off" placeholder="••••" value="${escapeHTML(state.pin)}" required>`;
}
function cartItems() {
  return (state.bootstrap?.products || []).filter(
    (p) => Number(state.cart[p.id]) > 0,
  );
}
function productOptions() {
  return (state.bootstrap?.products || []).filter(
    (p) => p.category === state.cat,
  );
}
function catalogueCategories() {
  return (state.bootstrap?.categories || []).map((category) => category.name);
}
function basket() {
  const sel = cartItems(),
    sum = sel.reduce(
      (n, p) => n + Number(p.price_kobo || 0) * state.cart[p.id],
      0,
    ),
    count = sel.reduce((n, p) => n + state.cart[p.id], 0),
    ready =
      sel.length && sel.every((x) => x.price_kobo !== null && x.available);
  let payment = state.bootstrap.payment;
  return `<section class="surface basket-panel"><div class="section-head"><div><h2>Your basket</h2><p class="sub">${count} item${count === 1 ? "" : "s"} selected</p></div>${icon("bag", 22)}</div>${sel.length ? `<div class="basket-list">${sel.map((p) => `<div class="basket-line"><div><div class="name">${escapeHTML(p.name)} × ${state.cart[p.id]}</div><div class="meta">${money(p.price_kobo)} each</div></div><b>${money(p.price_kobo * state.cart[p.id])}</b></div>`).join("")}</div>` : `<div class="blank"><div class="circle">${icon("basket")}</div>Your basket is empty.<br><span class="tiny">Add refreshments from the catalogue.</span></div>`}<div class="total-box"><span class="strong">Order total</span><strong>${money(sum)}</strong></div>${payment?.bank_name || payment?.account_number ? `<div class="payment-box"><div class="strong">Payment details</div>${payment.bank_name ? `<div>${escapeHTML(payment.bank_name)}</div>` : ""}${payment.account_name ? `<div>${escapeHTML(payment.account_name)}</div>` : ""}${payment.account_number ? `<div class="strong">${escapeHTML(payment.account_number)}</div>` : ""}${payment.payment_instructions ? `<div>${escapeHTML(payment.payment_instructions)}</div>` : ""}</div>` : ""}<label class="check-row"><input id="paid-claim" type="checkbox" ${state.paid ? "checked" : ""}><span><b>I have made payment</b><br><span class="muted small">The seller will confirm receipt separately.</span></span></label><button class="btn wide" data-action="submit-order" ${!ready || state.bootstrap?.session.status !== "open" ? "disabled" : ""}>${state.editing ? "Update My Order" : "Submit Order"} ${icon("arrow", 17)}</button>${state.editing ? `<button class="btn secondary wide" style="margin-top:8px" data-action="cancel-edit">Cancel editing</button>` : ""}<p class="help" style="text-align:center;margin-top:11px">You can order before paying. The seller verifies all payments.</p></section>`;
}
function buyer() {
  if (!state.bootstrap)
    return buyerShell('<div class="loading-screen">Loading menu…</div>');
  let s = state.bootstrap.session;
  let status = badge(
    s.status === "open" ? "Ordering open" : "Ordering closed",
    s.status === "open" ? "success" : "warn",
  );
  let ready = (state.bootstrap.products || []).filter(
    (x) => x.price_kobo !== null && x.available,
  ).length;
  buyerShell(
    `${titleHead("Staff refreshment ordering", state.editing ? "Edit your order" : "What are you craving today?", "", status)}<div class="order-layout"><div class="panel-stack"><div class="status-row"><span class="small"><b>${s.status === "open" ? "Orders are being accepted" : "Orders are currently closed"}</b>${s.closes_at ? ` · Closes ${fmtDate(s.closes_at)}` : ""}</span><span class="small muted">${ready} products available</span></div><section class="surface"><div class="section-head"><div><h2>1. Your details</h2><p class="sub">Select your registered name and enter your personal PIN.</p></div>${icon("shield", 22)}</div><div class="grid-2"><div class="field"><label for="staff-select">Staff name</label>${publicStaffSelect()}</div><div class="field"><label for="staff-pin">4-digit PIN</label>${pinInput()}</div></div></section><section class="surface"><div class="section-head"><div><h2>2. Choose refreshments</h2><p class="sub">Pick items and adjust quantities.</p></div>${icon("basket", 22)}</div><div class="tabs" role="tablist">${catalogueCategories()
      .map(
        (c) =>
          `<button class="tab ${state.cat === c ? "active" : ""}" role="tab" aria-selected="${state.cat === c}" data-action="category" data-category="${c}">${c}</button>`,
      )
      .join(
        "",
      )}</div><div class="spacer-sm"></div><div class="products-grid">${productOptions()
      .map(
        (p) =>
          `<div class="product-card"><div><h3>${escapeHTML(p.name)}</h3><p>${p.price_kobo === null ? "Price pending" : money(p.price_kobo)}</p>${!p.available ? '<span class="tiny danger-text">Unavailable</span>' : ""}</div><div class="qty-controls"><button type="button" data-action="qty" data-id="${p.id}" data-delta="-1" ${!state.cart[p.id] ? "disabled" : ""} aria-label="Remove ${escapeHTML(p.name)}">−</button><strong>${state.cart[p.id] || 0}</strong><button type="button" data-action="qty" data-id="${p.id}" data-delta="1" ${p.price_kobo === null || !p.available || s.status !== "open" ? "disabled" : ""} aria-label="Add ${escapeHTML(p.name)}">+</button></div></div>`,
      )
      .join(
        "",
      )}</div></section><section class="surface"><div class="section-head"><div><h2>3. Additional note</h2><p class="sub">Optional: Special instructions for the seller.</p></div></div><div class="field"><label for="order-notes">Order note</label><textarea id="order-notes" maxlength="400" placeholder="For example: Cold Pepsi, please">${escapeHTML(state.notes)}</textarea></div></section></div><aside>${basket()}</aside></div>`,
  );
}
function identityForm(formId, buttonText) {
  return `<form data-form="${formId}" class="surface" style="max-width:600px"><div class="grid-2"><div class="field"><label>Staff name</label>${publicStaffSelect(formId + "-staff")}</div><div class="field"><label>Personal 4-digit PIN</label>${pinInput(formId + "-pin")}</div></div><div class="spacer-sm"></div><button class="btn" type="submit">${buttonText} ${icon("arrow", 16)}</button></form>`;
}
function historyBuyer() {
  buyerShell(
    `${titleHead("Order records", "My orders", "View your existing orders and their payment or collection status.")}<div class="stack">${identityForm("my-orders", "Find my orders")}${state.myOrders.length ? `<section class="surface flat"><div style="padding:17px"><h2>Order history</h2></div>${state.myOrders.map((o) => `<div class="order-card"><div class="order-card-top"><b>${escapeHTML(o.reference)}</b>${payBadge(o.payment_status)}</div><p class="small muted">${fmtDate(o.created_at)} · ${orderBadge(o.fulfilment_status)}</p><div class="order-card-items">${o.items.map((i) => `${escapeHTML(i.name_snapshot)} ×${i.quantity}`).join(" · ")}</div><div class="action-row" style="justify-content:space-between;margin-top:10px"><b>${money(o.total_kobo)}</b><div><button class="btn secondary sm" data-action="view-order" data-reference="${escapeHTML(o.reference)}">${o.document_type === "receipt" ? "Receipt" : "Invoice"}</button> ${o.fulfilment_status === "submitted" && o.payment_status !== "verified" ? `<button class="btn sm" data-action="edit-order" data-reference="${escapeHTML(o.reference)}">Edit</button><button class="btn danger sm" data-action="cancel-buyer-order" data-reference="${escapeHTML(o.reference)}">Cancel</button>` : ""}</div></div></div>`).join("")}</section>` : ""}</div>`,
  );
}
function orderReceipt() {
  const o = state.receipt;
  let requested = location.pathname.split("/").pop();
  if (!o || o.reference !== requested) {
    buyerShell(
      `${titleHead("Order document", "Check your order", "Enter your staff PIN to access your invoice or receipt.")}<div class="stack">${identityForm("receipt", "View order document")}</div>`,
    );
    return;
  }
  const isReceipt = o.document_type === "receipt";
  buyerShell(
    `<div class="receipt"><div class="page-head"><div><div class="eyebrow">${isReceipt ? "Payment receipt" : "Order invoice"}</div><h1 class="page-title">${isReceipt ? "Payment received." : "Your order is recorded."}</h1><p class="lead">${isReceipt ? "Your full payment has been confirmed by the seller." : "This is an invoice, not a payment receipt. It becomes a receipt once your full payment is confirmed."}</p></div>${orderBadge(o.fulfilment_status)}</div><div class="surface"><div class="receipt-header"><div><div class="muted tiny">${isReceipt ? "RECEIPT" : "INVOICE"} REFERENCE</div><div class="receipt-ref">${escapeHTML(o.reference)}</div><div class="small muted">${fmtDate(o.created_at)}</div></div><div>${payBadge(o.payment_status)}</div></div><div class="notice ${isReceipt ? "success" : "warn"}">${isReceipt ? "Full payment confirmed — this document is your receipt." : "Payment is still pending or incomplete"}</div><hr class="divider"><div class="basket-line"><b>Staff name</b><span>${escapeHTML(o.staff_name)}</span></div><hr class="divider"><h2 style="font-size:16px;margin-bottom:13px">Order items</h2>${o.items.map((i) => `<div class="basket-line" style="margin-bottom:12px"><div><b>${escapeHTML(i.name_snapshot)}</b><div class="meta">${i.quantity} × ${money(i.unit_kobo)}</div></div><b>${money(i.line_kobo)}</b></div>`).join("")}<div class="total-box"><b>Total amount</b><strong>${money(o.total_kobo)}</strong></div>${o.notes ? `<p class="note-box">${escapeHTML(o.notes)}</p>` : ""}</div><div class="action-row" style="margin-top:20px"><a class="btn" href="/my-orders" data-link>My orders</a><a class="btn secondary" href="/" data-link>Back to catalogue</a></div></div>`,
  );
}
const NAV = [
  ["/admin", "grid", "Dashboard"],
  ["/admin/orders", "bag", "Orders"],
  ["/admin/products", "box", "Products & prices"],
  ["/admin/staff", "users", "Staff & PINs"],
  ["/admin/payments", "credit", "Payments"],
  ["/admin/debts", "credit", "Staff Debts"],
  ["/admin/reports", "file", "Reports"],
  ["/admin/history", "history", "History"],
  ["/admin/settings", "settings", "Settings"],
];
function adminShell(
  body,
  title = "Dashboard",
  desc = "Manage incoming refreshment orders.",
) {
  let route = location.pathname;
  app.innerHTML = `<div class="admin-app ${state.menuOpen ? "menu-open" : ""}"><aside class="sidebar"><div class="brand">${brand()}</div><nav class="sidebar-nav">${NAV.map(([href, ico, text]) => `<a href="${href}" data-link class="${href === route ? "active" : ""}">${icon(ico, 18)}<span>${text}</span></a>`).join("")}</nav><div class="sidebar-bottom"><div class="small muted label">Signed in as <b>${escapeHTML(state.admin?.username || "Admin")}</b></div><button data-action="logout" class="btn secondary sm wide" style="margin-top:12px">${icon("logout", 16)} <span class="label">Sign out</span></button></div></aside><div class="admin-main"><header class="admin-head"><div class="action-row"><button data-action="toggle-menu" class="btn secondary icon-btn mobile-menu" aria-label="Toggle navigation">${icon("menu", 18)}</button><strong style="color:var(--navy);font-size:13px">PFG Cravings <span class="muted">/ Seller</span></strong></div><div class="action-row"><a href="/" data-link class="admin-top-link">Buyer portal ↗</a>${badge("Admin", "navy")}</div></header><main class="admin-content">${titleHead("Seller workspace", escapeHTML(title), escapeHTML(desc))}${body}</main></div></div>`;
}
function login() {
  app.innerHTML = `${topbar()}<main class="auth-wrap"><form class="surface auth-card" data-form="login">${brand()}<h2>Seller sign in</h2><p>Sign in to manage products, orders, payments and reports.</p><div class="form-stack"><div class="field"><label for="username">Administrator username</label><input required id="username" name="username" autocomplete="username"></div><div class="field"><label for="password">Password</label><input required id="password" name="password" type="password" autocomplete="current-password"></div><button class="btn wide" type="submit">Sign in securely ${icon("arrow", 17)}</button></div><div class="notice" style="margin-top:20px">First time? Run <b>python -m app.manage setup-admin</b> on the server.</div></form></main>`;
}
function summaryMetric(label, value, sub = "") {
  return `<div class="surface metric"><div class="metric-label">${label}</div><div class="metric-number">${value}</div><div class="metric-sub">${sub}</div></div>`;
}
function orderBlock(o) {
  return `<div class="order-card"><div class="order-card-top"><div><b>${escapeHTML(o.staff_name)}</b> <span class="muted tiny">${escapeHTML(o.reference)}</span></div><div class="action-row">${payBadge(o.payment_status)} ${orderBadge(o.fulfilment_status)}</div></div><div class="order-card-items">${o.items.map((i) => `${escapeHTML(i.name_snapshot)} ×${i.quantity}`).join(" · ")}</div><div class="action-row" style="margin-top:12px;justify-content:space-between"><b>${money(o.total_kobo)}</b><span class="tiny muted">${fmtDate(o.created_at)}</span></div></div>`;
}
function dashboard() {
  const d = state.adminData || { stats: {}, session: {}, recent: [] };
  const s = d.stats || {};
  adminShell(
    `<div class="metric-grid">${summaryMetric("Total orders", s.orders || 0, "Current ordering session")}${summaryMetric("Expected sales", money(s.expected_kobo || 0), "Before payment verification")}${summaryMetric("Verified payments", money(s.verified_kobo || 0), "Confirmed by seller")}${summaryMetric("Outstanding", money((s.expected_kobo || 0) - (s.verified_kobo || 0)), "Not yet verified")}</div><div class="split section-gap"><section class="surface flat"><div class="section-head" style="padding:18px 18px 0"><div><h2>Latest orders</h2><p class="sub">Refreshes automatically while this page is open.</p></div><a href="/admin/orders" data-link class="link">View all</a></div>${d.recent?.length ? d.recent.slice(0, 8).map(orderBlock).join("") : '<div class="blank">No orders yet. Submitted orders will appear here.</div>'}</section><div class="stack"><section class="surface"><div class="section-head"><h2>Ordering control</h2>${badge(d.session?.status === "open" ? "Open" : "Closed", d.session?.status === "open" ? "success" : "warn")}</div><p class="small muted">Session date: ${escapeHTML(d.session?.date || "Not configured")}<br>${d.session?.closes_at ? "Closes: " + fmtDate(d.session.closes_at) : "No automatic deadline set"}</p><div class="action-row">${d.session?.status === "open" ? `<button class="btn secondary" data-action="session-close" data-id="${d.session.id}">Close ordering</button>` : d.session?.id ? `<button class="btn" data-action="session-open" data-id="${d.session.id}">Reopen session</button>` : ""}<button class="btn ${d.session?.status === "open" ? "secondary" : ""}" data-action="session-new">New session</button></div><p class="help">A new session closes the previous one. Ordering is blocked until products are priced and staff have PINs.</p>${d.session?.status === "open" ? `<form data-form="session-deadline" class="form-stack" style="margin-top:12px"><div class="field"><label>Optional deadline (local time)</label><input type="datetime-local" name="deadline"></div><button type="submit" class="btn secondary sm">Set closing deadline</button></form>` : ""}</section><section class="surface"><div class="section-head"><h2>Quick actions</h2>${icon("arrow")}</div><div class="stack" style="gap:9px"><a class="btn secondary wide" data-link href="/admin/products">${icon("box")} Set product prices</a><a class="btn secondary wide" data-link href="/admin/staff">${icon("users")} Register staff</a><a class="btn wide" data-link href="/admin/reports">${icon("download")} Generate PDF reports</a><button class="btn secondary wide" data-action="sound-toggle">${icon("bell")} ${state.sound ? "Mute order sound" : "Enable order sound"}</button></div></section><section class="surface"><h2 style="font-size:16px">Payment overview</h2><div class="spacer-sm"></div><div class="basket-line"><span>Payment claims</span><b>${s.claimed || 0}</b></div><div class="basket-line" style="margin-top:9px"><span>Unpaid orders</span><b>${s.unpaid || 0}</b></div><div class="basket-line" style="margin-top:9px"><span>Collected</span><b>${s.collected || 0}</b></div></section></div></div>`,
    "Dashboard",
    "Today’s ordering activity, at a glance.",
  );
}
function filtering() {
  let f = state.filters;
  return `<form class="filterbar" data-form="filter-orders"><div class="field grow"><label>Search</label><input name="q" placeholder="Name or reference" value="${escapeHTML(f.q)}"></div><div class="field"><label>From</label><input type="date" name="start" value="${escapeHTML(f.start)}"></div><div class="field"><label>To</label><input type="date" name="end" value="${escapeHTML(f.end)}"></div><div class="field"><label>Status</label><select name="status"><option value="">All statuses</option>${["unpaid", "claimed", "verified", "submitted", "preparing", "ready", "collected", "cancelled"].map((v) => `<option value="${v}" ${f.status === v ? "selected" : ""}>${v}</option>`).join("")}</select></div><button class="btn" type="submit">${icon("search", 15)} Filter</button></form>`;
}
function orderActions(o) {
  return `<div class="action-row"><button class="btn secondary sm" data-action="edit-admin-order" data-id="${o.id}" ${["cancelled", "collected"].includes(o.fulfilment_status) ? "disabled" : ""}>Edit</button><select class="select-sm" aria-label="Payment for ${escapeHTML(o.staff_name)}" data-payment="${o.id}">${["unpaid", "claimed", "verified"].map((s) => `<option ${o.payment_status === s ? "selected" : ""} value="${s}">${s === "claimed" ? "Claimed" : s === "verified" ? "Verified" : "Unpaid"}</option>`).join("")}</select><select class="select-sm" aria-label="Order status for ${escapeHTML(o.staff_name)}" data-fulfilment="${o.id}">${["submitted", "preparing", "ready", "collected", "cancelled"].map((s) => `<option ${o.fulfilment_status === s ? "selected" : ""} value="${s}">${s}</option>`).join("")}</select></div>`;
}
async function openAdminEditor(order) {
  state.adminEdit = order;
  const productData = await api("/admin/products");
  state.adminProducts = productData.products;
  const quantities = Object.fromEntries(
    order.items.map((i) => [i.product_id, i.quantity]),
  );
  const choices = state.adminProducts.filter(
    (p) => p.available && p.price_kobo !== null,
  );
  app.insertAdjacentHTML(
    "beforeend",
    `<div class="modal-backdrop" data-admin-editor role="presentation"><section class="modal surface" role="dialog" aria-modal="true" aria-labelledby="edit-order-title"><div class="section-head"><div><h2 id="edit-order-title">Amend order</h2><p class="sub">${escapeHTML(order.staff_name)} · ${escapeHTML(order.reference)}</p></div><button class="btn ghost icon-btn" data-action="close-admin-edit" aria-label="Close">${icon("close")}</button></div><form data-form="admin-order-edit" data-id="${order.id}" class="form-stack"><div class="notice">Prices are recalculated from the current catalogue. If a verified payment total changes, return it to payment claims for re-verification. The former item and price snapshot is retained.</div><div class="editor-products">${choices.map((p) => `<label class="editor-product"><span><b>${escapeHTML(p.name)}</b><small>${escapeHTML(p.category)} · ${money(p.price_kobo)}</small></span><input name="item_${p.id}" type="number" inputmode="numeric" min="0" max="99" value="${quantities[p.id] || 0}" aria-label="Quantity for ${escapeHTML(p.name)}"></label>`).join("")}</div><div class="field"><label>Order notes</label><textarea name="notes">${escapeHTML(order.notes || "")}</textarea></div><div class="field"><label>Reason for amendment (optional)</label><input name="reason" maxlength="300" placeholder="For example: corrected after staff request"></div>${order.payment_status === "verified" ? `<label class="check-row"><input name="reverify_payment" type="checkbox"><span><b>Return payment to “claimed” if the total changes</b><br><span class="muted small">The seller must verify the amended amount again.</span></span></label>` : ""}<div class="action-row"><button type="submit" class="btn">Save amendment</button><button type="button" data-action="close-admin-edit" class="btn secondary">Cancel</button></div></form></section></div>`,
  );
}
function ordersView(
  title = "Orders",
  desc = "Manage all submitted orders and their fulfilment status.",
) {
  let d = state.adminData || { rows: [], total: 0, pages: 1, page: 1 };
  adminShell(
    `<section class="surface flat">${filtering()}<div class="table-wrap"><table><thead><tr><th>Staff / Reference</th><th>Items</th><th>Total</th><th>Payment</th><th>Fulfilment</th><th>Actions</th><th>Date</th></tr></thead><tbody>${d.rows?.length ? d.rows.map((o) => `<tr><td><b>${escapeHTML(o.staff_name)}</b><div class="tiny muted">${escapeHTML(o.reference)}</div></td><td>${o.items.map((i) => `${escapeHTML(i.name_snapshot)} ×${i.quantity}`).join("<br>")}</td><td class="nowrap"><b>${money(o.total_kobo)}</b></td><td>${payBadge(o.payment_status)}</td><td>${orderBadge(o.fulfilment_status)}</td><td>${orderActions(o)}</td><td class="nowrap">${fmtDate(o.created_at)}</td></tr>`).join("") : '<tr><td colspan="7" class="blank">No matching orders.</td></tr>'}</tbody></table></div><div class="order-mobile" style="display:none">${d.rows?.length ? d.rows.map((o) => `${orderBlock(o)}<div style="padding:0 15px 15px">${orderActions(o)}</div>`).join("") : '<div class="blank">No matching orders.</div>'}</div><div class="pagination"><span class="small muted">${d.total} records · Page ${d.page} of ${d.pages}</span><button class="btn secondary sm" data-action="page" data-delta="-1" ${d.page <= 1 ? "disabled" : ""}>Previous</button><button class="btn secondary sm" data-action="page" data-delta="1" ${d.page >= d.pages ? "disabled" : ""}>Next</button></div></section>`,
    title,
    desc,
  );
}
function productsView() {
  let data = state.adminData || { products: [], categories: [] };
  let byCat = Object.groupBy
    ? Object.groupBy(data.products, (p) => p.category)
    : data.products.reduce((m, p) => {
        (m[p.category] ??= []).push(p);
        return m;
      }, {});
  adminShell(
    `<section class="surface"><div class="section-head"><div><h2>Add product</h2><p class="sub">All price changes affect new orders only.</p></div>${icon("plus")}</div><form data-form="add-product" class="grid-3"><div class="field"><label>Product name</label><input name="name" required placeholder="New snack or drink"></div><div class="field"><label>Category</label><select name="category_id">${data.categories.map((c) => `<option value="${c.id}">${escapeHTML(c.name)}</option>`).join("")}</select></div><div class="field"><label>Price (₦)</label><input name="price_naira" type="number" min="0" step="0.01" placeholder="Set price"></div><div><button class="btn" type="submit">${icon("plus", 16)} Add product</button></div></form></section><div class="stack section-gap">${Object.entries(
      byCat,
    )
      .map(
        ([cat, rows]) =>
          `<section class="surface flat"><div style="padding:18px"><h2>${escapeHTML(cat)}</h2><p class="sub">${rows.length} products</p></div>${rows.map((p) => `<form data-form="edit-product" data-id="${p.id}" class="product-edit-row"><div class="field"><label>Product</label><input name="name" required value="${escapeHTML(p.name)}"></div><div class="field"><label>Category</label><select name="category_id">${data.categories.map((c) => `<option value="${c.id}" ${c.id === p.category_id ? "selected" : ""}>${escapeHTML(c.name)}</option>`).join("")}</select></div><div class="field"><label>Price (₦)</label><input name="price_naira" type="number" step="0.01" min="0" placeholder="Not set" value="${p.price_kobo === null ? "" : (p.price_kobo / 100).toFixed(2)}"></div><div class="action-row"><label class="checkbox-inline"><input type="checkbox" name="available" ${p.available ? "checked" : ""}>Available</label><button class="btn sm" type="submit">Save</button><button class="btn danger sm" type="button" data-action="archive-product" data-id="${p.id}">Archive</button></div></form>`).join("")}</section>`,
      )
      .join("")}</div>`,
    "Products & prices",
    "Control what staff can order, current prices and availability.",
  );
}
function staffView() {
  let staff = state.adminData || [];
  adminShell(
    `<section class="surface"><div class="section-head"><div><h2>Register a staff member</h2><p class="sub">Generate a random unique PIN or assign exactly four digits.</p></div>${icon("users")}</div><form data-form="add-staff" class="grid-3"><div class="field"><label>Full name</label><input required name="full_name" placeholder="Staff member name"></div><div class="field"><label>4-digit PIN (optional)</label><input name="pin" inputmode="numeric" pattern="[0-9]{4}" maxlength="4" placeholder="Generate automatically"></div><div style="display:flex;align-items:end"><button type="submit" class="btn wide">${icon("plus", 16)} Register staff</button></div></form>${state.issued ? `<div class="issued"><b>One-time PIN issued for ${escapeHTML(state.issued.name)}</b><div class="pin">${escapeHTML(state.issued.pin)}</div><div class="help">Share privately with the staff member. This PIN cannot be viewed again, only reset.</div><button data-action="clear-pin" class="btn secondary sm" style="margin-top:9px">Hide PIN</button></div>` : ""}</section><section class="surface flat section-gap"><div style="padding:18px"><h2>Staff directory</h2><p class="sub">${staff.length} registered staff members</p></div>${staff.length ? staff.map((s) => `<div class="staff-row"><div><b>${escapeHTML(s.full_name)}</b><div class="staff-meta">Staff #${s.id} · ${s.active ? "Active" : "Inactive"}</div></div><div class="action-row">${badge(s.active ? "Active" : "Inactive", s.active ? "success" : "warn")}<button class="btn secondary sm" data-action="reset-pin" data-id="${s.id}" data-name="${escapeHTML(s.full_name)}">Reset PIN</button><button class="btn ${s.active ? "danger" : "secondary"} sm" data-action="toggle-staff" data-id="${s.id}" data-active="${s.active ? "1" : "0"}">${s.active ? "Deactivate" : "Activate"}</button></div></div>`).join("") : '<div class="blank">No staff registered yet.</div>'}</section>`,
    "Staff & PINs",
    "Maintain the staff directory and issue four-digit ordering PINs.",
  );
}
function debtsView() {
  const d = state.adminData || { rows: [], summary: {} };
  const s = d.summary || {};
  adminShell(
    `<div class="metric-grid">${summaryMetric("Outstanding debt", money(s.outstanding_kobo || 0), "Across all staff")}${summaryMetric("Staff owing", s.staff_owing || 0, "Accounts with a balance")}${summaryMetric("Payment claims", s.payment_claims || 0, "Awaiting review")}${summaryMetric("Verified payments", money(s.verified_kobo || 0), "Confirmed ledger payments")}</div><section class="surface flat section-gap"><div style="padding:18px"><h2>Staff debts</h2><p class="sub">Balances are purchases less administrator-confirmed ledger payments.</p></div>${d.rows.length ? d.rows.map((x) => `<div class="staff-row"><div><b>${escapeHTML(x.staff_name)}</b><div class="staff-meta">${x.total_orders} order${x.total_orders === 1 ? "" : "s"} · Last order ${x.last_order_at ? fmtDate(x.last_order_at) : "—"}</div><div class="staff-meta">Purchases ${money(x.total_purchases_kobo)} · Verified ${money(x.verified_payments_kobo)}</div></div><div class="action-row">${badge(money(x.outstanding_kobo), x.outstanding_kobo ? "warn" : "success")}<button class="btn secondary sm" data-action="view-debt" data-id="${x.staff_id}">View / pay</button><button class="btn secondary sm" data-action="debt-statement" data-id="${x.staff_id}">Statement PDF</button></div></div>`).join("") : '<div class="blank">No staff accounts yet.</div>'}</section><div class="action-row section-gap"><button class="btn secondary" data-action="debt-report">${icon("download", 17)} Download debt report</button></div>`,
    "Staff Debts",
    "Outstanding balances carry across sessions until an administrator records a payment.",
  );
}
async function openDebtDetail(id) {
  const d = await api("/admin/debts/" + id);
  app.insertAdjacentHTML(
    "beforeend",
    `<div class="modal-backdrop" data-debt-modal><section class="modal surface" role="dialog" aria-modal="true"><div class="section-head"><div><h2>${escapeHTML(d.staff_name)}</h2><p class="sub">Outstanding balance: ${money(d.outstanding_kobo)}</p></div><button class="btn ghost icon-btn" data-action="close-debt" aria-label="Close">${icon("close")}</button></div><div class="notice ${d.outstanding_kobo ? "warn" : "success"}">${d.outstanding_kobo ? "Payment declarations do not reduce this balance." : "This account is fully settled."}</div><div class="spacer-sm"></div><div class="table-wrap"><table><thead><tr><th>Order</th><th>Total</th><th>Paid</th><th>Remaining</th></tr></thead><tbody>${d.orders.map((o) => `<tr><td>${escapeHTML(o.reference)}</td><td>${money(o.total_kobo)}</td><td>${money(o.paid_kobo)}</td><td>${money(o.outstanding_kobo)}</td></tr>`).join("")}</tbody></table></div><form data-form="debt-payment" data-id="${d.staff_id}" class="form-stack" style="margin-top:16px"><div class="field"><label>Confirmed amount received (₦)</label><input name="amount_naira" type="number" min="0.01" step="0.01" placeholder="For partial settlement"></div><div class="field"><label>Apply to one order (optional)</label><select name="order_id"><option value="">Oldest outstanding orders first</option>${d.orders
      .filter((o) => o.outstanding_kobo > 0)
      .map(
        (o) =>
          `<option value="${o.id}">${escapeHTML(o.reference)} — ${money(o.outstanding_kobo)} remaining</option>`,
      )
      .join(
        "",
      )}</select></div><div class="field"><label>Payment note</label><input name="notes" maxlength="400" placeholder="Optional receipt or transfer note"></div><label class="check-row"><input name="settle_all" type="checkbox"><span><b>Settle entire outstanding balance</b><br><span class="muted small">Ignores the amount field and allocates oldest orders first.</span></span></label><div class="action-row"><button class="btn" type="submit">Confirm payment</button><button class="btn secondary" type="button" data-action="close-debt">Cancel</button></div></form><hr class="divider"><h3 style="font-size:14px">Payment history</h3>${d.payments.length ? d.payments.map((p) => `<div class="small" style="margin-top:8px"><b>${money(p.amount_kobo)}</b> · ${fmtDate(p.verified_at)}${p.notes ? " · " + escapeHTML(p.notes) : ""}</div>`).join("") : '<p class="small muted">No confirmed payments recorded.</p>'}</section></div>`,
  );
}
function reportsView() {
  let sess = state.adminData || [];
  adminShell(
    `<div class="split"><section class="surface"><div class="section-head"><div><h2>Generate PDF reports</h2><p class="sub">Choose a session, date range and order statuses before downloading.</p></div>${icon("file", 24)}</div><form data-form="report-filters" class="form-stack"><div class="field"><label>Ordering session (optional)</label><select name="session_id"><option value="">All sessions in date filter</option>${sess.map((s) => `<option value="${s.id}" ${String(state.report.session_id) === String(s.id) ? "selected" : ""}>Session #${s.id} — ${escapeHTML(s.session_date)}</option>`).join("")}</select></div><div class="grid-2"><div class="field"><label>From date</label><input name="start" type="date" value="${escapeHTML(state.report.start)}"></div><div class="field"><label>To date</label><input name="end" type="date" value="${escapeHTML(state.report.end)}"></div></div><div class="grid-2"><div class="field"><label>Payment status</label><select name="payment_status"><option value="">All payment statuses</option>${["unpaid", "claimed", "verified"].map((v) => `<option value="${v}" ${state.report.payment_status === v ? "selected" : ""}>${v[0].toUpperCase() + v.slice(1)}</option>`).join("")}</select></div><div class="field"><label>Order status</label><select name="fulfilment_status"><option value="active" ${state.report.fulfilment_status === "active" ? "selected" : ""}>Active only (exclude cancelled)</option><option value="submitted" ${state.report.fulfilment_status === "submitted" ? "selected" : ""}>Submitted</option><option value="preparing" ${state.report.fulfilment_status === "preparing" ? "selected" : ""}>Preparing</option><option value="ready" ${state.report.fulfilment_status === "ready" ? "selected" : ""}>Ready</option><option value="collected" ${state.report.fulfilment_status === "collected" ? "selected" : ""}>Collected</option><option value="cancelled" ${state.report.fulfilment_status === "cancelled" ? "selected" : ""}>Cancelled only</option><option value="all" ${state.report.fulfilment_status === "all" ? "selected" : ""}>All statuses</option></select></div></div><div class="action-row"><button class="btn" name="kind" value="orders" type="submit">${icon("download", 17)} Staff orders PDF</button><button class="btn secondary" name="kind" value="shopping" type="submit">${icon("download", 17)} Shopping list PDF</button><button class="btn secondary" name="kind" value="debts" type="submit">${icon("download", 17)} Debt report PDF</button></div></form></section><section class="surface"><h2 style="font-size:17px">Included in reports</h2><div class="spacer-sm"></div><p class="small muted">Staff order reports show names, items, quantities, individual totals, payment status, order dates and financial summaries.</p><hr class="divider"><p class="small muted">Cancelled orders are excluded by default. Select “Cancelled only” or “All statuses” only when you intentionally need them in a staff-order report.</p><hr class="divider"><p class="small muted">Debt reports calculate outstanding balances from active purchases less confirmed payment allocations. Cancelled orders are excluded.</p><div class="notice">Reports are downloaded from the server and archived in the local data directory.</div></section></div>`,
    "PDF reports",
    "Download staff order records, a consolidated purchasing list, or debt balances.",
  );
}
function settingsView() {
  const s = state.adminData || {};
  adminShell(
    `<div class="split"><section class="surface"><div class="section-head"><h2>Payment & application details</h2>${icon("settings")}</div><form class="form-stack" data-form="settings"><div class="field"><label>Application subtitle</label><input name="app_subtitle" value="${escapeHTML(s.app_subtitle || "")}"></div><div class="field"><label>Bank name</label><input name="bank_name" value="${escapeHTML(s.bank_name || "")}"></div><div class="field"><label>Account name</label><input name="account_name" value="${escapeHTML(s.account_name || "")}"></div><div class="field"><label>Account number</label><input name="account_number" value="${escapeHTML(s.account_number || "")}"></div><div class="field"><label>Payment instructions</label><textarea name="payment_instructions">${escapeHTML(s.payment_instructions || "")}</textarea></div><button class="btn" type="submit">Save settings</button></form></section><div class="stack"><section class="surface"><h2 style="font-size:17px;margin-bottom:14px">Change admin password</h2><form class="form-stack" data-form="password"><div class="field"><label>Current password</label><input type="password" name="current_password" required></div><div class="field"><label>New password (12+ characters)</label><input type="password" name="new_password" minlength="12" required></div><button class="btn secondary" type="submit">Change password</button></form></section><section class="surface"><h2 style="font-size:17px">Backup & hosting</h2><p class="small muted">Run a safe SQLite backup from the server terminal:</p><div class="note-box"><code>python -m app.manage backup</code></div><p class="small muted">Production hosting is configured through the server environment and its HTTPS reverse proxy. See the deployment guide before changing domain or proxy settings.</p></section></div></div>`,
    "Settings",
    "Update payment information and administrator security.",
  );
}
async function showAdmin() {
  if (!state.admin) {
    try {
      state.admin = await api("/admin/me");
    } catch {
      login();
      return;
    }
  }
  const path = location.pathname;
  app.innerHTML = '<div class="loading-screen">Loading seller workspace…</div>';
  try {
    if (path === "/admin" || path === "/admin/") {
      state.adminData = await api("/admin/overview");
      dashboard();
      if (
        state.knownOrders !== null &&
        state.adminData.stats.orders > state.knownOrders
      ) {
        toast("New order received.");
        if (state.sound) beep();
      }
      state.knownOrders = state.adminData.stats.orders;
    } else if (
      path === "/admin/orders" ||
      path === "/admin/payments" ||
      path === "/admin/history"
    ) {
      let p = new URLSearchParams(
        Object.fromEntries(
          Object.entries(state.filters).filter(
            ([k, v]) => v !== "" && v !== undefined,
          ),
        ),
      );
      state.adminData = await api("/admin/orders?" + p);
      ordersView(
        path === "/admin/payments"
          ? "Payments"
          : path === "/admin/history"
            ? "Order history"
            : "Orders",
        path === "/admin/payments"
          ? "Verify staff payment claims and review outstanding amounts."
          : path === "/admin/history"
            ? "Find orders from previous dates and sessions."
            : "Manage submitted orders and fulfilment status.",
      );
    } else if (path === "/admin/products") {
      state.adminData = await api("/admin/products");
      productsView();
    } else if (path === "/admin/staff") {
      state.adminData = await api("/admin/staff");
      staffView();
    } else if (path === "/admin/debts") {
      state.adminData = await api("/admin/debts");
      debtsView();
    } else if (path === "/admin/reports") {
      state.adminData = await api("/admin/sessions");
      reportsView();
    } else if (path === "/admin/settings") {
      state.adminData = await api("/admin/settings");
      settingsView();
    } else dashboard();
  } catch (e) {
    if (!state.admin) {
      login();
    } else {
      adminShell(`<div class="notice warn">${escapeHTML(e.message)}</div>`);
      toast(e.message, true);
    }
  }
}
function beep() {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)(),
      osc = ctx.createOscillator(),
      gain = ctx.createGain();
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.type = "sine";
    osc.frequency.value = 720;
    gain.gain.value = 0.035;
    osc.start();
    osc.stop(ctx.currentTime + 0.12);
    osc.onended = () => ctx.close();
  } catch {}
}
async function route() {
  state.route = location.pathname;
  state.menuOpen = false;
  window.scrollTo({ top: 0, behavior: "instant" });
  if (state.route.startsWith("/admin")) {
    if (state.route === "/admin/login") {
      login();
      return;
    }
    await showAdmin();
    return;
  }
  try {
    await fetchBootstrap();
    if (!state.buyer) {
      buyerAccess();
      return;
    }
    if (state.route === "/my-orders") historyBuyer();
    else if (state.route.startsWith("/order/")) orderReceipt();
    else buyer();
  } catch (e) {
    buyerShell(`<div class="notice warn">${escapeHTML(e.message)}</div>`);
    toast(e.message, true);
  }
}
window.addEventListener("popstate", route);
document.addEventListener("click", async (e) => {
  const anchor = e.target.closest("a[data-link]");
  if (anchor) {
    e.preventDefault();
    navigate(anchor.getAttribute("href"));
    return;
  }
  const el = e.target.closest("[data-action]");
  if (!el) return;
  const act = el.dataset.action;
  try {
    if (act === "category") {
      state.cat = el.dataset.category;
      buyer();
      return;
    }
    if (act === "qty") {
      const id = el.dataset.id;
      state.cart[id] = Math.max(
        0,
        Math.min(99, (state.cart[id] || 0) + Number(el.dataset.delta)),
      );
      const y = window.scrollY;
      buyer();
      window.scrollTo(0, y);
      return;
    }
    if (act === "cancel-edit") {
      state.editing = null;
      state.cart = {};
      state.notes = "";
      state.paid = false;
      buyer();
      return;
    }
    if (act === "buyer-signout") {
      state.buyer = null;
      state.staffId = "";
      state.pin = "";
      state.cart = {};
      state.notes = "";
      state.debt = null;
      toast("Logged out.");
      buyerAccess();
      return;
    }
    if (act === "submit-order") {
      if (!state.staffId || !/^[0-9]{4}$/.test(state.pin))
        throw Error("Select your name and enter your 4-digit PIN.");
      const items = cartItems().map((p) => ({
        product_id: p.id,
        quantity: state.cart[p.id],
      }));
      if (!items.length) throw Error("Select at least one product.");
      el.disabled = true;
      el.textContent = "Submitting…";
      const body = {
        staff_id: Number(state.staffId),
        pin: state.pin,
        items,
        notes: state.notes,
        paid_claimed: state.paid,
        request_key:
          "pfg-" + Date.now() + "-" + Math.random().toString(36).slice(2, 12),
      };
      try {
        const result = await api(
          state.editing ? "/public/orders/update" : "/public/orders",
          {
            method: "POST",
            body: state.editing ? { ...body, reference: state.editing } : body,
          },
        );
        state.receipt = result;
        state.editing = null;
        state.cart = {};
        state.notes = "";
        state.paid = false;
        toast("Order saved successfully.");
        navigate("/order/" + encodeURIComponent(result.reference));
      } catch (err) {
        toast(err.message, true);
        el.disabled = false;
        el.textContent = "Submit Order";
      }
      return;
    }
    if (act === "view-order") {
      state.receipt = state.myOrders.find(
        (x) => x.reference === el.dataset.reference,
      );
      navigate("/order/" + encodeURIComponent(el.dataset.reference));
      return;
    }
    if (act === "cancel-buyer-order") {
      if (!confirm("Cancel this order?")) return;
      const pin = prompt("Enter your four-digit PIN to confirm cancellation:");
      if (pin === null) return;
      if (!/^[0-9]{4}$/.test(pin)) throw Error("A four-digit PIN is required.");
      await api("/public/orders/cancel", {
        method: "POST",
        body: {
          staff_id: Number(state.staffId),
          pin,
          reference: el.dataset.reference,
        },
      });
      state.myOrders = await api("/public/my-orders", {
        method: "POST",
        body: { staff_id: Number(state.staffId), pin },
      });
      toast("Order cancelled.");
      historyBuyer();
      return;
    }
    if (act === "edit-order") {
      const item = state.myOrders.find(
        (x) => x.reference === el.dataset.reference,
      );
      if (!item) return;
      state.cart = Object.fromEntries(
        item.items.map((i) => [i.product_id, i.quantity]),
      );
      state.editing = item.reference;
      state.notes = item.notes || "";
      state.paid = item.payment_status === "claimed";
      navigate("/");
      return;
    }
    if (act === "sound-toggle") {
      state.sound = !state.sound;
      if (state.sound) beep();
      toast(
        state.sound
          ? "Order notification sound enabled."
          : "Order notification sound muted.",
      );
      dashboard();
      return;
    }
    if (act === "toggle-menu") {
      state.menuOpen = !state.menuOpen;
      app
        .querySelector(".admin-app")
        ?.classList.toggle("menu-open", state.menuOpen);
      return;
    }
    if (act === "clear-pin") {
      state.issued = null;
      staffView();
      return;
    }
    if (act === "logout") {
      await api("/admin/logout", { method: "POST" });
      state.admin = null;
      state.issued = null;
      toast("Signed out.");
      navigate("/admin/login");
      return;
    }
    if (act === "page") {
      state.filters.page = Math.max(
        1,
        (state.filters.page || 1) + Number(el.dataset.delta),
      );
      await showAdmin();
      return;
    }
    if (act === "edit-admin-order") {
      const order = (state.adminData?.rows || []).find(
        (x) => String(x.id) === el.dataset.id,
      );
      if (!order) throw Error("The order is no longer available.");
      await openAdminEditor(order);
      return;
    }
    if (act === "close-admin-edit") {
      state.adminEdit = null;
      app.querySelector("[data-admin-editor]")?.remove();
      return;
    }
    if (act === "view-debt") {
      await openDebtDetail(el.dataset.id);
      return;
    }
    if (act === "close-debt") {
      app.querySelector("[data-debt-modal]")?.remove();
      return;
    }
    if (act === "debt-report") {
      await downloadPDF(
        "/admin/reports/debts.pdf",
        "PFG_Cravings_Debt_Report.pdf",
      );
      return;
    }
    if (act === "debt-statement") {
      await downloadPDF(
        "/admin/reports/statement.pdf?staff_id=" +
          encodeURIComponent(el.dataset.id),
        "PFG_Cravings_Debt_Statement.pdf",
      );
      return;
    }
    if (act === "check-debt") {
      if (!state.staffId || !/^[0-9]{4}$/.test(state.pin))
        throw Error("Select your name and enter your 4-digit PIN first.");
      state.debt = await api("/public/account-summary", {
        method: "POST",
        body: { staff_id: Number(state.staffId), pin: state.pin },
      });
      renderDebtNotice();
      return;
    }
    if (act === "archive-product") {
      if (
        !confirm("Archive this product? Historical orders will be preserved.")
      )
        return;
      await api("/admin/products/" + el.dataset.id, { method: "DELETE" });
      toast("Product archived.");
      await showAdmin();
      return;
    }
    if (act === "reset-pin") {
      if (
        !confirm(
          "Reset the PIN for " +
            el.dataset.name +
            "? Their existing PIN will stop working.",
        )
      )
        return;
      let r = await api("/admin/staff/" + el.dataset.id + "/reset-pin", {
        method: "POST",
        body: {},
      });
      state.issued = { name: el.dataset.name, pin: r.issued_pin };
      await showAdmin();
      return;
    }
    if (act === "toggle-staff") {
      await api("/admin/staff/" + el.dataset.id, {
        method: "PATCH",
        body: { active: el.dataset.active !== "1" },
      });
      toast("Staff status updated.");
      await showAdmin();
      return;
    }
    if (act === "session-new") {
      if (
        !confirm(
          "Start a new ordering session? The previous session will be closed.",
        )
      )
        return;
      await api("/admin/sessions", { method: "POST", body: {} });
      toast("New ordering session opened.");
      await showAdmin();
      return;
    }
    if (act === "session-close" || act === "session-open") {
      if (
        !confirm(
          (act === "session-close" ? "Close" : "Reopen") +
            " this ordering session?",
        )
      )
        return;
      await api("/admin/sessions/" + el.dataset.id, {
        method: "PATCH",
        body: { status: act === "session-close" ? "closed" : "open" },
      });
      toast("Ordering session updated.");
      await showAdmin();
      return;
    }
  } catch (err) {
    toast(err.message, true);
  }
});
document.addEventListener("input", (e) => {
  const el = e.target;
  if (
    el.id === "staff-pin" ||
    el.id === "my-orders-pin" ||
    el.id === "receipt-pin"
  ) {
    let value = el.value.replace(/\D/g, "").slice(0, 4);
    el.value = value;
    state.pin = value;
  } else if (el.id === "order-notes") state.notes = el.value;
  else if (
    el.id === "staff-select" ||
    el.id === "my-orders-staff" ||
    el.id === "receipt-staff"
  )
    state.staffId = el.value;
});
document.addEventListener("input", (e) => {
  if (["staff-pin", "staff-select"].includes(e.target.id)) {
    state.debt = null;
    app.querySelector("[data-debt-notice]")?.remove();
  }
});
document.addEventListener("change", async (e) => {
  const el = e.target;
  if (el.id === "paid-claim") {
    state.paid = el.checked;
    return;
  }
  try {
    if (el.dataset.payment) {
      await api("/admin/orders/" + el.dataset.payment + "/payment", {
        method: "PATCH",
        body: { status: el.value },
      });
      toast("Payment status updated.");
      await showAdmin();
    } else if (el.dataset.fulfilment) {
      await api("/admin/orders/" + el.dataset.fulfilment + "/fulfilment", {
        method: "PATCH",
        body: { status: el.value },
      });
      toast("Order status updated.");
      await showAdmin();
    }
  } catch (err) {
    toast(err.message, true);
    await showAdmin();
  }
});
document.addEventListener("change", (e) => {
  if (e.target.id === "staff-select") {
    state.debt = null;
    app.querySelector("[data-debt-notice]")?.remove();
  }
});
document.addEventListener("submit", async (e) => {
  const form = e.target.closest("[data-form]");
  if (!form) return;
  e.preventDefault();
  const id = form.dataset.form;
  const f = Object.fromEntries(new FormData(form).entries());
  let button = e.submitter || form.querySelector("button[type=submit]");
  if (button) button.disabled = true;
  try {
    if (id === "debt-payment") {
      const result = await api(
        "/admin/debts/" + form.dataset.id + "/payments",
        {
          method: "POST",
          body: {
            amount_naira: f.amount_naira || null,
            order_id: f.order_id ? Number(f.order_id) : null,
            notes: f.notes || "",
            settle_all: f.settle_all === "on",
            request_key:
              "debt-" +
              Date.now() +
              "-" +
              Math.random().toString(36).slice(2, 10),
          },
        },
      );
      app.querySelector("[data-debt-modal]")?.remove();
      toast(
        result.account.outstanding_kobo
          ? "Payment recorded; balance remains outstanding."
          : "Payment recorded; account is settled.",
      );
      await showAdmin();
      return;
    }
    if (id === "admin-order-edit") {
      const items = Object.entries(f)
        .filter(
          ([name, value]) => name.startsWith("item_") && Number(value) > 0,
        )
        .map(([name, value]) => ({
          product_id: Number(name.slice(5)),
          quantity: Number(value),
        }));
      if (!items.length) throw Error("Keep at least one product in the order.");
      const wasVerified = state.adminEdit?.payment_status === "verified";
      const updated = await api("/admin/orders/" + form.dataset.id, {
        method: "PUT",
        body: {
          items,
          notes: f.notes || "",
          reason: f.reason || "",
          reverify_payment: f.reverify_payment === "on",
        },
      });
      state.adminEdit = null;
      app.querySelector("[data-admin-editor]")?.remove();
      toast(
        wasVerified && updated.payment_status === "claimed"
          ? "Order amended; payment requires verification."
          : "Order amended.",
      );
      await showAdmin();
      return;
    }
    if (id === "buyer-access") {
      const staffId = Number(f.staff_id);
      const pin = String(f.pin || "");
      if (!staffId || !/^[0-9]{4}$/.test(pin))
        throw Error("Select your name and enter your valid four-digit PIN.");
      state.buyer = await api("/public/verify-identity", {
        method: "POST",
        body: { staff_id: staffId, pin },
      });
      state.staffId = String(staffId);
      state.pin = pin;
      toast("Identity verified. Welcome, " + state.buyer.staff_name + ".");
      await route();
      return;
    }
    if (id === "login") {
      state.admin = await api("/admin/login", {
        method: "POST",
        body: { username: f.username, password: f.password },
      });
      toast("Signed in.");
      navigate("/admin");
      return;
    }
    if (id === "my-orders" || id === "receipt") {
      const staffId = Number(form.querySelector("select").value);
      const pin = form.querySelector("input[type=password]").value;
      if (!staffId || !/^[0-9]{4}$/.test(pin))
        throw Error("Select your name and provide a valid four-digit PIN.");
      state.staffId = String(staffId);
      state.pin = pin;
      if (id === "my-orders") {
        state.myOrders = await api("/public/my-orders", {
          method: "POST",
          body: { staff_id: staffId, pin },
        });
        historyBuyer();
        if (!state.myOrders.length)
          toast("No orders found for this staff member.");
        return;
      } else {
        state.receipt = await api("/public/receipt", {
          method: "POST",
          body: {
            staff_id: staffId,
            pin,
            reference: location.pathname.split("/").pop(),
          },
        });
        orderReceipt();
        return;
      }
    }
    if (id === "filter-orders") {
      state.filters = {
        q: f.q || "",
        start: f.start || "",
        end: f.end || "",
        status: f.status || "",
        page: 1,
      };
      await showAdmin();
      return;
    }
    if (id === "add-product" || id === "edit-product") {
      const body = {
        name: f.name,
        category_id: Number(f.category_id),
        price_naira: f.price_naira || null,
        available:
          id === "add-product"
            ? true
            : !!form.querySelector("[name=available]").checked,
        sort_order: 0,
      };
      await api(
        id === "add-product"
          ? "/admin/products"
          : "/admin/products/" + form.dataset.id,
        { method: id === "add-product" ? "POST" : "PATCH", body },
      );
      toast("Product saved.");
      await showAdmin();
      return;
    }
    if (id === "add-staff") {
      let p = { full_name: f.full_name, pin: f.pin || null };
      let r = await api("/admin/staff", { method: "POST", body: p });
      state.issued = { name: f.full_name, pin: r.issued_pin };
      toast("Staff registered.");
      await showAdmin();
      return;
    }
    if (id === "session-deadline") {
      if (!f.deadline) throw Error("Choose a closing date and time.");
      const session = state.adminData?.session;
      if (!session?.id) throw Error("No active session.");
      const iso = new Date(f.deadline).toISOString();
      await api("/admin/sessions/" + session.id, {
        method: "PATCH",
        body: { status: "open", closes_at: iso },
      });
      toast("Closing deadline saved.");
      await showAdmin();
      return;
    }
    if (id === "settings") {
      await api("/admin/settings", { method: "PUT", body: f });
      toast("Settings saved.");
      await showAdmin();
      return;
    }
    if (id === "password") {
      await api("/admin/change-password", { method: "POST", body: f });
      toast("Admin password changed.");
      form.reset();
      return;
    }
    if (id === "report-filters") {
      state.report = {
        session_id: f.session_id || "",
        start: f.start || "",
        end: f.end || "",
        payment_status: f.payment_status || "",
        fulfilment_status: f.fulfilment_status || "active",
      };
      const kind = e.submitter?.value || "orders";
      const params = new URLSearchParams(
        Object.entries(state.report).filter(([k, v]) => v),
      );
      await downloadPDF(
        `/admin/reports/${kind}.pdf?${params}`,
        `PFG_Cravings_${kind}.pdf`,
      );
      return;
    }
  } catch (err) {
    toast(err.message, true);
  } finally {
    if (button) button.disabled = false;
  }
});
async function downloadPDF(path, name) {
  const response = await fetch(N + path, { credentials: "same-origin" });
  if (!response.ok) {
    const d = await response.json().catch(() => ({}));
    throw Error(d.detail || "PDF generation failed.");
  }
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  const match = /filename="?([^";]+)"?/.exec(
    response.headers.get("content-disposition") || "",
  );
  link.download = match ? match[1] : name;
  document.body.append(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 15000);
  toast("PDF report downloaded.");
}
setInterval(async () => {
  if (location.pathname === "/admin" && state.admin && !document.hidden) {
    try {
      let d = await api("/admin/overview");
      let previous = state.knownOrders;
      state.knownOrders = d.stats.orders;
      if (previous !== null && d.stats.orders > previous) {
        toast("A new refreshment order has arrived.");
        if (state.sound) beep();
      }
      state.adminData = d;
      dashboard();
    } catch {
      /* visible network errors are shown on explicit operations */
    }
  }
}, 16000);
function renderDebtNotice() {
  const d = state.debt;
  if (!d || String(d.staff_id) !== String(state.staffId)) return;
  const target = [...app.querySelectorAll(".surface")].find((x) =>
    x.textContent.includes("1. Your details"),
  );
  if (!target || target.querySelector("[data-debt-notice]")) return;
  const current = cartItems().reduce(
    (sum, p) => sum + Number(p.price_kobo || 0) * Number(state.cart[p.id] || 0),
    0,
  );
  target.insertAdjacentHTML(
    "beforeend",
    `<div class="notice ${d.outstanding_kobo ? "warn" : "success"}" data-debt-notice style="margin-top:15px"><b>${d.outstanding_kobo ? "Outstanding Payment" : "Account summary"}</b><br>${escapeHTML(d.staff_name)}<div class="basket-line" style="margin-top:8px"><span>Previous outstanding debt</span><b>${money(d.outstanding_kobo)}</b></div><div class="basket-line"><span>Current order</span><b>${money(current)}</b></div><div class="basket-line strong"><span>Total outstanding after submission</span><b>${money(d.outstanding_kobo + current)}</b></div>${d.outstanding_kobo ? '<span class="small">Please clear your outstanding payment. Your balance changes only after seller confirmation.</span>' : '<span class="small">No confirmed outstanding balance.</span>'}</div>`,
  );
}
function lockBuyerDetails() {
  if (!state.buyer || location.pathname !== "/") return;
  const target = [...app.querySelectorAll(".surface")].find((x) =>
    x.textContent.includes("1. Your details"),
  );
  if (!target) return;
  target.querySelector("#staff-select")?.setAttribute("disabled", "");
  target.querySelector("#staff-pin")?.setAttribute("disabled", "");
  if (target.querySelector("[data-buyer-verified]")) return;
  target.insertAdjacentHTML(
    "beforeend",
    `<div class="notice success" data-buyer-verified style="margin-top:15px"><b>Signed in as ${escapeHTML(state.buyer.staff_name)}</b><br><span class="small">Your identity has been verified for this browser session.</span><div class="action-row" style="margin-top:10px"><button type="button" class="btn secondary sm" data-action="buyer-signout">Change buyer</button></div></div>`,
  );
}
function injectDebtCheck() {
  if (location.pathname !== "/") return;
  const target = [...app.querySelectorAll(".surface")].find((x) =>
    x.textContent.includes("1. Your details"),
  );
  if (!target || target.querySelector('[data-action="check-debt"]')) return;
  target.insertAdjacentHTML(
    "beforeend",
    `<div class="action-row" style="margin-top:14px"><button type="button" class="btn secondary sm" data-action="check-debt">Check outstanding balance</button><span class="help">Your PIN is required; selecting a name alone never reveals your balance.</span></div>`,
  );
  renderDebtNotice();
}
function injectReceiptDebt() {
  const d = state.receipt?.debt_summary;
  const target = app.querySelector(".receipt");
  if (!d || !target || target.querySelector("[data-receipt-debt]")) return;
  target.insertAdjacentHTML(
    "beforeend",
    `<section class="surface notice ${d.outstanding_after_kobo ? "warn" : "success"}" data-receipt-debt style="margin-top:18px"><b>Account payment summary</b><div class="basket-line" style="margin-top:8px"><span>Previous outstanding debt</span><b>${money(d.previous_outstanding_kobo)}</b></div><div class="basket-line"><span>New order</span><b>${money(d.current_order_kobo)}</b></div><div class="basket-line strong"><span>Total outstanding</span><b>${money(d.outstanding_after_kobo)}</b></div>${d.outstanding_after_kobo ? '<p class="small" style="margin-bottom:0">Your previous outstanding balance has been carried forward. It changes only when the seller confirms payment.</p>' : ""}</section>`,
  );
}
new MutationObserver(() => {
  lockBuyerDetails();
  injectDebtCheck();
  injectReceiptDebt();
}).observe(app, { childList: true, subtree: true });
route();
