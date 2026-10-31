"""Print the state of every replica, and check the invariants."""


def replicas_identical(replicas):
    snaps = [r.state.snapshot() for r in replicas]
    return all(s == snaps[0] for s in snaps)


def count_overlaps(state):
    bad = 0
    by_proc = {}
    for b in state.confirmed_bookings():
        by_proc.setdefault(b.procedure, []).append(b)
    for bookings in by_proc.values():
        bookings.sort(key=lambda b: b.start)
        bad += sum(1 for a, b in zip(bookings, bookings[1:]) if b.start < a.end)
    return bad


def print_cluster(sim, replicas, title=""):
    print(f"\n=== t={sim.now}  {title} ===")
    for r in replicas:
        role = "leader  " if r.is_leader else "follower"
        status = "CRASHED" if r.crashed else "up     "
        n = len(r.state.confirmed_bookings())
        print(f"  {r.id} [{role}] {status}  applied={r.applied_seq:<4} bookings={n:<4} "
              f"overlaps={count_overlaps(r.state)}")
    print(f"  all replicas identical: {'YES' if replicas_identical(replicas) else 'NO'}")


def print_bookings(replica, limit=10):
    """Show the first few bookings of one replica."""
    print(f"\n{replica.id}'s calendar (first {limit}):")
    for b in sorted(replica.state.confirmed_bookings(), key=lambda b: b.start)[:limit]:
        day, minute = divmod(b.start, 1440)
        print(f"  day {day:<2} {minute // 60:02d}:{minute % 60:02d}  "
              f"{b.procedure.value:<10} {b.customer.name}")

        