# Chapter 9. Invalidation, Consistency, Freshness and Provenance

> Companion materials from [the book's Chapter 9](https://github.com/danraid/cache/blob/main/manuscript/09.md). All example programs and data are synthetic, not production validations.

## Practical Laboratory

### Objective and constraints

Implement a small, deterministic Helix subsystem using only the Python standard library. It models a source, a cache, a simulated clock and a replayable event queue. It is **not** a distributed implementation: calls are sequential, the version oracle is synchronously available, and versions are simple integers. In particular, the security-critical test demonstrates immediate invalidation only because the fixture delivers the event immediately.

Save the following as `helix_freshness.py` and run:

```text
python3 helix_freshness.py
```

Executable Python source: [`helix_freshness.py`](./helix_freshness.py).

Run from the repository root: `python3 chapters/09/helix_freshness.py`.

A successful run prints `Helix freshness tests passed`, followed by the trace. The assertions cover a repeat hit, tenant-scoped values, immediate invalidation, a deliberately stale read, version mismatch detection, a late event and the expiry boundary.

The `validate_version=False` branch is deliberately unsafe for security-sensitive use: it makes the stale window observable. The `validate_version=True` branch reads the current version from the in-memory source on every call. In a real service that lookup has cost and failure modes, and the source read and cache use would need an appropriate concurrency protocol. The lab’s source string is a provenance locator, not a cryptographic integrity check.

For reproducible replay, retain the script, Python version and output alongside any modifications. Run with assertions enabled; do not use Python’s `-O` option, which disables `assert` statements. No latency, cost or correctness improvement is claimed from this fixture.

### Extending the experiment

Add counters for hits, misses, stale reads and invalidations. Replay the worked-example schedules twice, once per TTL, with version checking disabled and delayed events scheduled beyond the end of the trace. Compare each returned version with the source version at the read. The uncached baseline reads the source every time and is current under this sequential model. Keep the request order identical between policies.

For a real experiment, define independent workload units, repeat runs under controlled conditions and report uncertainty, such as confidence intervals appropriate to the sampling design. Twelve correlated reads in one synthetic trace are not enough to infer a population-level rate.

## Exercises

1. **Expiry boundary.** An entry is validated at time 10 with TTL 5. It expires when `now >= expires_at`. A source update occurs at time 11. Which reads at integer times 10–15 can return the old value if no invalidation or version check occurs?

2. **Delayed event.** An update commits at time 20; its invalidation arrives at time 23. Reads occur immediately after the update and then at times 21, 22 and 23, with event delivery before the time-23 read. How many reads can return the old value, assuming the entry does not expire?

3. **Provenance and index change.** A cached answer cites document revision 4 from index generation 12. The document is unchanged, but generation 13 adds a new, relevant document. Is validating revision 4 alone sufficient to establish that the cached retrieval is still appropriate?

4. **Design exercise.** A rule service commits a revocation and publishes an invalidation through an outbox. A worker is disconnected. State a policy that prevents the worker from serving a protected cached result after a completed revocation, and identify one availability consequence.

5. **Laboratory extension.** Modify the lab to queue a duplicate event and an older event after a newer value has been cached. What invariant should the test assert? Does passing the test establish correctness under concurrent cache fills?

### Checked solutions

1. The deadline is 15. Reads at times 11–14 can return the old value; the read at 10 precedes the update, and the read at 15 must refresh. This assumes the update occurs before the read at time 11.

2. Three: the reads immediately after commit, at 21 and at 22. The event is processed before the read at 23. The answer depends on the stated ordering and absence of expiry.

3. No. The old document is unchanged, but the newly relevant document could alter the candidate set or answer. Validate the retrieval against the relevant index generation or apply another explicitly justified policy.

4. Require an authoritative check participating in the protected operation’s required ordering, or fail closed whenever the worker cannot establish that its authorisation state is current. During disconnection, legitimate requests may be denied or delayed.

5. Assert that an event for version \(v\) does not evict an entry at version \(v\) or later. No: the sequential test does not cover a stale fill inserted after invalidation, distributed version lag or atomicity of validation and admission.
