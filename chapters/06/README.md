# Chapter 6. Semantic Caching and Similarity Thresholds

> Companion materials from [the book's Chapter 6](https://github.com/danraid/cache/blob/main/manuscript/06.md). All example programs and data are synthetic, not production validations.

## Practical Laboratory

The following **original illustrative** laboratory uses Python’s standard library only. It does not call a model, a real embedding service or a vector database. Fixed vectors make the similarity calculations reproducible; the strings are identifiers, not actual embedded text. The cache performs an exact scan after filtering. Its version and authorisation checks demonstrate control flow, not a complete production security system.

Save as `helix_semantic.py` and run with `python3 helix_semantic.py`.

Executable Python source: [`helix_semantic.py`](./helix_semantic.py).

Run from the repository root: `python3 chapters/06/helix_semantic.py`.

Expected output:

```text
cal t=0.95: accepted=2, precision=1.000, coverage=0.333
cal t=0.90: accepted=4, precision=0.750, coverage=0.667
cal t=0.80: accepted=6, precision=0.667, coverage=1.000
test t=0.95: accepted=1, precision=1.000, coverage=0.250
Helix isolation, version, expiry and admission checks: PASS
```

The first lookup deliberately contains a more similar tenant-B entry and an unadmitted tenant-A entry. Both are excluded before scoring can select a result. The policy-change assertion demonstrates a miss despite unchanged wording and vector. Expiry is inclusive: an entry is invalid at `now == expires_at`.

The calibration rows and cache entries serve different purposes. The rows model labelled candidate decisions; the cache tests demonstrate boundary enforcement. The code does not prove that the synthetic answer is semantically valid, that the Boolean admission flag reflects real validation, or that a database enforces equivalent isolation. A production extension would add a trusted identity provider, durable provenance, event-driven invalidation, access-controlled storage and an independently assessed test corpus.

For a reproducible performance experiment, compare this policy with a no-semantic-cache baseline on the same request trace and compatible source versions. Define cold and warm states, record per-request lookup and fresh-path timings, and calculate paired differences. Keep task correctness and authorisation failures as release constraints rather than averaging them into latency.

## Exercises

1. **Threshold calculation.** Add a valid calibration pair with score 0.94. Recalculate precision and coverage at 0.90 and 0.95. Does the stated selection rule change?

2. **Policy conflict.** A query and entry have similarity 0.999, but their policy versions differ. What should Helix do? Would lowering the threshold change the answer?

3. **Uncertain precision.** A test contains 100 eligible requests and accepts none. What are coverage and precision? Why should this not be reported as perfect precision?

4. **Invalidation design.** A source document is revoked after an entry is admitted but before its TTL expires. Name two actions the harness should take and one operational risk that remains.

5. **Experiment design.** Propose a comparison between an exact cache and a semantic cache. Specify the split, at least two correctness measures and two cost or latency measures.

### Checked solutions

1. At 0.90, five requests are accepted, four valid: precision \(4/5=80\%\), coverage \(5/7\). At 0.95, two are accepted, both valid: precision \(2/2=100\%\), coverage \(2/7\). The rule still selects 0.95.
2. Reject the entry before similarity selection and use the fresh path if authorised. Threshold changes cannot override a hard policy-version mismatch.
3. Coverage is \(0/100=0\%\); precision is undefined because its denominator is zero. No accepted decisions have been tested.
4. Invalidate entries linked to the revoked source and ensure new requests use the current authorised source or abstain. Delayed or lost invalidation events can still expose stale entries; version checks and monitoring are needed.
5. Use separate calibration and held-out request groups, keeping related requests or source clusters together where appropriate. Compare invalid-reuse rate and end-to-end task success, plus coverage. Measure end-to-end latency, including tail latency, and total estimated or billed cost with lookup and storage overhead stated. Keep the workload, permissions and source versions matched.
