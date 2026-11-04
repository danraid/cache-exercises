from collections import OrderedDict, Counter
from math import ceil

CAPACITY = 2
TTL = 3                       # logical request ticks
LOOKUP_MS, MISS_EXTRA_MS = 5, 100
MANAGEMENT_COST = 0.001       # synthetic currency units per request
HIT_COST, MISS_COST = 0.002, 0.020

# tenant, principal, policy version, tool version, source version, argument
def request(tenant, source, arg):
    return (tenant, "reader", 1, "tool-v1", source, arg)

A = request("alpha", 1, "a")
B = request("alpha", 1, "b")
C = request("alpha", 1, "c")
OTHER_TENANT = request("beta", 1, "a")
UPDATED = request("alpha", 2, "a")

TRACE = [A, A, B, A, OTHER_TENANT, A, UPDATED, UPDATED,
         B, C, B, A, A, C, C, UPDATED]

def tool(key):
    tenant, _, _, tool_version, source_version, arg = key
    return f"{tenant}:{tool_version}:{source_version}:{arg}"

def percentile(values, p):
    ordered = sorted(values)
    return ordered[ceil(p * len(ordered)) - 1]  # nearest rank

def replay(policy, trace):
    # Key maps to (value, insertion tick); order is LRU to MRU.
    cache = OrderedDict()
    seen = Counter()
    rows = []

    for tick, key in enumerate(trace):
        seen.update((key,))
        if key in cache and policy == "ttl":
            _, inserted = cache.get(key)
            if tick - inserted >= TTL:
                cache.pop(key)

        hit = key in cache
        if hit:
            value, inserted = cache.pop(key)
            cache.update({key: (value, inserted)})
        else:
            value = tool(key)
            # Adaptive policy admits a key from its second observation.
            admit = policy != "adaptive" or seen.get(key) >= 2
            if admit:
                if len(cache) == CAPACITY:
                    cache.popitem(last=False)
                cache.update({key: (value, tick)})

        latency = LOOKUP_MS + (0 if hit else MISS_EXTRA_MS)
        cost = MANAGEMENT_COST + (HIT_COST if hit else MISS_COST)
        rows.append({
            "key": key, "hit": hit, "correct": value == tool(key),
            "latency": latency, "cost": cost
        })
        assert len(cache) <= CAPACITY

    return rows

def report(name, rows):
    n = len(rows)
    latencies = [r["latency"] for r in rows]
    print(
        f"{name:8s} hits={sum(r['hit'] for r in rows)}/{n} "
        f"correct={sum(r['correct'] for r in rows)}/{n} "
        f"mean_ms={sum(latencies)/n:.2f} "
        f"p50_ms={percentile(latencies, .50)} "
        f"p99_ms={percentile(latencies, .99)} "
        f"cost={sum(r['cost'] for r in rows):.3f}"
    )

def safety_tests():
    # The repeat hits; tenant and source changes miss.
    rows = replay("lru", [A, A, OTHER_TENANT, UPDATED])
    assert [r["hit"] for r in rows] == [False, True, False, False]
    assert all(r["correct"] for r in rows)
    # Tool and policy version changes also force misses.
    tool_changed = A[:3] + ("tool-v2",) + A[4:]
    policy_changed = A[:2] + (2,) + A[3:]
    rows = replay("lru", [A, tool_changed, policy_changed])
    assert not any(r["hit"] for r in rows)
    print("Safety fixture assertions passed.")

if __name__ == "__main__":
    safety_tests()
    for name in ("lru", "ttl", "adaptive"):
        report(name, replay(name, TRACE))
