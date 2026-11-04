# Chapter 2. Caching Taxonomy and Memory Hierarchy

> Companion materials from [the book's Chapter 2](https://github.com/danraid/cache/blob/main/manuscript/02.md). All example programs and data are synthetic, not production validations.

## Practical Laboratory

### Aim and assumptions

Build one Helix subsystem: a deterministic two-cache simulator over a backing tool. The fixture reproduces the worked example. This is an **original illustrative simulation**, not a model of a real provider, LLM, clock or deployment. Its costs are synthetic accounting units, not measured timings or prices.

The simulator includes tenant, tool version and policy version in both keys. Changing a version causes a logical miss; old entries remain resident because this small example has no eviction or physical deletion. The simulated backing tool is deterministic and its entire relevant state is represented by the fixture inputs.

Save the following as `helix_ch2.py`. It requires Python 3 and no third-party packages.

Executable Python source: [`helix_ch2.py`](./helix_ch2.py).

Run from the repository root: `python3 chapters/02/helix_ch2.py`.

Run:

```bash
python3 helix_ch2.py
```

The main trace reports response hits of `1 / 4`, tool hits of `1 / 3`, cache cost `30` and baseline cost `40`. The unique trace reports `52` against `40`. The assertions check synthetic output equality, tenant separation and version-induced misses.

These tests do **not** implement authentication, authorisation, TTL, concurrency or a real language model. In particular, the tenant field is trusted fixture data; a production gateway must derive scope from authenticated identity rather than accepting an arbitrary caller-supplied tenant. The test also cannot establish correctness for a tool whose external state changes without a corresponding version.

### Extending the measurement

Add an expiry clock or a byte budget as a separate experiment. Record admission, eviction, expiry and invalidation as distinct events. For a realistic evaluation, replay the same authorised tasks against a no-cache baseline and each policy, with declared cold and warm states. Preserve model, tool, index and policy versions; compare task success and safety before comparing latency and cost.

For repeated sampled workloads, report the number and sampling unit of tasks and an appropriate confidence interval for a paired difference. A deterministic four-request fixture has no basis for a population confidence interval. Likewise, passing these assertions is a software check, not independent scientific peer review.

## Exercises

1. **Conditional accounting.** In a six-request trace, the response tier hits twice. Of the four requests reaching the tool tier, three hit. With the worked-example costs, calculate total and mean cost. State both hit-rate denominators.

2. **Key design.** A retrieval cache key contains only query text. Name four additional categories of information that may be necessary for safe reuse, and explain why a TTL cannot replace all of them.

3. **Capacity and reuse.** A three-entry least-recently-used cache starts empty and receives `A, B, C, A, D, B`. List hits and misses. Which item is evicted on the insertion of D?

4. **Validation exercise.** Modify the lab so that a request with a changed policy version first checks an external authorisation predicate. Explain why versioned keys and this predicate serve different purposes.

### Checked solutions

1. Response hit rate is \(2/6\); conditional tool hit rate is \(3/4\). All six pay 1, four pay 2, and one pays 10: total \(6+8+10=24\), mean 4 units. No tool lookup is counted for either response hit.

2. Possible categories include tenant and current principal or role; corpus or index revision; retrieval and reranking configuration or model versions; and permission filters. A TTL does not encode which tenant is entitled to the result or guarantee that a source or permission remains unchanged during its lifetime.

3. `A`, `B`, `C` miss; the second `A` hits; `D` misses and evicts `B`, the least recently used; the final `B` misses. There is one hit and five misses. On the final insertion, `C` is then evicted.

4. The predicate should run before returning either a cached or freshly computed result and should deny access if current policy disallows it. The version in a key separates entries produced under different declared policies; the predicate checks the requester’s present authority. Neither compensates for a stale or incorrectly supplied policy version.
