"""
Piece downloading, assembly, and verification.

Orchestrates block-level requests for each piece, reassembles them,
and verifies the SHA-1 hash before marking the piece as complete.
"""

import hashlib
import logging

from constants import BLOCK_SIZE, MSG_PIECE, PIECE_MSG_HEADER_SIZE
from exceptions import PieceError

logger = logging.getLogger(__name__)


class PieceManager:
    """Tracks piece state and drives the block-by-block download loop."""

    def __init__(self, torrent):
        self.torrent = torrent
        self.piece_length = torrent.piece_length
        self.num_pieces = torrent.total_pieces
        self.completed = set()

    # ------------------------------------------------------------------
    # Piece geometry
    # ------------------------------------------------------------------

    def piece_size(self, piece_index):
        """Actual byte size of *piece_index* (the last piece may be shorter)."""
        remaining_bytes = self.torrent.length - (piece_index * self.piece_length)
        return min(remaining_bytes, self.piece_length)

    # ------------------------------------------------------------------
    # Hash verification
    # ------------------------------------------------------------------

    def expected_hash(self, piece_index):
        """Return the 20-byte expected SHA-1 hash for *piece_index*."""
        return self.torrent.piece_hash(piece_index)

    def verify_piece(self, piece_index, piece_data):
        """Return True if *piece_data* matches the expected hash."""
        actual = hashlib.sha1(piece_data).digest()
        return actual == self.expected_hash(piece_index)

    # ------------------------------------------------------------------
    # Completion tracking
    # ------------------------------------------------------------------

    def mark_complete(self, piece_index):
        """Record that *piece_index* has been downloaded and verified."""
        self.completed.add(piece_index)

    def next_piece(self):
        """Return the index of the next incomplete piece, or None if all done."""
        for i in range(self.num_pieces):
            if i not in self.completed:
                return i
        return None

    # ------------------------------------------------------------------
    # Block-level message parsing
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_piece_message(payload):
        """Extract (piece_index, begin, block) from a PIECE message payload.

        The first 4 bytes are the piece index, the next 4 are the byte
        offset, and the remainder is the block data.
        """
        piece_index = int.from_bytes(payload[:PIECE_MSG_HEADER_SIZE // 2], "big")
        begin = int.from_bytes(
            payload[PIECE_MSG_HEADER_SIZE // 2:PIECE_MSG_HEADER_SIZE], "big"
        )
        block = payload[PIECE_MSG_HEADER_SIZE:]
        return piece_index, begin, block

    # ------------------------------------------------------------------
    # Download
    # ------------------------------------------------------------------

    def download_piece(self, peer, piece_index):
        """Download all blocks for *piece_index*, verify, and return the data.

        Blocks are requested sequentially.  Non-PIECE messages received
        while waiting for a block are silently skipped (e.g. keep-alives,
        HAVEs).

        Raises :class:`PieceError` on hash mismatch or unexpected
        index / offset.
        """
        blocks = []
        total_size = self.piece_size(piece_index)

        for begin in range(0, total_size, BLOCK_SIZE):
            request_length = min(BLOCK_SIZE, total_size - begin)
            peer.request_piece(piece_index, begin, request_length)

            while True:
                msg_id, payload = peer.recv_message()
                if msg_id != MSG_PIECE:
                    continue

                recv_index, recv_begin, block = self._parse_piece_message(payload)

                if recv_index != piece_index:
                    raise PieceError(
                        f"Expected piece {piece_index}, got {recv_index}"
                    )
                if recv_begin != begin:
                    raise PieceError(
                        f"Expected block offset {begin}, got {recv_begin}"
                    )

                blocks.append(block)
                break

        piece_data = b"".join(blocks)

        if not self.verify_piece(piece_index, piece_data):
            raise PieceError(f"SHA-1 verification failed for piece {piece_index}")

        self.mark_complete(piece_index)
        logger.debug("Piece %d verified and complete", piece_index)
        return piece_data
