# Production deployment: pfgcravings.com

PFG Cravings serves the buyer portal at `https://pfgcravings.com` and the protected seller portal at `https://pfgcravings.com/admin`. The Python service should listen only on `127.0.0.1:8000`; Caddy terminates TLS and proxies the requests locally.

## Before deployment

1. Register `pfgcravings.com` with a domain registrar if it is not already owned.
2. Choose one hosting path:
   - A public server with a stable public IPv4/IPv6 address; create an `A` record for `pfgcravings.com` and, if used, `www` to that address.
   - An office-hosted machine with a supported secure tunnel/reverse-tunnel provider; point the provider's required DNS record (often a CNAME) at the tunnel. Do not expose port 8000 directly.
3. Verify DNS resolves publicly before starting Caddy. Caddy can obtain and renew public certificates only when the certificate authority can validate the domain.
4. Copy `deploy/.env.production.example` to the server-side `.env` file and keep it private. The process deliberately refuses production startup if its origin, exact CORS allowlist, or secure-cookie settings are unsafe.
5. Install Caddy and run it with `deploy/Caddyfile`, setting `PFG_DOMAIN=pfgcravings.com` and `CADDY_EMAIL` in Caddy's service environment. Permit inbound TCP 80 and 443 only at the reverse proxy/firewall.
6. Start PFG Cravings with `python run.py`. Keep port 8000 bound to loopback and do not publish it through firewall or router rules.

## Required checks

After DNS and TLS are live, verify the certificate and redirect with a browser or `curl -I https://pfgcravings.com`, then sign in at `/admin`. The browser must show a valid certificate, HTTPS-only requests, and a `Secure; HttpOnly; SameSite=Lax` administrator cookie. API writes require the configured `Origin` and the session-specific CSRF token.

For Starlink/office internet connections that cannot accept inbound traffic, use a secure tunnel supported by the selected provider, and restrict its published hostname to `pfgcravings.com`. A tunnel provider and DNS records are external prerequisites; this repository cannot create or verify them.
