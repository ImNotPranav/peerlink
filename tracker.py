"""
HTTP tracker communication.

Announces to the tracker and parses the compact or dictionary-mode peer list
returned in the response.
"""

import logging
import random
import string

import requests

from parser import bdecode
from peer import Peer
from constants import DEFAULT_PORT, TRACKER_TIMEOUT
from exceptions import TrackerError

logger = logging.getLogger(__name__)


class Tracker:
    """Manages communication with a single HTTP tracker."""

    def __init__(self, torrent):
        self.torrent = torrent
        self.peer_id = self._generate_peer_id().encode("ascii")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _generate_peer_id():
        """Build an Azureus-style peer ID: -PT0001- followed by 12 random alphanumeric chars."""
        suffix = "".join(
            random.choice(string.digits + string.ascii_letters)
            for _ in range(12)
        )
        return f"-PT0001-{suffix}"

    @property
    def params(self):
        """Query parameters for the tracker announce request."""
        return {
            "info_hash": self.torrent.info_hash,
            "peer_id": self.peer_id,
            "port": DEFAULT_PORT,
            "uploaded": 0,
            "downloaded": 0,
            "left": self.torrent.length,
            "compact": 1,
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_peers(self):
        """Announce to the tracker and return a list of :class:`Peer` objects."""
        response = requests.get(
            self.torrent.announce,
            params=self.params,
            timeout=TRACKER_TIMEOUT,
        )
        if not response.ok:
            logger.warning("Tracker returned HTTP %d: %s", response.status_code, response.text)
            raise TrackerError(
                f"Tracker request failed with status {response.status_code}"
            )

        decoded = bdecode(response.content)[0]
        peers = [
            Peer(entry[b"ip"], entry[b"port"], entry[b"peer id"])
            for entry in decoded[b"peers"]
        ]
        logger.info("Tracker returned %d peers", len(peers))
        return peers
