import pyqtgraph as pg
import numpy as np
from PyQt5 import QtGui, QtCore
from typing import List, Optional


class PiePlotWidget(pg.PlotWidget):
    sliceClicked = QtCore.pyqtSignal(int, float)   # index, value
    sliceEntered = QtCore.pyqtSignal(int, float)   # index, value  (hover in)
    sliceExited  = QtCore.pyqtSignal(int)          # index         (hover out)

    def __init__(self, parent=None, donut_ratio: float = 0.0, start_angle: float = 90):
        super().__init__(parent=parent)
        self.donut_ratio = donut_ratio
        self.start_angle = start_angle

        self.hideAxis('left')
        self.hideAxis('bottom')
        self.setAspectLocked(True)

        self.values = []
        self.labels = []
        self.colors = []
        self.explode = []

        self.pie_item = None
        self.legend = None

    def setData(self, values, labels=None, colors=None, explode=None):
        self.values = np.asarray(values, dtype=float)
        self.labels = labels or [f"Slice {i}" for i in range(len(values))]
        self.colors = colors or [pg.intColor(i, len(values), alpha=220) for i in range(len(values))]
        self.explode = explode or [0.0] * len(values)

        self.clear()
        if self.legend:
            self.legend.scene().removeItem(self.legend)

        self._create_pie()

    def _create_pie(self):
        self.pie_item = PieChartItem(
            values=self.values,
            labels=self.labels,
            colors=self.colors,
            explode=self.explode,
            donut_ratio=self.donut_ratio,
            start_angle=self.start_angle
        )
        self.pie_item.sliceClicked.connect(self.sliceClicked)
        self.pie_item.sliceEntered.connect(self.sliceEntered)
        self.pie_item.sliceExited.connect(self.sliceExited)
        self.addItem(self.pie_item)

    def add_legend(self):
        if not self.labels:
            return
        self.legend = pg.LegendItem(offset=(80, 20))
        self.legend.setParentItem(self.getViewBox())
        for i, (label, color) in enumerate(zip(self.labels, self.colors)):
            spot = pg.ScatterPlotItem(size=15, pen=pg.mkPen('w', width=2),
                                      brush=pg.mkBrush(color), symbol='s')
            self.legend.addItem(spot, label)


class PieChartItem(pg.GraphicsObject):
    sliceClicked = QtCore.pyqtSignal(int, float)
    sliceEntered = QtCore.pyqtSignal(int, float)
    sliceExited  = QtCore.pyqtSignal(int)

    def __init__(self, values, labels, colors, explode=None,
                 donut_ratio=0.0, start_angle=90):
        super().__init__()
        self.values = np.asarray(values)
        self.total = self.values.sum()
        self.labels = labels
        self.colors = [pg.mkBrush(c) for c in colors]
        self.explode = np.array(explode or [0.0] * len(values))
        self.donut_ratio = donut_ratio
        self.start_angle = start_angle

        self.hovered_index = -1
        self.generatePicture()

        self.setAcceptHoverEvents(True)

    def generatePicture(self):
        self.picture = QtGui.QPicture()
        p = QtGui.QPainter(self.picture)
        p.setRenderHint(QtGui.QPainter.Antialiasing)

        radius = 100
        inner_radius = radius * self.donut_ratio
        center = QtCore.QPointF(0, 0)
        current_angle = self.start_angle

        for i, value in enumerate(self.values):
            angle_span = 360.0 * value / self.total
            explode_offset = self.explode[i] * 12
            if i == self.hovered_index:
                explode_offset += 8

            mid_angle_rad = np.deg2rad(current_angle + angle_span / 2)
            offset = QtCore.QPointF(
                explode_offset * np.cos(mid_angle_rad),
                explode_offset * -np.sin(mid_angle_rad)
            )

            path = QtGui.QPainterPath()
            path.moveTo(center + offset)
            path.arcTo(QtCore.QRectF(-radius, -radius, radius*2, radius*2).translated(offset),
                       current_angle, angle_span)
            if self.donut_ratio > 0:
                path.arcTo(QtCore.QRectF(-inner_radius, -inner_radius, inner_radius*2, inner_radius*2).translated(offset),
                           current_angle + angle_span, -angle_span)
            else:
                path.lineTo(center + offset)
            path.closeSubpath()

            p.setBrush(self.colors[i])
            p.setPen(pg.mkPen('white', width=2.5 if i == self.hovered_index else 2))
            p.drawPath(path)

            # labels
            label_radius = radius * (0.65 if self.donut_ratio == 0 else (1.0 + self.donut_ratio) * 0.5)
            angle_rad = np.deg2rad(current_angle + angle_span / 2)

            label_pos = center + offset + QtCore.QPointF(
                label_radius * np.cos(angle_rad),
                -label_radius * np.sin(angle_rad)
            )

            p.setPen(QtGui.QPen(QtCore.Qt.white))
            p.setFont(QtGui.QFont("Arial", 11, weight=QtGui.QFont.Bold))

            text = self.labels[i]
            text_rect = p.fontMetrics().boundingRect(text)

            p.save()
            p.translate(label_pos)

            p.scale(1, -1)

            p.drawText(QtCore.QPointF(-text_rect.width() / 2, text_rect.height() / 3), text)
            p.restore()

            current_angle += angle_span

        p.end()

    def paint(self, p, *args):
        p.drawPicture(0, 0, self.picture)

    def boundingRect(self):
        return QtCore.QRectF(-130, -130, 260, 260)

    def hoverEnterEvent(self, ev):
        self._handle_hover(ev.pos(), enter=True)
        ev.accept()

    def hoverMoveEvent(self, ev):
        self._handle_hover(ev.pos(), enter=True)
        ev.accept()

    def hoverLeaveEvent(self, ev):
        if self.hovered_index != -1:
            old = self.hovered_index
            self.hovered_index = -1
            self.generatePicture()
            self.update()
            self.sliceExited.emit(old)
        ev.accept()

    def mousePressEvent(self, ev):
        index = self._get_slice_at_pos(ev.pos())
        if index >= 0:
            self.sliceClicked.emit(index, float(self.values[index]))
            print(f"CLICKED → {self.labels[index]} ({self.values[index]:.1f})")
        ev.accept()

    def _handle_hover(self, pos, enter=True):
        index = self._get_slice_at_pos(pos)
        if index != self.hovered_index:
            old = self.hovered_index
            self.hovered_index = index
            self.generatePicture()
            self.update()

            if index >= 0:
                self.sliceEntered.emit(index, float(self.values[index]))
                print(f"HOVER IN → {self.labels[index]} ({self.values[index]:.1f})")
            elif old >= 0:
                self.sliceExited.emit(old)
                print(f"HOVER OUT → {self.labels[old]}")

    def _get_slice_at_pos(self, pos):
        dx, dy = pos.x(), pos.y()
        dist = np.hypot(dx, dy)
        if dist > 115 or (self.donut_ratio > 0 and dist < self.donut_ratio * 100):
            return -1

        angle = np.degrees(np.arctan2(-dy, dx)) % 360
        angle = (angle - self.start_angle) % 360

        cum = 0
        for i, val in enumerate(self.values):
            span = 360 * val / self.total
            if cum <= angle < cum + span:
                return i
            cum += span
        return -1