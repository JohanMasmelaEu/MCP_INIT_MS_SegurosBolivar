# Secure Coding Rules — Seguros Bolivar

## Global Principles
- Security by Design
- Zero Trust Input (all input is malicious until validated)
- Prefer allowlists over blocklists
- Least privilege in app, DB, cloud, and CI/CD
- Generic errors to user, details only internal
- Never hardcode secrets

## Backend Validation
- Validate type, format, length, range, enum, and presence on the server ALWAYS
- Normalize inputs (trim, unicode)
- Limit body, header, query param, and file sizes
- Reject unexpected keys

## SQL / NoSQL / Command Injection
- Prepared statements / parameterized queries ALWAYS
- Never concatenate strings for SQL
- Never exec() with user input or shell=True

## Authentication and Sessions
- Short-lived tokens + refresh rotation
- Cookies: Secure + HttpOnly + SameSite
- Rate limit + lockouts against brute-force

## Authorization (BOLA/IDOR)
- Validate permissions on every request
- Never trust client-side IDs
- Explicit per-resource verification

## Security Headers
- HSTS, CSP, X-Content-Type-Options: nosniff, X-Frame-Options
- Force HTTPS, block unused HTTP methods

## Information Leakage
- No PII/secrets in logs, traces, errors
- API responses with allowlisted DTOs, never full objects
- Never expose stack traces to client
