import random
import pyqtgraph as pg
import numpy as np
from pyqtgraph.Qt.QtCore import *
from pyqtgraph.Qt.QtGui import *
from typing import List, Optional


class PiePlotWidget(pg.PlotWidget):
    sliceClicked = pyqtSignal(int, float)   # index, value
    sliceEntered = pyqtSignal(int, float)   # index, value  (hover in)
    sliceExited  = pyqtSignal(int)          # index         (hover out)

    def __init__(self, parent=None, background=None, donut_ratio: float = 0.0, start_angle: float = 270, label_pen=QPen(Qt.white), **kwargs):
        super().__init__(parent=parent, background=background, **kwargs)
        self.donut_ratio = donut_ratio
        self.start_angle = start_angle
        self.label_pen = label_pen

        self.hideAxis('left')
        self.hideAxis('bottom')
        self.setAspectLocked(True)

        self.getViewBox().setMouseEnabled(x=False, y=False)
        self.getViewBox().wheelEvent = lambda ev: None

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
            start_angle=self.start_angle,
            label_pen=self.label_pen,
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
    sliceClicked = pyqtSignal(int, float)
    sliceEntered = pyqtSignal(int, float)
    sliceExited  = pyqtSignal(int)

    def __init__(self, values, labels, colors, explode=None,
                 donut_ratio=0.0, start_angle=90, label_pen=QPen(Qt.white)):
        super().__init__()
        self.label_pen = label_pen
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
        self.picture = QPicture()
        p = QPainter(self.picture)
        p.setRenderHint(QPainter.Antialiasing)

        radius = 100
        if self.hovered_index == -1:
            # random so the labels are likely not to be over each other
            label_radiuses = [radius * (random.randint(30, 100)/100.0 if self.donut_ratio == 0 else (1.0 + self.donut_ratio) * 0.5) for _ in range(len(self.values))]
        else:
            label_radiuses = [radius * (0.65 if self.donut_ratio == 0 else (1.0 + self.donut_ratio) * 0.5) for _ in range(len(self.values))]
        inner_radius = radius * self.donut_ratio
        center = QPointF(0, 0)
        current_angle = self.start_angle

        slices = []

        for i, value in enumerate(self.values):
            angle_span = 360.0 * value / self.total

            explode_offset = self.explode[i] * 12
            if i == self.hovered_index:
                explode_offset += 8

            mid_angle_rad = np.deg2rad(current_angle + angle_span / 2)
            offset = QPointF(
                explode_offset * np.cos(mid_angle_rad),
                -explode_offset * np.sin(mid_angle_rad)
            )

            slices.append({
                'offset': offset,
                'start_angle': current_angle,
                'span': angle_span,
                'color': self.colors[i],
                'hovered': i == self.hovered_index,
                'show_label': (self.hovered_index == -1) or (i == self.hovered_index),
                'label': self.labels[i],
                'mid_angle': current_angle + angle_span / 2,
            })

            current_angle += angle_span

        for s in slices:
            path = QPainterPath()
            path.moveTo(center + s['offset'])
            path.arcTo(QRectF(-radius, -radius, radius * 2, radius * 2).translated(s['offset']),
                       s['start_angle'], s['span'])
            if self.donut_ratio > 0:
                path.arcTo(
                    QRectF(-inner_radius, -inner_radius, inner_radius * 2, inner_radius * 2).translated(s['offset']),
                    s['start_angle'] + s['span'], -s['span'])
            else:
                path.lineTo(center + s['offset'])
            path.closeSubpath()

            p.setBrush(s['color'])
            p.setPen(pg.mkPen('white', width=2.5 if s['hovered'] else 2))
            p.drawPath(path)

        p.setFont(QFont("Arial", 11, QFont.Bold))

        for i, s in enumerate(slices):
            if not s['show_label']:
                continue
            if s['span'] <= 8 and self.hovered_index != slices.index(s):
                continue

            angle_rad = np.deg2rad(s['mid_angle'])
            label_pos = center + s['offset'] + QPointF(
                label_radiuses[i] * np.cos(angle_rad),
                -label_radiuses[i] * np.sin(angle_rad)
            )

            p.save()
            p.translate(label_pos.x(), label_pos.y())
            p.scale(1, -1)
            p.setPen(self.label_pen)
            p.drawText(QRectF(-1000, -1000, 2000, 2000), Qt.AlignCenter, s['label'])
            p.restore()

        p.end()

    def paint(self, p, *args):
        p.drawPicture(0, 0, self.picture)

    def boundingRect(self):
        return QRectF(-130, -130, 260, 260)

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