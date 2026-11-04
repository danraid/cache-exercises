import json
from copy import deepcopy

FIXTURE = {
    ("north", "INV-17"): {"amount": 120, "currency": "GBP"},
    ("south", "INV-17"): {"amount": 240, "currency": "GBP"},
}
# Synthetic grants: (tenant, principal).
GRANTS = {("north", "alice"), ("north", "bob"),
          ("south", "alice")}


class Helix:
    def __init__(self, ttl=5):
        if ttl <= 0:
            raise ValueError("TTL must be positive")
        self.ttl = ttl
        self.now = 0                 # logical seconds
        self.cache = {}              # key -> (expiry, value)
        self.events = []
        self.calls = {"read": 0, "pay": 0}

    def advance(self, seconds):
        if seconds < 0:
            raise ValueError("clock must not move backwards")
        self.now += seconds

    def invoke(self, tenant, principal, policy_rev, tool,
               tool_rev, args):
        # Authorise before lookup, including on a potential hit.
        if (tenant, principal) not in GRANTS:
            self.events.append("DENY")
            raise PermissionError("not authorised")

        if tool not in ("read", "pay"):
            raise ValueError("unknown tool")
        if set(args) != {"invoice"} or not isinstance(args["invoice"], str):
            raise ValueError("expected a string invoice identifier")

        # Sorted keys make JSON object order irrelevant. This fixture
        # accepts strings only, avoiding ambiguous numeric coercion.
        canonical = json.dumps(args, sort_keys=True,
                               separators=(",", ":"), ensure_ascii=True)
        key = (tenant, principal, policy_rev, tool, tool_rev, canonical)

        if tool == "pay":
            # Side effects are never served from or written to cache.
            self.calls["pay"] += 1
            self.events.append("BYPASS_SIDE_EFFECT")
            return {"payment_invocation": self.calls["pay"]}

        entry = self.cache.get(key)
        if entry is not None:
            expiry, value = entry
            if self.now < expiry:
                self.events.append("HIT")
                return deepcopy(value)
            self.cache.pop(key)
            self.events.append("EXPIRED")

        self.events.append("MISS")
        self.calls["read"] += 1
        # A missing invoice raises; no negative entry is inserted.
        value = deepcopy(FIXTURE[(tenant, args["invoice"])])
        self.cache.update({key: (self.now + self.ttl, deepcopy(value))})
        return value


def main():
    h = Helix(ttl=5)
    args = {"invoice": "INV-17"}

    def read(tenant="north", principal="alice",
             policy="p1", version="v1"):
        return h.invoke(tenant, principal, policy, "read", version, args)

    assert read()["amount"] == 120          # miss
    result = read()                         # hit
    result["amount"] = -1                  # caller cannot mutate cache
    assert read()["amount"] == 120          # hit

    assert read(tenant="south")["amount"] == 240  # tenant miss
    assert read(principal="bob")["amount"] == 120  # principal miss
    read(version="v2")                      # tool-version miss
    read(policy="p2")                       # policy-version miss

    try:
        read(principal="mallory")
        raise AssertionError("unauthorised request was accepted")
    except PermissionError:
        pass

    h.advance(5)
    assert read()["amount"] == 120          # expired at boundary

    for _ in range(2):
        h.invoke("north", "alice", "p1", "pay", "v1", args)
    assert h.calls == {"read": 6, "pay": 2}
    assert h.events.count("HIT") == 2
    assert h.events.count("DENY") == 1
    assert h.events.count("BYPASS_SIDE_EFFECT") == 2

    # Missing resources are not cached: both attempts reach the tool.
    missing = {"invoice": "MISSING"}
    for _ in range(2):
        try:
            h.invoke("north", "alice", "p1", "read", "v1", missing)
            raise AssertionError("missing invoice unexpectedly found")
        except KeyError:
            pass
    assert h.calls["read"] == 8

    print("PASS")
    print("calls:", h.calls)
    print("events:", h.events)


if __name__ == "__main__":
    main()
