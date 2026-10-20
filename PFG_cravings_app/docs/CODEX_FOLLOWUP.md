# PFG Cravings — Suggested Codex refinement tasks

You are editing an existing working application. Inspect the project and current tests before making changes. Do not initialize Git or change branches/remotes, and do not replace the architecture without an explicit justification.

1. Preserve existing database and data-dir/secret migrations; introduce schema migration versions before making database changes.
2. Add seller-side order-item editing in a responsive modal, with a full price/payment reconciliation policy and audit history; do not corrupt verified amounts or historical price snapshots.
3. Replace the simple staff order PIN with stronger authentication if the office expands or if abuse becomes a problem; do not collect Windows usernames or device fingerprints.
4. Add configurable office LAN hostname deployment examples for Windows/Caddy/Linux; verify HTTPS and secure cookies with actual trusted certificates.
5. Improve admin order history filters, session schedules and optional date-limited export archives; keep the main forms compact.
6. Add browser end-to-end tests using Playwright in a real supported browser environment, and verify on iPhone Safari/Android Chrome and 320px desktop emulation.
7. Add a genuine PFG logo asset only if the user supplies one, without recreating an inaccurate logo. Retain corporate navy #181F63. No gradients or sci-fi motifs.
8. Add a friendly buyer QR code (prefer a server-generated QR for the actual configured reachable LAN URL).
9. Add an admin data-retention/backup rotation policy and periodically test restores.
10. Do not add cloud services, payment gateway integrations or unrelated features without asking.

Existing stack: FastAPI, SQLite, ReportLab, vanilla browser JavaScript/CSS. Tests run with `python -m pytest tests -q`. A deliberate migration to a React/Vite stack is possible, but should only be done if maintainability justifies the cost.
