"""
tar0bunny - Code & Chill Pomodoro
A cozy PyQt6 pomodoro timer with a centered clock,
built in tar0bunny brand colors (Midnight Navy / Blossom Pink / Soft Lavender).

Run with:
    pip install PyQt6 --break-system-packages
    python pomodoro.py

Folder layout expected:
    pomodoro.py
    assets/background.png
"""

import sys
from pathlib import Path

from PyQt6.QtCore import Qt, QTimer, QRectF, QUrl
from PyQt6.QtGui import QPixmap, QPainter, QFont, QColor, QPainterPath, QFontDatabase
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QGraphicsDropShadowEffect, QMessageBox
from PyQt6.QtMultimedia import QSoundEffect

ASSETS = Path(__file__).parent / "assets"

# brand colors
NAVY = QColor("#1B2447")
TWILIGHT = QColor("#3D4A7A")
AIR_BLUE = QColor("#718CA0")
LAVENDER = QColor("#E8E6F0")
BLOSSOM = QColor("#E5B8CF")
WHITE = QColor("#FFFFFF")

BLOSSOM_HOVER = "#eec6dc"
SECONDARY_BUTTON_BG = "rgba(255,255,255,140)"
SECONDARY_BUTTON_HOVER = "rgba(255,255,255,200)"

SHADOW_COLOR_R = 27
SHADOW_COLOR_G = 36
SHADOW_COLOR_B = 71
SESSION_SHADOW_ALPHA = 230
TIME_SHADOW_ALPHA = 220
PANEL_ALPHA = 90

# timing
FOCUS_MINUTES = 25
BREAK_MINUTES = 5
SECONDS_PER_MINUTE = 60
FOCUS_SECONDS = FOCUS_MINUTES * SECONDS_PER_MINUTE
BREAK_SECONDS = BREAK_MINUTES * SECONDS_PER_MINUTE
TICK_INTERVAL_MS = 1000

# window
WINDOW_TITLE = "tar0bunny \u2728 Code & Chill Pomodoro"
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 580
APP_STYLE = "Fusion"

# fonts
FONT_FAMILY = "Century Gothic"
FONT_FAMILY_SANS = "sans-serif"
LABEL_FONT_FAMILY = "Gabriola"
SESSION_FONT_SIZE = 27
TIME_FONT_SIZE = 56
TAGLINE_FONT_SIZE = 13
BUTTON_FONT_SIZE = 14

# button geometry / style
BUTTON_HEIGHT = 42
BUTTON_BORDER_WIDTH = 2
BUTTON_BORDER_RADIUS = 21
BUTTON_PADDING_HORIZONTAL = 22
BUTTON_FONT_WEIGHT = 600
BUTTON_PRESSED_PADDING_TOP = 2

# asset filenames
BACKGROUND_FILENAME = "background.png"
CHIME_FILENAME = "chime.wav"
CHIME_VOLUME = 0.9

# error / dialog text
ERROR_MESSAGE_HEADER = "tar0bunny Pomodoro couldn't load these image(s):\n  "
ERROR_MESSAGE_FOOTER = (
    "\n\nMake sure the 'assets' folder (with background.png) sits in the "
    "SAME folder as pomodoro.py."
)
MISSING_FILES_DIALOG_TITLE = "tar0bunny Pomodoro \u2014 missing files"

# modes
MODE_FOCUS = "focus"
MODE_BREAK = "break"

# time label geometry, centered in the window
TIME_LABEL_OFFSET_X = 220
TIME_LABEL_WIDTH = 440
TIME_LABEL_HEIGHT = 90
TIME_LABEL_Y = WINDOW_HEIGHT // 2 - TIME_LABEL_HEIGHT // 2
TIME_SHADOW_BLUR_RADIUS = 18

# gaps around the clock
GAP_ABOVE_CLOCK = 40
GAP_BELOW_CLOCK = 20
GAP_ABOVE_BUTTONS = 30
PANEL_PADDING = 30

