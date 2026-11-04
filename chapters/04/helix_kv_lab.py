from dataclasses import dataclass


@dataclass(frozen=True)
class Scope:
    tenant: str
    model: str       # Includes fixed execution/layout assumptions in this toy.
    template: str
    policy: str


@dataclass(frozen=True)
class Entry:
    scope: Scope
    tokens: tuple[int, ...]


class PrefixCache:
    """One-entry, exact, tenant-scoped illustrative cache."""

    def __init__(self):
        self.entry = None
        self.hits = 0
        self.misses = 0

    def lookup(self, scope, tokens):
        candidate = Entry(scope, tuple(tokens))
        if self.entry == candidate:
            self.hits += 1
            return True
        self.misses += 1
        return False

    def store(self, scope, tokens):
        self.entry = Entry(scope, tuple(tokens))

    def invalidate(self):
        self.entry = None


def kv_bytes(layers, kv_heads, head_dim, tokens, bytes_per_element):
    if min(layers, kv_heads, head_dim, tokens, bytes_per_element) < 0:
        raise ValueError("dimensions must be non-negative")
    return 2 * layers * kv_heads * head_dim * tokens * bytes_per_element


def triangular(n):
    return n * (n + 1) // 2


def simulate(prompt_tokens, output_tokens):
    """
    Prefill selects output token 1. Each additional output token requires
    processing the preceding generated token. Return pair-count proxies.
    """
    if prompt_tokens < 1 or output_tokens < 1:
        raise ValueError("prompt and output lengths must be positive")

    prefill = triangular(prompt_tokens)
    decode = sum(
        prompt_tokens + i for i in range(1, output_tokens)
    )
    recompute = sum(
        triangular(prompt_tokens + i) for i in range(output_tokens)
    )
    resident = prompt_tokens + output_tokens - 1
    return {
        "prefill_pairs": prefill,
        "decode_pairs": decode,
        "cached_total_pairs": prefill + decode,
        "recompute_pairs": recompute,
        "final_resident_tokens": resident,
    }


def main():
    scope = Scope("tenant-a", "model-v1", "template-v1", "policy-v1")
    tokens = (11, 12, 13, 14)
    cache = PrefixCache()

    # Lookup is preceded by assumed authorisation in this offline fixture.
    assert not cache.lookup(scope, tokens)
    cache.store(scope, tokens)
    assert cache.lookup(scope, tokens)

    assert not cache.lookup(
        Scope("tenant-b", "model-v1", "template-v1", "policy-v1"), tokens
    )
    assert not cache.lookup(
        Scope("tenant-a", "model-v2", "template-v1", "policy-v1"), tokens
    )
    assert not cache.lookup(
        Scope("tenant-a", "model-v1", "template-v2", "policy-v1"), tokens
    )
    assert not cache.lookup(
        Scope("tenant-a", "model-v1", "template-v1", "policy-v2"), tokens
    )
    assert not cache.lookup(scope, (11, 12, 13, 15))

    cache.invalidate()
    assert not cache.lookup(scope, tokens)

    trace = simulate(4, 3)
    assert trace == {
        "prefill_pairs": 10,
        "decode_pairs": 11,
        "cached_total_pairs": 21,
        "recompute_pairs": 46,
        "final_resident_tokens": 6,
    }

    per_token = kv_bytes(32, 8, 128, 1, 2)
    assert per_token == 131_072
    assert kv_bytes(32, 8, 128, 4096, 2) == 512 * 1024**2
    assert kv_bytes(32, 8, 128, 4096, 1) == 256 * 1024**2
    assert kv_bytes(32, 8, 128, 8192, 2) == 2 * kv_bytes(
        32, 8, 128, 4096, 2
    )

    print("trace:", trace)
    print("KV bytes per resident token:", per_token)
    print("prefix hits:", cache.hits, "misses:", cache.misses)
    print("all invariant checks passed")


if __name__ == "__main__":
    main()
