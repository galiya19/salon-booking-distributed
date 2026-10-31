from salonbook.salon_state import SalonState
from salonbook.types import Book, Cancel, Customer, Procedure

ANNA = Customer("Anna", "+77001112233", "anna@example.com")
BOB = Customer("Bob", "+77004445566", "bob@example.com")


def at(day, hour, minute=0):
    """Minutes since simulation start."""
    return day * 24 * 60 + hour * 60 + minute


def book(rid, proc, start, who=ANNA):
    return Book(rid, proc, start, who)


def test_booking_in_free_slot_succeeds():
    s = SalonState()
    r = s.apply(book("r1", Procedure.HAIRCUT, at(0, 10)))
    assert r.ok and r.booking_id is not None
    assert len(s.confirmed_bookings()) == 1


def test_overlapping_same_procedure_is_rejected():
    s = SalonState()
    s.apply(book("r1", Procedure.HAIRCUT, at(0, 10)))            # 10:00-11:00
    r = s.apply(book("r2", Procedure.HAIRCUT, at(0, 10, 30), BOB))  # 10:30-11:30
    assert not r.ok and r.reason == "slot_taken"
    assert len(s.confirmed_bookings()) == 1


def test_different_procedure_same_time_is_allowed():
    s = SalonState()
    s.apply(book("r1", Procedure.HAIRCUT, at(0, 10)))
    r = s.apply(book("r2", Procedure.BROWS, at(0, 10), BOB))
    assert r.ok


def test_back_to_back_is_not_an_overlap():
    s = SalonState()
    s.apply(book("r1", Procedure.HAIRCUT, at(0, 10)))            # ends 11:00
    r = s.apply(book("r2", Procedure.HAIRCUT, at(0, 11), BOB))   # starts 11:00
    assert r.ok


def test_same_time_on_a_different_day_is_allowed():
    s = SalonState()
    s.apply(book("r1", Procedure.HAIRCUT, at(0, 10)))
    r = s.apply(book("r2", Procedure.HAIRCUT, at(1, 10), BOB))
    assert r.ok


def test_before_opening_is_rejected():
    s = SalonState()
    r = s.apply(book("r1", Procedure.HAIRCUT, at(0, 8, 30)))
    assert not r.ok and r.reason == "outside_hours"


def test_ending_after_closing_is_rejected():
    s = SalonState()
    # eyelashes take 120 min: 17:00 -> 19:00, past closing
    r = s.apply(book("r1", Procedure.EYELASHES, at(0, 17)))
    assert not r.ok and r.reason == "outside_hours"


def test_ending_exactly_at_closing_is_allowed():
    s = SalonState()
    r = s.apply(book("r1", Procedure.EYELASHES, at(0, 16)))  # 16:00 -> 18:00
    assert r.ok
    

def test_late_night_booking_is_rejected():
    s = SalonState()
    r = s.apply(book("r1", Procedure.HAIRCUT, at(0, 23)))
    assert not r.ok and r.reason == "outside_hours"


def test_duplicate_request_id_returns_same_result_and_no_second_booking():
    s = SalonState()
    first = s.apply(book("r1", Procedure.HAIRCUT, at(0, 10)))
    again = s.apply(book("r1", Procedure.HAIRCUT, at(0, 10)))
    assert again == first
    assert len(s.confirmed_bookings()) == 1


def test_cancel_frees_the_slot():
    s = SalonState()
    first = s.apply(book("r1", Procedure.HAIRCUT, at(0, 10)))
    c = s.apply(Cancel("r2", first.booking_id))
    assert c.ok
    r = s.apply(book("r3", Procedure.HAIRCUT, at(0, 10), BOB))
    assert r.ok


def test_cancel_unknown_booking_fails():
    s = SalonState()
    c = s.apply(Cancel("r1", "does-not-exist"))
    assert not c.ok and c.reason == "not_found"


def test_same_commands_give_identical_state_on_two_replicas():
    cmds = [
        book("r1", Procedure.HAIRCUT, at(0, 10)),
        book("r2", Procedure.HAIRCUT, at(0, 10, 30), BOB),  # rejected
        book("r3", Procedure.WAX, at(0, 12), BOB),
        book("r1", Procedure.HAIRCUT, at(0, 10)),           # duplicate
    ]
    a, b = SalonState(), SalonState()
    results_a = [a.apply(c) for c in cmds]
    results_b = [b.apply(c) for c in cmds]
    assert results_a == results_b
    assert a.snapshot() == b.snapshot()