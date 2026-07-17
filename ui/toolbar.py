"""
ui/toolbar.py

Application toolbar.

Buttons
-------
Open .torrent   — opens a QFileDialog to pick a .torrent file
Paste Magnet    — placeholder (not yet implemented)
─────────────
Start           — begin download
Pause           — pause between pieces
Resume          — resume after pause
Stop            — abort download
─────────────
About           — simple about dialog

Each button exposes an objectName so the stylesheet can style it
individually (e.g. #btn_start gets green, #btn_stop gets red).

The toolbar does NOT reference backend objects directly; it only
emits signals. The main window listens and decides what to do.
"""

from PySide6.QtWidgets import QToolBar, QFileDialog, QMessageBox
from PySide6.QtGui import QAction, QIcon
from PySide6.QtCore import Qt, Signal, QObject


# ---------------------------------------------------------------------------
# Tiny helper: QAction factory (text only — icons added later if desired)
# ---------------------------------------------------------------------------

def _action(parent: QObject, name: str, text: str, tip: str, obj_name: str = "") -> QAction:
    act = QAction(text, parent)
    act.setToolTip(tip)
    act.setObjectName(obj_name or name)
    return act


class AppToolBar(QToolBar):
    """Main application toolbar."""

    # Signals emitted to the main window
    open_torrent_requested = Signal(str)   # absolute path to .torrent
    magnet_requested       = Signal(str)   # magnet URI (placeholder)
    start_requested        = Signal()
    pause_requested        = Signal()
    resume_requested       = Signal()
    stop_requested         = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMovable(False)
        self.setFloatable(False)
        self.setObjectName("main_toolbar")

        # ── File actions ───────────────────────────────────────────────
        self._act_open = _action(self, "open",   "📂  Open Torrent", "Open a .torrent file")
        self._act_magnet = _action(self, "magnet", "🔗  Paste Magnet", "Paste a magnet link (coming soon)")

        self.addAction(self._act_open)
        self.addAction(self._act_magnet)
        self.addSeparator()

        # ── Download control actions ───────────────────────────────────
        self._act_start  = _action(self, "start",  "▶  Start",  "Start download",  "btn_start")
        self._act_pause  = _action(self, "pause",  "⏸  Pause",  "Pause download")
        self._act_resume = _action(self, "resume", "↺  Resume", "Resume download")
        self._act_stop   = _action(self, "stop",   "■  Stop",   "Stop download",   "btn_stop")

        for act in (self._act_start, self._act_pause, self._act_resume, self._act_stop):
            self.addAction(act)

        self.addSeparator()

        self._act_about = _action(self, "about", "ℹ  About", "About PeerLink")
        self.addAction(self._act_about)

        # ── Wire internal signals ──────────────────────────────────────
        self._act_open.triggered.connect(self._on_open)
        self._act_magnet.triggered.connect(self._on_magnet)
        self._act_start.triggered.connect(self.start_requested)
        self._act_pause.triggered.connect(self.pause_requested)
        self._act_resume.triggered.connect(self.resume_requested)
        self._act_stop.triggered.connect(self.stop_requested)
        self._act_about.triggered.connect(self._on_about)

        # ── Initial button state ───────────────────────────────────────
        self.set_state("idle")

    # ------------------------------------------------------------------
    # State machine helper
    # ------------------------------------------------------------------

    def set_state(self, state: str):
        """Enable / disable buttons according to the download state.

        States: 'idle', 'ready', 'downloading', 'paused', 'complete', 'error'
        """
        self._act_open.setEnabled(True)
        self._act_magnet.setEnabled(True)

        if state == "idle":
            self._act_start.setEnabled(False)
            self._act_pause.setEnabled(False)
            self._act_resume.setEnabled(False)
            self._act_stop.setEnabled(False)

        elif state == "ready":
            self._act_start.setEnabled(True)
            self._act_pause.setEnabled(False)
            self._act_resume.setEnabled(False)
            self._act_stop.setEnabled(False)

        elif state == "downloading":
            self._act_start.setEnabled(False)
            self._act_pause.setEnabled(True)
            self._act_resume.setEnabled(False)
            self._act_stop.setEnabled(True)

        elif state == "paused":
            self._act_start.setEnabled(False)
            self._act_pause.setEnabled(False)
            self._act_resume.setEnabled(True)
            self._act_stop.setEnabled(True)

        elif state in ("complete", "error"):
            self._act_start.setEnabled(False)
            self._act_pause.setEnabled(False)
            self._act_resume.setEnabled(False)
            self._act_stop.setEnabled(False)

    # ------------------------------------------------------------------
    # Handlers
    # ------------------------------------------------------------------

    def _on_open(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Torrent File",
            "",
            "Torrent Files (*.torrent);;All Files (*)",
        )
        if path:
            self.open_torrent_requested.emit(path)

    def _on_magnet(self):
        QMessageBox.information(
            self,
            "Magnet Links",
            "Magnet link support is not yet implemented.\n\n"
            "This feature will be available in a future release.",
        )

    def _on_about(self):
        QMessageBox.about(
            self,
            "About PeerLink",
            "<b>PeerLink</b> — BitTorrent Client<br><br>"
            "A modern PySide6 desktop UI over a hand-written BitTorrent backend.<br><br>"
            "Protocol: <tt>BitTorrent v1 (BEP 3)</tt><br>"
            "UI: <tt>PySide6 / Qt 6</tt>",
        )
