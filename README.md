# TasteBridge — Find your common ground

A Qloo-powered group decision tool by **Carlosjv**. MIT licensed.

**Working demo:** https://tastebridge-carlosjv.zrm7tv2zmj.chatgpt.site/

## What the tool does

One host reviews a public cultural preference for each of 2–6 guests and 2–5 places in the same area. Budget, host-reported accessibility facts and group vetoes are applied first. Qloo then supplies taste evidence for each guest over the same feasible shortlist. Within-query midranks protect the lowest guest rank, with the mean used to break ties. Tied leaders stay visible. The group makes the final choice; the app makes no booking.

Qloo affinities are not probabilities of satisfaction. Prices and accessibility are host-reported, not independently verified. Missing or constant evidence causes abstention. This is a bounded deterministic decision tool; no deployed autonomous LLM agent or LLM superiority benchmark is claimed.

## Reproduce the current hosted source — version 14

This delivery includes a **self-contained full source patch**, [`hosted-v14.patch`](hosted-v14.patch), and the 147-file checksum inventory in [`SOURCE_SNAPSHOT_V14.json`](SOURCE_SNAPSHOT_V14.json). It reconstructs canonical hosted commit `2c24fa2b3a0e27af746e9eb6b037588bf4032a2d`, published as Sites version 14 on 30 October 2026. The deployment receipt is appgdep_6ae4ec9487648191bef906b00d6fba0a; Devpost receipt and eligibility remain separate. The historical ZIP and v9 patch are retained for history but are not needed for this reconstruction.

Use Python 3 and Git. From a clone or download of this repository:

```sh
python3 reproduce_hosted_v14.py
```

The helper creates a new `reproduced-v14/hosted/` directory. It checks the patch's SHA-256 and size before applying it, verifies the complete reconstructed file inventory, and regenerates the two public source-distribution artifacts. It verifies the resulting ZIP against the snapshot archive checksum. An existing destination is refused. The helper creates only an isolated local Git repository; it has no remote and makes no network, provider or payment calls. Run `python3 reproduce_hosted_v14.py --output PATH` to select another new destination.

Source patch SHA-256: `8ee24de3079d227b70b3021b4ade6fafaec419310ab6bb4e4dff440bbe70da87`.

Generated source ZIP SHA-256: `b55dbb9fb0e739afc082af5f407cd397ac59a7335464919340d40576bf67f06e`.

Hashes establish equality of bytes, not independent authenticity or security. The snapshot includes application code, assets, dependency locks, tests, license notices and build scripts. It excludes installed dependencies and runtime secrets/data. Dated notes inside the hosted README record the conditions when those releases were authored; this root README defines this v14 source delivery.

## Run and test

Use Node 24 and the pinned package manager in `hosted/package.json`. From `reproduced-v14/hosted/`, these decision and route checks require no API key and make no provider calls:

```sh
node test-policy.mjs
node test-rank-stability.mjs
node test-recovery.mjs
node test-api-local.mjs
node test-search-revision.mjs
node test-security-validation.mjs
node test-live-readiness.mjs
```

Install the locked dependencies to run the guest-identity harness or build:

```sh
pnpm install --frozen-lockfile
node test-guest-identity.mjs
pnpm build
```

The included Sites/Vinext integration is required. Hosting requires a D1 binding named `DB`, the migration `drizzle/0000_tan_spyke.sql`, and an existing authorized `QLOO_API_KEY` injected as a server-only secret. Use your own registered project identity for a separate deployment; do not overwrite the maintainer's site. Deployment uses the supported Sites build/package workflow. No credentials are included in source.

The public demo needs no visitor key. Its global durable allowance is 60 provider calls, with a one-hour cache and no automatic refill or retry. This is an application limit, not Qloo's provider quota. The explicitly dated recorded example works without new provider calls and is never substituted silently for live evidence.

## Readiness disclosure

Before a live plan, the interface shows a read-only snapshot of configuration presence and the shared remaining allowance, with an explicit link to the dated recorded example. A refresh does not contact Qloo or reserve allowance. A configured connection is not proof of a valid key or healthy provider; zero remaining new calls does not rule out still-cached queries.

The focused readiness checks cover configuration, unknown/exhausted allowance and presentation messages without live provider calls. The 60-call ceiling remains in place. A replay and this readiness disclosure do not establish unrestricted live access throughout judging or full compliance with that testing condition.

## Verify the demonstrated behavior

- Open the recorded example: two test profiles disagree and the policy returns a tie. Applying a veto leaves too few eligible places and produces recovery guidance.
- For the v13 regression, add a third guest, type Arrival / Spirited Away / The Matrix without searching, then remove the first guest. The remaining fields retain Spirited Away / The Matrix. A newly added guest starts empty.
- Unknown facts, over-budget options, accessibility conflicts and vetoes remain blockers; the recovery plan preserves the entered constraints.

The guest identity guard passes 2/6 expectations on v12 and 6/6 on v13; the corrected case was also checked in the production browser. Existing policy, recovery, rank and mocked route checks pass. The tests use synthetic inputs and mocks where documented. No new Qloo request was needed for the v13 repair.

Real provider evidence was recorded on 19 October: four hosted searches and two Insights calls produced an explicitly tied shortlist. Test preferences and prices were operator fixtures; the provider evidence was real. The synthetic policy benchmark covers 216 ordinal profiles: max-min changes 27 decisions versus mean-only and improves the minimum rank in those cases. Neither result measures real-user satisfaction or proves an award-winning outcome.

## Source and history

The v13 full patch, manifest and reproduction helper remain historical artifacts when retained in the repository; this snapshot uses the filenames above.

- Reconstructed `hosted/`: the current Vinext/Workers application and its tests.
- `hosted/public/lab/`: the earlier explicitly synthetic policy lab.
- Repository root and `backend/`: earlier static lab and Python runtime, retained as history.
- `TasteBridge-0.3.2-source.zip`, `hosted-v9.patch` and `SOURCE_SNAPSHOT_20261026.json`: historical v9 reconstruction; not needed for v13.
- `submission/HOSTED_EVIDENCE_20261019.json`: redacted historical hosted workflow evidence, if present in the existing repository history.

## License and limitations

MIT, see `LICENSE`; retained third-party components preserve their notices. The tool does not infer identities, make reservations or perform payments. Provider coverage and the finite live allowance can limit live operation. No customer outcome, prize, competition ranking or general AI superiority is claimed. Source publication is separate from a Devpost submission receipt.
