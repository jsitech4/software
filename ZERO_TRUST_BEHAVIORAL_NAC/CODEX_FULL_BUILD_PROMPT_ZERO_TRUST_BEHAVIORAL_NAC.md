# CODEX MASTER IMPLEMENTATION PROMPT
## Zero-Trust Network Access Control System Using Machine Learning-Based Behavioral Authentication

**Purpose:** Build, integrate, test, package, and document a real working academic research prototype, from an existing repository through local and secure single-server deployment.

**Read this entire specification and execute it as the software development brief. Do not stop after writing a plan, a UI mockup, or a few scaffolding files.**

### 0. Repository and execution rules (non-negotiable)

You are operating inside the CURRENTLY OPEN VS Code workspace/repository. Inspect the existing files, dependencies, README, and architecture before modifying anything. Preserve valid existing work and adapt it. If the repository is blank, create the project structure in place. Do not initialize another Git repository, create a new repository, create/rename branches, commit, push, pull, merge, rebase, reset, alter remotes, or use destructive Git commands unless I explicitly request them. You may inspect Git status/log read-only. Never delete unrelated project files. Never rely on a previous project being present.

If a file named `Oso Akinyemi Pro.docx` is present, read the research proposal first. Otherwise, use the complete requirements in this prompt as the authoritative functional brief. The title and research focus MUST remain: **Development of a Zero-Trust Network Access Control System Using Machine Learning-Based Behavioral Authentication**. The proposal is an MSc research proposal involving five consenting participants, browser-based behavior collection, per-user machine-learning profiles, continuous risk estimation, and actual protected-resource enforcement.

Use modular, understandable code and documentation authored in a professional maintainer voice. Do not claim tests, scans, deployments, ML accuracy, collected participant data, or security features are successful when they have not actually been executed. Distinguish seeded demonstration data from collected research data in the backend and in research exports. Do not disguise fake data as real. Do not implement a mock authorization decision as the final enforcement mechanism. If a dependency or platform prevents complete verification, document the blocker precisely, build meaningful automated tests using available facilities, and continue with other implementation stages.

### 1. Research mission and fixed scope

Build a **Zero-Trust Behavioral Access Control** research prototype protecting actual web application resources through an application-layer Policy Enforcement Point (PEP). Verify users at initial authentication and during subsequent observable in-application interactions; learn behavior from typing timing, mouse movement, scrolling, interaction/navigation frequency, and session context; generate risk estimates; evaluate deterministic policies that allow, challenge, restrict, or revoke resource access; and provide a research-grade administrative dashboard.

This scope is NOT a claim that browser JavaScript monitors every application or keyboard event across the entire laptop. It is NOT a genuine physical Ethernet/Wi-Fi admission-control system. The core system must enforce per-user, per-resource authorization at a proxy/API gateway. Prepare a documented **optional future phase** for IEEE 802.1X + FreeRADIUS + compatible switch/AP + dynamic authorization/CoA, but do not mislabel the core implementation as physical 802.1X NAC.

Specific functional objectives:
- Identity verification: username/password through an identity provider and operational MFA/step-up authentication.
- Participant enrollment: informed consent and multiple labeled genuine sessions.
- Continuous behavioral measurement: approved features collected only within the participant portal, with no text or password capture.
- Research ML: compare a statistical distance baseline, per-user Isolation Forest, One-Class SVM, and a supervised benchmark such as Random Forest where data suffices.
- Risk policy: deterministic, auditable decisions using identity, valid enrollment/model state, authentication strength, resource role, data quality, device-registration context, and behavioral anomaly evidence.
- Real gateway enforcement: fail-closed default deny for protected resource access, server-side session revoke, MFA gating, role restriction, and proof that direct protected-resource bypass is impossible.
- Admin operations: participants, consents, enrolled models, sessions, policies, security events, access logs, experiments, reports.
- Evaluation: session-grouped train/validation/test, FAR/FRR, precision/recall/F1, confusion matrices, class rates, score distributions, detection and enforcement delays, usable windows, and false challenge rate.

### 2. Architecture: make every connection executable

