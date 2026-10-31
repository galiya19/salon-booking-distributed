from dataclasses import dataclass
from enum import Enum

class Procedure(Enum):
    MANICURE = "manicure"
    PEDICURE = "pedicure"
    HAIRCUT = "haircut"
    BROWS = "brows"
    EYELASHES = "eyelashes"
    WAX = "wax"

# Not Enum values: Enum members with equal values become aliases,
# so MANICURE = 90 and PEDICURE = 90 would turn into the same member.
DURATION_MIN = {
    Procedure.MANICURE: 90, Procedure.PEDICURE: 90, Procedure.HAIRCUT: 60,
    Procedure.BROWS: 60, Procedure.EYELASHES: 120, Procedure.WAX: 45,
}

# Time is an integer: minutes since the start of the simulation.
# day = t // DAY_MIN, minute of day = t % DAY_MIN
DAY_MIN = 24 * 60
OPEN_MIN = 9 * 60      # 9:00
CLOSE_MIN = 18 * 60    # 18:00
SLOT_MIN = 15


@dataclass(frozen=True)
class Customer:
    name: str
    phone: str   # string, not a number
    email: str

@dataclass(frozen=True)
class Book:
    request_id: str      # client-generated, makes retries safe
    procedure: Procedure
    start: int           # minutes since simulation start
    customer: Customer

@dataclass(frozen=True)
class Cancel:
    request_id: str
    booking_id: str

@dataclass(frozen=True)
class Result:
    ok: bool
    booking_id: str | None = None
    reason: str | None = None   # e.g. "slot_taken", "outside_hours"