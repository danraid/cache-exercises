# Chapter 12. Benchmarking, Replay, Observability and Production Architecture

> Companion materials from [the book's Chapter 12](https://github.com/danraid/cache/blob/main/manuscript/12.md). All example programs and data are synthetic, not production validations.

## Practical Laboratory

### Objective and assumptions

The following standalone Python 3 program adds a **deterministic replay and reporting subsystem** to a miniature synthetic Helix harness. It models a retrieval layer and a tool-result layer; the “tool” is an immutable fixture, not an external service. It does not implement an LLM, a real vector index, distributed storage or a production authorisation service.

The fixture uses arbitrary latency and cost units. Its model, prompt, tool and index identifiers are illustrative version labels, not cryptographic hashes. The program contains checks for tenant segregation, an index-version miss, a tool-version miss, expiry, eviction, handling of an injection marker as data, and a correctness-regression gate. The tool-version check verifies key separation, not the behaviour of a real upgraded tool.

Save as `helix_replay.py` and run:

```bash
python3 helix_replay.py > report.json
python3 -m json.tool report.json
```

No third-party packages or network access are required. The program prints JSON and exits non-zero if an assertion fails. Because output is redirected, a failed run may leave an empty or incomplete `report.json`; check the first command’s exit status before treating the file as a report.

Executable Python source: [`helix_replay.py`](./helix_replay.py).

Run from the repository root: `python3 chapters/12/helix_replay.py`.

### Interpretation and extensions

The baseline performs two uncached operations per task. In the treatment, each layer incurs a lookup cost, then a simulated miss cost if needed. The initial repeated A request hits both layers; later distinct scopes or revisions miss. Capacity pressure causes eviction. The separate tool-version test uses a fresh harness and does not contribute to the five-task report totals.

By inspection of the fixture’s accounting, the five-task run is expected to report 5 correct answers in each arm, baseline latency of 400 units and cost of 40 units, and cached latency of 370 units and cost of 42 units. Each cached layer should show five lookups, one hit, four misses and two evictions. These are **expected synthetic values**, not independently rerun output. The complete program has not been executed for this revision; run the commands above to verify it and retain the generated report.

The injection test establishes only a property of this deliberately simple program: it never interprets document text as instructions. It does **not** test an LLM’s resistance to prompt injection. Similarly, the fixture authorisation check is not a production identity system. Extend the lab with independently versioned principal roles, an actual policy evaluator and a recorded provenance chain before claiming broader coverage.

For CI, run the program in a clean environment, retain `report.json`, and fail the job on a non-zero exit code. The program’s assertions are useful checks, but Python assertions can be disabled with optimisation flags; do not run this CI check with `python -O`. Production gates should use explicit exceptions and report all violations without leaking sensitive payloads.

## Exercises

1. **Paired arithmetic.** In the worked example, calculate the total latency reduction and identify the task that becomes slower.

2. **Scope and invalidation.** A cached retrieval key contains `(query, index_version)` but not tenant or permission revision. Give two distinct unsafe reuse scenarios and a corrected conceptual key.

3. **Shadow deployment.** A shadow cache returns a different answer from the authoritative path. List three plausible explanations and specify what should be returned to the user during shadow mode.

4. **Laboratory extension.** The lab checks that changing a tool-version label causes a tool miss, but both fixture versions return the same output. Extend the fixture so `t1` and `t2` have explicitly different authoritative outputs. Verify the new output and the retrieval-hit/tool-miss events without presenting the test as validation of a real tool.

### Checked solutions

1. Baseline total is \(400\) ms; cached total is \(320\) ms. The reduction is \(80\) ms, and task C rises from \(80\) to \(90\) ms.

2. One tenant may receive another tenant’s accessible document; a user whose access has been revoked may receive a previously authorised result. A conceptual key includes tenant, principal or effective permission scope, permission revision, canonical query, index revision and other retrieval dependencies. Authorisation must still be enforced independently of key matching.

3. The cache may be stale, the authoritative source may have changed, or the two paths may use different versions or permissions. During shadow mode, return the authorised authoritative result, not the unapproved shadow result; record the discrepancy without exposing protected content.

4. Define a deterministic mapping from tool version and retrieved text to the expected output, and use it both for the fresh tool fixture and an independently stated task oracle. Replay otherwise identical tasks with `t1` then `t2`. The retrieval key remains unchanged, so retrieval can hit; the tool key changes, so the tool must miss. Assert both events and the `t2` answer. This tests the synthetic version boundary, not an actual upgraded tool.
