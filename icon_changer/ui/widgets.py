from typing import Optional, List
import sip
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, pyqtSignal, QRunnable, QThreadPool, QObject

from icon_changer.providers.base import IconResult
from icon_changer.core.icon_engine import IconEngine

class ImageLoadSignals(QObject):
    finished = pyqtSignal(str, bytes)
    error = pyqtSignal(str, str)

class ImageLoadTask(QRunnable):
    """
    Downloads image data purely as raw bytes in the background.
    Never creates QPixmap in worker threads (ensuring complete Qt thread safety).
    """
    def __init__(self, url: str) -> None:
        super().__init__()
        self.url = url
        self.signals = ImageLoadSignals()
        self.setAutoDelete(True)
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    def run(self) -> None:
        if self._cancelled:
            return
        try:
            raw_bytes = IconEngine.download_image(self.url, timeout=8)
            if self._cancelled:
                return
            if raw_bytes and len(raw_bytes) > 0:
                self.signals.finished.emit(self.url, raw_bytes)
            else:
                self.signals.error.emit(self.url, "Empty response")
        except Exception as e:
            if not self._cancelled:
                self.signals.error.emit(self.url, str(e))

class IconCard(QtWidgets.QFrame):
    """
    Card widget displaying an icon with a subtle transparency checkerboard pattern,
    hover highlights, selection borders, and async image loading.
    """
    clicked = pyqtSignal(object)       # Emits IconResult
    doubleClicked = pyqtSignal(object) # Emits IconResult

    def __init__(self, icon_result: IconResult, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.result = icon_result
        self.pixmap: Optional[QtGui.QPixmap] = None
        self.is_selected = False
        self.is_hovered = False

        self.setFixedSize(100, 100)
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setToolTip(f"{icon_result.title}\nSource: {icon_result.source}")

        # Precompute checkerboard pattern for transparent PNG display
        self._checkerboard = self._create_checkerboard_pattern()

    @staticmethod
    def _create_checkerboard_pattern() -> QtGui.QPixmap:
        pm = QtGui.QPixmap(16, 16)
        p = QtGui.QPainter(pm)
        p.fillRect(0, 0, 8, 8, QtGui.QColor("#242428"))
        p.fillRect(8, 0, 8, 8, QtGui.QColor("#1e1e22"))
        p.fillRect(0, 8, 8, 8, QtGui.QColor("#1e1e22"))
        p.fillRect(8, 8, 8, 8, QtGui.QColor("#242428"))
        p.end()
        return pm

    def set_pixmap(self, pixmap: QtGui.QPixmap) -> None:
        if sip.isdeleted(self):
            return
        # Pre-scale pixmap once on the main thread so paintEvent is ultra-fast
        target_size = 72
        self.pixmap = pixmap.scaled(
            target_size, target_size,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.update()

    def set_selected(self, selected: bool) -> None:
        if sip.isdeleted(self):
            return
        if self.is_selected != selected:
            self.is_selected = selected
            self.update()

    def enterEvent(self, event: QtCore.QEvent) -> None:
        self.is_hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event: QtCore.QEvent) -> None:
        self.is_hovered = False
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.result)
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event: QtGui.QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            self.doubleClicked.emit(self.result)
        super().mouseDoubleClickEvent(event)

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        if event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space):
            self.clicked.emit(self.result)
            event.accept()
        else:
            super().keyPressEvent(event)

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setRenderHint(QtGui.QPainter.SmoothPixmapTransform)

        rect = self.rect().adjusted(2, 2, -2, -2)

        # 1. Background checkerboard
        painter.save()
        path = QtGui.QPainterPath()
        path.addRoundedRect(QtCore.QRectF(rect), 8, 8)
        painter.setClipPath(path)
        painter.drawTiledPixmap(rect, self._checkerboard)
        painter.restore()

        # 2. Draw image
        if self.pixmap and not self.pixmap.isNull():
            x = (self.width() - self.pixmap.width()) // 2
            y = (self.height() - self.pixmap.height()) // 2
            painter.drawPixmap(x, y, self.pixmap)
        else:
            painter.setPen(QtGui.QColor("#666670"))
            painter.drawText(rect, Qt.AlignCenter, "...")

        # 3. Draw border
        if self.is_selected:
            painter.setPen(QtGui.QPen(QtGui.QColor("#0078d4"), 2.5))
            painter.drawRoundedRect(QtCore.QRectF(rect), 8, 8)
        elif self.is_hovered or self.hasFocus():
            painter.setPen(QtGui.QPen(QtGui.QColor("#50a0f0"), 1.8))
            painter.drawRoundedRect(QtCore.QRectF(rect), 8, 8)
        else:
            painter.setPen(QtGui.QPen(QtGui.QColor("#38383e"), 1.0))
            painter.drawRoundedRect(QtCore.QRectF(rect), 8, 8)

