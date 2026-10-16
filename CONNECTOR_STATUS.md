# Qloo connector status — 16 October 2026

Implemented: a trusted Node.js wrapper for the official CLI entity-search command. It is NOT an agent, ranking integration, HTTP service or deployed backend. The public browser demo remains synthetic.

## Verified
- Official @qloo/qloo-harness 0.1.26 installed in an isolated development directory using npm with lifecycle scripts disabled.
- Version command returned 0.1.26. Search help confirms --query, --json and --dry-run.
- Nine mock subprocess tests passed: no-key behavior, argument isolation, fixed hackathon origin, call budget, bad input, response validation, credential echo protection, redacted errors, timeouts and missing binary.
- The documented dry-run command was attempted without a key; the CLI returned AUTH_FAILED before producing a request. No successful live call or completed dry-run is claimed.

## Run the tests
```sh
node qloo-search.test.mjs
```

## Intended trusted-process use
Install the official CLI version 0.1.26 or a separately reviewed compatible version; ensure qloo is on PATH. Read a real event credential from a server-side secret into createQlooSearch({apiKey: process.env.QLOO_API_KEY}). Never put a credential in source, a static bundle, logs or command-line arguments.

The adapter uses execFile with shell disabled, a 15-second timeout, a 512 KiB output cap and three attempts per adapter instance by default. The instance must be shared at the intended scope: this is NOT a deployment-wide rate limiter. Failed requests also consume that budget. No automatic retry or fixture fallback is performed.

Only pass reviewed cultural titles or concepts. No free-form guest biography, contact details, medical requirements or personal identifiers should enter this search path. The adapter does not constitute a general PII detector.

All returned JSON objects are labeled unvalidated_evidence, require entity review, and are not ready for ranking. This intentionally does not invent the upstream result schema or treat an error-shaped JSON object as validated data. Validation of the real response, entity review, affinity retrieval, cross-guest comparability, server hosting, authentication and browser integration remain unfinished. Upstream failure classification is deliberately generic until the actual documented error contract is verified.

## References
- https://github.com/qloo/qloo-hackathon-kit
- https://github.com/qloo/qloo-hackathon-kit/blob/main/starter/cli-workflow/README.md

The key request remains pending as of the last mailbox check. Do not submit this as a completed Qloo integration.
