# TasteBridge live integration acceptance contract

Status (19 October 2026): `backend/` contains a bounded Qloo HTTPS adapter and local application, tested with synthetic provider fixtures. No authenticated Qloo response, event credential, public backend or judge-accessible live demo has been verified. The root static demo remains synthetic and must not be relabeled as Qloo-connected.

1. Keep the event credential exclusively in a server-side secret. Never ship it in dist/, logs, browser requests, exports, screenshots or repository history.
2. Use explicit guest-provided cultural likes, with pseudonymous session participant IDs. Resolve entities through the official Qloo interface and ask guests to review ambiguous matches. Do not infer sensitive attributes.
3. Keep Qloo affinity provenance separate from operational facts. Each signal needs source entity, candidate entity, retrieval time and a documented interpretation. Do not assume scores from different requests are calibrated or comparable. Validate that assumption before applying max-min across guests.
4. Keep independent venue evidence for price, accessibility and availability. Unknown required facts hold the option for clarification. A cultural affinity response cannot supply these facts implicitly.
5. Agent workflow: clarify intent -> resolve reviewed entities -> retrieve bounded evidence -> validate candidates -> invoke deterministic decision tool -> explain trade-off -> request group confirmation. The backend implements a local function-tool path and deterministic decision policy; no embedded model, real Qloo result or end-to-end agent execution has been validated.
6. Set explicit call/time limits. Auth failures, quota limits, timeouts and malformed responses must produce a visible blocked or clarification state. Never fall back silently to fictional fixtures in live mode.
7. Test real success, authentication failure, rate limiting, unknown entity, incomplete operational evidence and no feasible candidate. Redact credentials from retained traces. Record fixture tests separately from live integration results.
8. Evaluate Qloo contribution against a baseline on the same candidates and constraints. Record query and candidate selection procedure before comparison. Do not hand-pick only favorable cases or call synthetic utility guest satisfaction.
9. Release only with a public open-source repository, licensed dependencies, a working externally accessible demo, and completed end-to-end checks. This public repository alone does not establish live functionality. A private Sites publication and the current synthetic GitHub Pages site are not a competition-ready live demo.

Official references to verify when implementing:
- https://github.com/qloo/qloo-hackathon-kit
- https://qloo.devpost.com/resources
- https://qloo.devpost.com/rules

No endpoint schemas or live score normalization are assumed by this document.
