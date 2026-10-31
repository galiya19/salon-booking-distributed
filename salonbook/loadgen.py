import random
import time
from collections import Counter

from .cluster import Envelope
from .types import (
    Book, Customer, Procedure, DAY_MIN, OPEN_MIN, CLOSE_MIN, SLOT_MIN,
)

PROCEDURES = list(Procedure)


def generate_requests(num_salons, num_requests, seed=1, days=30,
                      hot_prob=0.3, retry_prob=0.05):
    """Seeded, so a failing run can be replayed exactly.

    - Salon popularity is skewed: weight 1/(i+1), so a few salons get most traffic.
    - With probability hot_prob a request goes for a 'prime time' slot
      (14:00 on a Saturday), which creates heavy contention.
    - With probability retry_prob an earlier request is re-sent unchanged
      (same request_id), like an impatient client.
    """
    rng = random.Random(seed)
    salon_ids = list(range(num_salons))
    weights = [1 / (i + 1) for i in salon_ids]
    saturdays = [d for d in range(days) if d % 7 == 5] or [0]
    slots_per_day = (CLOSE_MIN - OPEN_MIN) // SLOT_MIN

    requests = []
    for n in range(num_requests):
        if requests and rng.random() < retry_prob:
            requests.append(rng.choice(requests))  # exact duplicate
            continue
        salon = rng.choices(salon_ids, weights=weights)[0]
        proc = rng.choice(PROCEDURES)
        if rng.random() < hot_prob:
            day, minute = rng.choice(saturdays), 14 * 60
        else:
            day = rng.randrange(days)
            minute = OPEN_MIN + rng.randrange(slots_per_day) * SLOT_MIN
        customer = Customer(f"c{n}", f"+7700{n:07d}", f"c{n}@example.com")
        requests.append(
            Envelope(salon, Book(f"r{n}", proc, day * DAY_MIN + minute, customer))
        )
    return requests


def count_double_bookings(cluster):
    """Correctness invariant. Must always be 0."""
    bad = 0
    for state in cluster.salons.values():
        by_proc = {}
        for b in state.confirmed_bookings():
            by_proc.setdefault(b.procedure, []).append(b)
        for bookings in by_proc.values():
            bookings.sort(key=lambda b: b.start)
            for a, b in zip(bookings, bookings[1:]):
                if b.start < a.end:
                    bad += 1
    return bad


def run_load(cluster, requests):
    """Send every request, collect metrics."""
    first_result = {}          # request_id -> first Result seen
    retry_mismatches = 0       # a retry must get the same answer
    outcomes = Counter()
    per_salon = Counter()
    per_group = Counter()

    t0 = time.perf_counter()
    for env in requests:
        result = cluster.apply(env)
        rid = env.command.request_id
        if rid in first_result:
            if result != first_result[rid]:
                retry_mismatches += 1
        else:
            first_result[rid] = result
        outcomes["accepted" if result.ok else f"rejected:{result.reason}"] += 1
        per_salon[env.salon_id] += 1
        per_group[cluster.router.group_for(env.salon_id)] += 1
    elapsed = time.perf_counter() - t0

    return {
        "requests": len(requests),
        "seconds": elapsed,
        "throughput": len(requests) / elapsed if elapsed else float("inf"),
        "outcomes": dict(outcomes),
        "top_salons": per_salon.most_common(5),
        "per_group": dict(sorted(per_group.items())),
        "double_bookings": count_double_bookings(cluster),
        "retry_mismatches": retry_mismatches,
    }