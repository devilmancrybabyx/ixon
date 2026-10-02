import math
from typing import Optional
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, QPointF, QRectF
from PyQt5.QtGui import QPainter, QPainterPath, QColor, QPen, QBrush, QPixmap, QIcon, QFont

def create_google_icon(size: int = 24) -> QIcon:
    """Draws a clean Google 'G' logo."""
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)

    cx = size / 2.0
    cy = size / 2.0
    r = size * 0.42

    # Draw colored Google 'G' arcs
    pen_w = max(2.5, size * 0.16)
    rect = QRectF(cx - r, cy - r, r * 2, r * 2)

    # Red top
    pen = QPen(QColor("#EA4335"), pen_w, Qt.SolidLine, Qt.FlatCap)
    p.setPen(pen)
    p.drawArc(rect, 45 * 16, 85 * 16)

    # Yellow top-left
    pen.setColor(QColor("#FBBC05"))
    p.setPen(pen)
    p.drawArc(rect, 130 * 16, 80 * 16)

    # Green bottom
    pen.setColor(QColor("#34A853"))
    p.setPen(pen)
    p.drawArc(rect, 210 * 16, 95 * 16)

    # Blue right & bar
    pen.setColor(QColor("#4285F4"))
    p.setPen(pen)
    p.drawArc(rect, 305 * 16, 55 * 16)

    p.drawLine(QPointF(cx - 1, cy), QPointF(cx + r, cy))
    p.end()
    return QIcon(pm)

def create_icons8_icon(size: int = 24) -> QIcon:
    """Draws modern Icons8 '8' emblem."""
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)

    cx = size / 2.0
    cy = size / 2.0
    
    # Outer circle with bright emerald glow
    pen = QPen(QColor("#10B981"), max(2.0, size * 0.12))
    pen.setCapStyle(Qt.RoundCap)
    p.setPen(pen)

    top_r = size * 0.20
    bot_r = size * 0.23
    top_cy = cy - top_r * 0.8
    bot_cy = cy + bot_r * 0.85

    p.drawEllipse(QRectF(cx - top_r, top_cy - top_r, top_r * 2, top_r * 2))
    p.drawEllipse(QRectF(cx - bot_r, bot_cy - bot_r, bot_r * 2, bot_r * 2))

    p.end()
    return QIcon(pm)

def create_api_icon(size: int = 24) -> QIcon:
    """Draws modern API badge."""
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setRenderHint(QPainter.TextAntialiasing)

    # Pill background
    p.setPen(Qt.NoPen)
    p.setBrush(QBrush(QColor("#2c274c")))
    p.drawRoundedRect(QRectF(2, 4, size - 4, size - 8), 4, 4)

    # Border
    p.setPen(QPen(QColor("#8B5CF6"), 1.5))
    p.setBrush(Qt.NoBrush)
    p.drawRoundedRect(QRectF(2, 4, size - 4, size - 8), 4, 4)

    # Bold "API"
    font = QFont("Segoe UI", int(size * 0.28), QFont.Bold)
    font.setLetterSpacing(QFont.AbsoluteSpacing, 0.5)
    p.setFont(font)
    p.setPen(QColor("#C4B5FD"))
    p.drawText(QRectF(0, 0, size, size), Qt.AlignCenter, "API")

    p.end()
    return QIcon(pm)

