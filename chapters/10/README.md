# Chapter 10. Security, Tenant Isolation and Cache Poisoning

> Companion materials from [the book's Chapter 10](https://github.com/danraid/cache/blob/main/manuscript/10.md). All example programs and data are synthetic, not production validations.

## Practical Laboratory

This **original illustrative** laboratory uses Python’s standard library. It models:

- trusted authentication context separate from caller-supplied request fields;
- policy, tool and source revisions obtained inside Helix;
- a protected cache-write API with writer authorisation and provenance checks;
- tenant, role, revocation and version behaviour;
- a synthetic vector-store pre-filter and a deliberately unsafe post-filter.

The “agent” is a deterministic handler, not a language model. Python’s underscore-prefixed fields and object-identity tokens model a trusted in-process boundary; they are **not** a security sandbox. The test code can inspect internal state, but setup and normal operations use the model’s APIs. A real deployment needs independently protected identity, policy, source, storage and writer services.

Save as `helix_security.py` and run:

```bash
python3 helix_security.py
```

Executable Python source: [`helix_security.py`](./helix_security.py).

Run from the repository root: `python3 chapters/10/helix_security.py`.

Expected output:

```text
PASS: exact-cache fixture and protected admission
PASS: synthetic pre-filter and post-filter comparison
```

The cache-write tests reject an unauthorised token, a writer operating without a grant, and forged text or metadata. The admission check compares against the fixture’s authoritative document; it does not detect hostile text that was legitimately present in that document. The old entries remain in memory after changes or revocation, although the model’s read path no longer selects them.

The vector experiment defines the store as the trusted boundary and the application as unable to see another tenant’s candidates. With pre-filtering, the application receives only Birch’s candidate. With global top-one retrieval, it receives Alder’s identifier, score, metadata and content before post-filtering; the forbidden result also displaces Birch’s result. A real system must test its own API responses, logs, traces and enforcement boundary.

### Laboratory Limits

This single-process fixture does **not** establish general cache-poisoning mitigation. It does not test expiry, concurrent policy changes, distributed invalidation, real source-revision integrity, compromised trusted writers, cryptographic metadata protection, an actual vector database or model behaviour. Its source and version authorities are trusted assumptions, not independently secured services. Production acceptance requires tests of those paths and of the actual identity, policy, storage and model-serving boundaries.

## Exercises

1. **Key design.** Two employees share a role but have different document grants. Is `(tenant, role, query)` sufficient?

   **Checked solution:** No. Check current authorisation for the resource and include an appropriate actor or entitlement scope and resource identity in the reuse decision, along with relevant versions.

2. **Permission change.** Why is incrementing a policy version not by itself a complete revocation mechanism?

   **Checked solution:** A current-version request could still be authorised if its grant remains. The grant must change too. Distributed propagation and concurrent requests also require a consistency strategy.

3. **Risk arithmetic.** Under the worked example’s assumptions, what is the expected number of harmful actions after 50 reuses at probability 0.01 per reuse?

   **Checked solution:** \(50 \times 0.01 = 0.5\). This expectation is neither the probability of at least one event nor a measured production rate.

4. **Laboratory extension.** Add an expiry time and a controllable clock. Assert that an expired entry is not reused. What remains untested?

   **Checked solution:** The test would exercise the fixture’s expiry decision. It would not establish real clock synchronisation, distributed expiry behaviour, immediate revocation or trustworthy source revisions.

5. **Semantic cache.** A cross-tenant candidate scores 0.99 against a threshold of 0.95. Should it be returned?

   **Checked solution:** No. Similarity does not override authorisation. If the application is outside the candidate’s trust boundary, the candidate should not be exposed to it before filtering either.
