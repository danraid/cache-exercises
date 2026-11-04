from dataclasses import dataclass
import json


@dataclass(frozen=True)
class Key:
    tenant: str
    model: str
    session: str


class PagePool:
    def __init__(self, capacity):
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        self.capacity = capacity
        self.entries = {}       # key -> (page count, last access)
        self.clock = 0
        self.events = []

    @property
    def used(self):
        return sum(pages for pages, _ in self.entries.values())

    def check(self):
        assert 0 <= self.used <= self.capacity
        assert all(pages > 0 for pages, _ in self.entries.values())

    def lookup(self, key):
        self.clock += 1
        if key not in self.entries:
            self.events.append(["miss", key.session])
            return False
        pages, _ = self.entries.get(key)
        self.entries.update({key: (pages, self.clock)})
        self.events.append(["hit", key.session])
        self.check()
        return True

    def choose_victim(self):
        # Insertion order resolves ties deterministically.
        def last_access(key):
            _, timestamp = self.entries.get(key)
            return timestamp

        return min(self.entries, key=last_access)

    def allocate(self, key, pages):
        if pages <= 0:
            raise ValueError("pages must be positive")
        if key in self.entries:
            raise ValueError("entry already exists")
        if pages > self.capacity:
            self.events.append(["reject", key.session])
            self.check()
            return False

        while self.used + pages > self.capacity:
            victim = self.choose_victim()
            count, _ = self.entries.pop(victim)
            self.events.append(["evict", victim.session, count])

        self.clock += 1
        self.entries.update({key: (pages, self.clock)})
        self.events.append(["allocate", key.session, pages])
        self.check()
        return True


def main():
    pool = PagePool(capacity=4)
    a = Key("tenant-A", "model-v1", "A")
    b = Key("tenant-B", "model-v1", "B")
    c = Key("tenant-A", "model-v1", "C")

    assert pool.allocate(a, 2)
    assert pool.allocate(b, 1)
    assert pool.lookup(a)  # A is now newer than B.
    assert not pool.lookup(Key("tenant-B", "model-v1", "A"))
    assert not pool.lookup(Key("tenant-A", "model-v2", "A"))
    assert pool.allocate(c, 2)  # B is the LRU victim.
    assert b not in pool.entries
    assert a in pool.entries and c in pool.entries
    assert pool.used == 4

    before = dict(pool.entries)
    assert not pool.allocate(Key("tenant-A", "model-v1", "large"), 5)
    assert pool.entries == before
    pool.check()

    print(json.dumps({
        "capacity_pages": pool.capacity,
        "used_pages": pool.used,
        "resident_sessions": sorted(k.session for k in pool.entries),
        "events": pool.events,
    }, indent=2))


if __name__ == "__main__":
    main()
