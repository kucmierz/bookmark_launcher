from pathlib import Path
from PySide6.QtGui import QPixmap, QPainter, QColor, QPainterPath, QBrush, QPen
from PySide6.QtCore import Qt, QPointF, QRectF


ICON_SIZE = 256
ICON_PATH = Path(__file__).parent.parent.parent / "icon.png"

COLOR_BG = QColor("#1E2A3A")
COLOR_BODY = QColor("#22C5A0")
COLOR_BODY_DARK = QColor("#16A97F")
COLOR_WINDOW = QColor("#E8F8F5")
COLOR_FLAME = QColor("#F59E0B")
COLOR_FLAME_INNER = QColor("#FEF3C7")


def generate_icon() -> Path:
    """Generate the app icon PNG if it doesn't exist yet. Returns the icon path."""
    if ICON_PATH.exists():
        return ICON_PATH

    pixmap = QPixmap(ICON_SIZE, ICON_SIZE)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)

    _draw_background(painter)
    _draw_rocket(painter)

    painter.end()
    pixmap.save(str(ICON_PATH), "PNG")
    return ICON_PATH


def _draw_background(painter: QPainter) -> None:
    path = QPainterPath()
    path.addRoundedRect(QRectF(0, 0, ICON_SIZE, ICON_SIZE), 48, 48)
    painter.fillPath(path, QBrush(COLOR_BG))


def _draw_rocket(painter: QPainter) -> None:
    cx = ICON_SIZE / 2
    s = ICON_SIZE / 256  # scale factor — keeps coordinates readable at 1:1

    # flame (drawn first — behind the body)
    painter.setBrush(QBrush(COLOR_FLAME))
    painter.setPen(Qt.NoPen)
    painter.drawEllipse(QPointF(cx, 172 * s), 18 * s, 26 * s)

    painter.setBrush(QBrush(COLOR_FLAME_INNER))
    painter.drawEllipse(QPointF(cx, 178 * s), 9 * s, 15 * s)

    # left fin
    fin_left = QPainterPath()
    fin_left.moveTo((cx - 22) * 1, 145 * s)
    fin_left.lineTo(84 * s, 172 * s)
    fin_left.lineTo(110 * s, 157 * s)
    fin_left.closeSubpath()
    painter.fillPath(fin_left, QBrush(COLOR_BODY_DARK))

    # right fin
    fin_right = QPainterPath()
    fin_right.moveTo((cx + 22) * 1, 145 * s)
    fin_right.lineTo(172 * s, 172 * s)
    fin_right.lineTo(146 * s, 157 * s)
    fin_right.closeSubpath()
    painter.fillPath(fin_right, QBrush(COLOR_BODY_DARK))

    # rocket body (ellipse)
    painter.setBrush(QBrush(COLOR_BODY))
    painter.drawEllipse(QPointF(cx, 122 * s), 26 * s, 40 * s)

    # nose cone
    nose = QPainterPath()
    nose.moveTo((cx - 26), 122 * s)
    nose.quadTo(cx, 54 * s, (cx + 26), 122 * s)
    nose.closeSubpath()
    painter.fillPath(nose, QBrush(COLOR_BODY_DARK))

    # porthole
    painter.setBrush(QBrush(COLOR_WINDOW))
    painter.drawEllipse(QPointF(cx, 116 * s), 12 * s, 12 * s)
    painter.setBrush(QBrush(COLOR_BODY))
    painter.drawEllipse(QPointF(cx, 116 * s), 6 * s, 6 * s)