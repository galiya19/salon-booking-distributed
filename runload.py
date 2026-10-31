import argparse

from salonbook.cluster import SalonCluster
from salonbook.loadgen import generate_requests, run_load


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--salons", type=int, default=100)
    p.add_argument("--groups", type=int, default=10)
    p.add_argument("--requests", type=int, default=20000)
    p.add_argument("--seed", type=int, default=1)
    args = p.parse_args()

    cluster = SalonCluster(args.salons, args.groups)
    requests = generate_requests(args.salons, args.requests, seed=args.seed)
    r = run_load(cluster, requests)

    print(f"salons={args.salons} groups={args.groups} requests={r['requests']}")
    print(f"time: {r['seconds']:.2f}s  throughput: {r['throughput']:.0f} req/s")
    print("outcomes:", r["outcomes"])
    print("top 5 salons (id, requests):", r["top_salons"])
    print("requests per group:", r["per_group"])
    print("DOUBLE BOOKINGS:", r["double_bookings"], "(must be 0)")
    print("retry mismatches:", r["retry_mismatches"], "(must be 0)")


if __name__ == "__main__":
    main()