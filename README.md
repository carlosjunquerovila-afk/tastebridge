# TasteBridge

Group cultural decision lab by Carlosjv. Developed with AI assistance. MIT licensed.

## Status
Synthetic offline prototype, not a completed Qloo submission. All venues, costs, facts and preferences are fictional. No live Qloo integration, model inference, real recommendations, bookings, verified group consent or revenue is claimed. API access was requested on 16 October 2026 and remains pending.

## Run
Requires Node.js 22+ for the tests and Python 3 for this optional local static server. No package installation is needed.

```sh
node test.mjs
python3 -m http.server 8000 --bind 127.0.0.1
```

Open http://127.0.0.1:8000 in your browser. The application is browser-local and does not persist sessions or send form inputs to a backend. Optional Google Fonts requests expose ordinary network metadata to the font provider.

## Decision policy
Filter individual vetoes, budget and required step-free evidence before ranking by the lowest of three declared preference proxies, then mean, then locale-independent candidate ID. Unknown evidence holds an option for clarification. Mean-only comparison makes the trade-off visible. This policy does not establish real satisfaction or universal fairness.

Confirmation applies only to the local test. Input changes clear it. JSON exports are explicitly synthetic, and invalid updates cannot export a stale result.

## Validation
26 internal checks pass, including one generated-case check with 200 deterministic synthetic candidate sets. Checks cover constraints, missing evidence, malformed values, sparse arrays, permutation stability and confirmation lifecycle. They are not external validation or live Qloo results. Desktop smoke tests on the public GitHub Pages demo verified the baseline comparison, individual veto, zero-budget abstention, missing-evidence clarification and confirmation invalidation. Mobile, export download and live integration QA remain pending.

## Known gaps before submission
- Live Qloo-backed agent workflow and explicit provenance.
- Validation that affinity signals are comparable before group aggregation.
- Independently sourced operational facts or clarifying questions.
- Full end-to-end verification of the future live integration.
- Real usefulness and commercial validation.

See INTEGRATION_CONTRACT.md for acceptance requirements. A subscription concierge for independent accommodation hosts is a hypothesis, not a validated business.

## Audit finding corrected
Revision 2 allowed sparse JavaScript score arrays to bypass validation and produce NaN. Revision 3 materializes the array and abstains on missing evidence; a regression check reproduces the case. Missing score containers now clarify, while malformed containers and flags are rejected explicitly.

## Public demo and connector progress

https://carlosjunquerovila-afk.github.io/tastebridge/

The demo is public and still synthetic. A server-only CLI search adapter is now included; it is not wired to the demo and has not made a successful live request. See CONNECTOR_STATUS.md for installation checks, nine mock tests and the missing credential blocker.
