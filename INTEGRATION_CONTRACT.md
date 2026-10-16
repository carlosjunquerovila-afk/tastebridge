# TasteBridge live integration acceptance contract

Status: design only. No live adapter or credential is present. The synthetic engine must not be relabeled as Qloo-connected.

1. Keep the event credential exclusively in a server-side secret. Never ship it in dist/, logs, browser requests, exports, screenshots or repository history.
2. Use explicit guest-provided cultural likes, with pseudonymous session participant IDs. Resolve entities through the official Qloo interface and ask guests to review ambiguous matches. Do not infer sensitive attributes.
3. Keep Qloo affinity provenance separate from operational facts. Each signal needs source entity, candidate entity, retrieval time and a documented interpretation. Do not assume scores from different requests are calibrated or comparable. Validate that assumption before applying max-min across guests.
4. Keep independent venue evidence for price, accessibility and availability. Unknown required facts hold the option for clarification. A cultural affinity response cannot supply these facts implicitly.
5. Agent workflow: clarify intent -> resolve reviewed entities -> retrieve bounded evidence -> validate candidates -> invoke deterministic decision tool -> explain trade-off -> request group confirmation. The current prototype implements only the synthetic decision/confirmation portion.
6. Set explicit call/time limits. Auth failures, quota limits, timeouts and malformed responses must produce a visible blocked or clarification state. Never fall back silently to fictional fixtures in live mode.
7. Test real success, authentication failure, rate limiting, unknown entity, incomplete operational evidence and no feasible candidate. Redact credentials from retained traces. Record fixture tests separately from live integration results.
8. Evaluate Qloo contribution against a baseline on the same candidates and constraints. Record query and candidate selection procedure before comparison. Do not hand-pick only favorable cases or call synthetic utility guest satisfaction.
9. Release only with a public open-source repository, licensed dependencies, a working externally accessible demo, and completed end-to-end checks. A private Sites publication is not a competition-ready public demo.

Official references to verify when implementing:
- https://github.com/qloo/qloo-hackathon-kit
- https://qloo.devpost.com/resources
- https://qloo.devpost.com/rules

No endpoint schemas or live score normalization are assumed by this document.
