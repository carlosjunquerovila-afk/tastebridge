# TasteBridge — Find your common ground

A Qloo-powered group decision tool by **Carlosjv**.

**Live demo:** https://tastebridge-carlosjv.zrm7tv2zmj.chatgpt.site

## What it does

A host reviews one cultural preference for each of 2–6 guests and a shortlist of 2–5 places. TasteBridge checks host-reported budgets, accessibility needs and vetoes before asking Qloo for each guest’s cultural affinity over the same eligible places. It compares within-query midranks, maximizing the lowest rank before the mean. Ties stay visible; the group makes the final decision.

Qloo provides the search and affinity evidence. Prices and accessibility facts are host-reported. Missing or constant evidence causes abstention rather than invented scores. This is a bounded deterministic decision tool, not a tested autonomous LLM agent, and ranks are not satisfaction probabilities.

## Reproduce the deployed source from the historical archive

The existing [`TasteBridge-0.3.2-source.zip`](TasteBridge-0.3.2-source.zip) plus [`hosted-v9.patch`](hosted-v9.patch) reconstructs all **137 tracked hosted source files** at deployed canonical commit `b9a5087699f6d84f7723eb88347c43eacf5f8819` (site version 9). The patch changes six files, including the two new test files. It is a complete source update; it does not require a new ZIP. The historical archive remains unchanged.

Download or clone this repository so the ZIP, patch and [`SOURCE_SNAPSHOT_20261026.json`](SOURCE_SNAPSHOT_20261026.json) are in one directory. The following commands verify both input hashes, extract into a new directory, check and apply the patch with Git, then verify the complete hosted file set against the canonical SHA-256 manifest. Use Python 3, Git and Node 24.

```sh
git clone https://github.com/carlosjunquerovila-afk/tastebridge.git
cd tastebridge
python3 - <<'PYTHON'
from pathlib import Path
import hashlib, json, subprocess, zipfile

manifest = json.loads(Path("SOURCE_SNAPSHOT_20261026.json").read_text())
for name, expected in [(manifest["base_archive"], manifest["base_archive_sha256"]),
                       (manifest["patch"], manifest["patch_sha256"])]:
    assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == expected, name
root = Path("reproduced-v9")
if root.exists():
    raise SystemExit("reproduced-v9 already exists; use a fresh directory")
root.mkdir()
with zipfile.ZipFile(manifest["base_archive"]) as archive:
    for info in archive.infolist():
        relative = Path(info.filename)
        assert not relative.is_absolute() and ".." not in relative.parts
        target = Path(archive.extract(info, root))
        mode = (info.external_attr >> 16) & 0o777
        if mode:
            target.chmod(mode)
patch = str(Path(manifest["patch"]).resolve())
subprocess.run(["git", "apply", "--no-index", "-p0", "--check", patch],
               cwd=root, check=True)
subprocess.run(["git", "apply", "--no-index", "-p0", patch],
               cwd=root, check=True)
hosted = root / "hosted"
actual = {p.relative_to(hosted).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
          for p in hosted.rglob("*") if p.is_file()}
assert actual == manifest["source_file_hashes"], "Hosted file set or hashes differ"
print("Verified", len(actual), "hosted files against the canonical v9 manifest")
PYTHON
cd reproduced-v9/hosted
node test-policy.mjs
node test-rank-stability.mjs
node test-api-local.mjs
pnpm install --frozen-lockfile
pnpm build
```

Historical ZIP SHA-256: `8bb5a9f5a2d046595b932259f2fd1eb898f620cc8298a1e6e03fc2648b106a91`.

Patch SHA-256: `048564190e41ec309d141dc4c237b9070f5ac4b47796631972ccbf1c6897aa02`.

The three direct tests require no installed dependencies, API key, network or provider calls. A full application build additionally requires the locked dependencies and supported Sites build integration. The manifest hashes verify source bytes; they do not replace review or an independent trust anchor.

