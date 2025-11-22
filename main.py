# additional main requirements
#    - PyQt5 == 5.15.11

import sys
import random
from datetime import datetime, timedelta
from pyqtgraph.Qt.QtWidgets import QApplication, QMainWindow
from pqgext import TimeDistWidget



def random_datetime(start: datetime, end: datetime) -> datetime:
    """
    Returns a random datetime between start (inclusive) and end (exclusive).
    """
    delta = end - start
    random_seconds = random.randint(0, int(delta.total_seconds()) - 1)
    return start + timedelta(seconds=random_seconds)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = QMainWindow()
    win.setWindowTitle("My Plot")
    win.resize(1000, 700)

    plot = TimeDistWidget()
    dts = [random_datetime(datetime(year=2025, month=3, day=4), datetime(year=2025, month=8, day=15)) for _ in range(1000)]
    plot.setData(dts)

    win.setCentralWidget(plot)

    win.show()
    sys.exit(app.exec())