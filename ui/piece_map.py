"""
ui/piece_map.py

Visual piece-progress map.

Each piece is represented as a small coloured square:

  ● Gray  (#21262d) — pending / not started
  ● Blue  (#3b82f6) — currently downloading
  ● Teal  (#2ea043) — downloaded and SHA-1 verified
  ● Red   (#f85149) — SHA-1 verification failed

Squares automatically reflow when the widget is resized.
"""

import math

from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QFrame, QSizePolicy
from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QPainter, QColor, QPen


# Piece state → fill colour
_STATE_COLOURS = {
    "pending":     QColor("#21262d"),
    "downloading": QColor("#3b82f6"),
    "verified":    QColor("#2ea043"),
    "failed":      QColor("#f85149"),
}

_SQUARE_SIZE   = 10   # px per square (inner area)
_SQUARE_GAP    = 2    # px gap between squares


class _PieceCanvas(QWidget):
    """Bare widget that paints the piece grid."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._states: list[str] = []   # one entry per piece
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumHeight(60)

    def set_num_pieces(self, n: int):
        self._states = ["pending"] * n
        self._recalc_height()
        self.update()

    def set_piece_state(self, index: int, state: str):
        if 0 <= index < len(self._states):
            self._states[index] = state
            self.update()

    def reset(self):
        self._states = []
        self.update()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _cols(self) -> int:
        step = _SQUARE_SIZE + _SQUARE_GAP
        return max(1, (self.width() + _SQUARE_GAP) // step)

    def _recalc_height(self):
        if not self._states:
            self.setMinimumHeight(60)
            return
        cols  = self._cols()
        rows  = math.ceil(len(self._states) / cols)
        step  = _SQUARE_SIZE + _SQUARE_GAP
        self.setMinimumHeight(rows * step + _SQUARE_GAP + 4)

    def resizeEvent(self, event):
        self._recalc_height()
        super().resizeEvent(event)

    def paintEvent(self, event):
        if not self._states:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, False)

        step  = _SQUARE_SIZE + _SQUARE_GAP
        cols  = self._cols()

        for i, state in enumerate(self._states):
            row = i // cols
            col = i % cols
            x   = col * step + _SQUARE_GAP
            y   = row * step + _SQUARE_GAP

            colour = _STATE_COLOURS.get(state, _STATE_COLOURS["pending"])
            painter.fillRect(x, y, _SQUARE_SIZE, _SQUARE_SIZE, colour)

        painter.end()


class PieceMapWidget(QFrame):
    """Card that wraps the piece canvas with a title label."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        self._title = QLabel("PIECE MAP")
        self._title.setObjectName("section_title")
        layout.addWidget(self._title)

        self._canvas = _PieceCanvas()
        layout.addWidget(self._canvas)

        self._legend = QLabel(
            "<span style='color:#21262d'>■</span> Pending &nbsp;"
            "<span style='color:#3b82f6'>■</span> Downloading &nbsp;"
            "<span style='color:#2ea043'>■</span> Verified &nbsp;"
            "<span style='color:#f85149'>■</span> Failed"
        )
        self._legend.setStyleSheet("color: #8b949e; font-size: 11px;")
        self._legend.setTextFormat(Qt.RichText)
        layout.addWidget(self._legend)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def initialize(self, num_pieces: int):
        """Set up the grid for *num_pieces* pieces (all pending)."""
        self._title.setText(f"PIECE MAP  ({num_pieces} pieces)")
        self._canvas.set_num_pieces(num_pieces)

    def update_piece(self, index: int, state: str):
        """Update a single piece square to *state*."""
        self._canvas.set_piece_state(index, state)

    def reset(self):
        """Clear the piece map."""
        self._title.setText("PIECE MAP")
        self._canvas.reset()
