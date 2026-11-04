# Chapter 5. Paged Attention, Quantisation and KV Eviction

> Companion materials from [the book's Chapter 5](https://github.com/danraid/cache/blob/main/manuscript/05.md). All example programs and data are synthetic, not production validations.

## Practical Laboratory

### Aim and assumptions

This **original illustrative** Helix component models a fixed page pool with whole-entry LRU eviction. It does not implement transformer attention, quantisation, GPU memory, concurrent requests or actual prefix sharing. Each entry is an immutable collection of abstract pages; a version change creates a different lookup identity. The simulator’s page counts are accounting units, not measured memory use.

The fixture tests tenant isolation, model-version invalidation, deterministic eviction and bounded capacity. A deliberately oversize request is rejected without disturbing existing entries. Replace the eviction method to investigate another policy.

Save the following as `helix_pages.py` and run it with Python 3:

Executable Python source: [`helix_pages.py`](./helix_pages.py).

Run from the repository root: `python3 chapters/05/helix_pages.py`.

The final report should show four used pages, resident sessions `A` and `C`, one eviction of `B`, two isolation/version misses and rejection of `large`. The assertions are the acceptance tests. The fixture checks logical key separation only; it does not demonstrate real authorisation, device-memory clearing or resistance to timing leakage.

### Extend and evaluate

1. Add a pinned flag and ensure the victim selector cannot evict a pinned entry. Define what happens when insufficient unpinned space exists; test that failed admission does not partially evict entries.
2. Add page size in token positions and compute reserved versus occupied slots. Test an exact multiple and a one-token overflow.
3. Replay the same fixed trace under LRU and a second deterministic policy. Log evicted pages and reconstruction work as **synthetic counters**, not measured latency.
4. Add a representation label and assumed bytes per page. Keep metadata as a separate parameter; do not call the resulting total measured GPU usage.

For a real benchmark, establish a no-compression or full-precision baseline and use paired requests with identical token IDs, model revision, generation parameters and workload arrival trace. State warm-up and cache state. Repeat runs; report uncertainty, for example confidence intervals for paired task outcomes or latency differences using a suitable resampling unit. Do not treat individual tokens from one request as independent requests. Include safety and tenant-isolation tests, and retain enough versioned traces to replay failures.

## Exercises

### 1. Capacity and slack

Using the worked example’s geometry and FP16 payload, calculate the ideal payload for 2,048 tokens. If pages hold 256 tokens, how many pages are reserved for 2,049 tokens?

**Checked solution:** Half the tokens require **256 MiB** of ideal payload. For 2,049 tokens, \(\lceil 2049/256\rceil=9\) pages are reserved; the ninth contains one occupied position. Metadata and other allocations remain excluded.

### 2. Eviction semantics

A session’s complete token history is retained outside the KV pool. Compare dropping its inactive KV entry with deleting its oldest KV page and continuing generation immediately.

**Checked solution:** Dropping the inactive entry can be followed by reconstruction from compatible history before continuation. Deleting an old page and continuing without reconstruction removes context from attention and can change output. Neither option guarantees identical numerical output without testing the implementation.

### 3. Precision comparison

A service reports that four-bit KV storage uses one quarter of FP16 storage. Identify three measurements needed before accepting an operational claim.

**Checked solution:** Measure total peak memory including metadata and temporary buffers; compare TTFT and decode latency under matched workload and concurrency; and evaluate output quality against a defined FP16 baseline. Throughput and tail latency are also relevant. The quarter-size figure is only an ideal payload ratio.

### 4. Policy and isolation

In the laboratory, `A` occupies two pages and `C` occupies two pages. A new two-page request arrives. What does LRU do, and does the tenant field itself authorise access?

**Checked solution:** Given the fixture’s timestamps, `A` is older than `C`, so the existing LRU implementation evicts `A` and admits the new entry. The tenant field separates dictionary keys; it is not an authentication or authorisation mechanism. A real service must check access independently.
