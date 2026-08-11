import sys

from PyQt6.QtCore import Qt, QTimer, QRectF, QUrl
from PyQt6.QtGui import QPixmap, QPainter, QFont, QColor, QPainterPath
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QGraphicsDropShadowEffect, QMessageBox
from PyQt6.QtMultimedia import QSoundEffect

from constants import *

class Button(QPushButton):
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