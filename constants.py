"""
Protocol constants for the BitTorrent client.

Single source of truth for every magic number, byte sequence, and message ID
used across the codebase. Values match the BitTorrent protocol specification.
"""

# ---------------------------------------------------------------------------
# Protocol handshake
# ---------------------------------------------------------------------------

PROTOCOL_STRING = b"BitTorrent protocol"
PROTOCOL_STRING_LENGTH = len(PROTOCOL_STRING)  # 19
RESERVED_BYTES = b"\x00" * 8
HANDSHAKE_LENGTH = 68  # 1 + 19 + 8 + 20 + 20

# ---------------------------------------------------------------------------
# Peer message IDs  (BEP 3)
# ---------------------------------------------------------------------------

MSG_CHOKE = 0
MSG_UNCHOKE = 1
MSG_INTERESTED = 2
MSG_NOT_INTERESTED = 3
MSG_HAVE = 4
MSG_BITFIELD = 5
MSG_REQUEST = 6
MSG_PIECE = 7
MSG_CANCEL = 8

# ---------------------------------------------------------------------------
# Data transfer
# ---------------------------------------------------------------------------

BLOCK_SIZE = 16384  # 16 KiB — standard BitTorrent block size
REQUEST_PAYLOAD_LENGTH = 13  # 4 (index) + 4 (begin) + 4 (length) + 1 (id)
PIECE_MSG_INDEX_SIZE = 4  # bytes for piece index in a piece message
PIECE_MSG_OFFSET_SIZE = 4  # bytes for block offset in a piece message
PIECE_MSG_HEADER_SIZE = PIECE_MSG_INDEX_SIZE + PIECE_MSG_OFFSET_SIZE  # 8

# ---------------------------------------------------------------------------
# Hashing
# ---------------------------------------------------------------------------

SHA1_HASH_SIZE = 20  # bytes per SHA-1 digest

# ---------------------------------------------------------------------------
# Networking defaults
# ---------------------------------------------------------------------------

CONNECT_TIMEOUT = 10  # seconds — TCP connect timeout for peers
TRACKER_TIMEOUT = 10  # seconds — HTTP timeout for tracker requests
DEFAULT_PORT = 6881  # listening port announced to the tracker
