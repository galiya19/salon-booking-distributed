from dataclasses import dataclass

from .types import Result


@dataclass(frozen=True)
class Request:
    """Client -> leader. `command` is a Book or Cancel."""
    command: object


@dataclass(frozen=True)
class Response:
    """Leader -> client."""
    request_id: str
    result: Result

# Messages between replicas (replicate, ack, catch-up, ...) are for YOU to define.