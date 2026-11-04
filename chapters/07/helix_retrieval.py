import hashlib
import json
import re
from dataclasses import dataclass


def digest(value):
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def tokens(text):
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def candidate_order(item):
    score, chunk = item
    return -score, chunk.source, chunk.chunk


@dataclass(frozen=True)
class Chunk:
    tenant: str
    source: str
    chunk: str
    text: str
    readers: tuple[str, ...]


class HelixRetrieval:
    def __init__(self, chunks):
        self.chunks = list(chunks)
        self.index_generation = "index-1"
        self.ranker_version = "overlap-1"
        self.cache = {}
        self.hits = 0
        self.misses = 0

    def snapshot(self):
        # Includes unreturned documents and ACLs, not only previous hits.
        records = [
            [c.tenant, c.source, c.chunk, c.text, sorted(c.readers)]
            for c in self.chunks
        ]
        return digest(sorted(records))

    def search(self, tenant, principal, policy_revision, query, k=2):
        # Illustrative trusted boundary: real authentication occurs upstream.
        assert tenant and principal and policy_revision and k > 0
        snap = self.snapshot()
        key = digest({
            "schema": 1,
            "tenant": tenant,
            "principal": principal,
            "policy_revision": policy_revision,
            "query": query,
            "index_generation": self.index_generation,
            "snapshot": snap,
            "ranker": self.ranker_version,
            "k": k,
        })
        if key in self.cache:
            self.hits += 1
            return "hit", self.cache.get(key)

        self.misses += 1
        query_tokens = tokens(query)
        candidates = []
        for c in self.chunks:
            # Filter before ranking and top-k selection.
            if c.tenant != tenant or principal not in c.readers:
                continue
            score = len(query_tokens & tokens(c.text))
            if score:
                candidates.append((score, c))

        candidates.sort(key=candidate_order)
        result = tuple(
            (
                c.source,
                c.chunk,
                digest(c.text),
                c.text,
                score,
            )
            for score, c in candidates[:k]
        )
        self.cache.update({key: result})
        return "miss", result


def run():
    h = HelixRetrieval([
        Chunk("A", "policy", "p1",
              "audit records retained for six months", ("alice",)),
        Chunk("A", "guide", "g1",
              "audit records are reviewed monthly", ("alice", "bob")),
        Chunk("B", "private", "b1",
              "audit records tenant B secret", ("alice",)),
    ])
    q = "audit records retained"

    status, first = h.search("A", "alice", "acl-1", q)
    first_source, _, first_hash, _, _ = next(iter(first))
    assert status == "miss" and first_source == "policy"
    status, repeat = h.search("A", "alice", "acl-1", q)
    assert status == "hit" and repeat == first

    status, other_tenant = h.search("B", "alice", "acl-1", q)
    assert status == "miss"
    assert all(source != "policy" for source, *_ in other_tenant)

    # Revoke Alice's access to policy, and publish a policy revision.
    h.chunks.pop(0)
    h.chunks.insert(0, Chunk(
        "A", "policy", "p1",
        "audit records retained for six months", ()
    ))
    status, revoked = h.search("A", "alice", "acl-2", q)
    assert status == "miss"
    assert all(source != "policy" for source, *_ in revoked)

    # Restore access with changed content and a new published index.
    h.chunks.pop(0)
    h.chunks.insert(0, Chunk(
        "A", "policy", "p1",
        "audit records retained for twelve months", ("alice",)
    ))
    h.index_generation = "index-2"
    status, refreshed = h.search("A", "alice", "acl-3", q)
    source, chunk, content_hash, text, _ = next(iter(refreshed))
    assert status == "miss" and source == "policy"
    assert content_hash != first_hash
    assert "twelve months" in text

    # A changed index generation alone also invalidates.
    h.index_generation = "index-3"
    status, replay = h.search("A", "alice", "acl-3", q)
    assert status == "miss" and replay == refreshed

    print("All invariants passed.")
    print(f"hits={h.hits} misses={h.misses}")
    print("refreshed provenance:", (source, chunk, content_hash))


if __name__ == "__main__":
    run()