Use the following preferred stack unless existing repo constraints strongly justify another. Pin compatible, supported versions and record them:
- React + TypeScript + Vite (participant app and admin app; route/role isolation), Tailwind CSS for responsive UI.
- Python + FastAPI + Pydantic + SQLAlchemy + Alembic for APIs and orchestration.
- Keycloak with OIDC Authorization Code flow; backend-for-frontend (BFF) where reasonable, server-side sessions, secure HttpOnly SameSite cookies, PKCE on applicable OIDC flows; TOTP as minimum MFA implementation. Support WebAuthn later if practical.
- Redis for active session/security state, invalidation, and optional background work queue; PostgreSQL for authoritative structured records.
- Machine learning: Python, NumPy, Pandas, Scikit-learn, Joblib with strict artifact metadata and validation; stable JSON numeric-feature schemas.
- Open Policy Agent (Rego) for policy decisions.
- Envoy HTTP proxy with ext_authz check via a **tested authz-adapter** or the OPA-Envoy plugin; choose a SINGLE integration contract and implement it completely. The component performing ext_authz must authenticate the session/identity and consult the current authoritative authorization/risk state before permitting protected resource requests. Distinguish Policy Engine, Policy Administrator and PEP.
- Docker Compose with health checks and segmented internal networks. Only the explicitly intended TLS edge endpoint may be externally exposed.
- Caddy (or an equivalent reverse proxy) as HTTPS edge termination for real deployment; use local HTTPS as appropriate for development.
- Pytest, Playwright, and selected load tests. Structured JSON logging with correlation IDs; optional Prometheus/OpenTelemetry only after core logic works.

Proposed flow:
1. Participant visits the public gateway, accesses the application, and authenticates through Keycloak.
2. Backend establishes an application session, validating OIDC tokens securely. Browser receives a secure session cookie, not a long-lived accessible bearer token.
3. User accesses protected resources *only through Envoy*. The upstream resource service must not publish an alternate host port or have any public bypass route.
4. Envoy asks the ext_authz provider about every relevant protected HTTP request; provider confirms server-side session status and role, requests OPA decision, and returns allow or denial/challenge semantics. No stale positive cache may authorize revoked sessions.
5. Participant's JS feature aggregator produces approved numeric behavioral windows during real interaction (e.g., 30 or 60 seconds plus minimum-event thresholds), sends with session/authenticated user context over HTTPS. Never trust client-provided `user_id`, role or claimed session ownership.
6. Worker/API validates feature schemas, timestamps, volume, session binding, replay/duplicate limits and rate limits; scores with the current signed/versioned enrolled model where valid.
7. Risk decision is updated in Redis and persisted to PostgreSQL with model version, data quality, rule version, evidence, timestamp and decision reason.
8. OPA policy recalculates access. On REVOKE, disable the app session and ensure ALL later resource requests receive denial; make long-running/WebSocket access explicitly revalidated, closed or unsupported with a stated limitation.
9. Dashboard receives only authorized, non-sensitive security status and research metrics.

### 3. Exact project layout

Fit any present source tree. If creating from scratch, use:

```
apps/participant-web/
apps/admin-web/
apps/protected-resource/
services/api/app/{auth,users,devices,consent,behavior,enrollment,models,risk,policies,sessions,enforcement,audit,reports}/
services/ml-worker/{features,training,inference,model_registry,evaluation}/
packages/contracts/
infra/{compose,caddy,envoy,opa,keycloak,postgres,redis}/
research/{protocols,fixtures,notebooks,scripts,results}/
tests/{unit,integration,e2e,security,performance}/
docs/{architecture,requirements,api,ml_protocol,privacy,operations,testing,deploy,limitations}/
scripts/
compose.yaml
compose.production.yaml
.env.example
.gitignore
README.md
```

Produce architecture decision records (ADRs) covering browser-only monitoring, application-layer enforcement, identity provider choice, feature privacy, absence of raw text capture, model-split strategy and risk calibration.

### 4. Data model and migrations

