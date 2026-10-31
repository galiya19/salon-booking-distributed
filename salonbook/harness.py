from .replica import ReplicaNode
from .sim import Simulation
from .simclient import SimClient


def build_cluster(seed=1, drop_prob=0.0, num_replicas=3, timeout=50):
    sim = Simulation(seed=seed, drop_prob=drop_prob)
    ids = [f"r{i}" for i in range(num_replicas)]
    replicas = []
    for i, rid in enumerate(ids):
        peers = [x for x in ids if x != rid]
        rep = ReplicaNode(rid, peers, is_leader=(i == 0))
        sim.add_node(rep)
        replicas.append(rep)
    client = SimClient("client", leader_id=ids[0], timeout=timeout)
    sim.add_node(client)
    return sim, replicas, client


def submit_all(sim, client, commands, spacing=5):
    for i, cmd in enumerate(commands):
        sim.schedule(i * spacing, lambda c=cmd: client.submit(c))
