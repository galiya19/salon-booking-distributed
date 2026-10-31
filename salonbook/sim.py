"""A tiny discrete-event simulator: a clock, a lossy network, and nodes.

Time is an integer number of ticks (milliseconds). Nothing here sleeps:
the simulator jumps from one event to the next, so a long scenario runs instantly
and, because everything is seeded, the same seed always gives the same run.

Crash model: a crashed node receives nothing and its timers do nothing,
but its in-memory state survives (like data on a disk).
"""
import heapq            # to process events in order of time
import random           # for delays and dropped messages
from collections import Counter


class Simulation:
    def __init__(self, seed=1, drop_prob=0.0, min_delay=1, max_delay=10):
        self.now = 0
        self.rng = random.Random(seed)
        self.drop_prob = drop_prob
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.nodes = {}
        self.stats = Counter()  # sent / dropped / delivered / lost_to_crash
        self._queue = []        # (time, tiebreak, callable)
        self._tiebreak = 0

    def add_node(self, node):
        self.nodes[node.id] = node
        node.sim = self
        node.on_start()

    def schedule(self, delay, fn):
        """Run fn() `delay` ticks from now."""
        self._tiebreak += 1
        heapq.heappush(self._queue, (self.now + delay, self._tiebreak, fn))

    def send(self, src, dst, msg):
        self.stats["sent"] += 1
        if self.rng.random() < self.drop_prob:
            self.stats["dropped"] += 1
            return
        delay = self.rng.randint(self.min_delay, self.max_delay)
        self.schedule(delay, lambda: self._deliver(src, dst, msg))

    def _deliver(self, src, dst, msg):
        node = self.nodes[dst]
        if node.crashed:
            self.stats["lost_to_crash"] += 1
            return
        self.stats["delivered"] += 1
        node.on_message(src, msg)

    def run(self, until):
        """Process events up to time `until`."""
        while self._queue and self._queue[0][0] <= until:
            t, _, fn = heapq.heappop(self._queue)
            self.now = t
            fn()
        self.now = until


class Node:
    def __init__(self, node_id):
        self.id = node_id
        self.sim = None
        self.crashed = False

    # --- hooks you override ---
    def on_start(self):
        """Called once when the node is added to the simulation."""

    def on_message(self, src, msg):
        raise NotImplementedError

    def on_recover(self):
        """Called when the node comes back after a crash.
        Timers that fired while crashed did nothing, so restart yours here."""

    # --- tools you call ---
    def send(self, dst, msg):
        if not self.crashed:
            self.sim.send(self.id, dst, msg)

    def set_timer(self, delay, fn):
        self.sim.schedule(delay, lambda: None if self.crashed else fn())

    def crash(self):
        self.crashed = True

    def recover(self):
        self.crashed = False
        self.on_recover()