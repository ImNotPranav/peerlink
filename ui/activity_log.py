"""
ui/activity_log.py

Scrollable activity log panel.

Appends colour-coded log lines (info / success / warning / error).
Newest messages appear at the bottom and the view auto-scrolls.
"""

from PySide6.QtWidgets import QFrame, QVBoxLayout, QPlainTextEdit, QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import QTextCharFormat, QColor, QTextCursor


# Colour map for each log level
_LEVEL_COLOURS = {
    "info":    "#8b949e",
    "success": "#2ea043",
    "warning": "#e3b341",
    "error":   "#f85149",
}

_LEVEL_PREFIX = {
    "info":    "ℹ",
    "success": "✓",
    "warning": "⚠",
    "error":   "✗",
}


class ActivityLog(QFrame):
    """Card-styled panel showing timestamped, colour-coded log messages."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        title = QLabel("ACTIVITY LOG")
        title.setObjectName("section_title")
        layout.addWidget(title)

        self._log = QPlainTextEdit()
        self._log.setReadOnly(True)
        self._log.setMinimumHeight(140)
        self._log.setPlaceholderText("Events will appear here…")
        layout.addWidget(self._log)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def append(self, message: str, level: str = "info"):
        """Append a styled log line.

        Parameters
        ----------
        message:
            The human-readable log text.
        level:
            One of ``'info'``, ``'success'``, ``'warning'``, ``'error'``.
        """
        import datetime
        colour = _LEVEL_COLOURS.get(level, _LEVEL_COLOURS["info"])
        prefix = _LEVEL_PREFIX.get(level, "ℹ")
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")

        fmt = QTextCharFormat()
        fmt.setForeground(QColor(colour))

        cursor = self._log.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(f"[{timestamp}]  {prefix}  {message}\n", fmt)

        # Auto-scroll to bottom
        self._log.setTextCursor(cursor)
        self._log.ensureCursorVisible()

    def clear_log(self):
        """Remove all log entries."""
        self._log.clear()
