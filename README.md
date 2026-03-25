# deGuppe

`TOR` `Blockchain` `Python` `WebSockets` `SQLite`

**Decentralized, peer-run, real-time communication system over TOR with hybrid blockchain storage.**

> 🏆 Best Poster Presentation — 47th National Systems Conference, Systems Society of India
> · International Soonami Cohort 3 Funded · Best Project Web3/AI for Good — IITD Tryst
> · Third Prize Overall — IITD Tryst Track · Best Live Demo — IITD Tryst

![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

---

## What makes it different

- **TOR hidden services as addresses** — each peer spawns an ephemeral v3 `.onion` address via `stem`; messages never leave the TOR network and neither endpoint's IP is exposed, even to each other
- **No signaling server** — peer discovery is out-of-band (you share your `.onion` address); there is no directory, no relay, no broker
- **Two independent client implementations** — `cli-client/` uses raw TCP sockets over TOR's SOCKS5 proxy; `web-client/` uses FastAPI + WebSocket for the browser UI with HTTP POST over TOR for inter-peer transport
- **Persistent identity** — the hidden service private key is saved locally so your `.onion` address survives restarts

---

## Architecture

```
  Peer A                        TOR Network                      Peer B
  ──────                        ───────────                      ──────
  stem launches TOR                                         stem launches TOR
  Controller creates                                        Controller creates
  ephemeral hidden service                                  ephemeral hidden service
  → gets <hash_a>.onion                                     → gets <hash_b>.onion

  [Out-of-band: A tells B their .onion address, B tells A theirs]

  CLI client:                                               CLI client:
  socks.socksocket()         ──── TCP over TOR ────>        socket.listen()
  s.connect(hash_b.onion, 81)                               conn.recv(1024)
  s.sendall(str(event)+"###")                               INSERT INTO msgs
  INSERT INTO msgs                                          (SQLite local)
  (SQLite local)

  Web client:                                               Web client:
  Browser ←──WebSocket──→ FastAPI                           FastAPI
                           tor_repo.post(                   POST /api/event_bucket
                             hash_b.onion,                  → broadcast via WebSocket
                             {"sender":…,"content":…}       → Browser
                           )  [HTTP over TOR SOCKS5]
```

Neither peer's IP address is visible to the other or to any intermediate node.
The `.onion` address is the only identifier.

---

## Recognition

- **Best Poster Presentation** — 47th National Systems Conference (NSC-47), Systems Society of India
- **International Soonami Cohort 3** — Funded project, Web3/AI for Good category
- **Best Project: Web3/AI for Good** — IITD Tryst
- **Third Prize Overall** — IITD Tryst Track
- **Best Live Demo** — IITD Tryst

---

## Installation

```bash
# Requirements: Python 3.8+, TOR binary installed
# Debian/Ubuntu:  sudo apt install tor
# macOS:          brew install tor

pip install stem PySocks requests fastapi uvicorn jinja2 orjson pydantic

git clone https://github.com/QuditWolf/deGuppe.git
cd deGuppe
```

### Terminal client

```bash
cd cli-client
python3 cli_deGuppe.py
# Prompts: port to listen on (default 6666), peer's .onion address, your alias
# Your .onion address is printed at startup — share it with your peer
```

### Web client

```bash
cd web-client
uvicorn main:app --host 0.0.0.0 --port 8000
# Prompts: peer's .onion address, your nickname
# Open http://localhost:8000 in a browser
# Your identity (nick @ .onion address) is shown in the UI
```

---

## How it works

### TOR hidden service setup

On startup, both clients call `stem.process.launch_tor_with_config()` to spawn a
TOR process with a local SOCKS5 proxy (port 9050) and a control port (9151 for
CLI, 9051 for web). They authenticate to the control port and call
`controller.create_ephemeral_hidden_service({81: PORT})` (CLI) or `{80: 8000}`
(web), which registers a v3 onion hidden service with the TOR network.
The private key is written to `./my_service_key` on first run; subsequent runs
reload it so the same `.onion` address is reused.
`await_publication=True` blocks until the descriptor is published to the TOR
HSDir nodes (~30–60 s on first run).

### Peer-to-peer transport

**CLI client**: Uses `PySocks` (`socks.socksocket()`) to open a raw TCP connection
through TOR's SOCKS5 proxy to the peer's `.onion` address on port 81. Messages
are Python dicts serialized with `str()` and delimited with `"###"`:

```
{'type': 'message', 'fromalias': 'alice', 'payload': 'hello'}###
```

Two threads run concurrently: `get_thread()` binds a listening socket on
`0.0.0.0:PORT` and accepts an incoming connection; `send_thread()` connects to
the remote peer and loops on stdin.

**Web client**: The FastAPI server exposes `/api/event_bucket` as the inbound
endpoint for TOR-routed POST requests (JSON: `{"sender": str, "content": str}`).
Outbound messages go through `TorRequest`, a `requests.Session` proxied via
`socks5h://localhost:9050` — the `socks5h` scheme resolves `.onion` hostnames
through TOR rather than the system resolver. The browser connects via WebSocket
to `/ws/{client_id}`; inbound TOR messages are broadcast to all active WebSocket
connections via `ConnectionManager.broadcast()`.

### Message storage

The CLI client creates a session-scoped SQLite file (`msgs<random>.db`) with
a single table:

```sql
CREATE TABLE msgs (frome VARCHAR(20), time VARCHAR(20), msg VARCHAR(100));
```

Each sent and received message is inserted with a local timestamp. If no messages
were exchanged the file is deleted on exit. The `api.py` module (experimental
backend) appends events as a JSON list to `msgs.txt`.

### Peer discovery

There is no DHT, no rendezvous server, and no protocol-level peer discovery.
Each node's `.onion` address is printed to stdout at startup; peers exchange
it out-of-band. The CLI client supports loopback testing by leaving the peer
address blank (connects to your own `.onion`).

### Blockchain layer [work in progress]

`cli-client/api.py` accumulates events into an in-memory list returned as
`{"blockchain": [...]}`. This is scaffolding for a planned append-only event
log; the current implementation is a flat list (`fake_db`) and does not yet
implement hashing, chaining, or public anchoring. [TODO: verify if this layer
is under active development]

---

## Limitations / Known issues

- **Requires local TOR binary** — `stem` launches TOR as a subprocess; TOR must be installed separately
- **Single connection per session (CLI)** — `get_thread()` calls `l.accept()` once; only one peer can connect per run
- **Manual peer discovery** — `.onion` addresses must be shared out-of-band
- **No E2E encryption beyond TOR** — message payloads are plaintext within the TOR circuit; TOR provides transport anonymity, not message-level encryption between aliases
- **SQLite not suitable for groups** — designed for 1:1 messaging; no group membership or fanout logic
- **`api.py` has extra dependencies** (`orjson`, `fastapi`) not needed by the CLI client; no separate requirements file exists

