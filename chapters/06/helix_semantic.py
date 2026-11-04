from dataclasses import dataclass
from math import sqrt, isclose

# Synthetic labelled pairs: (similarity, valid reuse).
CAL = [(0.98, True), (0.96, True), (0.93, False),
       (0.90, True), (0.86, False), (0.80, True)]
TEST = [(0.97, True), (0.94, True),
        (0.92, False), (0.89, True)]
THRESHOLDS = [0.95, 0.90, 0.80]


def metrics(rows, threshold):
    accepted = [valid for score, valid in rows if score >= threshold]
    precision = sum(accepted) / len(accepted) if accepted else None
    coverage = len(accepted) / len(rows) if rows else 0.0
    return precision, coverage, len(accepted)


def select_threshold(rows):
    # Illustrative rule only: observed precision >= 0.90,
    # then greatest coverage. Abstain if none qualifies.
    choices = []
    for t in THRESHOLDS:
        p, c, _ = metrics(rows, t)
        if p is not None and p >= 0.90:
            choices.append((c, t))
    if not choices:
        return None
    _, selected = max(choices)
    return selected


def cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = sqrt(sum(x * x for x in a))
    nb = sqrt(sum(y * y for y in b))
    if len(a) != len(b) or na == 0 or nb == 0:
        raise ValueError("vectors must have equal dimensions and non-zero norm")
    return dot / (na * nb)


@dataclass(frozen=True)
class Context:
    tenant: str
    scope: str
    policy: str
    prompt: str
    model: str
    corpus: str
    embedding: str


@dataclass(frozen=True)
class Entry:
    entry_id: str
    context: Context
    vector: tuple
    answer: str
    expires_at: int
    admitted: bool


def lookup(entries, context, vector, threshold, now, authorised):
    # Authentication/authorisation is represented by a Boolean fixture.
    # A real service must establish it independently for each request.
    if not authorised or threshold is None:
        return None

    candidates = []
    for entry in entries:
        if (entry.context != context or not entry.admitted
                or now >= entry.expires_at):
            continue
        score = cosine(vector, entry.vector)
        if score >= threshold:
            candidates.append((score, entry.entry_id, entry.answer))

    # Deterministic tie-breaking by entry ID.
    if not candidates:
        return None
    score, entry_id, answer = max(
        candidates, key=lambda candidate: candidate[:2]
    )
    return entry_id, answer, score


def vector_with_cosine(score):
    # Unit vector whose cosine with (1, 0) is score.
    return (score, sqrt(1.0 - score * score))


def main():
    for t in THRESHOLDS:
        p, c, n = metrics(CAL, t)
        print(f"cal t={t:.2f}: accepted={n}, precision={p:.3f}, "
              f"coverage={c:.3f}")

    threshold = select_threshold(CAL)
    assert threshold == 0.95
    p, c, n = metrics(TEST, threshold)
    print(f"test t={threshold:.2f}: accepted={n}, "
          f"precision={p:.3f}, coverage={c:.3f}")

    a = Context("tenant-A", "staff", "policy-1", "prompt-1",
                "model-1", "corpus-1", "embed-1")
    b = Context("tenant-B", "staff", "policy-1", "prompt-1",
                "model-1", "corpus-1", "embed-1")
    changed_policy = Context("tenant-A", "staff", "policy-2", "prompt-1",
                             "model-1", "corpus-1", "embed-1")
    entries = [
        Entry("A1", a, vector_with_cosine(0.98),
              "Synthetic answer A", 10, True),
        Entry("B1", b, vector_with_cosine(1.00),
              "Synthetic answer B", 10, True),
        Entry("A-unverified", a, vector_with_cosine(1.00),
              "Do not reuse", 10, False),
    ]
    query = (1.0, 0.0)
    hit = lookup(entries, a, query, threshold, now=5, authorised=True)
    assert hit is not None
    hit_id, _, hit_score = hit
    assert hit_id == "A1"
    assert isclose(hit_score, 0.98)
    assert lookup(entries[:1], b, query, threshold, 5, True) is None
    assert lookup(entries, changed_policy, query, threshold, 5, True) is None
    assert lookup(entries, a, query, threshold, 10, True) is None
    assert lookup(entries, a, query, threshold, 5, False) is None
    print("Helix isolation, version, expiry and admission checks: PASS")


if __name__ == "__main__":
    main()
