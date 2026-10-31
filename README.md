**Distributed Beauty Salon Booking System**
Overview:

This project is a distributed booking system for beauty salons. The system allows customers to book and cancel beauty appointments and replicates booking data across multiple nodes. It’s inspired by online beauty booking platforms back in my hometown.

The main goal is to investigate how distributed systems maintain data consistency in the presence of message delays or losses, and temporary failures of individual nodes.

**Assumptions**
* Every salon is open between 9:00-18:00.
* Every salon offers the same 6 procedures: manicure (90 min), pedicure (90), haircut (60), brows (60), eyelashes (120), wax (45).
* Each salon has one specialist per procedure, so the bookable resource is (salon, procedure). Two bookings conflict when they are for the same procedure at overlapping times. A booking that ends exactly when another starts is not a conflict.
* A customer is just name, phone, email. There are no accounts.
* Time is an integer: minutes since the start of the simulation. The state machine never reads a clock.

**Features**
* Book beauty services such as manicures, pedicures, haircuts, brows, eyelashes, and waxing.
* Cancel existing appointments.
* Prevent overlapping bookings for the same service.
* Validate bookings against salon opening hours.
* Replicate booking commands across three simulated nodes.
* Retry client requests when responses are lost.
* Recover missing updates after a follower crashes or messages are dropped.
* Inspect the state of individual replicas.

**System Architecture**
The system uses a leader-follower replication model with three nodes:

* r0 — Leader: Receives client requests, processes bookings, assigns sequence numbers, and sends updates to followers.
* r1 — Follower: Maintains a replicated copy of the booking calendar.
* r2 — Follower: Maintains another replicated copy of the booking calendar.

The nodes communicate through a simulated network.

**Replication Process**
1. The client sends a booking or cancel request to the leader. Every request has a unique request_id.
2. If the leader has already seen that request_id (a client retry), it replies with the saved answer and does nothing else.
3. Otherwise, the leader gives the command the next sequence number, saves it in its log, and applies it to its own calendar. The booking rules decide whether it is accepted or rejected.
4. The leader sends the numbered command to both followers and replies to the client right away. It does not wait for the followers.
5. Each follower applies commands strictly in sequence order. If one arrives early, the follower buffers it. If one is missing, the follower asks the leader for it, using the heartbeat and catch-up messages described below.

**Failure Recovery**
The system uses heartbeat and catch-up messages.

The leader periodically announces its latest sequence number. If a follower discovers that it is behind, it requests the missing commands from the leader.

This allows followers to recover from temporary crashes and lost messages.


**Project Structure**
Distributed Booking system/
├── salonbook/
│   ├── types.py
│   ├── salon_state.py
│   ├── messages.py
│   ├── sim.py
│   ├── simclient.py
│   ├── replica.py
│   ├── cluster.py
│   ├── harness.py
│   ├── loadgen.py
│   └── view.py
├── tests/
├── check_replicas.py
├── demo.py
├── README.md
└── .gitignore

**Technologies**
Python 3
pytest for automated testing
Custom discrete-event network simulator

**Running it**
Requires Python 3.10 or newer.

git clone <repo-url>
cd <repo-folder>

python3 -m venv .venv
source .venv/bin/activate
pip install pytest

**Tests**
python3 -m pytest
To inspect replica states: python3 check_replicas.py

**Demo Link**
https://www.loom.com/share/e65f82ec3c2f447e8b9d0b91c7be7eb4 
