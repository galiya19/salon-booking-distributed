"""Demo: 3 replicas of one salon, lossy network, a follower crashes and recovers."""
from salonbook.harness import build_cluster, submit_all
from salonbook.loadgen import generate_requests
from salonbook.view import print_cluster, print_bookings, replicas_identical, count_overlaps

NUM_REQUESTS = 200
DROP_PROB = 0.15

sim, replicas, client = build_cluster(seed=1, drop_prob=DROP_PROB)
leader, follower_a, follower_b = replicas

# One salon, heavy contention (many clients chase the same slots)
commands = [env.command for env in generate_requests(1, NUM_REQUESTS, seed=1)]
unique_ids = {c.request_id for c in commands}  # some commands are client retries
submit_all(sim, client, commands, spacing=5)

# Failure scenario: follower r2 is down for part of the run
sim.schedule(300, follower_b.crash)
sim.schedule(700, follower_b.recover)

# Snapshots of the cluster at interesting moments
sim.schedule(250, lambda: print_cluster(sim, replicas, "before the crash"))
sim.schedule(600, lambda: print_cluster(sim, replicas, "r2 is DOWN (it is missing bookings)"))
sim.schedule(1200, lambda: print_cluster(sim, replicas, "after r2 recovered"))

sim.run(until=5000)

print_cluster(sim, replicas, "FINAL")
print_bookings(leader)
print("\nnetwork:", dict(sim.stats))
print(f"client: answered={len(client.results)}/{len(unique_ids)} distinct requests "
      f"gave_up={len(client.failed)} total_sends={client.total_sends}")
print("DOUBLE BOOKINGS (any replica):", sum(count_overlaps(r.state) for r in replicas))
print("REPLICAS IDENTICAL:", replicas_identical(replicas))