# session label geometry, stacked above the clock
SESSION_LABEL_OFFSET_X = 180
SESSION_LABEL_WIDTH = 360
SESSION_LABEL_HEIGHT = 48
SESSION_LABEL_Y = TIME_LABEL_Y - SESSION_LABEL_HEIGHT - GAP_ABOVE_CLOCK
SESSION_SHADOW_BLUR_RADIUS = 14
SHADOW_OFFSET_X = 0
SHADOW_OFFSET_Y = 2

# tagline geometry, below the clock
TAGLINE_TEXT = "Stay curious."
TAGLINE_OFFSET_X = 150
TAGLINE_WIDTH = 300
TAGLINE_HEIGHT = 26
TAGLINE_Y = TIME_LABEL_Y + TIME_LABEL_HEIGHT + GAP_BELOW_CLOCK

# button row geometry, below the tagline
BUTTON_ROW_Y = TAGLINE_Y + TAGLINE_HEIGHT + GAP_ABOVE_BUTTONS
START_BUTTON_OFFSET_X = 195
START_BUTTON_WIDTH = 120
RESET_BUTTON_OFFSET_X = 65
RESET_BUTTON_WIDTH = 120
MODE_BUTTON_OFFSET_X = 65
MODE_BUTTON_WIDTH = 130

# button text
START_BUTTON_START_TEXT = "\u25b6  Start"
START_BUTTON_PAUSE_TEXT = "\u23f8  Pause"
RESET_BUTTON_TEXT = "\u21bb  Reset"
MODE_BUTTON_BREAK_TEXT = "\U0001f375 Break"
MODE_BUTTON_BREAK_SHORT_TEXT = "Break"
MODE_BUTTON_FOCUS_SHORT_TEXT = "Focus"

# session label text
SESSION_LABEL_FOCUS_TEXT = "Focus Mode"
SESSION_LABEL_BREAK_TEXT = "Break Mode"

# time formatting
TIME_FORMAT = "{:02d}:{:02d}"

# background panel geometry, wraps session label through button row
PANEL_OFFSET_X = 260
PANEL_WIDTH = 520
PANEL_Y = SESSION_LABEL_Y - PANEL_PADDING
PANEL_BOTTOM = BUTTON_ROW_Y + BUTTON_HEIGHT + PANEL_PADDING
PANEL_HEIGHT = PANEL_BOTTOM - PANEL_Y
PANEL_BORDER_RADIUS = 28


