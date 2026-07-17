"""
main.py — PeerLink application entry point.

Launches the PySide6 desktop UI.

Original CLI usage is preserved below as a comment for reference:

    # from torrent import Torrent
    # from tracker import Tracker
    # from piecemanager import PieceManager
    #
    # def download(torrent_path, output_path):
    #     torrent = Torrent(torrent_path)
    #     tracker = Tracker(torrent)
    #     peers   = tracker.get_peers()
    #     peer    = peers[0]
    #     peer.handshake(torrent.info_hash, tracker.peer_id)
    #     _, _ = peer.recv_message()   # bitfield
    #     peer.send_interested()
    #     _, _ = peer.recv_message()   # unchoke
    #     pm = PieceManager(torrent)
    #     with open(output_path, "wb") as f:
    #         for i in range(pm.num_pieces):
    #             f.write(pm.download_piece(peer, i))
    #
    # if __name__ == "__main__":
    #     import sys, logging
    #     logging.basicConfig(level=logging.INFO)
    #     download(sys.argv[1], sys.argv[2] if len(sys.argv) >= 3 else "test_output.bin")
"""

import sys
import os

# ---------------------------------------------------------------------------
# Ensure the project root is always on sys.path regardless of working dir.
# ---------------------------------------------------------------------------
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt

from ui.main_window import MainWindow


def _load_stylesheet(app: QApplication) -> None:
    """Apply the global dark theme QSS file."""
    qss_path = os.path.join(_HERE, "resources", "styles", "dark_theme.qss")
    if os.path.exists(qss_path):
        with open(qss_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())


def main() -> int:
    # High-DPI support (Qt 6 handles this automatically, but be explicit)
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("PeerLink")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("PeerLink")

    # Base font
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    _load_stylesheet(app)

    window = MainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