Create strongly typed models, safe migrations and indexes for at least:
- identity-linked `users` (UUID pseudonym, IdP subject reference, participant/admin role, enrollment state);
- `registered_devices` (opaque enrollment label, observed browser/device context, trust_claim limitations);
- `consent_records` (scopes, date, status, withdrawal, research export eligibility);
- `sessions` (opaque session id, IdP subject, auth strength, created/expiry, state, revoked_at, revoked_reason, state_version);
- `behavior_windows` (user, session, source task, measured window time, 30/60-second parameter, quality flags, feature JSON/typed columns, pseudonymous labels for research, dataset version);
- `enrollment_runs` (number of usable windows, time/date, platform/browser/device conditions);
- `model_versions` (per-user identity, model type, artifact hash, feature-schema version, training sessions/dates, validation thresholds, promotion status);
- `risk_assessments` (risk score, provenance, insufficient-evidence state, model version, policy version, reason codes, confidence/quality score);
- `policies`, `resources`, `authorization_decisions`, `enforcement_actions` (request id, expected/actual PEP response, timestamps, outcome);
- `audit_events`, `experiment_runs`, `experiment_results`, `export_jobs`, `research_data_retention_actions`.

Use Alembic migrations; maintain foreign keys, unique event identifiers, pagination, filtering by date/time/subject/risk/type; do not let API return biometric feature values to unauthorized roles. Never store Keycloak passwords, typed keys/text, screenshots or secrets in behavioral tables.

### 5. Keycloak, sessions and MFA: MUST work for real

Provision an isolated Keycloak realm in development using reproducible configuration (realm import or provisioning script). Create admin and participant roles and a controlled seed procedure. Disable dangerous first-run defaults in production. Implement OIDC state/nonce/PKCE where relevant; require HTTPS outside local development; protect against CSRF and login fixation; validate issuer, audience, signature, expiration and auth context.

Functional MFA requirement: TOTP registration and successful challenge must take place in the IdP, not as a cosmetic modal. Include an integration flow for step-up authentication/reauthentication at elevated risk (using supported Keycloak flows, OIDC prompt/max_age/acr as appropriate), and **verify the returned authentication assurance/session state server-side**. If a particular Keycloak version cannot meet an exact step-up variant, implement a real secure reauthentication fallback and record that decision in documentation. No artificial 'MFA approved' button may unlock resources.

Define explicit login/session states: unauthenticated, authenticated-unenrolled, enrolled-allowed, challenge-required, restricted, revoked, expired, and observation-insufficient. All protected endpoints must enforce the current state.

### 6. Browser behavioral collection: privacy-first and technically correct

Build a consent-gated feature collector as a reusable TypeScript library using standard browser DOM events:
- `keydown`/`keyup` ONLY within approved research text-entry tasks or explicitly approved app controls; calculate hold time and between-key timing from monotonic timestamps. Ignore repeat events, unsupported composition/IME scenarios or account for them clearly.
- `pointermove`, `pointerdown`, `pointerup`, `click` and `wheel` in approved areas for movement velocity, acceleration, direction-change rate, click duration/frequency, scroll magnitude and direction.
- `visibilitychange`, page focus, task/navigation counters and elapsed session time as context; show when page is not observable; do not claim cross-application observation.
- exclude all password, OTP, authentication, personal-data, financial, sensitive and editable private-content fields, plus browser extensions/out-of-page activity; do not capture pasted strings, input values, keyboard codes, full coordinates over time or private files.
- compute aggregate features locally, transmit numeric features and quality metadata only, drop raw events immediately. Enforce min sample counts, outlier validation, schema versioning, replay identifiers and server-side deduplication.
- document that synthetic client telemetry is forgeable; browser-only collection does NOT provide a cryptographic assertion of human identity and is one risk input, not a standalone strong authenticator.
- provide persistent visible consent/research status, the ability to decline and withdraw, and a process to erase/anonymize research data subject to documented requirements.

Create enrollment tasks: instructed typing passage (no storage of text entered); copy/edit interaction; navigation; cursor selection and scrolling. Offer clear instructions and progress. Create 30-second and 60-second observation windows with `insufficient_evidence` decisions rather than fabricated zero-risk behavior.

### 7. Research sampling design: five participants, genuine/impostor

