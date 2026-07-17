"""
ui/main_window.py

Main application window.

Wires together:
  • AppToolBar          (top)
  • TorrentInfoPanel    (left column, top)
  • ProgressPanel       (left column, middle)
  • PieceMapWidget      (left column, bottom)
  • PeerTableWidget     (right column, top)
  • ActivityLog         (right column, bottom)

The DownloadWorker runs in a QThread.  All backend work happens there;
the main window only reacts to signals.
"""

import os
import sys

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QFileDialog, QMessageBox, QStatusBar, QLabel,
)
from PySide6.QtCore import Qt, QThread

# Ensure the project root is on sys.path (needed when launched from a subdirectory)
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from torrent import Torrent                         # noqa: E402

from ui.toolbar       import AppToolBar             # noqa: E402
from ui.torrent_panel import TorrentInfoPanel       # noqa: E402
from ui.progress_panel import ProgressPanel         # noqa: E402
from ui.piece_map     import PieceMapWidget         # noqa: E402
from ui.peer_table    import PeerTableWidget        # noqa: E402
from ui.activity_log  import ActivityLog            # noqa: E402
from backend.download_worker import DownloadWorker  # noqa: E402


class MainWindow(QMainWindow):
    """Top-level application window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("PeerLink — BitTorrent Client")
        self.setMinimumSize(1100, 720)
        self.resize(1280, 820)

        # Internal state
        self._torrent_path: str | None = None
        self._output_path:  str | None = None
        self._worker:       DownloadWorker | None = None
        self._torrent:      Torrent | None = None
        self._dl_pieces   = 0
        self._ok_pieces   = 0

        self._build_ui()
        self._connect_toolbar()

    # ==================================================================
    # UI construction
    # ==================================================================

    def _build_ui(self):
        # ── Toolbar ────────────────────────────────────────────────────
        self._toolbar = AppToolBar(self)
        self.addToolBar(Qt.TopToolBarArea, self._toolbar)

        # ── Central widget ─────────────────────────────────────────────
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(10, 10, 10, 10)
        root_layout.setSpacing(8)

        # ── Horizontal splitter: left | right ─────────────────────────
        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)
        root_layout.addWidget(splitter)

        # LEFT column
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)

        self._torrent_panel  = TorrentInfoPanel()
        self._progress_panel = ProgressPanel()
        self._piece_map      = PieceMapWidget()

        left_layout.addWidget(self._torrent_panel)
        left_layout.addWidget(self._progress_panel)
        left_layout.addWidget(self._piece_map)
        left_layout.addStretch()
        splitter.addWidget(left_widget)

        # RIGHT column
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)

        self._peer_table   = PeerTableWidget()
        self._activity_log = ActivityLog()

        right_layout.addWidget(self._peer_table, stretch=1)
        right_layout.addWidget(self._activity_log, stretch=2)
        splitter.addWidget(right_widget)

        splitter.setStretchFactor(0, 5)
        splitter.setStretchFactor(1, 4)

        # ── Status bar ─────────────────────────────────────────────────
        sb = QStatusBar()
        self.setStatusBar(sb)
        self._status_label = QLabel("Ready — open a .torrent file to begin")
        sb.addWidget(self._status_label)

    # ==================================================================
    # Toolbar signal wiring
    # ==================================================================

    def _connect_toolbar(self):
        tb = self._toolbar
        tb.open_torrent_requested.connect(self._on_open_torrent)
        tb.start_requested.connect(self._on_start)
        tb.pause_requested.connect(self._on_pause)
        tb.resume_requested.connect(self._on_resume)
        tb.stop_requested.connect(self._on_stop)

    # ==================================================================
    # Toolbar handlers
    # ==================================================================

    def _on_open_torrent(self, path: str):
        """Parse the torrent file and populate the info panel."""
        try:
            self._torrent      = Torrent(path)
            self._torrent_path = path
        except Exception as exc:                    # pylint: disable=broad-except
            QMessageBox.critical(self, "Parse Error", str(exc))
            return

        self._output_path = self._ask_save_path()
        if not self._output_path:
            return   # user cancelled

        # Reset UI
        self._torrent_panel.populate(self._torrent)
        self._progress_panel.reset()
        self._piece_map.initialize(self._torrent.total_pieces)
        self._peer_table.clear_peers()
        self._activity_log.clear_log()

        self._dl_pieces = 0
        self._ok_pieces = 0

        name = self._torrent.name
        if isinstance(name, bytes):
            name = name.decode(errors="replace")
        self._activity_log.append(f"Opened: {name}", "info")
        self._activity_log.append(
            f"Saving to: {self._output_path}", "info"
        )

        self._toolbar.set_state("ready")
        self._torrent_panel.set_status("Ready")
        self._set_status("Torrent loaded — click Start to download")

    def _ask_save_path(self) -> str | None:
        """Open a Save dialog and return the chosen path, or None."""
        name = self._torrent.name
        if isinstance(name, bytes):
            name = name.decode(errors="replace")
        default = os.path.join(os.path.expanduser("~"), "Downloads", name)

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Download As",
            default,
            "All Files (*)",
        )
        return path or None

    def _on_start(self):
        if not self._torrent_path or not self._output_path:
            return

        self._worker = DownloadWorker(self._torrent_path, self._output_path)

        # Wire worker signals → UI slots
        self._worker.log_message.connect(self._on_log)
        self._worker.piece_done.connect(self._on_piece_done)
        self._worker.progress_update.connect(self._on_progress)
        self._worker.peer_connected.connect(self._on_peer_connected)
        self._worker.download_complete.connect(self._on_complete)
        self._worker.error_occurred.connect(self._on_error)

        self._worker.start()

        self._toolbar.set_state("downloading")
        self._torrent_panel.set_status("Downloading…")
        self._set_status("Downloading…")
        self._activity_log.append("Download started.", "info")

    def _on_pause(self):
        if self._worker:
            self._worker.pause()
        self._toolbar.set_state("paused")
        self._torrent_panel.set_status("Paused")
        self._set_status("Paused — click Resume to continue")
        self._activity_log.append("Download paused (will pause between pieces).", "warning")

    def _on_resume(self):
        if self._worker:
            self._worker.resume()
        self._toolbar.set_state("downloading")
        self._torrent_panel.set_status("Downloading…")
        self._set_status("Resumed…")
        self._activity_log.append("Download resumed.", "info")

    def _on_stop(self):
        if self._worker:
            self._worker.stop()
            self._worker.wait(3000)
            self._worker = None
        self._toolbar.set_state("ready")
        self._torrent_panel.set_status("Stopped")
        self._set_status("Stopped — click Start to restart")
        self._activity_log.append("Download stopped by user.", "warning")

    # ==================================================================
    # Worker signal handlers  (called on the UI thread via Qt signals)
    # ==================================================================

    def _on_log(self, message: str, level: str):
        self._activity_log.append(message, level)

    def _on_piece_done(self, index: int, state: str):
        self._piece_map.update_piece(index, state)

        if state == "downloading":
            self._dl_pieces += 1
        elif state == "verified":
            self._ok_pieces += 1
        elif state == "failed":
            pass  # already handled by error signal

        # Mirror piece counter in progress panel (without full update)
        if self._torrent:
            self._progress_panel.update_progress(
                downloaded=self._ok_pieces * self._torrent.piece_length,
                total=self._torrent.length,
                speed_bps=0.0,
                eta_seconds=0.0,
                current_piece=index,
                verified_pieces=self._ok_pieces,
                dl_pieces=self._dl_pieces,
            )

    def _on_progress(
        self,
        downloaded: int,
        total: int,
        elapsed: int,
        speed_bps: float,
        eta: float,
    ):
        self._progress_panel.update_progress(
            downloaded=downloaded,
            total=total,
            speed_bps=speed_bps,
            eta_seconds=eta,
            current_piece=self._dl_pieces,
            verified_pieces=self._ok_pieces,
            dl_pieces=self._dl_pieces,
        )

    def _on_peer_connected(self, ip: str, port: int, peer_id_hex: str):
        self._peer_table.add_peer(
            ip=ip,
            port=port,
            client=f"…{peer_id_hex[:8]}",
            status="Downloading",
        )
        self._progress_panel.set_peers(1)

    def _on_complete(self):
        self._toolbar.set_state("complete")
        self._torrent_panel.set_status("Complete ✓")
        self._set_status("Download complete!")
        self._activity_log.append("All pieces verified and written to disk.", "success")
        # Mark every connected peer as done
        for key in list(self._peer_table._peer_rows.keys()):
            try:
                ip, port_str = key.rsplit(":", 1)
                self._peer_table.update_peer(
                    ip=ip, port=int(port_str), status="Done", dl_speed="0 B/s"
                )
            except (ValueError, KeyError):
                pass

    def _on_error(self, message: str):
        self._toolbar.set_state("error")
        self._torrent_panel.set_status("Error")
        self._set_status(f"Error: {message}")
        self._activity_log.append(f"Fatal: {message}", "error")
        QMessageBox.critical(self, "Download Error", message)

    # ==================================================================
    # Helpers
    # ==================================================================

    def _set_status(self, text: str):
        self._status_label.setText(text)

    def closeEvent(self, event):
        """Stop worker cleanly on window close."""
        if self._worker and self._worker.isRunning():
            self._worker.stop()
            self._worker.wait(3000)
        event.accept()
