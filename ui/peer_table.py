"""
ui/peer_table.py

Peer table panel showing all connected peers and their live statistics.

Columns: IP Address | Port | Client | Status | ↓ Speed | ↑ Speed | Interested | Choked
"""

from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView,
)
from PySide6.QtCore import Qt


_COLUMNS = [
    "IP Address",
    "Port",
    "Client",
    "Status",
    "↓ Speed",
    "↑ Speed",
    "Interested",
    "Choked",
]


def _item(text: str, align=Qt.AlignLeft | Qt.AlignVCenter) -> QTableWidgetItem:
    it = QTableWidgetItem(text)
    it.setTextAlignment(align)
    it.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
    return it


class PeerTableWidget(QFrame):
    """Card-styled table that lists connected peers."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        title = QLabel("CONNECTED PEERS")
        title.setObjectName("section_title")
        layout.addWidget(title)

        self._table = QTableWidget(0, len(_COLUMNS))
        self._table.setHorizontalHeaderLabels(_COLUMNS)
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        self._table.setShowGrid(False)
        self._table.setMinimumHeight(120)

        hdr = self._table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.Stretch)          # IP — stretch
        for col in range(1, len(_COLUMNS)):
            hdr.setSectionResizeMode(col, QHeaderView.ResizeToContents)

        layout.addWidget(self._table)

        # Key: ip:port → row index
        self._peer_rows: dict[str, int] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_peer(
        self,
        ip: str,
        port: int,
        client: str = "Unknown",
        status: str = "Connected",
        dl_speed: str = "—",
        ul_speed: str = "—",
        interested: str = "Yes",
        choked: str = "No",
    ):
        """Add a new peer row; does nothing if the peer already exists."""
        key = f"{ip}:{port}"
        if key in self._peer_rows:
            return

        row = self._table.rowCount()
        self._table.insertRow(row)
        self._peer_rows[key] = row

        center = Qt.AlignHCenter | Qt.AlignVCenter
        self._table.setItem(row, 0, _item(ip))
        self._table.setItem(row, 1, _item(str(port), center))
        self._table.setItem(row, 2, _item(client))
        self._table.setItem(row, 3, _item(status))
        self._table.setItem(row, 4, _item(dl_speed, center))
        self._table.setItem(row, 5, _item(ul_speed, center))
        self._table.setItem(row, 6, _item(interested, center))
        self._table.setItem(row, 7, _item(choked, center))

    def update_peer(
        self,
        ip: str,
        port: int,
        *,
        status: str | None = None,
        dl_speed: str | None = None,
        ul_speed: str | None = None,
    ):
        """Update mutable fields for an existing peer row."""
        key = f"{ip}:{port}"
        row = self._peer_rows.get(key)
        if row is None:
            return
        center = Qt.AlignHCenter | Qt.AlignVCenter
        if status   is not None:
            self._table.setItem(row, 3, _item(status))
        if dl_speed is not None:
            self._table.setItem(row, 4, _item(dl_speed, center))
        if ul_speed is not None:
            self._table.setItem(row, 5, _item(ul_speed, center))

    def clear_peers(self):
        """Remove all rows."""
        self._table.setRowCount(0)
        self._peer_rows.clear()
