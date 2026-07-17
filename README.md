# BitTorrent Client

A minimal BitTorrent client written in Python. Downloads single-file torrents sequentially from an HTTP tracker using the core BitTorrent wire protocol.

Built as a learning project to understand the internals of BitTorrent — from bencoding and tracker announces to peer handshakes, block-level requests, and SHA-1 piece verification.

## Features

- **Torrent parsing** — decodes `.torrent` files using a from-scratch bencode parser
- **HTTP tracker** — announces to the tracker and receives a peer list
- **Peer wire protocol** — TCP handshake, bitfield, interested/unchoke messaging
- **Block-level downloading** — requests 16 KiB blocks and assembles them into pieces
- **SHA-1 verification** — every piece is hash-checked before being written to disk
- **Sequential download** — pieces are downloaded and written in order

## Project Structure

```
├── main.py            # Entry point — orchestrates the download pipeline
├── torrent.py         # Parses .torrent files and exposes metadata
├── tracker.py         # Announces to the HTTP tracker and returns peers
├── peer.py            # TCP connection, handshake, and wire protocol messages
├── piecemanager.py    # Block requests, piece assembly, and SHA-1 verification
├── parser.py          # Bencode encoder / decoder
├── constants.py       # Protocol constants (message IDs, sizes, timeouts)
└── exceptions.py      # Custom exception types
```

## Desktop UI (PySide6)

A modern desktop UI built with **PySide6 (Qt)** provides a clean, dark‑themed interface similar to qBittorrent. It includes:
- Toolbar with start, pause, stop, and magnet‑link actions
- Torrent details panel with info‑hash, tracker, and status
- Progress view with speed, ETA, and piece map
- Peer table and activity log
- Dark theme with rounded cards and modern typography


## Requirements

- Python 3.8+
- [requests](https://pypi.org/project/requests/)

## Usage

```bash
python main.py <torrent-file> [output-file]
```

| Argument | Required | Description |
|---|---|---|
| `torrent-file` | Yes | Path to a `.torrent` file |
| `output-file` | No | Output filename (defaults to `test_output.bin`) |

### Example

```bash
python main.py ubuntu-26.04-desktop-amd64.iso.torrent ubuntu.iso
```

Output:

```
2026-07-13 22:50:00  INFO      __main__  Received message id=5 (bitfield)
2026-07-13 22:50:00  INFO      __main__  Received message id=1 (unchoke)
2026-07-13 22:50:00  INFO      __main__  Piece length: 262144
2026-07-13 22:50:00  INFO      __main__  Total pieces: 237
2026-07-13 22:50:01  INFO      __main__  [1/237] 0.42%
2026-07-13 22:50:01  INFO      __main__  [2/237] 0.84%
...
2026-07-13 22:52:30  INFO      __main__  [237/237] 100.00%
2026-07-13 22:52:30  INFO      __main__  Download complete: ubuntu.iso
```

## How It Works

```
┌──────────┐      ┌──────────┐      ┌──────────┐      ┌──────────────┐
│  Torrent │─────▶│ Tracker  │─────▶│   Peer   │─────▶│ PieceManager │
│  (.torrent)     │ (HTTP)   │      │ (TCP)    │      │ (verify+write)│
└──────────┘      └──────────┘      └──────────┘      └──────────────┘
```

1. **Parse** — `Torrent` reads the `.torrent` file, decodes its bencoded metadata, and computes the SHA-1 info hash.
2. **Announce** — `Tracker` sends an HTTP GET to the tracker's announce URL with the info hash, peer ID, and download state. The tracker responds with a list of peers.
3. **Connect** — `Peer` opens a TCP socket to the first available peer and performs the BitTorrent handshake (protocol string, reserved bytes, info hash, peer ID).
4. **Negotiate** — The client receives the peer's bitfield, sends an `interested` message, and waits for an `unchoke` response.
5. **Download** — `PieceManager` iterates through every piece sequentially. For each piece, it requests 16 KiB blocks, reassembles them, and verifies the SHA-1 hash against the expected hash from the torrent metadata.
6. **Write** — Verified pieces are written to the output file in order.

## Future Plans

- **Multi-peer downloads** — connect to multiple peers simultaneously
- **Rarest-first piece selection** — prioritise rare pieces to improve swarm health
- **Seeding / uploading** — share downloaded pieces with other peers
- **Multi-file torrent support** — handle torrents containing multiple files
- **UDP tracker & DHT** — decentralised peer discovery
- **Magnet link support** — start downloads without a `.torrent` file
- **Concurrent I/O** — async or multi-threaded block requests for faster downloads

## License

This project is for educational purposes.
