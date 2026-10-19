# Qloo integration status — 19 October 2026

**Current evidence:** `backend/` contains a working loopback application and a direct HTTPS adapter that constructs bounded Qloo search and insights requests. It has **not** produced an authenticated Qloo response in the evidence available here. The public GitHub Pages build remains a separate fictional-data demo. The Devpost project remains a draft.

## Implemented locally

- `backend/qloo_http.py`: fixed `https://hackathon.api.qloo.com` origin; `/search` and `/v2/insights`; server-only `X-Api-Key`; no redirect, retry or synthetic fallback; timeout, output limit, error categories and SHA-256 response fingerprint. Keys are neither logged nor returned. Calls require both `QLOO_API_KEY` and an explicitly confirmed free event-access flag.
- `backend/qloo_adapter.py`: validated public entity names, type and count; explicit review of search matches; bounded shortlist IDs; response shape and finite-affinity checks.
- `backend/workflow.py`: 2–6 anonymous guests, at most three reviewed interests per guest, at most five reviewed places, facts with timestamps, hard constraints, equal feasible shortlist, within-query midranks, revision/cache controls and group confirmation. Practical facts are user-reported and not authenticated.
- `backend/server.py`: local HTTP function tool and browser interface. It binds to loopback; its local token, Host and Origin checks are **not a public-hosting security assessment**.

## Reproduced checks

On 19 October 2026, `python3 -m unittest -q` passed **52 tests**, and `node test_ui.cjs` passed **8 controller checks**. The Python tests exercise loopback HTTP and synthetic Qloo response fixtures, including failures and credential-redaction paths. The JavaScript test runs the real controller with a simulated DOM, not rendered-browser QA. No live request or independent outcome study was performed in these checks.

The older root `qloo-search.mjs` and its nine simulated subprocess checks remain historical work. It is not the adapter used by the current backend. The official `@qloo/qloo-harness` package contract was inspected to cross-check route and parameter names, but the direct backend adapter has not been accepted as an organizer-verified event integration.

## Release gates

1. Obtain and verify an individually attributable event credential and published free quota, rate limit and expiry. The requested access is still unconfirmed here. Do not paste any key into GitHub, Devpost, screenshots or chat.
2. Use a server-side secret, record one bounded successful search and shortlisted affinity request, check the actual response schema and redact the trace. An HTTP 200 alone is insufficient.
3. Run an end-to-end browser flow using the actual provider, including failed auth, rate limit, unknown entity, incomplete practical evidence, no feasible option and stale revision.
4. Host the working backend and interface free for judges through the judging period, with an appropriate public access and security design. A loopback URL is not a public demo.
5. Reconcile the Devpost text, source and demo links with the same tested version before the entrant finalizes the submission under the official rules.

Official references: [rules](https://qloo.devpost.com/rules), [event access and limits](https://github.com/qloo/qloo-hackathon-kit/blob/main/docs/API_ACCESS.md), [submission guide](https://github.com/qloo/qloo-hackathon-kit/blob/main/docs/SUBMISSION.md).
