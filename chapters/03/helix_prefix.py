from dataclasses import dataclass


@dataclass
class Entry:
    tokens: tuple
    stored_at: int
    touched: int


class PrefixPredictor:
    def __init__(self, capacity=2, ttl=10):
        assert capacity > 0 and ttl > 0
        self.capacity = capacity
        self.ttl = ttl
        self.entries = {}  # Maps (namespace, complete tokens) to Entry.
        self.tick = 0

    @staticmethod
    def common_prefix(a, b):
        count = 0
        for x, y in zip(a, b):
            if x != y:
                break
            count += 1
        return count

    def request(self, namespace, text, now):
        tokens = tuple(text.split())
        assert tokens
        self.tick += 1

        # Expiry is based on insertion time, not most recent access.
        expired = tuple(
            identity for identity, entry in self.entries.items()
            if now - entry.stored_at >= self.ttl
        )
        for identity in expired:
            self.entries.pop(identity)

        best_identity, best = None, 0
        for identity, entry in self.entries.items():
            entry_namespace, _ = identity
            if entry_namespace == namespace:
                length = self.common_prefix(tokens, entry.tokens)
                if length > best:
                    best_identity, best = identity, length

        if best_identity is not None:
            self.entries.get(best_identity).touched = self.tick

        # Admission: store every complete request. Exact repeats retain
        # their original insertion time; expiry is not sliding.
        identity = (namespace, tokens)
        if identity not in self.entries:
            if len(self.entries) >= self.capacity:
                least_recent = min(
                    self.entries,
                    key=lambda key: self.entries.get(key).touched,
                )
                self.entries.pop(least_recent)
            self.entries.update({identity: Entry(tokens, now, self.tick)})

        return best


def run():
    # namespace = tenant, model, tokenizer, template, policy
    a = ("tenant-A", "model-1", "tok-1", "tpl-1", "policy-1")
    b = ("tenant-B", "model-1", "tok-1", "tpl-1", "policy-1")
    changed_template = (
        "tenant-A", "model-1", "tok-1", "tpl-2", "policy-1"
    )
    cache = PrefixPredictor(capacity=8, ttl=10)
    first = "SYSTEM safe TOOLS search USER alpha"
    second = "SYSTEM safe TOOLS search USER beta"

    assert cache.request(a, first, 0) == 0              # cold
    reused = cache.request(a, second, 1)
    assert reused == 5                                # stable prefix
    assert cache.request(b, second, 2) == 0           # tenant isolation
    assert cache.request(changed_template, second, 3) == 0
    assert cache.request(a, "SYSTEM revised USER beta", 4) == 1
    assert cache.request(a, first, 20) == 0           # expired

    # A first-token edit forces a complete exact-prefix miss.
    c = PrefixPredictor(capacity=2, ttl=10)
    assert c.request(a, "TIME1 SYSTEM safe USER alpha", 0) == 0
    assert c.request(a, "TIME2 SYSTEM safe USER alpha", 1) == 0

    # Capacity-one admission evicts the earlier entry.
    e = PrefixPredictor(capacity=1, ttl=10)
    assert e.request(a, "ONE stable", 0) == 0
    assert e.request(a, "TWO stable", 1) == 0
    assert e.request(a, "ONE stable", 2) == 0

    print("stable prefix: estimated reuse =", reused, "token-like units")
    print("provider-reported reuse = unavailable (offline simulation)")
    print("tenant, version, edit, expiry and eviction checks passed")


if __name__ == "__main__":
    run()
