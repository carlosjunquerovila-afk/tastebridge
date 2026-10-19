# TasteBridge

A group cultural decision lab by **Carlosjv**, developed with AI assistance. MIT licensed.

## Current status (19 October 2026)

This repository contains two distinct builds:

| Build | Location | What it does | Limitation |
| --- | --- | --- | --- |
| Public static demo | [GitHub Pages](https://carlosjunquerovila-afk.github.io/tastebridge/) and root `index.html` | Explains and exercises the group decision policy with fictional venues and preferences. | Synthetic offline prototype; no Qloo requests, live recommendations or bookings. |
| Backend candidate 0.2.2 | [`backend/`](backend/) | Local HTTP interface, explicit entity review, Qloo HTTPS transport, bounded function-tool workflow and deterministic group comparison. | No authenticated Qloo success, publicly hosted backend, judge-accessible live demo or independent benefit measurement has been verified. |

The current Devpost project is a **draft**, not a submitted or winning entry. Do not interpret the static GitHub Pages demo as evidence that the backend is online. Qloo event access was requested and remains unverified in this repository.

## Run and verify

The static demo needs Node.js 22+ for its checks and Python 3 for an optional local server. It requires no package installation:

```sh
node test.mjs
python3 -m http.server 8000 --bind 127.0.0.1
```

Open `http://127.0.0.1:8000`. The static app stores no session on a backend and uses explicitly fictional examples. Optional Google Fonts requests expose ordinary network metadata to the font provider.

For the separate local backend candidate, use Python 3.12+:

```sh
cd backend
python3 -m unittest -q
node test_ui.cjs
python3 server.py
```

Open `http://127.0.0.1:8766` on the same machine. It binds to loopback and must not be publicly exposed in its current form. The code was checked on 19 October: 52 Python tests and 8 simulated-DOM controller checks passed. Provider responses in these tests are simulated; they are **not live Qloo validation**. See [backend/README.md](backend/README.md) for the current workflow, input limits and security boundaries.

## Decision policy

The static demo filters individual vetoes, budget and required step-free evidence before ranking by the minimum of three declared preference proxies, then mean and stable candidate ID. The backend filters the same hard constraints, explicitly reviews cultural entities and compares within-query ordinal midranks on the same feasible shortlist for every guest. Neither policy proves satisfaction, universal fairness or a real benefit. Missing or stale facts cause clarification or abstention. Confirmation remains with the group; the application does not book or pay.

## Submission gates

- An individually attributable event credential, published free quota and expiry, and a redacted successful Qloo request-to-result trace.
- End-to-end browser testing against the live backend and a functional demo accessible to judges for the judging period.
- A coherent agent or function-tool path demonstrably using Qloo, plus a comparison that separates measured outcomes from the synthetic policy illustration.
- Devpost fields, eligibility and any required legal acceptance completed by the entrant before final submission.

Read [CONNECTOR_STATUS.md](CONNECTOR_STATUS.md) for technical provenance and [INTEGRATION_CONTRACT.md](INTEGRATION_CONTRACT.md) for the remaining verification criteria. The official [hackathon rules](https://qloo.devpost.com/rules) control the entry requirements.