Implement a research protocol and exportable data manifest:
- configurable research design default: five consenting participants; target 6-8 sessions per participant across multiple days; 10-15 minutes/session; a user may complete fewer sessions but the report must display insufficient coverage warnings.
- normal/genuine runs and ethically controlled impostor runs, in which participant B operates a test session identifying as participant A under researcher supervision. Do NOT collect real passwords or illicitly hijack accounts; use instructor-generated designated demo accounts and a sandbox task.
- all sessions labeled with `claimed_user`, `operator_participant` (research-only pseudonym), genuine/impostor ground truth, task, device/browser context, collection date and session id. Do not claim an ML prediction itself 'confirms' an impostor.
- implement reproducible session-based train/validation/test manifests where windows from a session never appear in multiple partitions; never tune models/thresholds on test set. Chronological separation where sensible; retain enough genuine training sessions for each user.
- any dataset bundled to demonstrate UI/CI MUST be synthetic and unambiguously marked SYNTHETIC; never publish private participant features as part of Git commits.

### 8. ML algorithms, training, score calibration and metrics

Produce separate modular pipelines for feature quality checks, missing-value handling, scaling (fitted on training ONLY), user-specific model fitting, score orientation, calibration, threshold selection, held-out evaluation and inference.

Minimum comparator models:
1. simple statistical robust z-score / standardized-distance baseline per user;
2. per-user Isolation Forest trained on genuine training windows;
3. per-user One-Class SVM with tuned feature scaling;
4. Random Forest supervised comparator where train data has sufficient genuine and known-impostor sessions.

Use a documented, fixed set of numeric features, session-level cross-validation, deterministic seeds, serialized sklearn pipelines, model integrity checks and a model registry. Outputs must distinguish an **anomaly score** from a calibrated probability; do not present arbitrary Isolation Forest scores as '99% chance of attack'. Define risk conversion/thresholding transparently, show distributions, and calculate uncertainty where sample size allows.

Positive class convention across ALL metrics: positive = IMPOSTOR. Define TP=correct impostor detection; FP=legitimate flagged; FN=impostor accepted; TN=legitimate accepted. Report confusion matrix, precision/recall/F1, FAR (impostor accepted / total impostor attempts), FRR (legitimate rejected / total legitimate attempts), ROC-AUC or EER where statistically supportable, coverage, prediction latency, challenge rate, and detection lag. Avoid claiming enterprise generalization from five people. Show held-out results with dataset version, participant count, session count, sample count, seeds, splits and confidence caveats. Do not fabricate metrics when empirical samples are absent.

Implement model lifecycle: train -> evaluate -> candidate -> approve/promote -> active -> retire; never auto-promote without validation and an authorized action. Handle missing model or insufficient behavioral evidence with a distinct policy state and safe fallback.

### 9. Policy engine, PEP, effective network resource restriction

Implement explicit least privilege with roles such as participant, researcher, admin; resources such as public onboarding, protected documents, restricted records, administrative action. Normal participant may reach only designated resources; even an authenticated user must not access forbidden endpoints.

OPA/Rego inputs include identity, resource, method, role, authentication strength, active-session state, enrollment state, risk band, quality state, and policy version. Outputs include `allow`, `challenge`, `restrict`, `revoke`, reason code and expiry/recheck instructions. Produce tested Rego unit cases with default deny.

**The actual gateway is the proof of NAC-like enforcement**. Put a separate demo resource behind Envoy on a private network with no public port. For each protected resource request Envoy MUST authorize against the current server-managed state via ext_authz/adapter/OPA; direct access to the service must fail from the host and participant network. Revoke must immediately prevent the NEXT request even if a stale unexpired browser cookie exists. In-memory dashboard flags do not satisfy enforcement. Explain bounds for already-open HTTP streams/WebSockets and close/revalidate them if supported.

For risk changes, implement conservative policy: low = allow only authorized resources; moderate = MFA step-up; high = restrict high-value operations; extreme + sufficient corroborating evidence = revoke and notify admin. Include temporal smoothing/hysteresis, challenge cooldown, evidence quality, false-positive recovery, data-stale logic and risk decay. Calibrate thresholds in validation, not using arbitrary permanent defaults. Data loss must not be treated as either 'impostor proven' or 'normal user' by itself.

### 10. User interfaces (production-grade quality)

Participant web:
- accessible responsive login/access screen integrated with real IdP;
- privacy/consent notices and withdrawal workflow;
- enrollment wizard and task progress with profile readiness;
- protected demo resources and permissions in effect;
- simple visible security state (allowed/challenge/restricted/revoked) with clear recoverable actions; no surveillance aesthetic;
- live session state without aggressive flicker and clear telemetry availability indicators.

