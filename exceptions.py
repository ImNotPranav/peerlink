"""
Custom exception hierarchy for the BitTorrent client.

Each exception replaces a generic ValueError with a descriptive type,
making it easier to catch specific failure modes without changing control flow.
"""


class BencodeError(Exception):
    """Raised when bencoded data cannot be decoded or an object cannot be encoded."""


class HandshakeError(Exception):
    """Raised when the peer handshake fails — wrong protocol, short response, or info-hash mismatch."""


class TrackerError(Exception):
    """Raised when the tracker HTTP request fails or returns an unparseable response."""


class PieceError(Exception):
    """Raised when a downloaded piece is corrupt, has a wrong index, or has a wrong offset."""
