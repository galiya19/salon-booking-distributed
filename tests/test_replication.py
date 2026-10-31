import pytest

from salonbook.harness import build_cluster, submit_all
from salonbook.loadgen import generate_requests
from salonbook.view import count_overlaps, replicas_identical


def run(drop_prob=0.0, crash=None, n=100, seed=1, until=5000):
    sim, replicas, client = build_cluster(seed=seed, drop_prob=drop_prob)
    cmds = [e.command for e in generate_requests(1, n, seed=seed)]
    submit_all(sim, client, cmds, spacing=5)
    if crash:
        who, down, up = crash
        sim.schedule(down, replicas[who].crash)
        sim.schedule(up, replicas[who].recover)
    sim.run(until=until)
    return sim, replicas, client, cmds


def check_correct(replicas, client, cmds):
    assert len(client.results) == len({c.request_id for c in cmds})
    assert not client.failed
    assert all(count_overlaps(r.state) == 0 for r in replicas)
    assert replicas_identical(replicas)


def test_no_faults_replicas_identical():
    _, replicas, client, cmds = run()
    check_correct(replicas, client, cmds)
    assert replicas[0].applied_seq > 0


@pytest.mark.parametrize("drop", [0.1, 0.3])
def test_message_drops_replicas_still_identical(drop):
    _, replicas, client, cmds = run(drop_prob=drop)
    check_correct(replicas, client, cmds)


def test_follower_crash_and_recovery():
    _, replicas, client, cmds = run(crash=(2, 100, 400))
    check_correct(replicas, client, cmds)


def test_crash_plus_drops():
    _, replicas, client, cmds = run(drop_prob=0.2, crash=(1, 150, 450))
    check_correct(replicas, client, cmds)


def test_follower_is_actually_behind_while_crashed():
    sim, replicas, client, cmds = run(crash=(2, 100, 4000), until=1000)
    assert replicas[2].applied_seq < replicas[0].applied_seq
    assert not replicas_identical(replicas)