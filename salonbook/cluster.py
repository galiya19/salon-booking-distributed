from dataclasses import dataclass

from .salon_state import SalonState
from .types import Result


@dataclass(frozen=True)
class Envelope:
    """A command addressed to one salon."""
    salon_id: int
    command: object  # a Book or Cancel


class Router:
    """Maps a salon to a replica group (0 .. num_groups-1)."""

    def __init__(self, num_groups: int):
        self.num_groups = num_groups

    def group_for(self, salon_id: int) -> int:
        """Return the replica group for a given salon_id."""
        return salon_id % self.num_groups


class SalonCluster:
    """Single-process stand-in for 'many replica groups'.

    Later, apply() becomes: send the command to the right replica group.
    """

    def __init__(self, num_salons: int, num_groups: int):
        self.num_salons = num_salons
        self.router = Router(num_groups)
        self.salons = {i: SalonState() for i in range(num_salons)}

    def apply(self, envelope: Envelope) -> Result:
        """Apply a command to the right salon, return the Result."""
        salon_state = self.salons.get(envelope.salon_id)
       
        if salon_state is None:
            
            return Result(ok=False, reason="unknown_salon")
        return salon_state.apply(envelope.command)