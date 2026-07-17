"""
ui/progress_panel.py

Download progress panel.

Contains:
  • A large progress bar (0–100 %)
  • A row of stat tiles: Downloaded, Remaining, Speed, ETA
  • A statistics card row: Connected Peers, Downloaded Pieces,
    Verified Pieces, Current Piece, Active Connections
"""

from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QWidget,
)
from PySide6.QtCore import Qt


def _fmt_bytes(n: float) -> str:
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} PiB"


def _fmt_speed(bps: float) -> str:
    return _fmt_bytes(bps) + "/s"


def _fmt_eta(seconds: float) -> str:
    if seconds <= 0:
        return "—"
    seconds = int(seconds)
    h, rem  = divmod(seconds, 3600)
    m, s    = divmod(rem, 60)
    if h:
        return f"{h}h {m:02d}m {s:02d}s"
    if m:
        return f"{m}m {s:02d}s"
    return f"{s}s"


# ---------------------------------------------------------------------------
# Small helper: a single stat "tile" (label on top, value below)
# ---------------------------------------------------------------------------

class _StatTile(QWidget):
    def __init__(self, label: str, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(1)

        self._lbl = QLabel(label)
        self._lbl.setObjectName("stat_label")
        self._lbl.setAlignment(Qt.AlignHCenter)
        layout.addWidget(self._lbl)

        self._val = QLabel("—")
        self._val.setObjectName("stat_value")
        self._val.setAlignment(Qt.AlignHCenter)
        layout.addWidget(self._val)

    def set_value(self, text: str):
        self._val.setText(text)


# ---------------------------------------------------------------------------
# Small helper: a counter "card" for the statistics row
# ---------------------------------------------------------------------------

class _CounterCard(QFrame):
    def __init__(self, label: str, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(2)

        self._num = QLabel("0")
        self._num.setObjectName("stat_value")
        self._num.setAlignment(Qt.AlignHCenter)
        self._num.setStyleSheet("font-size: 22px; font-weight: 700; color: #3b82f6;")
        layout.addWidget(self._num)

        self._lbl = QLabel(label)
        self._lbl.setObjectName("stat_label")
        self._lbl.setAlignment(Qt.AlignHCenter)
        layout.addWidget(self._lbl)

    def set_value(self, n: int | str):
        self._num.setText(str(n))


# ---------------------------------------------------------------------------
# Main panel
# ---------------------------------------------------------------------------

class ProgressPanel(QFrame):
    """Card-styled panel holding the progress bar, speed stats, and counters."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 12)
        layout.setSpacing(10)

        # -- Title row ---------------------------------------------------
        title_row = QHBoxLayout()
        title = QLabel("DOWNLOAD PROGRESS")
        title.setObjectName("section_title")
        title_row.addWidget(title)
        title_row.addStretch()
        self._pct_label = QLabel("0%")
        self._pct_label.setStyleSheet("color: #3b82f6; font-size: 13px; font-weight: 700;")
        title_row.addWidget(self._pct_label)
        layout.addLayout(title_row)

        # -- Progress bar ------------------------------------------------
        self._bar = QProgressBar()
        self._bar.setRange(0, 1000)   # use 0–1000 for sub-percent precision
        self._bar.setValue(0)
        self._bar.setFixedHeight(14)
        self._bar.setTextVisible(False)
        layout.addWidget(self._bar)

        # -- Stat tiles --------------------------------------------------
        stats_row = QHBoxLayout()
        stats_row.setSpacing(24)
        self._tiles: dict[str, _StatTile] = {}
        for key, label in [
            ("downloaded", "Downloaded"),
            ("remaining",  "Remaining"),
            ("speed",      "Speed"),
            ("upload",     "Upload"),
            ("eta",        "ETA"),
        ]:
            tile = _StatTile(label)
            self._tiles[key] = tile
            stats_row.addWidget(tile)
            stats_row.addStretch() if key != "eta" else None
        layout.addLayout(stats_row)

        # -- Counter cards -----------------------------------------------
        counters_row = QHBoxLayout()
        counters_row.setSpacing(8)
        self._counters: dict[str, _CounterCard] = {}
        for key, label in [
            ("peers",       "Connected Peers"),
            ("dl_pieces",   "Downloaded Pieces"),
            ("ok_pieces",   "Verified Pieces"),
            ("cur_piece",   "Current Piece"),
            ("connections", "Active Connections"),
        ]:
            card = _CounterCard(label)
            self._counters[key] = card
            counters_row.addWidget(card)
        layout.addLayout(counters_row)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def update_progress(
        self,
        downloaded: int,
        total: int,
        speed_bps: float,
        eta_seconds: float,
        current_piece: int,
        verified_pieces: int,
        dl_pieces: int,
    ):
        """Refresh the entire progress section."""
        if total > 0:
            frac = downloaded / total
            self._bar.setValue(int(frac * 1000))
            self._pct_label.setText(f"{frac * 100:.1f}%")
        else:
            self._bar.setValue(0)
            self._pct_label.setText("0%")

        remaining = max(0, total - downloaded)
        self._tiles["downloaded"].set_value(_fmt_bytes(downloaded))
        self._tiles["remaining"].set_value(_fmt_bytes(remaining))
        self._tiles["speed"].set_value(_fmt_speed(speed_bps))
        self._tiles["upload"].set_value("—")       # placeholder
        self._tiles["eta"].set_value(_fmt_eta(eta_seconds))

        self._counters["cur_piece"].set_value(current_piece)
        self._counters["dl_pieces"].set_value(dl_pieces)
        self._counters["ok_pieces"].set_value(verified_pieces)

    def set_peers(self, n: int):
        self._counters["peers"].set_value(n)
        self._counters["connections"].set_value(n)

    def reset(self):
        self._bar.setValue(0)
        self._pct_label.setText("0%")
        for tile in self._tiles.values():
            tile.set_value("—")
        for counter in self._counters.values():
            counter.set_value(0)
