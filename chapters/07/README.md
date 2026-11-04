# Chapter 7. Retrieval, RAG and Vector-Store Cache Strategies

> Companion materials from [the book's Chapter 7](https://github.com/danraid/cache/blob/main/manuscript/07.md). All example programs and data are synthetic, not production validations.

## Practical Laboratory

This standalone Python 3 laboratory adds a small retrieval-result cache to a synthetic Helix boundary. It uses only the standard library. It is deliberately **not** a vector store, ANN benchmark, language-model evaluation or production authorisation service. Its token-overlap ranking makes the fixture reproducible.

The trusted caller supplies a tenant, principal and policy revision. The laboratory assumes policy revisions are updated reliably when permissions change. It validates the whole in-memory corpus fingerprint on every lookup; a production system would normally use a trustworthy published snapshot identifier rather than hashing an entire corpus per request.

Save as `helix_retrieval.py` and run:

```bash
python3 helix_retrieval.py
```

Executable Python source: [`helix_retrieval.py`](./helix_retrieval.py).

Run from the repository root: `python3 chapters/07/helix_retrieval.py`.

Expected output begins:

```text
All invariants passed.
hits=1 misses=5
```

The final line includes the source ID, chunk ID and deterministic SHA-256 content hash. The cache stores no generated answer. The assertions check that a repeat hits, another tenant misses, revocation prevents reuse, updated evidence receives a new hash, and a new index generation causes a miss even when the returned content is unchanged.

The example retains old cache entries in memory. They are unreachable under the changed key but not deleted; a production system needs bounded storage, eviction and possibly explicit deletion for confidentiality or retention obligations. It also needs authenticated principals, policy enforcement independent of caller-provided strings, atomic snapshot publication and concurrency controls. The script’s assertions are local invariant tests, not evidence that a deployed system is secure.

### Extending the replay

To evaluate a real Helix subsystem, record a fixed request trace with tenant-safe identifiers, query and configuration fingerprints, corpus and index snapshots, authorisation revisions, cache decisions and evidence locators. Replay the same requests against cache-disabled and cache-enabled paths using the same published snapshots and initial conditions. Include explicit cold and warm runs.

For each request, compare authorised retrieved IDs and relevant-evidence coverage; then assess the answer against an independently specified task criterion. Report hit rate and invalidations separately from correctness. Measure latency and resource consumption at defined boundaries; use actual billing records if making billing claims. Across a sufficiently representative sample, report uncertainty, such as a confidence interval for a paired mean latency difference, and describe the sampling unit and method. A deterministic six-call fixture cannot justify a population-level confidence interval.

## Exercises

All numerical data below are synthetic.

1. **Key design.** A result cache key contains query text, tenant and embedding-model version. The corpus and access policy can change independently. Name four missing dependencies or checks and explain one failure for each.

   **Checked solution.** Add a corpus snapshot to prevent reuse after source changes; an index generation and search configuration to distinguish different candidate spaces or search behaviour; principal/effective permission scope and policy revision to prevent reuse after revocation; and reranker version and selection parameters to prevent reuse of an ordering produced under a different ranking policy. Current authorisation must still be checked on access.

2. **Latency.** Using the worked-example costs, calculate total latency for ten requests with four valid hits and six misses, first with caching enabled and then with caching disabled. Assume the same sequential model for every request.

   **Checked solution.** Enabled: \(4(103)+6(165)=1{,}402\) ms. Disabled: \(10(162)=1{,}620\) ms. The illustrative difference is 218 ms. This comparison says nothing about correctness unless all four hits satisfy the reuse contract.

3. **Unreturned documents.** A cache stores source hashes for its two returned chunks. A third, previously irrelevant document is edited and becomes the strongest match. Why can both stored hashes remain valid while the result cache is wrong?

   **Checked solution.** Neither returned chunk changed, but the ranking over the search universe did. Per-result hashes establish the identity of those chunks, not the completeness or ordering of the result set. A new trustworthy corpus/index snapshot must invalidate the old search result.

4. **Laboratory modification.** Add a new authorised chunk to `h.chunks` after a hit, then repeat the query without changing `index_generation`. What should happen under this toy implementation, and why might this differ from a production index?

   **Checked solution.** The request misses because `snapshot()` hashes every current chunk, including the new one. In production, the published index might not yet contain that document; the system must define whether it searches the last published snapshot or waits for a new one. It must not label a mixture of corpus and index states as a coherent snapshot.

5. **Evaluation design.** A semantic retrieval cache produces 80 hits on 100 eligible requests; manual assessment finds eight of those hits invalid. Calculate valid-reuse precision and coverage, then identify a limitation.

   **Checked solution.** Precision is \(72/80=90\%\); hit coverage is \(80/100=80\%\). The numbers do not reveal the severity of invalid hits, performance on future workloads, or whether the resulting answers were correct. Threshold selection and final assessment should use separate data.