Admin web:
- sidebar/dashboard overview with active sessions, pending challenges, blocks, enrollment health and trend summaries;
- searchable participants, pseudonymous identities, model versions, feature coverage and device registrations;
- session detail: chronology of behavioral windows, data quality, risk score, model ID, policy decision, enforcement outcome and reason;
- policy configuration with valid server-side guardrails and immutable audit trail of changes;
- consenting research run registration, dataset manifest, ethical exports and CSV reports;
- model evaluation: confusion matrix, FAR, FRR, precision/recall/F1, per-user breakdown, detection delay and leakage-proof split manifest;
- date-range audit filtering and stable pagination; no endless auto-scrolling logs;
- real WebSocket/SSE updates for monitoring where useful, with fallback/reconnect.

A coherent dark theme is acceptable; use professional information hierarchy, responsive cards, keyboard accessibility and clear loading/error/empty states. Never label synthetic data as live empirical measurements. Every button and form must be functional or explicitly disabled with an explanation.

### 11. API surface and contracts

Design and implement versioned `/api/v1` contracts with typed OpenAPI documentation for:
- `/auth/session`, `/auth/login`, `/auth/callback`, `/auth/logout`, `/auth/step-up`, `/auth/step-up/callback`;
- `/participants`, `/participants/{id}`, `/consent`, `/enrollments`, `/enrollments/{id}`;
- `/behavior/windows`, `/behavior/quality`, `/models`, `/models/train`, `/models/{id}/evaluate`, `/models/{id}/promote`;
- `/sessions`, `/sessions/{id}`, `/sessions/{id}/revoke`, `/sessions/{id}/restore` (restore requires NEW authorized session per policy);
- `/policy/evaluate`, `/policies`, `/resources`, `/events`, `/audit`, `/experiments`, `/reports/export`;
- `/health/live`, `/health/ready`, `/metrics` (internal only).

Harden authorization on every handler. A participant can never submit a score for another participant, promote a model, edit policies or access all-user behavioral data. Use strict schema validation, pagination, DTOs, safe exception messages and audit correlation IDs. The ext_authz adapter must be internal-only, validate trusted gateway identity/context and resist forged forwarded headers.

### 12. Security requirements

Threat-model credential theft, session hijacking, impersonation, client telemetry forgery, replay, token theft, cross-site requests, malicious research data uploads, cross-user data leakage, admin compromise, policy bypass, ML evasion, availability/DoS and container misconfiguration.

Minimum mitigations: TLS end-to-end where appropriate, CSP, security headers, HttpOnly Secure SameSite cookies, CSRF protections, strong IdP config, RBAC, request rate limits, MFA, CSRF/redirect URI allowlists, secure logging and secret redaction, dependency audits, cryptographic randomness, minimal container privileges, non-root containers where possible, health checks, private networking, service-to-service trust, least-privilege DB users, encryption/backup of stored biometric feature data, retention/deletion procedures, centralized server time and strict no untrusted pickle loading. Only load locally generated trusted versioned model artifacts with verified hashes; do not accept uploaded arbitrary .pkl files.

Never record raw passwords, OTPs, typed characters, sensitive input values, exact browsing histories outside portal, screenshot/video capture, or background global keyboard activity. Prior consent and participant withdrawal must be functional. Research exports must minimize identity linkage.

### 13. Testing: mandatory gates and measurable evidence

Write and execute:
- Unit tests for feature extraction (keyup matching, repeats, zero activity, focus loss, wrong clock order, event quality), schemas, risk smoothing, policies, model selection, score calculations, FAR/FRR.
- Integration tests for Keycloak auth, OIDC callback/session, API->Redis->OPA->Envoy authorization, DB migrations, revocation persistence, admin RBAC and consent handling.
- Playwright e2e for enrollment, task interaction, valid login/MFA, unauthorized route, moderate step-up, restricted resource, revoke/deny, logout, page reload, browser offline/reconnect.
- Security-specific tests demonstrating: direct upstream bypass fails; forged headers rejected; mismatched user/session window rejected; replay window dropped; revoked session denied on next request; role escalation blocked; stale risk model handled; missing model handled; OPA/adapter failure fails closed for protected resources.
- ML tests: no overlapping session IDs between splits; no data leakage during scaling; correct impostor-positive confusion matrix; synthetic deterministic training works; model registry and schema checks; real empirical metrics printed ONLY when genuine research data exists.
- Performance tests: protected request overhead, behavioral window throughput, inference time, revocation-to-enforced-denial delay, browser performance.

