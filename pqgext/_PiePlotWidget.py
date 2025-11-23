import numpy as np
from typing import Tuple, Iterable, Optional
import pyqtgraph as pg
from pyqtgraph.Qt.QtCore import pyqtSignal, QRectF, Qt
from pyqtgraph.Qt.QtGui import QFont, QPainterPath, QColor
from pyqtgraph.Qt.QtWidgets import QGraphicsPathItem, QWidget, QVBoxLayout, QGraphicsEllipseItem

from ._style import style


class PiePlotWidget(pg.PlotWidget):
    sliceClicked = pyqtSignal(int, str, float)  # index, label, value
    sliceHovered = pyqtSignal(int, str, float)

    def __init__(self, parent=None, background=None, **kwargs):
        super().__init__(parent=parent, background=background, **kwargs)

        # Appearance settings
        self.setAspectLocked(True)
        self.hideAxis('left')
        self.hideAxis('bottom')
        self.hideButtons()
        self.setContentsMargins(0, 0, 0, 0)

        self.getViewBox().setMouseEnabled(x=False, y=False)
        self.getViewBox().wheelEvent = lambda ev: None

        # Pie data & visual settings
        self._values = []
        self._labels = []
        self._colors = []
        self._explode = []  # explode distance per slice (0 = none)
        self._text_color = 'black'
        self._radius = 200
        self._start_angle = 270  # 12 o'clock start

        self._slice_items = []
        self._text_items = []

    def setData(self, values: Iterable[int | float],
                labels: Optional[Iterable[str]] = None,
                colors: Optional[Iterable[QColor]] = None,
                explode: Optional[Iterable[float]] = None):
        """
        Set or update the pie chart data.

        Parameters
        ----------
        values : Iterable[int | float]
            Slice values (will be normalized to percentages)
        labels : list[str], optional
            Slice labels. If None, uses "Slice 0", "Slice 1", ...
        colors : list[str or QColor], optional
            Custom colors. If None, uses pyqtgraph default color cycle.
        explode : list[float], optional
            Explode offset (0–1) for each slice.
        """
        assert isinstance(values, Iterable), f"values must be iterable, not {type(values)}"
        self._values = list(values)
        N = len(values)
        self._labels = labels or [f"Slice {i}" for i in range(N)]
        self._colors = colors or [style.palette[i%(len(style.palette))] for i in range(N)]
        self._explode = explode or [0.0] * N

        self._redraw()

    def setRadius(self, radius: float):
        self._radius = radius
        self._redraw()

    def setStartAngle(self, degrees: float):
        self._start_angle = degrees % 360
        self._redraw()

    def setTextColor(self, color):
        self._text_color = color
        self._redraw()

    def clear(self):
        self._values = []
        self._redraw()

    @staticmethod
    def _get_anchor(angle: float) -> Tuple[float, float]:
        angle = angle % 360
        if 22.5 <= angle < 157.5:
            a = 0
        elif (angle >= 337.5) or (angle < 22.5) or (157.5 <= angle < 202.5):
            a = 0.5
        elif 202.5 <= angle < 337.5:
            a = 1
        else:
            raise ValueError

        if angle >= 292.5 or angle < 67.5:
            b = 0
        elif (67.5 <= angle < 112.5) or (247.5 <= angle < 292.5):
            b = 0.5
        elif 112.5 <= angle < 247.5:
            b = 1
        else:
            raise ValueError

        return a, b

    def _redraw(self):
        vb = self.getViewBox()
        vb.clear()  # remove old items
        self._slice_items.clear()
        self._text_items.clear()

        if not self._values:
            vb.autoRange()
            return

        total = sum(self._values)
        cum = 0

        for i, (val, label, color, expl) in enumerate(zip(self._values, self._labels, self._colors, self._explode)):

            span = 360.0 * val / total

            if val == total:
                mid_rad = np.deg2rad(self._start_angle)
                explode_offset = self._radius * expl
                center_x = explode_offset * np.cos(mid_rad)
                center_y = explode_offset * np.sin(mid_rad)

                # Draw a simple filled circle → no seam!
                ellipse = QGraphicsEllipseItem(center_x - self._radius, center_y - self._radius, self._radius * 2, self._radius * 2)
                ellipse.setBrush(pg.mkBrush(color))
                ellipse.setPen(pg.mkPen(None))  # no border
                ellipse.setZValue(10 - i)
                vb.addItem(ellipse)
                self._slice_items.append(ellipse)

                # Hover/click (we have to set the methods on the item itself)
                ellipse.setAcceptHoverEvents(True)
                ellipse.mousePressEvent = lambda ev, idx=i: self._on_slice_clicked(ev, idx)
                ellipse.hoverEnterEvent = lambda ev, idx=i: self._on_slice_hover(ev, idx, enter=True)
                ellipse.hoverLeaveEvent = lambda ev, idx=i: self._on_slice_hover(ev, idx, enter=False)

                # Label (placed at the configured start angle, looks natural)
                label_angle_deg = self._start_angle % 360
                label_angle = np.deg2rad(label_angle_deg)
                label_radius = self._radius * 1.25 * (1 + expl * 0.5)
                txt_x = center_x + label_radius * np.cos(label_angle)
                txt_y = center_y - label_radius * np.sin(label_angle)

                percent = val / total * 100
                txt = pg.TextItem(f"{label}\n100%", color=self._text_color, anchor=(0.5, 0.5))
                txt.setFont(QFont("Arial", 10, weight=QFont.Bold))
                txt.setPos(txt_x, txt_y)
                txt.setZValue(100)
                vb.addItem(txt)
                self._text_items.append(txt)

                cum += span
                continue

            if span == 0:
                continue

            # Explode: move slice outward
            mid_angle = self._start_angle + cum + span / 2
            mid_rad = np.deg2rad(mid_angle)
            explode_offset = self._radius * expl
            center_x = explode_offset * np.cos(mid_rad)
            center_y = explode_offset * np.sin(mid_rad)

            # Create perfect arc using QPainterPath.arcTo()
            path = QPainterPath()
            path.moveTo(center_x, center_y)
            rect = QRectF(center_x - self._radius, center_y - self._radius, self._radius * 2, self._radius * 2)
            path.arcTo(rect, self._start_angle + cum, span)
            path.closeSubpath()

            # Graphics item
            item = QGraphicsPathItem(path)
            item.setBrush(pg.mkBrush(color))
            item.setZValue(10 - i)
            vb.addItem(item)
            self._slice_items.append(item)

            # Hover & click handling
            item.setAcceptHoverEvents(True)
            item.mousePressEvent = lambda ev, idx=i: self._on_slice_clicked(ev, idx)
            item.hoverEnterEvent = lambda ev, idx=i: self._on_slice_hover(ev, idx, enter=True)
            item.hoverLeaveEvent = lambda ev, idx=i: self._on_slice_hover(ev, idx, enter=False)

            # Label
            label_angle_deg = (self._start_angle + cum + span / 2) % 360
            label_angle = np.deg2rad(label_angle_deg)
            label_radius = self._radius * 1.25 * (1 + expl * 0.5)
            txt_x = center_x + label_radius * np.cos(label_angle)
            txt_y = center_y - label_radius * np.sin(label_angle)

            # print(f"Anchor for {label} - {anchor}     [{txt_x}, {txt_y}]")

            percent = val / total * 100
            txt = pg.TextItem(f"{label}\n{percent:.1f}%", color=self._text_color, anchor=(0.5, 0.5))
            txt.setFont(QFont("Arial", 10, weight=QFont.Bold))
            txt.setPos(txt_x, txt_y)
            txt.setZValue(100)

            vb.addItem(txt)
            self._text_items.append(txt)

            cum += span

        # Auto fit view with small padding
        vb.autoRange(padding=0.15)

    def add_legend(self):
        """
        Add a legend to the pie chart.
        """
        # Remove old legend if exists
        if hasattr(self, "_legend"):
            self._legend.close()
            self.removeItem(self._legend)

        # Create legend (size, offset)
        self._legend = pg.LegendItem(offset=(0, 0))
        self._legend.setParentItem(self.getViewBox())

        # Add one entry per slice
        for i, (label, color) in enumerate(zip(self._labels, self._colors)):
            # Create a dummy plot item just for the color swatch
            dummy = pg.ScatterPlotItem(x=[0], y=[0], pen=None, brush=pg.mkBrush(color), size=12, symbol='s')
            self._legend.addItem(dummy, label)

    def _on_slice_clicked(self, event, index):
        if event.button() == Qt.LeftButton:
            self.sliceClicked.emit(index, self._labels[index], self._values[index])

    def _on_slice_hover(self, event, index, enter=True):
        item = self._slice_items[index]
        if enter:
            item.setPen(pg.mkPen('k', width=4))
            self.sliceHovered.emit(index, self._labels[index], self._values[index])
        else:
            item.setPen(pg.mkPen('k', width=0))


def place_PiePlotWidget(placeholder: QWidget, parent=None, background=None) -> PiePlotWidget:
    for child in placeholder.findChildren(QWidget):
        child.deleteLater()

    pie = PiePlotWidget(parent=parent, background=background)

    layout = QVBoxLayout(placeholder)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.addWidget(pie)

    return pie
