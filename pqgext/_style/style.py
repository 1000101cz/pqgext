import pyqtgraph as pg
from pyqtgraph.Qt.QtGui import QColor

from .._settings import pqgext_settings as pes


class PQGExtStyle:
    @staticmethod
    def generate_palette(length: int, alpha: int = 255):
        return [pg.intColor(i, length, alpha=alpha) for i in range(length)]

    @property
    def palette(self):
        if pes.palette is None:
            def_palette = self.generate_palette(10)
            return def_palette
        else:
            return pes.palette

    @property
    def primary_color(self) -> QColor:
        if pes.primary_color is None:
            def_prim_col = QColor(50, 120, 220)
            return def_prim_col
        else:
            return pes.primary_color

    @property
    def secondary_color(self) -> QColor:
        if pes.secondary_color is None:
            def_sec_col = QColor(220, 120, 50)
            return def_sec_col
        return pes.secondary_color