Create an automated `scripts/verify_all.*` entry point suitable for Windows/WSL and Linux that runs format/lint/typecheck, unit tests, integration tests, front-end builds, policy tests, container config validation, and smoke tests. Store test evidence/results to `artifacts/test-reports/` (gitignored where appropriate). Provide a traceability document mapping research objectives to implemented services and tests.

### 14. Deployment A: reproducible local development/demo

Target OS: Windows 11 with WSL2 Ubuntu and Docker Desktop (or native Linux). Provide exact installation prerequisites, hardware requirements (16 GB RAM recommended, 32 GB ideal for full suite; 4+ CPU cores, ~80 GB free), `.env.example` with non-secret placeholders, local hostnames/ports and an optional trusted local TLS workflow. No hardcoded admin credentials or production secrets.

Create working scripts:
- `scripts/bootstrap-dev.*` to check prerequisites and config;
- `scripts/start-dev.*` to initialize local containers, migrations and test realm idempotently;
- `scripts/seed-demo.*` to create only unmistakably labeled synthetic fixtures;
- `scripts/test-all.*` / `scripts/verify-all.*`;
- `scripts/stop-dev.*` without deleting persisted data;
- `scripts/backup.*` and `scripts/restore.*` with dry-run and validation.

`docker compose config`, `docker compose build` and startup must be executable with no unspecified files. All services need health checks, persisted volumes for PostgreSQL/Keycloak and consistent startup ordering. Document exactly which URLs an operator opens, how to enroll MFA, how to register a user, and how to conduct a valid controlled impostor test. Production and development must have separate identity/secret configuration.

### 15. Deployment B: secure single-server Linux/VPS

Also implement `compose.production.yaml`, production Caddy/Envoy configuration, DNS/TLS instructions, firewall rules exposing only 80/443 (and restricted admin SSH), non-root service and network isolation, secure environment and Docker Compose secrets where appropriate, DB volume/backups, log rotation, restart policies, health checks and minimum-resource guidance. Include migration workflow, predeployment checklist, rollback procedure, backup restore drill and runbook for incident response and key rotation.

Document:
1. provision supported Ubuntu LTS server, user account, SSH key, updates and firewall;
2. install Docker Engine/Compose per official docs; avoid exposing Docker daemon remotely;
3. configure DNS and HTTPS reverse proxy;
4. create production secrets outside Git and valid IdP realm config;
5. deploy/build with `docker compose -f compose.yaml -f compose.production.yaml up -d --build` after validating config;
6. apply migrations; initialize identity provider and roles; verify TLS and health;
7. execute smoke tests for auth, MFA, allowed resource, denied resource, revoked session and bypass prevention;
8. configure backups, monitoring, retention and an operations handover process.

Do NOT attempt to buy a domain, provision a cloud account, open firewall ports on real infrastructure, or deploy to a remote server without explicit user-provided credentials/environment and authorization. Prepare fully executable deployment artifacts and run them against a locally available runtime when possible. Report exactly what remains unverified without remote access.

### 16. Optional Phase 2: genuine physical network admission control

Write `docs/optional-8021x-nac.md` with future architecture: FreeRADIUS, EAP-TLS, PKI certificates, managed 802.1X switch or AP, protected/quarantine VLAN, RADIUS CoA/Disconnect if supported, identity-to-network-session mapping, policy controller integration, PoC equipment and verification scenarios. Be explicit this is OPTIONAL and NOT claimed implemented unless hardware/network testing actually occurs. Do not replace the core research emphasis with packet-based IDS/traffic ML.

### 17. Required documentation and handover

