from salonbook.cluster import Envelope, Router, SalonCluster
from salonbook.loadgen import generate_requests, run_load
from salonbook.types import Book, Cancel, Customer, Procedure

ANNA = Customer("Anna", "+77001112233", "anna@example.com")
T = 10 * 60  # 10:00 on day 0


def test_same_salon_always_routes_to_same_group():
    r = Router(10)
    assert r.group_for(42) == r.group_for(42)
    assert 0 <= r.group_for(42) < 10


def test_routes_spread_across_groups():
    r = Router(10)
    assert len({r.group_for(i) for i in range(100)}) == 10


def test_salons_do_not_interfere():
    c = SalonCluster(num_salons=2, num_groups=2)
    a = c.apply(Envelope(0, Book("r1", Procedure.HAIRCUT, T, ANNA)))
    b = c.apply(Envelope(1, Book("r2", Procedure.HAIRCUT, T, ANNA)))
    assert a.ok and b.ok  # same time, same procedure, different salons


def test_conflict_inside_one_salon_still_rejected():
    c = SalonCluster(2, 2)
    c.apply(Envelope(0, Book("r1", Procedure.HAIRCUT, T, ANNA)))
    r = c.apply(Envelope(0, Book("r2", Procedure.HAIRCUT, T + 30, ANNA)))
    assert not r.ok and r.reason == "slot_taken"


def test_unknown_salon_is_rejected():
    c = SalonCluster(2, 2)
    r = c.apply(Envelope(99, Book("r1", Procedure.HAIRCUT, T, ANNA)))
    assert not r.ok and r.reason == "unknown_salon"


def test_cancel_goes_to_the_right_salon():
    c = SalonCluster(2, 2)
    first = c.apply(Envelope(1, Book("r1", Procedure.WAX, T, ANNA)))
    assert c.apply(Envelope(1, Cancel("r2", first.booking_id))).ok


def test_loadgen_is_deterministic():
    assert generate_requests(20, 500, seed=7) == generate_requests(20, 500, seed=7)
    assert generate_requests(20, 500, seed=7) != generate_requests(20, 500, seed=8)


def test_load_run_has_no_double_bookings_and_stable_retries():
    c = SalonCluster(100, 10)
    reqs = generate_requests(100, 5000, seed=3)
    stats = run_load(c, reqs)
    assert stats["double_bookings"] == 0
    assert stats["retry_mismatches"] == 0
    assert stats["outcomes"].get("accepted", 0) > 0