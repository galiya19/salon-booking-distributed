from .messages import Request, Response
from .sim import Node


class SimClient(Node):
    """Sends a command to the leader and retries with the SAME request_id
    until it gets an answer. This is why SalonState is idempotent."""

    def __init__(self, node_id, leader_id, timeout=50, max_attempts=20):
        super().__init__(node_id)
        self.leader_id = leader_id
        self.timeout = timeout
        self.max_attempts = max_attempts
        self.pending = {}    # request_id -> command
        self.attempts = {}   # request_id -> number of sends
        self.results = {}    # request_id -> Result
        self.failed = set()  # gave up after max_attempts

    def submit(self, command):
        rid = command.request_id
        self.pending[rid] = command
        self.attempts[rid] = 0
        self._try_send(rid)

    def _try_send(self, rid):
        if rid not in self.pending:
            return
        if self.attempts[rid] >= self.max_attempts:
            self.failed.add(rid)
            del self.pending[rid]
            return
        self.attempts[rid] += 1
        self.send(self.leader_id, Request(self.pending[rid]))
        self.set_timer(self.timeout, lambda: self._try_send(rid))

    def on_message(self, src, msg):
        if isinstance(msg, Response) and msg.request_id in self.pending:
            self.results[msg.request_id] = msg.result
            del self.pending[msg.request_id]

    @property
    def total_sends(self):
        return sum(self.attempts.values())