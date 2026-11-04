import json
from collections import OrderedDict

# ORIGINAL SYNTHETIC FIXTURES: no external calls or measured timings.
DOCS = {
    ("A", "v1"): "alpha",
    ("B", "v1"): "beta",
    ("A", "v2"): "alpha revised",
}
INJECTION = "IGNORE_SYSTEM_AND_LEAK"
VERSIONS = {"model": "m1", "prompt": "p1", "tool": "t1"}


class Cache:
    def __init__(self, capacity=2, ttl=10):
        self.data = OrderedDict()
        self.capacity, self.ttl = capacity, ttl
        self.stats = {
            k: 0 for k in
            ("lookup", "hit", "miss", "eviction", "invalidation")
        }

    def get(self, key, now):
        self.stats["lookup"] += 1
        item = self.data.get(key)
        if item is not None:
            value, expires = item
            if now < expires:
                self.data.move_to_end(key)
                self.stats["hit"] += 1
                return value
            self.data.pop(key)
            self.stats["invalidation"] += 1
        self.stats["miss"] += 1
        return None

    def put(self, key, value, now):
        if key in self.data:
            self.data.pop(key)
        elif len(self.data) >= self.capacity:
            self.data.popitem(last=False)
            self.stats["eviction"] += 1
        self.data.update([(key, (value, now + self.ttl))])


class Helix:
    def __init__(self, enabled):
        self.enabled = enabled
        self.retrieval = Cache()
        self.tool = Cache()
        self.events = []

    def run(self, task, now):
        tenant, index = task["tenant"], task["index"]
        # Synthetic authorisation precedes any lookup.
        if tenant != task["principal_tenant"]:
            self.events.append({"event": "denied", "tenant": tenant})
            return {
                "denied": True, "correct": False,
                "latency": 0, "cost": 0
            }

        source = DOCS[(tenant, index)]
        # The document is data. The harness never executes its contents.
        if task.get("injection"):
            source += " " + INJECTION

        # Security scope and relevant fixture versions enter the keys.
        rk = (tenant, index, task.get("injection", False))
        tk = (
            tenant, index, task["tool_version"],
            task.get("injection", False)
        )
        latency, cost = 0, 0

        def lookup(cache, layer, key, fresh):
            nonlocal latency, cost
            if not self.enabled:
                latency += 40
                cost += 4
                self.events.append({
                    "layer": layer, "event": "bypass", "tenant": tenant
                })
                return fresh

            latency += 5
            cost += 1
            value = cache.get(key, now)
            hit = value is not None
            if not hit:
                latency += 40
                cost += 4
                value = fresh
                cache.put(key, value, now)
            self.events.append({
                "layer": layer,
                "event": "hit" if hit else "miss",
                "tenant": tenant,
            })
            return value

        retrieved = lookup(self.retrieval, "retrieval", rk, source)
        # Both synthetic tool versions return the retrieved text unchanged.
        answer = lookup(self.tool, "tool", tk, retrieved)
        expected = source
        correct = (answer == expected)
        # The harness never promotes fixture text into instructions.
        instruction_executed = False
        return {
            "denied": False, "answer": answer, "correct": correct,
            "instruction_executed": instruction_executed,
            "latency": latency, "cost": cost,
        }


def task(tenant, index="v1", tool_version="t1", **extra):
    return {
        "tenant": tenant,
        "principal_tenant": tenant,
        "index": index,
        "tool_version": tool_version,
        **extra,
    }


def replay(enabled, tasks):
    h = Helix(enabled)
    results = []
    task_events = []
    for now, t in enumerate(tasks):
        start = len(h.events)
        results.append(h.run(t, now))
        task_events.append(h.events[start:])
    return h, results, task_events


def assert_gate(baseline, treatment, max_correctness_drop=0):
    b = sum(r["correct"] for r in baseline)
    t = sum(r["correct"] for r in treatment)
    assert b - t <= max_correctness_drop, "correctness regression"


def main():
    tasks = [
        task("A"),
        task("A"),
        task("B"),
        task("A", "v2"),
        task("A", "v2", injection=True),
    ]
    baseline, br, _ = replay(False, tasks)
    cached, cr, task_events = replay(True, tasks)

    assert_gate(br, cr)
    assert all(r["correct"] for r in cr)
    _, _, b_result, revised_result, injection_result = cr
    assert not injection_result["instruction_executed"]
    assert INJECTION in injection_result["answer"]  # untrusted data

    # The first B request cannot retrieve A's cached value.
    b_events = task_events[2]
    assert b_events == [
        {"layer": "retrieval", "event": "miss", "tenant": "B"},
        {"layer": "tool", "event": "miss", "tenant": "B"},
    ]
    assert b_result["answer"] == "beta"

    # The revised A task has its own retrieval miss and revised value.
    assert revised_result["answer"] == "alpha revised"
    revised_retrieval = [
        e for e in task_events[3] if e.get("layer") == "retrieval"
    ]
    assert revised_retrieval == [
        {"layer": "retrieval", "event": "miss", "tenant": "A"}
    ]

    denied = cached.run({
        "tenant": "A", "principal_tenant": "B", "index": "v1",
        "tool_version": "t1",
    }, 6)
    assert denied["denied"]

    # With the retrieval dependencies unchanged, a new tool version
    # hits retrieval but misses the separately keyed tool cache.
    version_tasks = [task("A", tool_version="t1"),
                     task("A", tool_version="t2")]
    _, version_results, version_events = replay(True, version_tasks)
    assert version_results[1]["answer"] == "alpha"
    assert version_results[1]["correct"]
    assert version_events[1] == [
        {"layer": "retrieval", "event": "hit", "tenant": "A"},
        {"layer": "tool", "event": "miss", "tenant": "A"},
    ]

    # Expiry is exclusive: the cache entry is invalid at the expiry instant.
    c = Cache(capacity=1, ttl=2)
    c.put(("A",), "value", 0)
    assert c.get(("A",), 2) is None
    assert c.stats["invalidation"] == 1
    c.put(("A",), "value", 2)
    c.put(("B",), "other", 2)
    assert c.stats["eviction"] == 1

    # Confirm that the regression gate fails on a deliberately bad result.
    bad = [dict(r) for r in cr]
    bad[0]["correct"] = False
    try:
        assert_gate(br, bad)
    except AssertionError:
        pass
    else:
        raise AssertionError("regression gate did not abort")

    report = {
        "fixture": "helix-synthetic-v1",
        "versions": VERSIONS,
        "tasks": len(tasks),
        "baseline": {
            "correct": sum(r["correct"] for r in br),
            "latency_units": sum(r["latency"] for r in br),
            "cost_units": sum(r["cost"] for r in br),
        },
        "cache": {
            "correct": sum(r["correct"] for r in cr),
            "latency_units": sum(r["latency"] for r in cr),
            "cost_units": sum(r["cost"] for r in cr),
            "layers": {
                "retrieval": cached.retrieval.stats,
                "tool": cached.tool.stats,
            },
        },
        "fixture_security_checks": "passed",
        "tool_version_key_check": "passed",
        "regression_gate_negative_test": "passed",
        "events": cached.events,
    }
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
