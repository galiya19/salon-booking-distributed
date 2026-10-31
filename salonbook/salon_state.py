from dataclasses import dataclass
from .types import Book, Cancel, Result, DURATION_MIN, DAY_MIN, OPEN_MIN, CLOSE_MIN


@dataclass
class StoredBooking:
    booking_id: str
    procedure: object
    start: int
    end: int
    customer: object
    status: str  # "CONFIRMED" or "CANCELLED"


class SalonState:
    def __init__(self):
        self.bookings = {}        # booking_id -> StoredBooking
        self.seen = {}            # request_id -> Result
        self.counter = 0

    def apply(self, command) -> Result:
        # 1. If command.request_id is in self.seen, return that stored result.
        # 2. If it's a Book, call self._book(command); if Cancel, self._cancel(command)
        # 3. Save the result in self.seen[command.request_id]
        # 4. Return it
        if command.request_id in self.seen:
            return self.seen[command.request_id]
        
        if isinstance(command, Book):
            result = self._book(command)
        elif isinstance(command, Cancel):
            result = self._cancel(command)
        else:
            raise ValueError(f"Unknown command type: {type(command)}")
        self.seen[command.request_id] = result
        
        return result

    def _book(self, cmd) -> Result:
        # a) end = cmd.start + DURATION_MIN[cmd.procedure]
        # b) opening hours check
        # c) overlap check against CONFIRMED bookings of the same procedure
        # d) otherwise: self.counter += 1, create a StoredBooking, return ok
        end = cmd.start + DURATION_MIN[cmd.procedure]
        
        minute_of_day = cmd.start % DAY_MIN
        if minute_of_day < OPEN_MIN or minute_of_day + DURATION_MIN[cmd.procedure] > CLOSE_MIN:
            return Result(ok=False, reason="outside_hours")
        
        bookings = [b for b in self.bookings.values() if b.status == "CONFIRMED" and b.procedure == cmd.procedure]
        for b in bookings:
            if not (end <= b.start or cmd.start >= b.end):
                return Result(ok=False, reason="slot_taken")
        self.counter += 1
        booking_id = f"b{self.counter}"
        new_booking = StoredBooking(
            booking_id=booking_id,
            procedure=cmd.procedure,
            start=cmd.start,
            end=end,
            customer=cmd.customer,
            status="CONFIRMED"
        )
        self.bookings[booking_id] = new_booking
        return Result(ok=True, booking_id=booking_id)       

    def _cancel(self, cmd) -> Result:
        booking = self.bookings.get(cmd.booking_id)
        
        if booking is None:
            return Result(ok=False, reason="not_found")
        
        booking.status = "CANCELLED"
        
        return Result(ok=True, booking_id=cmd.booking_id)

    def confirmed_bookings(self) -> list:
        confirmed = [
        b for b in self.bookings.values()
        if b.status == "CONFIRMED"
        ]

        return sorted(
         confirmed,
            key=lambda b: (b.procedure.value, b.start)
         )

    def snapshot(self):
        rows = tuple(
        (
            b.booking_id,
            b.procedure.value,
            b.start,
            b.end,
            b.status
        )
        for b in sorted(
            self.bookings.values(),
            key=lambda b: b.booking_id
         )
    )

        return (self.counter, rows)