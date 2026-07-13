"""
BitTorrent client — entry point.

Downloads a single-file torrent sequentially: parses the .torrent,
contacts the tracker, connects to the first available peer, and
writes verified pieces to disk.
"""

import logging
import sys

from torrent import Torrent
from tracker import Tracker
from piecemanager import PieceManager

logger = logging.getLogger(__name__)


def download(torrent_path, output_path):
    """Run the full download pipeline for a single torrent.

    1. Parse the .torrent file.
    2. Announce to the tracker and pick the first peer.
    3. Handshake → bitfield → interested → unchoke.
    4. Download every piece sequentially, verify SHA-1, write to disk.
    """
    torrent = Torrent(torrent_path)
    tracker = Tracker(torrent)
    peers = tracker.get_peers()
    peer = peers[0]

    peer.handshake(torrent.info_hash, tracker.peer_id)

    msg_id, payload = peer.recv_message()  # bitfield
    logger.info("Received message id=%s (bitfield)", msg_id)

    peer.send_interested()

    msg_id, payload = peer.recv_message()  # unchoke
    logger.info("Received message id=%s (unchoke)", msg_id)

    logger.info("Piece length: %d", torrent.piece_length)
    logger.info("Total pieces: %d", torrent.total_pieces)

    pm = PieceManager(torrent)

    with open(output_path, "wb") as f:
        for piece_index in range(pm.num_pieces):
            piece_data = pm.download_piece(peer, piece_index)
            f.write(piece_data)

            percent = (piece_index + 1) / pm.num_pieces * 100
            logger.info(
                "[%d/%d] %.2f%%",
                piece_index + 1,
                pm.num_pieces,
                percent,
            )

    logger.info("Download complete: %s", output_path)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    )

    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} <torrent-file> [output-file]")
        sys.exit(1)

    torrent_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) >= 3 else "test_output.bin"

    download(torrent_file, output_file)
