"""
Peer connection and BitTorrent wire protocol.

Handles TCP socket management, the protocol handshake, and sending /
receiving peer messages.
"""

import logging
import socket
import struct

from constants import (
    CONNECT_TIMEOUT,
    HANDSHAKE_LENGTH,
    MSG_INTERESTED,
    MSG_REQUEST,
    PROTOCOL_STRING,
    REQUEST_PAYLOAD_LENGTH,
    RESERVED_BYTES,
)
from exceptions import HandshakeError

logger = logging.getLogger(__name__)


class Peer:
    """A single BitTorrent peer connected over TCP."""

    def __init__(self, ip, port, peer_id=None):
        self.ip = ip.decode()
        self.port = port
        self.peer_id = peer_id
        self.sock = None

    # ------------------------------------------------------------------
    # Connection management
    # ------------------------------------------------------------------

    def connect(self):
        """Open a TCP connection to this peer."""
        family = socket.AF_INET6 if ":" in self.ip else socket.AF_INET
        self.sock = socket.socket(family, socket.SOCK_STREAM)
        self.sock.settimeout(CONNECT_TIMEOUT)
        self.sock.connect((self.ip, self.port))

    # ------------------------------------------------------------------
    # Handshake
    # ------------------------------------------------------------------

    @staticmethod
    def _build_handshake(info_hash, peer_id):
        """Construct the 68-byte handshake message."""
        return (
            bytes([len(PROTOCOL_STRING)])
            + PROTOCOL_STRING
            + RESERVED_BYTES
            + info_hash
            + peer_id
        )

    @staticmethod
    def _validate_handshake(response, info_hash):
        """Verify the peer's handshake response.

        Checks length, protocol string, and info hash — raises
        :class:`HandshakeError` on any mismatch.
        """
        if len(response) < HANDSHAKE_LENGTH:
            raise HandshakeError(
                f"Short handshake: expected {HANDSHAKE_LENGTH} bytes, got {len(response)}"
            )
        if response[1:20] != PROTOCOL_STRING:
            raise HandshakeError("Peer returned an invalid protocol string")
        if response[28:48] != info_hash:
            raise HandshakeError("Peer info hash does not match ours")

    def handshake(self, info_hash, peer_id):
        """Connect to the peer and perform the BitTorrent handshake."""
        self.connect()

        message = self._build_handshake(info_hash, peer_id)
        logger.debug("Sending handshake (%d bytes) to %s", len(message), self)
        self.sock.sendall(message)

        response = self.sock.recv(HANDSHAKE_LENGTH)
        self._validate_handshake(response, info_hash)
        logger.debug("Handshake successful with %s", self)

    # ------------------------------------------------------------------
    # Sending messages
    # ------------------------------------------------------------------

    def send_interested(self):
        """Send an INTERESTED message to the peer."""
        message = struct.pack(">IB", 1, MSG_INTERESTED)
        self.sock.sendall(message)

    def request_piece(self, piece_index, begin, length):
        """Send a REQUEST message for a single block.

        Parameters correspond to the three fields of the REQUEST payload:
        piece index, byte offset within the piece, and block length.
        """
        message = (
            struct.pack(">I", REQUEST_PAYLOAD_LENGTH)
            + struct.pack(">B", MSG_REQUEST)
            + struct.pack(">I", piece_index)
            + struct.pack(">I", begin)
            + struct.pack(">I", length)
        )
        self.sock.sendall(message)

    # ------------------------------------------------------------------
    # Receiving messages
    # ------------------------------------------------------------------

    def recv_exact(self, num_bytes):
        """Read exactly *num_bytes* from the socket, looping until complete."""
        data = b""
        while len(data) < num_bytes:
            chunk = self.sock.recv(num_bytes - len(data))
            if not chunk:
                raise ConnectionError("Connection closed while reading data")
            data += chunk
        return data

    def recv_message(self):
        """Read one length-prefixed peer message.

        Returns a ``(message_id, payload)`` tuple.  Keep-alive messages
        (length == 0) return ``("keepalive", None)``.
        """
        length_bytes = self.recv_exact(4)
        length = int.from_bytes(length_bytes, byteorder="big")

        if length == 0:
            return ("keepalive", None)

        message_id = self.sock.recv(1)[0]
        payload = self.recv_exact(length - 1)
        return message_id, payload

    # ------------------------------------------------------------------
    # Display
    # ------------------------------------------------------------------

    def __repr__(self):
        return f"Peer({self.ip}:{self.port})"