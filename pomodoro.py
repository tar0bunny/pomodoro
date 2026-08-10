import sys
from pathlib import Path

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QFont
from PyQt6.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel, QFrame,
    QVBoxLayout, QHBoxLayout,
)

ASSETS = Path(__file__).parent / "assets"
FOCUS_SECONDS = 1500 # 25 mins
BREAK_SECONDS = 300 # 5 mins

# brand colors
NAVY = "#1B2447"
TWILIGHT = "#3D4A7A"
LAVENDER = "#E8E6F0"
BLOSSOM = "#E5B8CF"
WHITE = "#FFFFFF"

class Button(QPushButton):
    def __init__(self, text, primary=True, parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(42)
        bg, bg_hover = (BLOSSOM, "#eec6dc") if primary else (WHITE, "#f4f2f8")
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg};
                color: {NAVY};
                border: 2px solid {NAVY};
                border-radius: 21px;
                padding: 0 20px;
                font-family: 'Century Gothic', 'Segoe UI', sans-serif;
                font-weight: 600;
                font-size: 14px;
            }}
            QPushButton:hover {{ background-color: {bg_hover}; }}
            QPushButton:pressed {{ padding-top: 2px; }}
        """)

class PomodoroWindow(QWidget):
    def __init__(self):
        super().__init__()
        
        self.mode = "focus"
        self.seconds_left = FOCUS_SECONDS
        self.running = False

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.setInterval(1000)

        self.mode_label = QLabel("Mode: Focus")
        self.time_label = QLabel(self.format_time())

        self.start_button = QPushButton("Start")
        self.pause_button = QPushButton("Pause")
        self.reset_button = QPushButton("Reset")
        self.focus_button = QPushButton("Switch to Focus")
        self.break_button = QPushButton("Switch to Break")

        self.start_button.clicked.connect(self.start)
        self.pause_button.clicked.connect(self.pause)
        self.reset_button.clicked.connect(self.reset)
        self.focus_button.clicked.connect(lambda: self.switch_mode("focus"))
        self.break_button.clicked.connect(lambda: self.switch_mode("break"))

        row1 = QHBoxLayout()
        row1.addWidget(self.start_button)
        row1.addWidget(self.pause_button)
        row1.addWidget(self.reset_button)

        row2 = QHBoxLayout()
        row2.addWidget(self.focus_button)
        row2.addWidget(self.break_button)

        layout = QVBoxLayout()
        layout.addWidget(self.mode_label)
        layout.addWidget(self.time_label)
        layout.addLayout(row1)
        layout.addLayout(row2)
        self.setLayout(layout)

    def start(self):
        self.running = True
        self.timer.start()

    def pause(self):
        self.running = False
        self.timer.stop()

    def reset(self):
        self.running = False
        self.timer.stop()
        self.mode = "focus"
        self.seconds_left = FOCUS_SECONDS
        self.refresh()

    def switch_mode(self, new_mode):
        self.running = False
        self.timer.stop()
        self.mode = new_mode
        self.seconds_left = FOCUS_SECONDS if new_mode == "focus" else BREAK_SECONDS
        self.refresh()

    def tick(self):
        if self.seconds_left > 0:
            self.seconds_left -= 1
            self.refresh()
        else:
            self.timer.stop()
            self.running = False
            self.switch_mode("break" if self.mode == "focus" else "focus")
            self.start()

    def format_time(self):
        m, s = divmod(self.seconds_left, 60)
        return f"{m:02d}:{s:02d}"

    def refresh(self):
        self.mode_label.setText(f"Mode: {'Focus' if self.mode == 'focus' else 'Break'}")
        self.time_label.setText(self.format_time())


def main():
    app = QApplication(sys.argv)
    window = PomodoroWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()