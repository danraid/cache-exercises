# Chapter 11. Cost, Latency, Energy and Adaptive Cache Policies

> Companion materials from [the book's Chapter 11](https://github.com/danraid/cache/blob/main/manuscript/11.md). All example programs and data are synthetic, not production validations.

## Practical Laboratory

### Objective and assumptions

The following **original illustrative** Python laboratory adds a deterministic tool-result cache policy simulator to Helix. It uses no external packages or network access. It compares LRU, TTL-limited LRU and a simple adaptive admission rule on the same synthetic trace.

The tool value is determined by tenant, argument and source version. The key also contains principal, policy version and tool version. The simulator assumes that current versions and authorisation have already been obtained correctly. Thus, its isolation and invalidation tests exercise key separation, **not** a real access-control system or distributed invalidation protocol.

Latency and prices are fictional accounting units. Storage, telemetry and invalidation are represented by a fixed per-request management charge, not independently metered. There is no energy measurement and no simulated concurrency.

Save the code as `helix_ch11.py` and run `python3 helix_ch11.py`.

Executable Python source: [`helix_ch11.py`](./helix_ch11.py).

Run from the repository root: `python3 chapters/11/helix_ch11.py`.

### Procedure and interpretation

1. Run the program unchanged and retain its output with the code and Python version. Each policy starts with an empty cache and receives the identical ordered trace.
2. Check the safety assertions. A changed tenant, source version, tool version or policy version must not reuse the original entry. The assertions do not test credential revocation, malicious inputs or actual access-control enforcement.
3. Compare hits, correct outcomes, latency and cost. All fixture outcomes should be correct because the tool is deterministic and the complete synthetic key identifies its value. This is a property of the fixture, not proof of production correctness.
4. Change `CAPACITY` to 1, then to 3, and rerun. Explain changes using the ordered trace rather than assuming that more capacity always improves every metric in every implementation.
5. Change `TTL` and identify requests that become misses because an entry expired. The TTL is measured from insertion, not refreshed on hits.
6. Replace the latter half of `TRACE` with repeated new keys to represent a popularity shift. Compare the adaptive rule’s delay in admitting a newly popular key with LRU’s susceptibility to one-off keys.

The p99 of 16 observations is the maximum under this convention. It is useful for checking the calculation but is not a stable estimate of a service’s production p99. The simulator assigns every miss the same latency and cost, so it cannot reproduce the worked example’s tail counterexample. Add a separately specified slow validation event or incorrect semantic match if investigating that behaviour; do not present the altered fixture as an observed system result.

For a more credible experiment, use paired baseline and treatment runs on representative held-out traces, repeat across independent workload windows, and report sample counts and uncertainty. Bootstrap **independent workload blocks**, rather than individual correlated requests, for intervals on paired differences when that resampling assumption is appropriate. Rare security failures require dedicated adversarial tests as well as statistical summaries.

## Exercises

1. **Accounting.** In the worked example, suppose B incurs an additional £0.03 in storage charges not previously included. Calculate its revised cost. Does it remain cheaper than A?

2. **Tail latency.** A replay has 100 latencies: 99 at 50 ms and one at 5,000 ms. Calculate the mean and nearest-rank p99. Why does p99 not show the slowest request?

3. **Admission and expiry.** A source changes immediately after a value is cached with a ten-minute TTL. No invalidation event is delivered. Can the TTL alone guarantee that every subsequent hit is current?

4. **Laboratory extension.** Add a simulated per-request invalidation charge of 0.004 when the source version changes from one request to the next for the same tenant and argument. State whether this models a delivered event or merely detects a change in the trace. Report the revised cost separately from the original.

### Checked solutions

1. B costs £0.660 + £0.030 = **£0.690**. It remains £0.020 cheaper than A, assuming no other costs change.
2. Mean \(=(99\times50+5000)/100=99.5\) ms. Nearest-rank p99 is the 99th observation, **50 ms**. The single 5,000 ms request is the 100th; maximum and p99 answer different questions.
3. **No.** Until expiry, the cached value can be stale. A version check or reliable invalidation mechanism is needed if every hit must reflect the update.
4. One valid solution keeps a dictionary mapping `(tenant, argument)` to the last observed source version, adds 0.004 when a later version differs, then updates the dictionary. This detects changes visible in request order; it does **not** establish when the underlying update occurred or that an invalidation event was delivered. The revised total depends on the trace and policy accounting boundary.