class IconGrid(QtWidgets.QScrollArea):
    """
    Scrollable responsive grid that arranges icon cards,
    manages background image loading, and handles keyboard selection.
    """
    iconSelected = pyqtSignal(object)   # Emits IconResult on single-click / enter
    iconActivated = pyqtSignal(object)  # Emits IconResult on double-click

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.cards: List[IconCard] = []
        self.tasks: List[ImageLoadTask] = []
        self.selected_index: int = -1
        self.thread_pool = QThreadPool(self)
        self.thread_pool.setMaxThreadCount(6)

        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.container = QtWidgets.QWidget()
        self.container.setStyleSheet("background-color: transparent;")
        self.flow_layout = QtWidgets.QGridLayout(self.container)
        self.flow_layout.setContentsMargins(8, 8, 8, 8)
        self.flow_layout.setSpacing(10)
        self.flow_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        self.setWidget(self.container)

    def set_results(self, results: List[IconResult]) -> None:
        self.clear()
        if not results:
            return

        columns = 5  # default columns, dynamically wraps
        for idx, result in enumerate(results):
            card = IconCard(result)
            card.clicked.connect(self._on_card_clicked)
            card.doubleClicked.connect(self._on_card_double_clicked)
            
            row = idx // columns
            col = idx % columns
            self.flow_layout.addWidget(card, row, col)
            self.cards.append(card)

            # Spawn async image load task (passes raw bytes to main thread)
            task = ImageLoadTask(result.thumb_url or result.image_url)
            task.signals.finished.connect(self._make_image_callback(card))
            self.tasks.append(task)
            self.thread_pool.start(task)

        # Select first card by default for instant keyboard navigation
        if self.cards:
            self.set_selected_index(0)

    def _make_image_callback(self, card: IconCard):
        def on_image_loaded(url: str, raw_bytes: bytes) -> None:
            if sip.isdeleted(card):
                return
            try:
                pixmap = QtGui.QPixmap()
                if pixmap.loadFromData(raw_bytes):
                    card.set_pixmap(pixmap)
            except Exception as e:
                pass
        return on_image_loaded

    def _on_card_clicked(self, result: IconResult) -> None:
        for idx, card in enumerate(self.cards):
            if card.result == result:
                self.set_selected_index(idx)
                break
        self.iconSelected.emit(result)

    def _on_card_double_clicked(self, result: IconResult) -> None:
        self.iconActivated.emit(result)

    def set_selected_index(self, index: int) -> None:
        if not self.cards:
            self.selected_index = -1
            return

        index = max(0, min(index, len(self.cards) - 1))
        self.selected_index = index

        for i, card in enumerate(self.cards):
            if not sip.isdeleted(card):
                card.set_selected(i == index)
                if i == index:
                    card.setFocus()
                    self.ensureWidgetVisible(card)

    def get_selected_result(self) -> Optional[IconResult]:
        if 0 <= self.selected_index < len(self.cards):
            card = self.cards[self.selected_index]
            if not sip.isdeleted(card):
                return card.result
        return None

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        if not self.cards:
            super().keyPressEvent(event)
            return

        key = event.key()
        columns = 5
        if key == Qt.Key_Right:
            self.set_selected_index(self.selected_index + 1)
            event.accept()
        elif key == Qt.Key_Left:
            self.set_selected_index(self.selected_index - 1)
            event.accept()
        elif key == Qt.Key_Down:
            self.set_selected_index(self.selected_index + columns)
            event.accept()
        elif key == Qt.Key_Up:
            self.set_selected_index(self.selected_index - columns)
            event.accept()
        elif key in (Qt.Key_Return, Qt.Key_Enter):
            selected = self.get_selected_result()
            if selected:
                self.iconSelected.emit(selected)
            event.accept()
        else:
            super().keyPressEvent(event)

    def clear(self) -> None:
        for task in self.tasks:
            task.cancel()
        self.tasks.clear()
        self.thread_pool.clear()
        for card in self.cards:
            if not sip.isdeleted(card):
                self.flow_layout.removeWidget(card)
                card.deleteLater()
        self.cards.clear()
        self.selected_index = -1

    def stop(self) -> None:
        """Stops all running image tasks and waits briefly."""
        for task in self.tasks:
            task.cancel()
        self.tasks.clear()
        self.thread_pool.clear()
        self.thread_pool.waitForDone(300)
