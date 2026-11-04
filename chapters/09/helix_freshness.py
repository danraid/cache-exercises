from dataclasses import dataclass


@dataclass(frozen=True)
class Entry:
    value: str
    version: int
    validated_at: int
    expires_at: int
    source: str


class Helix:
    def __init__(self, ttl=4):
        if ttl <= 0:
            raise ValueError("ttl must be positive")
        self.ttl = ttl
        self.now = 0
        self.source = {}       # (tenant, object) -> (version, value)
        self.cache = {}        # (tenant, object) -> Entry
        self.events = list()   # (delivery_time, tenant, object, version)
        self.trace = list()    # synthetic observability record

    def seed(self, tenant, obj, value):
        key = (tenant, obj)
        if key in self.source:
            raise ValueError("already seeded")
        self.source.update({key: (1, value)})

    def advance(self, time):
        if time < self.now:
            raise ValueError("clock cannot move backwards")
        self.now = time
        self.deliver()

    def update(self, tenant, obj, value, delay=0):
        if delay < 0:
            raise ValueError("delay cannot be negative")
        key = (tenant, obj)
        if key not in self.source:
            raise KeyError(key)
        old_version, _ = self.source.get(key)
        version = old_version + 1
        self.source.update({key: (version, value)})
        self.events.append((self.now + delay, tenant, obj, version))
        self.trace.append(("update", self.now, key, version))
        self.deliver()

    def deliver(self):
        ready = []
        pending = []
        for event in self.events:
            delivery_time, _, _, _ = event
            if delivery_time <= self.now:
                ready.append(event)
            else:
                pending.append(event)
        self.events = pending

        for _, tenant, obj, version in sorted(ready):
            key = (tenant, obj)
            entry = self.cache.get(key)
            # An old or duplicate event cannot evict a newer entry.
            if entry is not None and entry.version < version:
                self.cache.pop(key)
                self.trace.append(("invalidate", self.now, key, version))

    def read(self, tenant, obj, validate_version=True):
        key = (tenant, obj)
        if key not in self.source:
            raise KeyError(key)
        current_version, current_value = self.source.get(key)
        entry = self.cache.get(key)

        if entry is not None:
            expired = self.now >= entry.expires_at
            mismatch = validate_version and entry.version != current_version
            if not expired and not mismatch:
                self.trace.append(("hit", self.now, key, entry.version))
                return entry
            reason = "expired" if expired else "version"
            self.trace.append((reason, self.now, key, entry.version))
            self.cache.pop(key)

        entry = Entry(
            value=current_value,
            version=current_version,
            validated_at=self.now,
            expires_at=self.now + self.ttl,
            source=f"authority:{tenant}/{obj}",
        )
        self.cache.update({key: entry})
        self.trace.append(("miss", self.now, key, entry.version))
        return entry


def tests():
    h = Helix(ttl=4)
    h.seed("A", "doc", "allow")
    h.seed("B", "doc", "B-only")

    first = h.read("A", "doc")
    assert first.version == 1
    assert h.read("A", "doc") == first       # repeat hits
    assert h.read("B", "doc").value == "B-only"

    # Immediate delivery models the security-critical fixture.
    h.advance(1)
    h.update("A", "doc", "deny", delay=0)
    assert ("A", "doc") not in h.cache
    assert h.read("A", "doc").value == "deny"
    assert h.read("B", "doc").value == "B-only"

    # Delayed event: an unvalidated read can return stale data.
    h.advance(2)
    h.update("A", "doc", "allow-again", delay=2)
    stale = h.read("A", "doc", validate_version=False)
    assert stale.version == 2 and stale.value == "deny"

    # Synchronous authoritative version check detects the mismatch.
    fresh = h.read("A", "doc", validate_version=True)
    assert fresh.version == 3 and fresh.value == "allow-again"
    assert fresh.source == "authority:A/doc"

    # Late revision-3 event must not evict the revision-3 entry.
    h.advance(4)
    assert h.read("A", "doc").version == 3

    # Expiry is inclusive at the deadline: filled at 2, TTL 4.
    h.advance(6)
    assert h.read("A", "doc").validated_at == 6

    print("Helix freshness tests passed")
    for record in h.trace:
        print(record)


if __name__ == "__main__":
    tests()
