# Chapter 1. The Cache Problem in Agent Harness Engineering

> Companion materials from [the book's Chapter 1](https://github.com/danraid/cache/blob/main/manuscript/01.md). All example programs and data are synthetic, not production validations.

## Practical Laboratory

This first Helix component is an **original synthetic exercise**. It implements an in-memory, tenant-scoped cache for an immutable revision-lookup fixture. It does not call a model, retrieval service or external API. Its authorisation gate is deliberately small so that the boundary is visible; it is not a production identity system.

Save the following as `helix_ch01.py` and run it with Python 3 using `python helix_ch01.py`. It uses only the standard library.

Executable Python source: [`helix_ch01.py`](./helix_ch01.py).

Run from the repository root: `python3 chapters/01/helix_ch01.py`.

The first authorised request is a cold miss: an empty cache becomes populated with tenant A’s fixture value. The second is a warm hit. The third misses because tenant B has a separate key and receives its own revision. The fourth misses because changing the tool version changes the key. This is **logical invalidation by versioning**: the older entry remains in memory but is no longer selected by the new version. A production implementation would also need bounded retention and deletion.

The final request is denied before lookup, despite a matching tenant-A entry already being present. The JSON report should show four eligible requests, one hit, a hit rate of `0.25`, four checked correct outcomes and one denial. The trace records actual transitions in this simulation; it does not measure real latency or billing.

The fixture assumes every authorised actor within a tenant can read every fixture document. Real document-level permissions would require a more granular scope and current checks. The constant data version is safe only because the fixture is immutable; mutable sources require revision-aware keys or an explicit invalidation and freshness mechanism. Production telemetry should also avoid logging sensitive document contents or unnecessary identifiers.

## Exercises

1. **Trace arithmetic.** A cache sees the event sequence `miss, hit, hit, miss, hit`. Calculate its hit rate. If one hit returns an outdated result, what are the hit rate and correct-outcome rate, assuming all other outcomes are correct?

   **Checked solution:** Three of five requests are hits, so the hit rate is 60%. Four of five outcomes are correct, so the correct-outcome rate is 80%. The hit rate does not change merely because a hit was wrong.

2. **Key design.** Helix adds a retrieval cache. Identify at least four distinctions that can make two otherwise identical query strings unsafe to share.

   **Checked solution:** Tenant or authorisation scope; index or corpus revision; retrieval or reranker version; and query options such as filters. Depending on the implementation, language, embedding version and document-level permissions may also matter. Current authorisation must still be checked on a hit.

3. **Version experiment.** In the lab, change the fourth request’s tool version from `v2` to `v1` and update its expected event from `miss` to `hit`. Predict the hit rate before running it.

   **Checked solution:** The first request still misses; the second and fourth hit; the tenant-B request misses. The rate is two out of four, or 50%. The version test has been removed by this change, so restore the original fixture afterwards.

4. **Net benefit.** In the worked example, suppose cache B’s operation costs 320 rather than 20 units per 100 requests. What is its net monetary benefit relative to no cache, under the same other assumptions?

   **Checked solution:** Avoided tool cost is 300 units; cache operation costs 320. Net benefit is −20 units. Its assumed mean latency remains 50 ms, illustrating a latency–cost trade-off rather than an overall improvement.

5. **Design review.** An agent caches a successful permission check for an hour and then uses it to execute a document edit. Explain why a matching key may be insufficient and propose a safer boundary.

   **Checked solution:** Permission may be revoked during the hour. Check current authority at the action boundary, or use an explicitly specified and enforced authorisation mechanism with suitable validity and revocation properties. Do not assume TTL alone provides immediate revocation.
