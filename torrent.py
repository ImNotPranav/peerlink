"""
Torrent metadata.

Parses a .torrent file and exposes the metadata needed by the tracker,
peer connections, and piece manager.
"""

import hashlib

from parser import bdecode, bencode
from constants import SHA1_HASH_SIZE


class Torrent:
    """Immutable view over the contents of a .torrent file."""

    def __init__(self, path):
        with open(path, "rb") as f:
            torrent_data = f.read()
        self.meta = bdecode(torrent_data)[0]
        self._info_hash = None

    # ------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------

    @property
    def info_hash(self):
        """Raw 20-byte SHA-1 hash of the bencoded info dictionary."""
        if self._info_hash is None:
            self._info_hash = hashlib.sha1(bencode(self.meta[b'info'])).digest()
        return self._info_hash

    @property
    def info_hash_hex(self):
        """Hex-encoded info hash (useful for debugging and display)."""
        return self.info_hash.hex()

    # ------------------------------------------------------------------
    # Tracker / download metadata
    # ------------------------------------------------------------------

    @property
    def announce(self):
        """Tracker announce URL as raw bytes."""
        return self.meta[b"announce"]

    @property
    def length(self):
        """Total size of the content in bytes (single-file torrents only)."""
        return self.meta[b"info"][b"length"]

    @property
    def name(self):
        """Suggested filename from the torrent metadata."""
        return self.meta[b"info"][b"name"]

    # ------------------------------------------------------------------
    # Piece information
    # ------------------------------------------------------------------

    @property
    def piece_length(self):
        """Nominal size of each piece in bytes (the last piece may be smaller)."""
        return self.meta[b"info"][b"piece length"]

    @property
    def total_pieces(self):
        """Number of pieces in the torrent."""
        return len(self.meta[b"info"][b"pieces"]) // SHA1_HASH_SIZE

    @property
    def piece_hashes(self):
        """Raw concatenated SHA-1 hashes for all pieces."""
        return self.meta[b"info"][b"pieces"]

    def piece_hash(self, piece_index):
        """Return the expected 20-byte SHA-1 hash for a single piece."""
        start = piece_index * SHA1_HASH_SIZE
        return self.piece_hashes[start:start + SHA1_HASH_SIZE]
