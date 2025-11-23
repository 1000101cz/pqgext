from typing import Optional
from pyqtgraph.Qt.QtGui import QColor


class PQGExtSettings:
    def __init__(self, primary_color: Optional[QColor] = None, secondary_color: Optional[QColor] = None, palette: list[QColor] = None):
        self.primary_color = primary_color
        self.secondary_color = secondary_color
        self.palette = palette