Deliver a professional README and these documents:
- `docs/client-scope-and-limitations.md`: behavioral authentication focus, five participants, no cross-application monitoring, optional physical NAC;
- `docs/architecture.md`: logical components, state machine, data and control plane diagrams, sequence and threat model;
- `docs/stack-and-prerequisites.md`: runtime versions, OS, tool install, ports and resource requirements;
- `docs/development.md`: bootstrap, environment variables, common commands, migrations, seed and troubleshooting;
- `docs/deployment.md`: local and production single-server step-by-step;
- `docs/api.md`: reference to OpenAPI plus key examples;
- `docs/privacy-and-ethics.md`: consent, collection exclusions, retention, withdrawal and non-collection guarantees;
- `docs/ml-methodology.md`: features, datasets, participants, train/validation/test grouping, algorithms, formulas, thresholds and reproducibility;
- `docs/test-plan.md`: at least 25 objective test cases with evidence capture and pass/fail rules;
- `docs/acceptance-criteria.md`: project-wide acceptance gate;
- `docs/optional-8021x-nac.md`: phase 2 design;
- `docs/known-limitations.md`: realistic limits, demo vs research vs enterprise distinctions.

Provide actual diagrams in Mermaid source where useful. Preserve user privacy: only synthetic/demo screenshots in public-facing documentation unless explicit consent exists. Provide report-generation code for empirical metrics/figures and a clear explanation of unavailable results when no real collection is loaded.

### 18. Concrete acceptance criteria (do not mark complete without verification)

AC-01: clean checkout with supported prerequisites can build, launch and run core services.
AC-02: real Keycloak OIDC login succeeds; bad credentials fail; real MFA/step-up challenge blocks protected resource until completed.
AC-03: consent-based JS feature collection works; excludes all sensitive fields/text, and submits validated numeric-only windows.
AC-04: train at least one user-specific model on permitted sample features; model registry and held-out split are correct; do not claim empirical performance from synthetic-only data.
AC-05: risk engine can produce LOW, CHALLENGE, RESTRICT, REVOKE and INSUFFICIENT_EVIDENCE states, logging why each was selected.
AC-06: two user roles produce different real protected resource access through Envoy.
AC-07: direct protected upstream cannot be reached from participant host; no bypass port is published.
AC-08: admin-revoked active session immediately fails subsequent protected requests, regardless of browser UI state.
AC-09: risk-based MFA is real; no UI-only mock button unlocks access.
AC-10: admin dashboard reflects genuine backend data and audit trails; seeded demo entries are explicitly marked.
AC-11: session-grouped metrics use correct labels and clearly show sample size, train/test provenance, and FAR/FRR.
AC-12: automated unit, integration, e2e and gateway authorization smoke tests pass in the documented environment.
AC-13: local Compose boots repeatably, survives restart with persisted data, and produces no leaked production secrets.
AC-14: production Compose and deployment runbook are provided, with remote deployment status not overstated.
AC-15: all major requirements map to implementation files, validation steps and documentation.

### 19. Implementation order and completion procedure

Work in phases and actually create files throughout, not merely describe them:
1. Inspect repo -> inventory and gap report, with read-only Git status.
2. Architecture/contracts/ADRs -> Compose skeleton, DB schemas, services health endpoints.
3. Keycloak auth/roles/MFA, protected resource and real Envoy/OPA enforcement.
4. Consent, participant tasks and numeric behavioral window aggregator.
5. Dataset protocol, feature quality, ML training/comparators and model registry.
6. Risk orchestration, session revocation, step-up and restriction, complete event audit.
7. Participant/admin UI and research evaluation dashboards.
8. Test suite, security hardening, local validation and performance probes.
9. Production deployment artifacts, backup/restore, operator manuals and optional physical NAC design.
10. Run comprehensive verifications, repair failures and produce final factual delivery summary.

If the work is too large for one coding run, leave the repository in a buildable state, commit nothing, write `docs/IMPLEMENTATION_PROGRESS.md` with file-level progress and exact next commands, then continue from that file when invoked again. Never imply remaining phases are complete.

### 20. Final response from Codex

Once code changes are finished, report only observed facts:
- files/modules created or modified;
- exact commands run and whether they passed;
- URLs of running local services if genuinely started;
- MFA and protected-resource enforcement results supported by actual tests;
- whether real five-user data was collected (normally NOT unless explicitly supplied);
- how to start, test and deploy, with copy-paste commands;
- remaining human steps (consent, real participant collection, real server/domain credentials, physical NAC hardware if chosen);
- unresolved blockers/limitations, without claiming complete A-Z delivery unless acceptance gates are actually satisfied.

**START NOW. Build the actual application and infrastructure in the currently opened repository, prioritize authentic enforcement and verifiable research results, and complete as much of the end-to-end specification as the available environment permits.**
