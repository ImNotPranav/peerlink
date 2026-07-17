"""
ui/torrent_panel.py

Torrent information card.

Displays static metadata read from the .torrent file:
  • File Name
  • Total Size
  • Piece Length
  • Number of Pieces
  • Tracker URL
  • Info Hash
  • Status  (dynamic — updated by the main window)
"""

from PySide6.QtWidgets import QFrame, QGridLayout, QLabel, QVBoxLayout
from PySide6.QtCore import Qt


def _fmt_bytes(n: int) -> str:
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if n < 1024:
            return f"{n:.2f} {unit}"
        n /= 1024
    return f"{n:.2f} PiB"


class TorrentInfoPanel(QFrame):
    """Card showing torrent metadata and live status."""

    _FIELD_KEYS = [
        ("Name",         "name"),
        ("Size",         "size"),
        ("Piece Length", "piece_length"),
        ("Pieces",       "pieces"),
        ("Tracker",      "tracker"),
        ("Info Hash",    "info_hash"),
        ("Status",       "status"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 10, 12, 12)
        outer.setSpacing(6)

        title = QLabel("TORRENT INFO")
        title.setObjectName("section_title")
        outer.addWidget(title)

        grid = QGridLayout()
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(5)
        outer.addLayout(grid)

        self._value_labels: dict[str, QLabel] = {}

        for row, (display, key) in enumerate(self._FIELD_KEYS):
            lbl = QLabel(display)
            lbl.setObjectName("field_label")
            lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            grid.addWidget(lbl, row, 0)

            val = QLabel("—")
            val.setObjectName("field_value")
            val.setWordWrap(True)
            val.setTextInteractionFlags(Qt.TextSelectableByMouse)
            grid.addWidget(val, row, 1)

            self._value_labels[key] = val

        grid.setColumnStretch(1, 1)

        # Status label gets a special colour treatment via setObjectName
        self._value_labels["status"].setObjectName("status_idle")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def populate(self, torrent) -> None:
        """Fill in all fields from a :class:`~torrent.Torrent` instance."""
        name = torrent.name
        if isinstance(name, bytes):
            name = name.decode(errors="replace")
        self._value_labels["name"].setText(name)
        self._value_labels["size"].setText(_fmt_bytes(torrent.length))
        self._value_labels["piece_length"].setText(
            _fmt_bytes(torrent.piece_length)
        )
        self._value_labels["pieces"].setText(str(torrent.total_pieces))

        announce = torrent.announce
        if isinstance(announce, bytes):
            announce = announce.decode(errors="replace")
        self._value_labels["tracker"].setText(announce)
        self._value_labels["info_hash"].setText(torrent.info_hash_hex)
        self.set_status("Idle")

    def set_status(self, text: str) -> None:
        """Update the Status row with coloured styling."""
        lbl = self._value_labels["status"]
        lbl.setText(text)

        t = text.lower()
        if "download" in t or "fetch" in t:
            lbl.setObjectName("status_downloading")
        elif "connect" in t or "handshake" in t:
            lbl.setObjectName("status_connecting")
        elif "complete" in t or "verified" in t or "done" in t:
            lbl.setObjectName("status_complete")
        elif "error" in t or "fail" in t:
            lbl.setObjectName("status_error")
        else:
            lbl.setObjectName("status_idle")

        # Force stylesheet re-evaluation
        lbl.style().unpolish(lbl)
        lbl.style().polish(lbl)

    def clear(self) -> None:
        """Reset all fields to placeholder dashes."""
        for lbl in self._value_labels.values():
            lbl.setText("—")
        self._value_labels["status"].setObjectName("status_idle")
