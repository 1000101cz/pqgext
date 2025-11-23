# additional main requirements
#    - PyQt5 == 5.15.11

import sys
import random
from datetime import datetime, timedelta
from pyqtgraph.Qt.QtWidgets import QApplication, QMainWindow



def random_datetime(start: datetime, end: datetime) -> datetime:
    """
    Returns a random datetime between start (inclusive) and end (exclusive).
    """
    delta = end - start
    random_seconds = random.randint(0, int(delta.total_seconds()) - 1)
    return start + timedelta(seconds=random_seconds)


app = QApplication(sys.argv)

# ------------------------------------------------------------------
# Registry: maps command-line name → function that creates & shows the widget
# ------------------------------------------------------------------
examples = {}


def register(name):
    """Decorator to register an example function"""

    def decorator(func):
        examples[name] = func
        return func

    return decorator

@register("TimeDistWidget")
def show_TimeDistWidget():
    from pqgext import TimeDistWidget
    win = QMainWindow()
    plot = TimeDistWidget()
    dts = [random_datetime(datetime(year=2025, month=3, day=4), datetime(year=2025, month=8, day=15)) for _ in range(1000)]
    plot.setData(dts)
    win.setCentralWidget(plot)
    win.setWindowTitle("TimeDistWidget")

    win.resize(1100, 800)
    win.show()
    return win


@register("PiePlotWidget")
def show_PiePlotWidget():
    from pqgext import PiePlotWidget
    win = QMainWindow()
    plot = PiePlotWidget()
    vls = [random.randint(5, 100) for _ in range(6)]
    plot.setData(values=vls)
    plot.add_legend()
    win.setCentralWidget(plot)

    win.resize(1200, 700)
    win.show()
    return win


# ------------------------------------------------------------------
# Launcher
# ------------------------------------------------------------------
def print_usage():
    print("Available examples:")
    for name in sorted(examples):
        print(f"  python main.py {name}")
    print("\n  python main.py list   → show this help")
    print("  python main.py all    → run ComboBox selector (dev mode)")


def launch_dev_selector():
    """Fallback interactive selector – perfect while developing"""
    from pyqtgraph.Qt.QtWidgets import QComboBox, QVBoxLayout, QWidget, QLabel

    class Selector(QWidget):
        def __init__(self):
            super().__init__()
            layout = QVBoxLayout(self)
            layout.addWidget(QLabel("Select widget to test:"))
            combo = QComboBox()
            combo.addItems(sorted(examples.keys()))
            layout.addWidget(combo)

            combo.currentTextChanged.connect(self.run_selected)
            self.setWindowTitle("pyqtgraph widget selector")
            self.resize(400, 100)

        def run_selected(self, name):
            if name:
                examples[name]()
                self.close()

    Selector().show()


def main():
    if len(sys.argv) < 2 or sys.argv[1] in {"-h", "--help", "list"}:
        print_usage()
        return

    if sys.argv[1] == "all":
        launch_dev_selector()
        app.exec_()
        return

    name = sys.argv[1]
    if name not in examples:
        print(f"Unknown widget: {name}")
        print_usage()
        return

    # Run the selected example function
    win = examples[name]()
    if win:
        win.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()