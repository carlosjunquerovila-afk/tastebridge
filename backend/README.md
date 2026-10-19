# TasteBridge backend 0.2.2

Local integrated candidate. Not a completed Qloo submission or public live demo.

Run with Python 3.12+: `python3 server.py`. Open http://127.0.0.1:8766 on the same machine. Run `python3 -m unittest -v` and `node test_ui.cjs`.

Verified internally: 52 Python tests and 8 simulated-DOM controller checks. Provider responses in tests are synthetic; zero successful authentic Qloo calls are claimed.

Default transport: fixed Qloo hackathon HTTPS origin, server-only credential, explicit entity review, bounded requests, no redirects/retries/fixture fallback, HTTP failure classification and response provenance. Set QLOO_API_KEY only as a server secret. Set QLOO_EVENT_ACCESS_CONFIRMED=1 only after real event access and free quota/expiry are verified.

The loopback server must not be exposed publicly. Public hosting, real provider traces, agentic interaction verification and browser end-to-end checks remain release gates. Midranks are ordinal policy, not satisfaction probabilities. Practical facts remain user-reported.

MIT license from repository root applies. Developed with AI assistance under Carlosjv.
