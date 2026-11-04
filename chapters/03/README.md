# Chapter 3. Prompt Prefix Caching and Stable Context Design

> Companion materials from [the book's Chapter 3](https://github.com/danraid/cache/blob/main/manuscript/03.md). All example programs and data are synthetic, not production validations.

## Practical Laboratory

### Objective and assumptions

Implement an **offline prefix predictor**, not a transformer or provider cache. Each whitespace-separated fixture element represents one token-like unit. The predictor stores complete prior sequences in a versioned tenant namespace, finds the longest exact common prefix, and models expiry and least-recently-used eviction.

The clock is supplied by the caller. An entry is valid while `now - stored_at < ttl`; a hit updates recency but does **not** extend expiry. Capacity is measured in entries, not bytes. A non-zero common prefix is called an estimated hit; no minimum length, block rounding, KV allocation or real billing is modelled.

Save the following as `helix_prefix.py` and run it with Python 3. No third-party packages are required.

Executable Python source: [`helix_prefix.py`](./helix_prefix.py).

Run from the repository root: `python3 chapters/03/helix_prefix.py`.

Expected output:

```text
stable prefix: estimated reuse = 5 token-like units
provider-reported reuse = unavailable (offline simulation)
tenant, version, edit, expiry and eviction checks passed
```

The system-instruction edit shares the first fixture token, `SYSTEM`, so its **raw overlap** is one unit. If a policy requires *any* instruction edit to force a complete miss, increment the policy or template revision in the namespace. Do not confuse this raw overlap with permission to reuse a production KV state.

### From simulation to experiment

For a real evaluation, prepare a fixed set of authorised requests and record the exact post-assembly prompt, model and template fingerprints, tokenisation method, tenant scope, cache state and timestamps. Avoid logging sensitive prompt contents in ordinary telemetry; protected fixtures or keyed fingerprints may be more appropriate.

Compare cache-enabled and baseline runs with the same tasks, model configuration and output limits. Specify whether each trial is cold or warm, how warm-up occurs, and how routing and expiry are controlled or observed. Record:

1. locally estimated common-prefix tokens;
2. provider-reported cached tokens, if exposed;
3. input and output usage and actual charges, if available;
4. time to first token, end-to-end latency and errors;
5. task correctness, grounding and security-test outcomes.

Use paired per-task differences where possible and report sample size, dispersion and confidence intervals. Repeat across independent runs rather than treating correlated requests as independent without justification. If cache state or routing cannot be controlled, describe that limitation. Do not convert a simulation’s deterministic output into a claim of production performance.

## Exercises

1. **Prefix reasoning.** Using whitespace units, find the longest common prefix of `SYSTEM rules TOOLS search USER red` and `SYSTEM rules TOOLS search USER blue`. What happens if the second sequence begins `CLOCK 2`?

2. **Versioning.** A tenant’s policy changes while its visible prompt happens to remain identical. Should the old entry be reused? Identify two other changes that can require a new compatibility namespace.

3. **Billing arithmetic.** Under the worked example’s fictional rates and £0.0001 overhead, calculate net savings when 600 input tokens are actually reused. What is the break-even number of reused tokens?

4. **Laboratory extension.** Add a fixture in which the model revision changes. Assert that the request misses. Then run a second request under that revision and assert that it obtains the expected local overlap.

5. **Experimental design.** A team observes a higher local prefix-overlap rate after moving timestamps. Give two reasons why this is insufficient to claim lower production latency.

### Checked solutions

1. The common prefix is five units: `SYSTEM rules TOOLS search USER`. With `CLOCK` first, it is zero.
2. Conservatively, no: a policy revision can alter authorisation even when visible text does not change. Model revision and tokenizer revision are two further examples; template or tool-schema changes may also matter.
3. Savings are \(600(£1.50/1{,}000{,}000)-£0.0001=£0.0008\). Break-even is \(£0.0001/(£1.50/1{,}000{,}000)\), or approximately **66.67 tokens**; at least 67 whole reused tokens are needed for a positive saving under these assumptions.
4. For example, create `new_model = ("tenant-A", "model-2", "tok-1", "tpl-1", "policy-1")`. In a fresh predictor, the first request in that namespace returns zero; the second fixture from the lab returns five.
5. The provider may not admit or reuse the estimated prefix, and lookup, routing or contention may offset avoided computation. Latency must be measured with comparable requests and cache-state reporting.
