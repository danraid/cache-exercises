# Chapter 4. Transformer KV-Cache and Attention Serving

> Companion materials from [the book's Chapter 4](https://github.com/danraid/cache/blob/main/manuscript/04.md). All example programs and data are synthetic, not production validations.

## Practical Laboratory

This **original illustrative Helix component** simulates token-level work and logical KV occupancy. It does not run a transformer, allocate GPU memory, measure latency or validate model quality. Its fixture uses synthetic token IDs. The work proxy counts causal query–key pairs; it excludes projections, attention-head multiplicity, layer multiplicity, batching and hardware effects.

The implementation models a strict, single-entry prefix cache. A hit requires equality of tenant, model, template, policy and entire token tuple. The fixture assumes a fixed tokeniser, positions, mask and KV layout, represented collectively by the model fingerprint. Real systems must include those conditions explicitly. The program uses only the Python standard library.

Save as `helix_kv_lab.py` and run:

```bash
python3 helix_kv_lab.py
```

Executable Python source: [`helix_kv_lab.py`](./helix_kv_lab.py).

Run from the repository root: `python3 chapters/04/helix_kv_lab.py`.

Expected output:

```text
trace: {'prefill_pairs': 10, 'decode_pairs': 11, 'cached_total_pairs': 21, 'recompute_pairs': 46, 'final_resident_tokens': 6}
KV bytes per resident token: 131072
prefix hits: 1 misses: 7
all invariant checks passed
```

The prefix-cache fixture tests matching and invalidation; it does not store or share actual tensors. Its hit counter is not used to alter `simulate`, which separately compares within-request incremental decoding with full recomputation. This separation is intentional: a cross-request prefix hit and request-local decode caching are different events.

### Extending the experiment

Add an event trace containing arrival, prefill, each decode step and release. Calculate occupancy after each event, then repeat with two interleaved requests. Specify whether prompt and output limits are known at admission. Compare a no-reuse baseline and a reuse-enabled policy on the **same trace**, retaining rejected hits and recomputation events in the log.

For a real model experiment, record hardware, model and adapter fingerprints, software versions, token IDs, precision, batching policy and warm-up procedure. Compare outputs or logits against a no-reuse baseline before interpreting speed. Use paired requests, report latency distributions and uncertainty intervals, and separate cold from warm conditions. A simulator’s passing assertions do not establish real-system correctness or performance.

## Exercises

1. **Memory geometry.** Using the worked example’s geometry and FP16 precision, calculate payload for 2,048 resident tokens. What happens if the number of KV heads doubles while everything else remains fixed?

2. **Decode accounting.** For a three-token prompt and two generated tokens, calculate the prefill and incremental decode pair proxies under the laboratory convention. How many tokens are resident after the final required forward pass?

3. **Compatibility.** A second request has the same rendered prompt and tenant as a cached request, but uses a new adapter. Should it reuse the old state? Explain.

4. **Architecture.** A worker transfers a cache to another machine before decoding. Name three measurements or checks needed before judging this better than recomputation.

5. **Experiment design.** Helix reports an 80% validated prefix-hit rate but a worse 99th-percentile end-to-end latency than its baseline. Give two plausible explanations and one test for each.

### Checked solutions

1. At 128 KiB per token, 2,048 tokens require **256 MiB** of logical payload. Doubling KV heads doubles the payload to **512 MiB**, provided the other assumptions remain unchanged.

2. Prefill is \(1+2+3=6\) pairs. One incremental forward processes the first generated token and attends to four positions, giving **4** more pairs. The total is **10**, with **4 resident tokens** after that forward pass. The second selected output token has not yet been processed into KV state.

3. **No.** The adapter can change projections and hidden states. The old KV tensors were computed under different model parameters. Recompute unless a separately validated implementation establishes a compatible transformation.

4. Check **compatibility and isolation** of the transferred state; measure **transfer and serialisation time**, including tail behaviour; and measure **end-to-end latency and memory occupancy** against a matched recomputation baseline. Network contention and failure recovery should also be considered.

5. Transfer or lookup overhead may dominate some hits: compare paired hit-path timings, including network time. Alternatively, retained state may increase memory pressure and queueing: correlate allocation and queue delay with latency, then replay the same workload with a controlled memory limit. Neither explanation follows from hit rate alone.
