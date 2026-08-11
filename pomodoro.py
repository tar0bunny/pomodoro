import sys
from pathlib import Path

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QFont
from PyQt6.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel, QFrame,
    QVBoxLayout, QHBoxLayout,
)

ASSETS = Path(__file__).parent / "assets"

# brand colors
NAVY = "#1B2447"
TWILIGHT = "#3D4A7A"
LAVENDER = "#E8E6F0"
BLOSSOM = "#E5B8CF"
BLOSSOM_HOVER = "#eec6dc"
WHITE = "#FFFFFF"
WHITE_HOVER = "#f4f2f8"

# timing
FOCUS_SECONDS = 1500  # 25 mins
BREAK_SECONDS = 300  # 5 mins
INTERVAL = 1000

# layout
UI_MARGIN = 36
SPACING = 18
CARD_MARGIN_LEFT = 24
CARD_MARGIN_TOP = 20
CARD_MARGIN_RIGHT = 24
CARD_MARGIN_BOTTOM = 20
CARD_SPACING = 4
BUTTON_ROW_SPACING = 12

# window
WINDOW_TITLE = "tar0bunny Pomodoro"
WINDOW_WIDTH = 480
WINDOW_HEIGHT = 560
APP_STYLE = "Fusion"

# fonts
FONT_FAMILY = "Century Gothic"
FONT_FAMILY_FALLBACK = "Segoe UI"
FONT_FAMILY_SANS = "sans-serif"
SESSION_FONT_SIZE = 15
TIME_FONT_SIZE = 48
TAGLINE_FONT_SIZE = 11
BUTTON_FONT_SIZE = 14

# bunny image
BUNNY_FILENAME = "bunny.png"
BUNNY_SCALE_WIDTH = 180

# button style
BUTTON_HEIGHT = 42
BUTTON_BORDER_WIDTH = 2
BUTTON_BORDER_RADIUS = 21
BUTTON_PADDING_HORIZONTAL = 20
BUTTON_FONT_WEIGHT = 600
BUTTON_PRESSED_PADDING_TOP = 2

# card style
CARD_BORDER_WIDTH = 2
CARD_BORDER_RADIUS = 24

# text
SESSION_LABEL_FOCUS_TEXT = "Focus Time"
SESSION_LABEL_BREAK_TEXT = "Break Time"
TAGLINE_TEXT = "Stay curious."
MODE_BUTTON_TO_BREAK_TEXT = "Switch to Break"
MODE_BUTTON_TO_FOCUS_TEXT = "Switch to Focus"
START_BUTTON_START_TEXT = "Start"
START_BUTTON_PAUSE_TEXT = "Pause"
RESET_BUTTON_TEXT = "Reset"

# modes
MODE_FOCUS = "focus"
MODE_BREAK = "break"

# time formatting
TIME_FORMAT = "{:02d}:{:02d}"
SECONDS_PER_MINUTE = 60


