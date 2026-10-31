from salonbook.harness import build_cluster
from salonbook.types import Book, Customer, Procedure

sim, replicas, client = build_cluster()

alice = Customer(
    name="Alice",
    phone="123456789",
    email="alice@example.com"
)

booking = Book(
    request_id="test1",
    procedure=Procedure.MANICURE,
    start=600,
    customer=alice
)

client.submit(booking)
sim.run(until=200)

for replica in replicas:
    print(
        replica.id,
        "applied_seq =", replica.applied_seq,
        "state =", replica.state.snapshot()
    )

print("Client results:", client.results)