## Source map (after reconstruction)

- `hosted/`: exact source snapshot of the public Vinext/Workers demo, from hosted commit `b9a5087699f6d84f7723eb88347c43eacf5f8819`.
- `hosted/public/lab/`: the earlier explicitly synthetic policy lab; not the live provider integration.
- The repository root and its `backend/` directory, outside this ZIP, preserve the earlier static lab and Python 0.2.2 local runtime.
- `submission/HOSTED_EVIDENCE_20261019.json`: redacted real hosted HTTP workflow evidence.
- `submission/DEVPOST_STORY_20261019.md`: reviewed text prepared for the existing Devpost entry; this file is not proof of submission.

## Run the hosted implementation

Use Node 24 (verified with 24.22.1) and pnpm. The project engine minimum is Node 22.13; older Node 22 builds may require experimental TypeScript stripping for the direct tests. From `reproduced-v9/hosted/`, run the commands above (the included Sites build integration is required). The hosting platform must provide a D1 binding named `DB`, apply `drizzle/0000_tan_spyke.sql`, and inject `QLOO_API_KEY` as a server-only secret. Use your own registered project ID when deploying a separate instance; never overwrite the maintainer’s deployment. Sites deployment uses its supplied build/package workflow. See `hosted/README.md` and the included scripts for details.

No API key is included. The existing public demo can be used without installing anything or supplying credentials. A persistent 60-call application allowance and one-hour cache bound provider use; this is not a representation of Qloo’s quota. There is no automatic refill or retry.

## Verified scope

On 19 October 2026, a hosted HTTP test completed four real searches and two real Qloo Insights calls, producing an explicitly tied shortlist. Test preferences and prices were synthetic operator inputs; provider evidence was real. The public homepage, API metadata and a cached search were reachable without sign-in. Ten hosted policy checks and 52 Python regression tests passed. Subsequent recorded-case browser checks were completed on 26 October. At a 390-pixel mobile viewport, the translated replay button now fits within the 375-pixel document width (305-pixel button, right edge 340); no horizontal document overflow was observed. Recorded replay also returned an honest tie and abstained when a veto left only one option. A comparative benchmark against LLM-only recommendations has not been completed.

## License

MIT, see `LICENSE`. Retained dependencies and vendor files keep their respective license notices. No booking, payment, personal identity inference or autonomous paid model call is performed.

## Recorded case and policy trade-off

The demo now offers an explicitly dated replay of real Qloo evidence that makes no live API calls. Live queries remain capped. `hosted/benchmark-policy.mjs` enumerates 216 synthetic 3-guest/3-option ordinal profiles; max-min improves the worst rank in 27 cases compared with mean-only, at an average mean-rank sacrifice of 0.013889. This is not a user-satisfaction or LLM benchmark.

## Source synchronization — 26 October 2026

The historical ZIP plus the patch reconstructs all tracked hosted source files at canonical commit `b9a5087699f6d84f7723eb88347c43eacf5f8819`, deployed as site version 9. `SOURCE_SNAPSHOT_20261026.json` records the base archive, patch and per-file hashes. The dated statements in the archived hosted README describe the work at that time; this section records the latest source scope.

The update includes the 192,000-byte streaming request limit and immediate abstention when one guest has constant affinity evidence; it does not reset the provider allowance. It also replaces floating-point accumulation with integer half-rank units before normalization, so exact ties and guest-order invariance are preserved, and wraps long action labels on narrow screens.

The direct offline test commands cover 10 prior decision/constraint checks, five rank regression/invariance tests (including 5,000 deterministic mixed-tie profiles against an integer oracle), and route regressions with fetch and D1 mocked. They make no provider calls and require no API key. The coordinator verified the post-fix 390-pixel mobile layout and the recorded tie/veto paths in the connected browser on 26 October; no new provider request was made. These are software-correctness checks, not measured customer impact or proof of competition superiority.