class Button(QPushButton):
    # rounded blossom-pink CTA button, tar0bunny-style

    def __init__(self, text, primary=True, parent=None):
        super().__init__(text, parent)
        self.primary = primary
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(BUTTON_HEIGHT)
        self.apply_style()

    def apply_style(self):
        if self.primary:
            bg, bg_hover, fg = BLOSSOM.name(), BLOSSOM_HOVER, NAVY.name()
        else:
            bg, bg_hover, fg = SECONDARY_BUTTON_BG, SECONDARY_BUTTON_HOVER, NAVY.name()
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg};
                color: {fg};
                border: {BUTTON_BORDER_WIDTH}px solid {NAVY.name()};
                border-radius: {BUTTON_BORDER_RADIUS}px;
                padding: 0 {BUTTON_PADDING_HORIZONTAL}px;
                font-family: '{FONT_FAMILY}', {FONT_FAMILY_SANS};
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

        # assets
        bg_path = ASSETS / BACKGROUND_FILENAME
        self.bg_pixmap = QPixmap(str(bg_path))

        missing = []
        if self.bg_pixmap.isNull():
            missing.append(str(bg_path))
        if missing:
            raise FileNotFoundError(
                ERROR_MESSAGE_HEADER + "\n  ".join(missing) + ERROR_MESSAGE_FOOTER
            )

        # chime sound, plays when a session finishes
        self.chime = QSoundEffect(self)
        chime_path = ASSETS / CHIME_FILENAME
        if chime_path.exists():
            self.chime.setSource(QUrl.fromLocalFile(str(chime_path)))
            self.chime.setVolume(CHIME_VOLUME)

        # script font for the session label
        self.label_family = LABEL_FONT_FAMILY

        # timer state
        self.mode = MODE_FOCUS
        self.seconds_left = FOCUS_SECONDS
        self.running = False

        self.countdown_timer = QTimer(self)
        self.countdown_timer.timeout.connect(self.tick)
        self.countdown_timer.setInterval(TICK_INTERVAL_MS)

        self.build_ui()

    # UI construction
    def build_ui(self):
        # session label, top of window
        self.session_label = QLabel(self)
        self.session_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.session_label.setGeometry(
            WINDOW_WIDTH // 2 - SESSION_LABEL_OFFSET_X, SESSION_LABEL_Y,
            SESSION_LABEL_WIDTH, SESSION_LABEL_HEIGHT,
        )
        session_font = QFont(self.label_family, SESSION_FONT_SIZE)
        self.session_label.setFont(session_font)
        self.session_label.setStyleSheet(f"""
            color: {WHITE.name()};
            background: transparent;
            border: none;
        """)
        session_shadow = QGraphicsDropShadowEffect(self)
        session_shadow.setBlurRadius(SESSION_SHADOW_BLUR_RADIUS)
        session_shadow.setOffset(SHADOW_OFFSET_X, SHADOW_OFFSET_Y)
        session_shadow.setColor(QColor(SHADOW_COLOR_R, SHADOW_COLOR_G, SHADOW_COLOR_B, SESSION_SHADOW_ALPHA))
        self.session_label.setGraphicsEffect(session_shadow)

        # big countdown time
        self.time_label = QLabel(self)
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_label.setGeometry(
            WINDOW_WIDTH // 2 - TIME_LABEL_OFFSET_X, TIME_LABEL_Y,
            TIME_LABEL_WIDTH, TIME_LABEL_HEIGHT,
        )
        time_font = QFont(FONT_FAMILY, TIME_FONT_SIZE, QFont.Weight.Bold)
        self.time_label.setFont(time_font)
        self.time_label.setStyleSheet(f"color: {WHITE.name()};")
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(TIME_SHADOW_BLUR_RADIUS)
        shadow.setOffset(SHADOW_OFFSET_X, SHADOW_OFFSET_Y)
        shadow.setColor(QColor(SHADOW_COLOR_R, SHADOW_COLOR_G, SHADOW_COLOR_B, TIME_SHADOW_ALPHA))
        self.time_label.setGraphicsEffect(shadow)

        # tagline under the clock
        self.tag_label = QLabel(TAGLINE_TEXT, self)
        self.tag_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.tag_label.setGeometry(
            WINDOW_WIDTH // 2 - TAGLINE_OFFSET_X, TAGLINE_Y,
            TAGLINE_WIDTH, TAGLINE_HEIGHT,
        )
        self.tag_label.setStyleSheet(f"""
            color: {LAVENDER.name()};
            font-family: '{FONT_FAMILY}', {FONT_FAMILY_SANS};
            font-style: italic;
            font-size: {TAGLINE_FONT_SIZE}px;
        """)

        # buttons row
        self.start_button = Button(START_BUTTON_START_TEXT, primary=True, parent=self)
        self.start_button.setGeometry(
            WINDOW_WIDTH // 2 - START_BUTTON_OFFSET_X, BUTTON_ROW_Y,
            START_BUTTON_WIDTH, BUTTON_HEIGHT,
        )
        self.start_button.clicked.connect(self.toggle_running)

        self.reset_button = Button(RESET_BUTTON_TEXT, primary=False, parent=self)
        self.reset_button.setGeometry(
            WINDOW_WIDTH // 2 - RESET_BUTTON_OFFSET_X, BUTTON_ROW_Y,
            RESET_BUTTON_WIDTH, BUTTON_HEIGHT,
        )
        self.reset_button.clicked.connect(self.reset)

        self.mode_button = Button(MODE_BUTTON_BREAK_TEXT, primary=False, parent=self)
        self.mode_button.setGeometry(
            WINDOW_WIDTH // 2 + MODE_BUTTON_OFFSET_X, BUTTON_ROW_Y,
            MODE_BUTTON_WIDTH, BUTTON_HEIGHT,
        )
        self.mode_button.clicked.connect(self.switch_mode)

        self.refresh_labels()

    # timer logic
    def toggle_running(self):
        self.running = not self.running
        if self.running:
            self.countdown_timer.start()
            self.start_button.setText(START_BUTTON_PAUSE_TEXT)
        else:
            self.countdown_timer.stop()
            self.start_button.setText(START_BUTTON_START_TEXT)

    def tick(self):
        if self.seconds_left > 0:
            self.seconds_left -= 1
            self.refresh_labels()
        else:
            self.session_complete()

    def session_complete(self):
        self.countdown_timer.stop()
        self.running = False
        self.start_button.setText(START_BUTTON_START_TEXT)
        if self.chime.isLoaded() or self.chime.source().isValid():
            self.chime.play()
        # flip mode and auto-start the next session
        self.mode = MODE_BREAK if self.mode == MODE_FOCUS else MODE_FOCUS
        self.seconds_left = BREAK_SECONDS if self.mode == MODE_BREAK else FOCUS_SECONDS
        self.refresh_labels()
        self.toggle_running()

    def reset(self):
        # always snaps back to a fresh focus session
        self.countdown_timer.stop()
        self.running = False
        self.start_button.setText(START_BUTTON_START_TEXT)
        self.mode = MODE_FOCUS
        self.seconds_left = FOCUS_SECONDS
        self.refresh_labels()

    def switch_mode(self):
        # one-click focus/break switch, works at any point
        self.countdown_timer.stop()
        self.running = False
        self.start_button.setText(START_BUTTON_START_TEXT)
        self.mode = MODE_BREAK if self.mode == MODE_FOCUS else MODE_FOCUS
        self.seconds_left = BREAK_SECONDS if self.mode == MODE_BREAK else FOCUS_SECONDS
        self.refresh_labels()

    def refresh_labels(self):
        mins, secs = divmod(self.seconds_left, SECONDS_PER_MINUTE)
        self.time_label.setText(TIME_FORMAT.format(mins, secs))
        if self.mode == MODE_FOCUS:
            self.session_label.setText(SESSION_LABEL_FOCUS_TEXT)
            self.mode_button.setText(MODE_BUTTON_BREAK_SHORT_TEXT)
        else:
            self.session_label.setText(SESSION_LABEL_BREAK_TEXT)
            self.mode_button.setText(MODE_BUTTON_FOCUS_SHORT_TEXT)

    # painting
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # background, scaled and cropped to fill window
        scaled = self.bg_pixmap.scaled(
            WINDOW_WIDTH, WINDOW_HEIGHT,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation,
        )
        x_off = (scaled.width() - WINDOW_WIDTH) // 2
        y_off = (scaled.height() - WINDOW_HEIGHT) // 2
        painter.drawPixmap(0, 0, scaled, x_off, y_off, WINDOW_WIDTH, WINDOW_HEIGHT)

        # soft rounded panel behind the clock/buttons area
        panel = QPainterPath()
        panel_rect = QRectF(WINDOW_WIDTH / 2 - PANEL_OFFSET_X, PANEL_Y, PANEL_WIDTH, PANEL_HEIGHT)
        panel.addRoundedRect(panel_rect, PANEL_BORDER_RADIUS, PANEL_BORDER_RADIUS)
        painter.fillPath(panel, QColor(SHADOW_COLOR_R, SHADOW_COLOR_G, SHADOW_COLOR_B, PANEL_ALPHA))

        painter.end()


def main():
    app = QApplication(sys.argv)
    app.setStyle(APP_STYLE)
    try:
        win = PomodoroWindow()
    except FileNotFoundError as e:
        # show this even on a double-clicked .py with no visible console
        QMessageBox.critical(None, MISSING_FILES_DIALOG_TITLE, str(e))
        sys.exit(1)
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()