import json
from dataclasses import dataclass

# Synthetic, immutable source fixtures. Tool version v2 represents
# a revised implementation; these examples happen to return the same value.
FIXTURES = {
    ("tenant-a", "paper-1"): "revision-3",
    ("tenant-b", "paper-1"): "revision-8",
}
GRANTS = {
    "alice": {"tenant-a"},
    "bob": {"tenant-b"},
}


@dataclass(frozen=True)
class Request:
    actor: str
    tenant: str
    tool_version: str
    document: str


class Helix:
    def __init__(self):
        self.cache = {}
        self.trace = []

    def lookup(self, req):
        # Check current access before looking in the cache.
        if req.tenant not in GRANTS.get(req.actor, set()):
            self.trace.append({"event": "denied"})
            raise PermissionError("tenant access denied")

        # Scope is tenant-wide in this fixture: all authorised actors
        # in a tenant are assumed to have identical document permissions.
        cache_key = (
            req.tenant,
            "tenant-wide-read",
            "revision_lookup",
            req.tool_version,
            req.document,
            "fixture-data-v1",
        )
        if cache_key in self.cache:
            result = self.cache.get(cache_key)
            event = "hit"
        else:
            result = FIXTURES[(req.tenant, req.document)]
            self.cache.update({cache_key: result})
            event = "miss"

        self.trace.append({
            "event": event,
            "tenant": req.tenant,
            "tool_version": req.tool_version,
            "document": req.document,
            "result": result,
        })
        return result


def main():
    h = Helix()
    requests = [
        Request("alice", "tenant-a", "v1", "paper-1"),
        Request("alice", "tenant-a", "v1", "paper-1"),
        Request("bob",   "tenant-b", "v1", "paper-1"),
        Request("alice", "tenant-a", "v2", "paper-1"),
    ]
    expected = ["revision-3", "revision-3", "revision-8", "revision-3"]
    outcomes = [h.lookup(r) for r in requests]
    assert outcomes == expected
    assert [x["event"] for x in h.trace] == ["miss", "hit", "miss", "miss"]

    # A cached value must not bypass authorisation.
    try:
        h.lookup(Request("bob", "tenant-a", "v1", "paper-1"))
    except PermissionError:
        pass
    else:
        raise AssertionError("unauthorised request was not denied")

    eligible = [x for x in h.trace if x["event"] in ("hit", "miss")]
    hits = sum(x["event"] == "hit" for x in eligible)
    report = {
        "trace": h.trace,
        "eligible_requests": len(eligible),
        "hits": hits,
        "hit_rate": hits / len(eligible),
        "correct_outcomes": sum(a == b for a, b in zip(outcomes, expected)),
        "outcomes_checked": len(expected),
        "denied_requests": sum(x["event"] == "denied" for x in h.trace),
    }
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
