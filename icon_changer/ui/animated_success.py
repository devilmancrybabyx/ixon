from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, QPointF, QRectF, QPropertyAnimation, QEasingCurve, pyqtSignal

class SuccessCheckmarkOverlay(QtWidgets.QWidget):
    """
    Animated overlay displaying a glowing green circle with drawing checkmark stroke
    upon successfully applying an icon.
    """
    animationFinished = pyqtSignal()

    def __init__(self, parent: QtWidgets.QWidget = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.hide()

        self._progress = 0.0
        self._opacity = 0.0

        self.anim = QtCore.QVariantAnimation(self)
        self.anim.setDuration(480)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.setEasingCurve(QEasingCurve.OutCubic)
        self.anim.valueChanged.connect(self._on_anim_val)
        self.anim.finished.connect(self._on_finished)

    def _on_anim_val(self, val: float) -> None:
        self._progress = val
        self.update()

    def _on_finished(self) -> None:
        QtCore.QTimer.singleShot(180, self.animationFinished.emit)

    def play(self) -> None:
        if self.parent():
            self.resize(self.parent().size())
            self.raise_()
        self.show()
        self.anim.start()

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        super().resizeEvent(event)
        self.update()

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        # 1. Subtle dark vignette backdrop
        bg_alpha = int(140 * min(1.0, self._progress * 2.0))
        painter.fillRect(self.rect(), QtGui.QColor(18, 20, 29, bg_alpha))

        # Center coordinates
        cx = self.width() / 2.0
        cy = self.height() / 2.0
        target_r = 38.0

        # Circle scale animation (0.0 to 0.4)
        circle_t = min(1.0, self._progress / 0.45)
        # Gentle spring overshoot
        scale = 1.0 + 0.15 * (1.0 - circle_t) if circle_t < 1.0 else 1.0
        current_r = target_r * circle_t * scale

        if current_r > 0:
            # Subtle radial outer glow
            glow = QtGui.QRadialGradient(cx, cy, current_r * 1.5)
            glow.setColorAt(0.0, QtGui.QColor(16, 185, 129, int(90 * circle_t)))
            glow.setColorAt(1.0, QtGui.QColor(16, 185, 129, 0))
            painter.setPen(Qt.NoPen)
            painter.setBrush(QtGui.QBrush(glow))
            painter.drawEllipse(QPointF(cx, cy), current_r * 1.5, current_r * 1.5)

            # Filled green circle
            painter.setPen(QtGui.QPen(QtGui.QColor("#059669"), 2.0))
            painter.setBrush(QtGui.QBrush(QtGui.QColor("#10b981")))
            painter.drawEllipse(QPointF(cx, cy), current_r, current_r)

        # Checkmark animation (starts at 0.3, ends at 0.9)
        if self._progress > 0.3:
            tick_t = min(1.0, (self._progress - 0.3) / 0.6)

            pen = QtGui.QPen(QtGui.QColor("#ffffff"), 4.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)

            p1 = QPointF(cx - 15, cy - 1)
            p2 = QPointF(cx - 4, cy + 11)
            p3 = QPointF(cx + 17, cy - 10)

            path = QtGui.QPainterPath()
            path.moveTo(p1)

            # Animate first segment (0.0 to 0.4)
            seg1_t = min(1.0, tick_t / 0.4)
            current_p2 = QPointF(p1.x() + (p2.x() - p1.x()) * seg1_t,
                                p1.y() + (p2.y() - p1.y()) * seg1_t)
            path.lineTo(current_p2)

            # Animate second segment (0.4 to 1.0)
            if tick_t > 0.4:
                seg2_t = (tick_t - 0.4) / 0.6
                current_p3 = QPointF(p2.x() + (p3.x() - p2.x()) * seg2_t,
                                    p2.y() + (p3.y() - p2.y()) * seg2_t)
                path.lineTo(current_p3)

            painter.drawPath(path)

            # Text: "Applied"
            if self._progress > 0.5:
                text_t = (self._progress - 0.5) / 0.5
                painter.setPen(QtGui.QColor(255, 255, 255, int(255 * text_t)))
                font = QtGui.QFont("Segoe UI Variable Display", 11, QtGui.QFont.Bold)
                painter.setFont(font)
                text_rect = QRectF(cx - 100, cy + current_r + 14, 200, 30)
                painter.drawText(text_rect, Qt.AlignCenter, "Applied!")

        painter.end()
