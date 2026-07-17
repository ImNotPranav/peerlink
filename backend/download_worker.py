"""
backend/download_worker.py

QThread-based worker that drives the full BitTorrent download pipeline.

Architecture
------------
* Runs entirely in a background thread — never touches Qt widgets.
* Communicates with the UI exclusively via Qt signals.
* The backend classes (Torrent, Tracker, PieceManager, Peer) are used
  exactly as they are; nothing in them is modified.

Signals emitted
---------------
log_message(str, str)
    A human-readable log line and its severity level
    ('info', 'success', 'warning', 'error').

piece_done(int, str)
    Piece index and its new state: 'downloading', 'verified', 'failed'.

progress_update(int, int, int, float, float)
    (downloaded_bytes, total_bytes, elapsed_seconds, speed_bps, eta_seconds)

peer_connected(str, int, str)
    (ip, port, peer_id_hex) — emitted when a peer handshake completes.

download_complete()
    Emitted once every piece is verified and written to disk.

error_occurred(str)
    Emitted on a fatal error; carries the error message string.
"""

import sys
import time
import os

from PySide6.QtCore import QThread, Signal

# ---------------------------------------------------------------------------
# Add the project root to sys.path so the existing backend modules resolve
# regardless of the working directory.
# ---------------------------------------------------------------------------
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from torrent import Torrent           # noqa: E402
from tracker import Tracker           # noqa: E402
from piecemanager import PieceManager # noqa: E402


class DownloadWorker(QThread):
    """Background thread that orchestrates a single-torrent download."""

    # ------------------------------------------------------------------
    # Signals
    # ------------------------------------------------------------------
    log_message      = Signal(str, str)          # (message, level)
    piece_done       = Signal(int, str)          # (piece_index, state)
    progress_update  = Signal(int, int, int, float, float)  # see module doc
    peer_connected   = Signal(str, int, str)     # (ip, port, peer_id_hex)
    download_complete = Signal()
    error_occurred   = Signal(str)

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def __init__(self, torrent_path: str, output_path: str, parent=None):
        super().__init__(parent)
        self.torrent_path = torrent_path
        self.output_path  = output_path

        self._pause_requested = False
        self._stop_requested  = False

    # ------------------------------------------------------------------
    # Control
    # ------------------------------------------------------------------

    def pause(self):
        """Request a pause between pieces (takes effect at next piece boundary)."""
        self._pause_requested = True

    def resume(self):
        """Clear the pause flag and wake the worker."""
        self._pause_requested = False

    def stop(self):
        """Request a clean stop."""
        self._stop_requested = True
        self._pause_requested = False   # unblock any waiting spin

    # ------------------------------------------------------------------
    # Main thread body
    # ------------------------------------------------------------------

    def run(self):
        """Full download pipeline — mirrors the original main.download() logic."""
        try:
            self._run_pipeline()
        except Exception as exc:                        # pylint: disable=broad-except
            self.error_occurred.emit(str(exc))

    def _run_pipeline(self):
        # ---- 1. Parse torrent ----------------------------------------
        self.log_message.emit("Parsing torrent file…", "info")
        torrent = Torrent(self.torrent_path)
        name = torrent.name.decode() if isinstance(torrent.name, bytes) else torrent.name
        self.log_message.emit(f"Torrent: {name}  ({torrent.total_pieces} pieces)", "info")

        if self._stop_requested:
            return

        # ---- 2. Contact tracker --------------------------------------
        self.log_message.emit(f"Contacting tracker: {torrent.announce.decode()}", "info")
        tracker = Tracker(torrent)
        peers = tracker.get_peers()
        self.log_message.emit(f"Tracker returned {len(peers)} peer(s)", "success")

        if self._stop_requested or not peers:
            if not peers:
                self.error_occurred.emit("Tracker returned no peers.")
            return

        # ---- 3. Handshake with first peer ----------------------------
        peer = peers[0]
        self.log_message.emit(f"Connecting to peer {peer.ip}:{peer.port}…", "info")
        peer.handshake(torrent.info_hash, tracker.peer_id)

        peer_id_hex = (
            peer.peer_id.hex() if isinstance(peer.peer_id, bytes) else str(peer.peer_id)
        )
        self.peer_connected.emit(peer.ip, peer.port, peer_id_hex)
        self.log_message.emit(
            f"Handshake successful with {peer.ip}:{peer.port}", "success"
        )

        if self._stop_requested:
            return

        # ---- 4. Bitfield + Unchoke -----------------------------------
        msg_id, _ = peer.recv_message()        # bitfield
        self.log_message.emit(f"Received message id={msg_id} (bitfield)", "info")

        peer.send_interested()
        self.log_message.emit("Sent INTERESTED", "info")

        msg_id, _ = peer.recv_message()        # unchoke
        self.log_message.emit(f"Received message id={msg_id} (unchoke) — ready", "success")

        if self._stop_requested:
            return

        # ---- 5. Download loop ----------------------------------------
        pm = PieceManager(torrent)
        total_bytes     = torrent.length
        downloaded      = 0
        start_time      = time.monotonic()
        last_speed_time = start_time
        last_speed_bytes = 0
        speed_bps       = 0.0

        with open(self.output_path, "wb") as f:
            for piece_index in range(pm.num_pieces):

                # Pause checkpoint (spins between pieces)
                while self._pause_requested and not self._stop_requested:
                    self.msleep(200)

                if self._stop_requested:
                    self.log_message.emit("Download stopped by user.", "warning")
                    return

                # Signal UI that this piece is being fetched
                self.piece_done.emit(piece_index, "downloading")

                try:
                    piece_data = pm.download_piece(peer, piece_index)
                except Exception as exc:               # pylint: disable=broad-except
                    self.log_message.emit(
                        f"Piece {piece_index} failed: {exc}", "error"
                    )
                    self.piece_done.emit(piece_index, "failed")
                    self.error_occurred.emit(str(exc))
                    return

                f.write(piece_data)
                downloaded += len(piece_data)

                # Verified
                self.piece_done.emit(piece_index, "verified")
                self.log_message.emit(
                    f"Piece {piece_index + 1}/{pm.num_pieces} verified ✓", "success"
                )

                # Speed calculation (rolling window)
                now = time.monotonic()
                elapsed_window = now - last_speed_time
                if elapsed_window >= 0.5:
                    bytes_in_window = downloaded - last_speed_bytes
                    speed_bps       = bytes_in_window / elapsed_window
                    last_speed_time  = now
                    last_speed_bytes = downloaded

                elapsed_total = now - start_time
                eta = (
                    (total_bytes - downloaded) / speed_bps
                    if speed_bps > 0
                    else 0.0
                )
                self.progress_update.emit(
                    downloaded, total_bytes, int(elapsed_total), speed_bps, eta
                )

        # ---- 6. Done -------------------------------------------------
        self.log_message.emit(
            f"Download complete → {self.output_path}", "success"
        )
        self.download_complete.emit()
