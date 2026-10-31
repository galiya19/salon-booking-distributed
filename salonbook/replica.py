from dataclasses import dataclass
from urllib import request

from .messages import Request, Response
from .salon_state import SalonState
from .sim import Node

@dataclass(frozen=True)
class Replicate:
    seq: int
    command: object


@dataclass(frozen=True)
class Heartbeat:
    last_seq: int


@dataclass(frozen=True)
class CatchUp:
    from_seq: int


class ReplicaNode(Node):
    """One copy of a salon's calendar. Node r0 is the leader.

    Contract with the rest of the project:
      - self.state        : a SalonState
      - self.applied_seq  : how many commands this replica has applied, in order
                            (view.py reads it)
      - the leader answers the client with Response(request_id, result)
    """

    def __init__(self, node_id, peers, is_leader=False):
        super().__init__(node_id)
        self.peers = peers            # ids of the other replicas
        self.is_leader = is_leader
        self.state = SalonState()
        self.applied_seq = 0
        self.log = {}
        self.buffer = {}
        self.heartbeat_interval = 10


    def on_start(self):
        if self.is_leader:
            self.set_timer(self.heartbeat_interval, self._heartbeat)    


    def on_message(self, src, msg):
        # A client sends a booking or cancellation request.
        if isinstance(msg, Request):
            if self.is_leader:
                self._handle_request(src, msg)

    # A follower receives a command from the leader.
        elif isinstance(msg, Replicate):
            if not self.is_leader:
                self._handle_replicate(msg)

    # A follower receives the leader's latest sequence number.
        elif isinstance(msg, Heartbeat):
            if not self.is_leader:
                if self.applied_seq < msg.last_seq:
                    self._request_catchup()

    # The leader receives a request for missing commands.
        elif isinstance(msg, CatchUp):
            if self.is_leader:
                self._send_missing(src, msg.from_seq)


    def _handle_request(self, src, msg):
        command = msg.command
        rid = command.request_id

        # Duplicate client request:
        # return the previous result without replicating again.
        if rid in self.state.seen:
            result = self.state.seen[rid]
            self.send(src, Response(rid, result))
            return

        # Assign the next sequence number.
        seq = self.applied_seq + 1

        # Save the command so followers can request it later.
        self.log[seq] = command

        # Apply the command to the leader's calendar.
        result = self.state.apply(command)
        self.applied_seq = seq

        # Send the command to every follower.
        for peer in self.peers:
            self.send(peer, Replicate(seq, command))

        # Respond to the client.
        self.send(src, Response(rid, result))


    def _handle_replicate(self, msg):
        seq = msg.seq

        # Already applied this command.
        if seq <= self.applied_seq:
            return

        # Store the command until it can be applied in order.
        self.buffer[seq] = msg.command

        # Apply any consecutive commands now available.
        self._apply_buffered()

        # If a gap remains, ask the leader for missing entries.
        if self.buffer:
            self._request_catchup()

    def _apply_buffered(self):
        next_seq = self.applied_seq + 1

        while next_seq in self.buffer:
            command = self.buffer.pop(next_seq)

            self.state.apply(command)
            self.applied_seq = next_seq

            next_seq += 1

    def _request_catchup(self):
        leader_id = "r0"

        self.send(
            leader_id,
            CatchUp(self.applied_seq + 1)
        )

    def _send_missing(self, follower_id, from_seq):
        for seq in range(from_seq, self.applied_seq + 1):
            command = self.log[seq]
            self.send(
                follower_id,
                Replicate(seq, command)
            )

    def _heartbeat(self):
        if not self.is_leader:
            return

        for peer in self.peers:
            self.send(peer, Heartbeat(self.applied_seq))

        # Schedule the next heartbeat.
        self.set_timer(
            self.heartbeat_interval,
            self._heartbeat
        )

    def on_recover(self):
        if self.is_leader:
            # Restart heartbeat after leader recovery.
            self.set_timer(
                self.heartbeat_interval,
                self._heartbeat
            )
        else:
            # Ask the leader for commands missed during the crash.
            self._request_catchup()
