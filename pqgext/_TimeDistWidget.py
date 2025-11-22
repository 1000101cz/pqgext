import pyqtgraph as pg
from pyqtgraph.Qt.QtWidgets import QWidget, QVBoxLayout
import numpy as np
from datetime import datetime, timedelta


class DateAxisItem(pg.AxisItem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setStyle(tickLength=8)

    def tickValues(self, minVal, maxVal, size):
        """
        Only "nice" timestamp ticks (multiples of 15 min, 1h, 1 day, etc.)
        """
        min_dt = datetime.fromtimestamp(minVal)
        max_dt = datetime.fromtimestamp(maxVal)

        length_seconds = maxVal - minVal

        if length_seconds > 3600 * 24 * 60:  # > 2 months
            step = timedelta(days=30)
        elif length_seconds > 3600 * 24 * 30:  # > 1 month
            step = timedelta(days=7)
        elif length_seconds > 3600 * 24 * 15:  # > 15 days
            step = timedelta(days=2)
        elif length_seconds > 3600 * 24 * 6:  # > 6 days
            step = timedelta(days=1)
        elif length_seconds > 3600 * 24:  # > 1 day
            step = timedelta(hours=12)
        elif length_seconds > 3600 * 12:  # > 12 hours
            step = timedelta(hours=2)
        elif length_seconds > 3600 * 6:  # > 6 hours
            step = timedelta(hours=1)
        elif length_seconds > 3600:  # > 1 hour
            step = timedelta(minutes=15)
        elif length_seconds > 600:  # > 10 min
            step = timedelta(minutes=5)
        else:
            step = timedelta(minutes=1)

        step_seconds = step.total_seconds()

        start_dt = min_dt - (min_dt - datetime(1970, 1, 1)) % step
        if (min_dt - start_dt) % step != timedelta(0):
            start_dt += step

        ticks = []
        current = start_dt
        while current <= max_dt:
            ticks.append(current.timestamp())
            current += step

        return [(step_seconds, ticks)]

    def tickStrings(self, values, scale, spacing):
        strings = []
        for v in values:
            try:
                dt = datetime.fromtimestamp(v)
                if spacing >= 3600*24*30:
                    s = dt.strftime("%b %Y")
                elif spacing >= 3600*24:
                    s = dt.strftime("%d.%m.%Y")
                elif spacing >= 3600:
                    s = dt.strftime("%d.%m %H:%M")
                else:
                    s = dt.strftime("%H:%M")
                strings.append(s)
            except ValueError:
                strings.append("")
        return strings


class TimeDistWidget(pg.PlotWidget):

    def __init__(self, parent=None, background=None, fixed_height=55, **kwargs):
        super().__init__(parent=parent, background=background, axisItems={'bottom': DateAxisItem(orientation='bottom')}, **kwargs)

        self.hideAxis('left')
        self.hideAxis('right')
        self.hideAxis('top')
        self.showAxis('bottom', show=True)

        self.setBackground(background)

        self.setYRange(-1.0, 1.0, padding=0)
        self.setLimits(yMin=-1.2, yMax=1.2, minYRange=0.001, maxYRange=2.4)
        self.setMouseEnabled(y=False)
        self.plotItem.vb.setMouseEnabled(y=False)
        self.plotItem.vb.disableAutoRange(axis=pg.ViewBox.YAxis)

        self.setMouseEnabled(x=True)

        self.scatter = pg.ScatterPlotItem(size=9, pen=None, brush=pg.mkBrush(50, 120, 220, 35))
        self.addItem(self.scatter)

        self.jitter = 0.35

        self.setFixedHeight(fixed_height)
        self.setMinimumHeight(fixed_height)
        self.setMaximumHeight(fixed_height)

        view = self.plotItem.vb
        view.sigRangeChanged.connect(self._on_view_changed)

    def setData(self, datetimes):
        if not datetimes:
            self.scatter.clear()
            return

        self.timestamps = np.array([dt.timestamp() for dt in datetimes], dtype=np.float64)
        self.timestamps.sort()
        if len(self.timestamps) == 1:
            center = self.timestamps[0]
            padding = 86400 * 5
            self._data_xmin = center - padding
            self._data_xmax = center + padding
        else:
            self._data_xmin = self.timestamps.min()
            self._data_xmax = self.timestamps.max()

        data_span = self._data_xmax - self._data_xmin
        tolerance = data_span * 0.05
        limit_min = self._data_xmin - tolerance
        limit_max = self._data_xmax + tolerance

        y = np.random.uniform(-self.jitter, self.jitter, size=len(self.timestamps))
        self.scatter.setData(x=self.timestamps, y=y)

        self.setXRange(self._data_xmin, self._data_xmax, padding=0.02)

        self.setLimits(
            xMin=limit_min,
            xMax=limit_max,
            minXRange=1e-5,
            maxXRange=(self._data_xmax - self._data_xmin) * 1.15
        )

    def _on_view_changed(self):
        """Called automatically on every zoom/pan"""
        if len(self.timestamps) == 0:
            visible = 0
        else:
            xmin, xmax = self.viewRange()[0]
            left_idx = np.searchsorted(self.timestamps, xmin, side='left')
            right_idx = np.searchsorted(self.timestamps, xmax, side='right')
            visible = right_idx - left_idx

        # tune params
        min_alpha = 20  # maximal allowed transparency
        points_count_bound = 1000   # number of points for maximal transparency (== min_alpha)
        exp = 4  # steepness
        # --------------

        if visible <= 1:
            alpha = 255
        elif visible >= points_count_bound:
            alpha = min_alpha
        else:
            alpha = int(((255.0 - min_alpha) / (points_count_bound ** exp)) * ((visible - points_count_bound) ** exp) + min_alpha)

        current_color = self.scatter.opts['brush'].color()
        current_color.setAlpha(alpha)
        new_brush = pg.mkBrush(current_color)
        self.scatter.setBrush(new_brush)
