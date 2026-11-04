# Chapter 8. Tool, API and Multi-Agent Result Caching

> Companion materials from [the book's Chapter 8](https://github.com/danraid/cache/blob/main/manuscript/08.md). All example programs and data are synthetic, not production validations.

## Practical Laboratory

The following original Helix exercise uses Python’s standard library and an in-memory synthetic invoice fixture. It models a deterministic read wrapper with a logical clock. It is **not** a production security implementation, distributed cache or external API benchmark.

The caller supplies a policy revision for the exercise; a real gateway must obtain it from a trusted policy service. The authorisation table is deliberately small and is checked before every cache lookup. Successful reads alone are cached. Side-effecting payment calls always execute.

Save as `helix_tool_cache.py` and run:

```bash
python3 helix_tool_cache.py
```

Executable Python source: [`helix_tool_cache.py`](./helix_tool_cache.py).

Run from the repository root: `python3 chapters/08/helix_tool_cache.py`.

The expected first line is `PASS`; the final call counts are `{'read': 8, 'pay': 2}`. The two extra reads arise from repeated missing-resource attempts. The logical clock makes the expiry boundary reproducible: an entry is valid only while `now < expiry`.

The test demonstrates tenant, principal, policy and tool-version separation; hit behaviour; expiry; denial before lookup; defensive copying; side-effect bypass; and non-caching of missing results. It does **not** demonstrate live revocation, distributed invalidation, concurrency safety, confidentiality at rest or resistance to malicious tool output. The `pay` operation is a counter, not a real payment.

For a larger experiment, replay the same fixed trace with caching disabled and enabled. Record eligible requests, upstream calls, hits, denials, stale or incorrect results and task success separately. Use paired task-level latency measurements under the same source and permission state; report uncertainty intervals and the workload and warm-up procedure. Do not infer scientific peer review from a passing test or an automated editorial check.

## Exercises

### 1. Scoped accounting

A cold cache receives six eligible reads: three identical calls from principal A, two identical calls from principal B, and one further call from A after its tool version changes. Each principal is authorised; there are no expiry events.

**Checked solution.** The first A call misses and the next two hit. B’s first call misses and its second hits. The version change causes another miss. There are three hits, three upstream reads and an eligible hit rate of \(3/6 = 50\%\).

### 2. Revocation test

Explain why deleting a principal’s grant must prevent a hit even if a matching entry already exists. Propose a test using the laboratory.

**Checked solution.** The cached value is not a continuing permission grant. Populate an entry, remove `("north", "alice")` from `GRANTS`, and repeat the request. It must raise `PermissionError` before lookup. Restore the grant afterwards to avoid contaminating other tests. A real system must also obtain current policy reliably; this in-memory test does not establish that property.

### 3. Error admission

A service returns a timeout twice and succeeds on the third attempt. What happens if the first timeout is cached for an hour?

**Checked solution.** Subsequent callers may receive the old timeout without reaching the recovered service. The cache obscures recovery. Excluding transient errors from admission avoids that particular failure; bounded retry and back-off remain separate concerns.

### 4. Single-flight limitation

Two workers request the same eligible read simultaneously from an empty shared cache. Both see a miss. Does the laboratory prevent duplicate calls?

**Checked solution.** No. It is sequential and has no locking or single-flight mechanism. A shared implementation could coalesce in-flight reads per fully scoped key, with timeouts and failure handling. Even then, it would not provide exactly-once semantics for side effects.