class Button(QPushButton):
    def __init__(self, text, primary=True, parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(BUTTON_HEIGHT)
        bg, bg_hover = (BLOSSOM, BLOSSOM_HOVER) if primary else (WHITE, WHITE_HOVER)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg};
                color: {NAVY};
                border: {BUTTON_BORDER_WIDTH}px solid {NAVY};
                border-radius: {BUTTON_BORDER_RADIUS}px;
                padding: 0 {BUTTON_PADDING_HORIZONTAL}px;
                font-family: '{FONT_FAMILY}', '{FONT_FAMILY_FALLBACK}', {FONT_FAMILY_SANS};
                font-weight: {BUTTON_FONT_WEIGHT};
                font-size: {BUTTON_FONT_SIZE}px;
            }}
            QPushButton:hover {{ background-color: {bg_hover}; }}
            QPushButton:pressed {{ padding-top: {BUTTON_PRESSED_PADDING_TOP}px; }}
        """)


class PomodoroWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(WINDOW_TITLE)
        self.setFixedSize(WINDOW_WIDTH, WINDOW_HEIGHT)

        self.setStyleSheet(f"background-color: {LAVENDER};")

        self.mode = MODE_FOCUS
        self.seconds_left = FOCUS_SECONDS
        self.running = False

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.setInterval(INTERVAL)

        self.build_ui()

    def build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(UI_MARGIN, UI_MARGIN, UI_MARGIN, UI_MARGIN)
        outer.setSpacing(SPACING)
        outer.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self.session_label = QLabel(SESSION_LABEL_FOCUS_TEXT)
        self.session_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        session_font = QFont(FONT_FAMILY, SESSION_FONT_SIZE, QFont.Weight.Bold)
        self.session_label.setFont(session_font)
        self.session_label.setStyleSheet(f"color: {TWILIGHT};")
        outer.addWidget(self.session_label)

        self.bunny_label = QLabel()
        bunny_path = ASSETS / BUNNY_FILENAME
        if bunny_path.exists():
            pix = QPixmap(str(bunny_path)).scaledToWidth(
                BUNNY_SCALE_WIDTH, Qt.TransformationMode.SmoothTransformation
            )
            self.bunny_label.setPixmap(pix)
        self.bunny_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer.addWidget(self.bunny_label)

        # clock card
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {WHITE};
                border: {CARD_BORDER_WIDTH}px solid {NAVY};
                border-radius: {CARD_BORDER_RADIUS}px;
            }}
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(
            CARD_MARGIN_LEFT, CARD_MARGIN_TOP, CARD_MARGIN_RIGHT, CARD_MARGIN_BOTTOM
        )
        card_layout.setSpacing(CARD_SPACING)

        self.time_label = QLabel(self.format_time())
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        time_font = QFont(FONT_FAMILY, TIME_FONT_SIZE, QFont.Weight.Bold)
        self.time_label.setFont(time_font)
        self.time_label.setStyleSheet(f"color: {NAVY}; border: none;")
        card_layout.addWidget(self.time_label)

        tagline = QLabel(TAGLINE_TEXT)
        tagline.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tagline.setFont(QFont(FONT_FAMILY, TAGLINE_FONT_SIZE, italic=True))
        tagline.setStyleSheet(f"color: {TWILIGHT}; border: none;")
        card_layout.addWidget(tagline)

        outer.addWidget(card)

        # buttons
        row1 = QHBoxLayout()
        row1.setSpacing(BUTTON_ROW_SPACING)
        self.start_button = Button(START_BUTTON_START_TEXT, primary=True)
        self.reset_button = Button(RESET_BUTTON_TEXT, primary=False)
        self.start_button.clicked.connect(self.toggle_running)
        self.reset_button.clicked.connect(self.reset)
        row1.addWidget(self.start_button)
        row1.addWidget(self.reset_button)
        outer.addLayout(row1)

        self.mode_button = Button(MODE_BUTTON_TO_BREAK_TEXT, primary=False)
        self.mode_button.clicked.connect(self.switch_mode)
        outer.addWidget(self.mode_button)

    # timer control
    def toggle_running(self):
        self.running = not self.running
        if self.running:
            self.timer.start()
            self.start_button.setText(START_BUTTON_PAUSE_TEXT)
        else:
            self.timer.stop()
            self.start_button.setText(START_BUTTON_START_TEXT)

    def tick(self):
        if self.seconds_left > 0:
            self.seconds_left -= 1
            self._refresh()
        else:
            self._session_complete()

    def session_complete(self):
        self.timer.stop()
        self.running = False
        self.start_button.setText(START_BUTTON_START_TEXT)
        self.mode = MODE_BREAK if self.mode == MODE_FOCUS else MODE_FOCUS
        self.seconds_left = BREAK_SECONDS if self.mode == MODE_BREAK else FOCUS_SECONDS
        self.refresh()
        self.toggle_running()

    def reset(self):
        self.timer.stop()
        self.running = False
        self.start_button.setText(START_BUTTON_START_TEXT)
        self.mode = MODE_FOCUS
        self.seconds_left = FOCUS_SECONDS
        self.refresh()

    def switch_mode(self):
        self.timer.stop()
        self.running = False
        self.start_button.setText(START_BUTTON_START_TEXT)
        self.mode = MODE_BREAK if self.mode == MODE_FOCUS else MODE_FOCUS
        self.seconds_left = BREAK_SECONDS if self.mode == MODE_BREAK else FOCUS_SECONDS
        self.refresh()

    # display
    def format_time(self):
        minutes, seconds = divmod(self.seconds_left, SECONDS_PER_MINUTE)
        return TIME_FORMAT.format(minutes, seconds)

    def refresh(self):
        self.time_label.setText(self.format_time())
        if self.mode == MODE_FOCUS:
            self.session_label.setText(SESSION_LABEL_FOCUS_TEXT)
            self.mode_button.setText(MODE_BUTTON_TO_BREAK_TEXT)
        else:
            self.session_label.setText(SESSION_LABEL_BREAK_TEXT)
            self.mode_button.setText(MODE_BUTTON_TO_FOCUS_TEXT)


def main():
    app = QApplication(sys.argv)
    app.setStyle(APP_STYLE)
    win = PomodoroWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()