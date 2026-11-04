from dataclasses import dataclass
from collections import Counter


@dataclass(frozen=True)
class Request:
    tenant: str
    question: str
    argument: str
    tool_version: str = "v1"
    policy_version: str = "p1"


def backing_tool(req):
    # Synthetic, deterministic result; not an external API.
    return f"status:{req.tenant}:{req.argument}:{req.tool_version}"


class Helix:
    def __init__(self):
        self.response_cache = {}
        self.tool_cache = {}
        self.events = Counter()
        self.cost = 0

    def record(self, event):
        self.events.update((event,))

    def run(self, req):
        # A production gateway must authenticate and authorise first.
        scope = (req.tenant, req.tool_version, req.policy_version)
        response_key = scope + (req.question, req.argument)
        tool_key = scope + (req.argument,)

        self.record("response_lookups")
        self.cost += 1
        if response_key in self.response_cache:
            self.record("response_hits")
            return self.response_cache.get(response_key)

        self.record("response_misses")
        self.record("tool_lookups")
        self.cost += 2
        if tool_key in self.tool_cache:
            self.record("tool_hits")
            result = self.tool_cache.get(tool_key)
        else:
            self.record("tool_misses")
            self.record("backend_calls")
            self.cost += 10
            result = backing_tool(req)
            self.tool_cache.update({tool_key: result})

        # The response is deliberately just the tool result.
        self.response_cache.update({response_key: result})
        return result


def rate(hits, lookups):
    return hits / lookups if lookups else 0.0


def main():
    trace = (
        Request("A", "q1", "X"),
        Request("A", "q1", "X"),
        Request("A", "q2", "X"),
        Request("B", "q1", "X"),
    )
    h = Helix()
    outputs = tuple(h.run(req) for req in trace)

    # Correctness is checked against the uncached synthetic tool.
    assert outputs == tuple(backing_tool(req) for req in trace)
    first, second, third, fourth = outputs
    assert first != fourth  # tenant-specific fixture values
    assert h.events.get("response_hits", 0) == 1
    assert h.events.get("response_lookups", 0) == 4
    assert h.events.get("tool_hits", 0) == 1
    assert h.events.get("tool_lookups", 0) == 3
    assert h.events.get("backend_calls", 0) == 2
    assert h.cost == 30

    response_hits = h.events.get("response_hits", 0)
    response_lookups = h.events.get("response_lookups", 0)
    tool_hits = h.events.get("tool_hits", 0)
    tool_lookups = h.events.get("tool_lookups", 0)

    print("response hits/lookups:", response_hits, "/", response_lookups)
    print("tool hits/lookups:", tool_hits, "/", tool_lookups)
    print("response hit rate:", f"{rate(response_hits, response_lookups):.3f}")
    print("conditional tool hit rate:", f"{rate(tool_hits, tool_lookups):.3f}")
    print("cache cost:", h.cost, "baseline cost:", 10 * len(trace))
    print("correct synthetic outputs:", len(outputs), "/", len(trace))

    # Version changes must miss both tiers even for a repeated question.
    before = h.events.get("backend_calls", 0)
    changed_tool = Request("A", "q1", "X", tool_version="v2")
    assert h.run(changed_tool) == backing_tool(changed_tool)
    assert h.events.get("backend_calls", 0) == before + 1

    before = h.events.get("backend_calls", 0)
    changed_policy = Request("A", "q1", "X", policy_version="p2")
    assert h.run(changed_policy) == backing_tool(changed_policy)
    assert h.events.get("backend_calls", 0) == before + 1

    # All-unique tenant scopes demonstrate lookup overhead.
    cold = Helix()
    unique = tuple(Request(str(i), "q1", "X") for i in range(4))
    assert tuple(cold.run(r) for r in unique) == tuple(
        backing_tool(r) for r in unique
    )
    assert cold.cost == 52
    print("unique-trace cache cost:", cold.cost,
          "baseline cost:", 10 * len(unique))
    print("tenant and version invariants: PASS")


if __name__ == "__main__":
    main()
