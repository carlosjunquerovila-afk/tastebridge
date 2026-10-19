# Integration contract — hosted revision

The current hosted source is `hosted/`; `backend/` retains the earlier local Python implementation.

1. Search only bounded public cultural titles/place names against the fixed official Qloo event origin. Show address and description for review; no silent place selection.
2. Authenticate reviewed entity selections with server-side HMAC proofs that expire after one hour.
3. Apply host-reviewed price, accessibility and veto constraints before cultural ranking. Facts expire after 24 hours.
4. Query each guest over the identical feasible shortlist. Require complete finite and discriminating affinity evidence; otherwise abstain.
5. Convert scores to within-query midranks. Maximize minimum guest rank, then mean. Display ties explicitly; do not label ranks as probabilities.
6. Require group confirmation. Do not book, pay, infer identities or call a paid model API.
7. Keep credentials server-only, reject redirects/non-2xx, cap response size at 2 MB and timeout at 15 seconds. Durable SQL permits at most 60 provider calls for this demo revision, with a one-hour cache and no automatic retries.
8. Invalidate displayed proposals on edits and ignore evaluation responses from an older input revision.

The hosted HTTP path has real provider evidence. The synthetic decision-policy lab remains a separate historical teaching artifact. Browser visual QA and autonomous LLM-agent execution are not claimed.

Source paths refer to the extracted `TasteBridge-0.3.2-source.zip` archive published at the repository root.