def create_search_icon(size: int = 24, color: str = "#ffffff") -> QIcon:
    """Draws vector magnifying glass search icon."""
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)

    pen = QPen(QColor(color), max(2.2, size * 0.12), Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
    p.setPen(pen)

    r = size * 0.28
    cx = size * 0.42
    cy = size * 0.42

    p.drawEllipse(QRectF(cx - r, cy - r, r * 2, r * 2))

    # Handle
    start_x = cx + r * math.cos(math.pi / 4)
    start_y = cy + r * math.sin(math.pi / 4)
    end_x = size - size * 0.14
    end_y = size - size * 0.14
    p.drawLine(QPointF(start_x, start_y), QPointF(end_x, end_y))

    p.end()
    return QIcon(pm)

def create_gear_icon(size: int = 24, color: str = "#a2a5b8") -> QIcon:
    """Draws crisp vector gear / settings icon."""
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)

    cx = size / 2.0
    cy = size / 2.0
    outer_r = size * 0.40
    inner_r = size * 0.30
    hole_r = size * 0.16

    pen = QPen(QColor(color), max(1.8, size * 0.08), Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
    p.setPen(pen)

    # 6 Cog Teeth Path
    path = QPainterPath()
    num_teeth = 6
    for i in range(num_teeth * 2):
        angle = i * (math.pi / num_teeth)
        r = outer_r if (i % 2 == 0) else inner_r
        x = cx + r * math.cos(angle)
        y = cy + r * math.sin(angle)
        if i == 0:
            path.moveTo(x, y)
        else:
            path.lineTo(x, y)
    path.closeSubpath()
    p.drawPath(path)

    # Central axle hole
    p.drawEllipse(QRectF(cx - hole_r, cy - hole_r, hole_r * 2, hole_r * 2))

    p.end()
    return QIcon(pm)

def create_hamburger_icon(size: int = 24, color: str = "#a2a5b8") -> QIcon:
    """Draws sleek 3-line hamburger menu icon."""
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)

    pen = QPen(QColor(color), max(2.2, size * 0.10), Qt.SolidLine, Qt.RoundCap)
    p.setPen(pen)

    margin = size * 0.22
    y_top = size * 0.30
    y_mid = size * 0.50
    y_bot = size * 0.70

    p.drawLine(QPointF(margin, y_top), QPointF(size - margin, y_top))
    p.drawLine(QPointF(margin, y_mid), QPointF(size - margin, y_mid))
    p.drawLine(QPointF(margin, y_bot), QPointF(size - margin, y_bot))

    p.end()
    return QIcon(pm)

def create_close_icon(size: int = 24, color: str = "#ef4444") -> QIcon:
    """Draws minimal red 'X' close icon."""
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)

    pen = QPen(QColor(color), max(2.0, size * 0.11), Qt.SolidLine, Qt.RoundCap)
    p.setPen(pen)

    m = size * 0.30
    p.drawLine(QPointF(m, m), QPointF(size - m, size - m))
    p.drawLine(QPointF(size - m, m), QPointF(m, size - m))

    p.end()
    return QIcon(pm)

def create_chevron_left_icon(size: int = 20, color: str = "#ffffff") -> QIcon:
    """Draws left chevron ‹."""
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)

    pen = QPen(QColor(color), max(2.0, size * 0.12), Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
    p.setPen(pen)

    cx = size / 2.0
    cy = size / 2.0
    dx = size * 0.18
    dy = size * 0.24

    path = QPainterPath()
    path.moveTo(cx + dx, cy - dy)
    path.lineTo(cx - dx, cy)
    path.lineTo(cx + dx, cy + dy)
    p.drawPath(path)

    p.end()
    return QIcon(pm)

def create_chevron_right_icon(size: int = 20, color: str = "#ffffff") -> QIcon:
    """Draws right chevron ›."""
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)

    pen = QPen(QColor(color), max(2.0, size * 0.12), Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
    p.setPen(pen)

    cx = size / 2.0
    cy = size / 2.0
    dx = size * 0.18
    dy = size * 0.24

    path = QPainterPath()
    path.moveTo(cx - dx, cy - dy)
    path.lineTo(cx + dx, cy)
    path.lineTo(cx - dx, cy + dy)
    p.drawPath(path)

    p.end()
    return QIcon(pm)

def create_folder_icon(size: int = 20, color: str = "#8b5cf6") -> QIcon:
    """Draws modern folder vector icon."""
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)

    pen = QPen(QColor(color), 1.8, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
    p.setPen(pen)

    path = QPainterPath()
    path.moveTo(size * 0.15, size * 0.30)
    path.lineTo(size * 0.40, size * 0.30)
    path.lineTo(size * 0.50, size * 0.40)
    path.lineTo(size * 0.85, size * 0.40)
    path.lineTo(size * 0.85, size * 0.75)
    path.lineTo(size * 0.15, size * 0.75)
    path.closeSubpath()
    p.drawPath(path)

    p.end()
    return QIcon(pm)

def create_reset_icon(size: int = 20, color: str = "#ef4444") -> QIcon:
    """Draws circular reset / undo arrow."""
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)

    pen = QPen(QColor(color), 1.8, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
    p.setPen(pen)

    cx = size / 2.0
    cy = size / 2.0
    r = size * 0.30

    p.drawArc(QRectF(cx - r, cy - r, r * 2, r * 2), 30 * 16, 280 * 16)
    # Arrow head
    p.drawLine(QPointF(cx + r * 0.6, cy - r * 0.7), QPointF(cx + r * 1.0, cy - r * 0.5))
    p.drawLine(QPointF(cx + r * 1.0, cy - r * 0.5), QPointF(cx + r * 1.2, cy - r * 1.0))

    p.end()
    return QIcon(pm)
