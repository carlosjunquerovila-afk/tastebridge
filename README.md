# TasteBridge — Find your common ground

A Qloo-powered group decision tool by **Carlosjv**.

**Live demo:** https://tastebridge-carlosjv.zrm7tv2zmj.chatgpt.site

## What it does

A host reviews one cultural preference for each of 2–6 guests and a shortlist of 2–5 places. TasteBridge checks host-reported budgets, accessibility needs and vetoes before asking Qloo for each guest’s cultural affinity over the same eligible places. It compares within-query midranks, maximizing the lowest rank before the mean. Ties stay visible; the group makes the final decision.

Qloo provides the search and affinity evidence. Prices and accessibility facts are host-reported. Missing or constant evidence causes abstention rather than invented scores. This is a bounded deterministic decision tool, not a tested autonomous LLM agent, and ranks are not satisfaction probabilities.

## Download and extract the complete live source

Download [`TasteBridge-0.3.2-source.zip`](TasteBridge-0.3.2-source.zip) from this repository and extract it before following the source paths below. The archive includes all tracked hosted source, assets, vendor notices, tests, and submission evidence. No credentials or installed dependencies are included.

```sh
unzip TasteBridge-0.3.2-source.zip
cd hosted
pnpm install --frozen-lockfile
node test-policy.mjs
pnpm build
```

SHA-256: `8bb5a9f5a2d046595b932259f2fd1eb898f620cc8298a1e6e03fc2648b106a91`.

## Source map (inside the archive)

- `hosted/`: exact source snapshot of the public Vinext/Workers demo, from hosted commit `6a47cbcd97239aa9da7864156d19046c13238310`.
- `backend/`: earlier Python 0.2.2 local runtime and tests.
- Root static files and `hosted/public/lab/`: earlier explicitly synthetic policy lab; not the live provider integration.
- `submission/HOSTED_EVIDENCE_20261019.json`: redacted real hosted HTTP workflow evidence.
- `submission/DEVPOST_STORY_20261019.md`: reviewed text prepared for the existing Devpost entry; this file is not proof of submission.

## Run the hosted implementation

Requires Node >=22.13 and pnpm. From `hosted/`, run `pnpm install --frozen-lockfile`, `node test-policy.mjs`, then `pnpm build` (the included Sites build integration is required). The hosting platform must provide a D1 binding named `DB`, apply `drizzle/0000_tan_spyke.sql`, and inject `QLOO_API_KEY` as a server-only secret. Use your own registered project ID when deploying a separate instance; never overwrite the maintainer’s deployment. Sites deployment uses its supplied build/package workflow. See `hosted/README.md` and the included scripts for details.

No API key is included. The existing public demo can be used without installing anything or supplying credentials. A persistent 60-call application allowance and one-hour cache bound provider use; this is not a representation of Qloo’s quota. There is no automatic refill or retry.

## Verified scope

On 19 October 2026, a hosted HTTP test completed four real searches and two real Qloo Insights calls, producing an explicitly tied shortlist. Test preferences and prices were synthetic operator inputs; provider evidence was real. The public homepage, API metadata and a cached search were reachable without sign-in. Ten hosted policy checks and 52 Python regression tests passed. Browser visual QA and a comparative benchmark against LLM-only recommendations have not been completed.

## License

MIT, see `LICENSE`. Retained dependencies and vendor files keep their respective license notices. No booking, payment, personal identity inference or autonomous paid model call is performed.

## Recorded case and policy trade-off

The demo now offers an explicitly dated replay of real Qloo evidence that makes no live API calls. Live queries remain capped. `hosted/benchmark-policy.mjs` enumerates 216 synthetic 3-guest/3-option ordinal profiles; max-min improves the worst rank in 27 cases compared with mean-only, at an average mean-rank sacrifice of 0.013889. This is not a user-satisfaction or LLM benchmark.
