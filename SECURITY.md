# Security

## API keys and secrets

- Never commit real API keys (OpenAI, Groq, database passwords, `JWT_SECRET`) to the repository.
- Use environment variables or a secrets manager in production; rotate keys if they were ever exposed (including in chat or logs).
- Prefer short-lived credentials and separate keys per environment (dev/staging/prod).

## Authentication and sessions

- The API uses HTTP-only cookies for access tokens in browser flows. Keep `cookie_secure=true` and HTTPS in production.
- Use a strong, random `JWT_SECRET` (not the default `change-me`).

## Public share links

- A share URL grants **read-only** access to the design artifact for anyone with the token.
- Treat share tokens like passwords: do not paste them in public channels; **revoke** a link when it is no longer needed (`DELETE /api/designs/{id}/share`).
- Responses under `/api/public/*` are sent with `Cache-Control: no-store` and related headers to reduce accidental caching by intermediaries.

## Dependency and supply chain

- Run `npm audit` / `pip audit` periodically and apply updates for critical CVEs.
- CI runs backend tests and a frontend build plus Playwright smoke tests on each push/PR.

## Reporting issues

- For responsible disclosure of security vulnerabilities, contact the maintainers privately with reproduction steps and impact; avoid filing public issues with exploit details until addressed.
