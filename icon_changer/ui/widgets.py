from typing import Optional, List
import sip
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, pyqtSignal, QRunnable, QThreadPool, QObject, QRectF, QPointF

from icon_changer.providers.base import IconResult
from icon_changer.core.icon_engine import IconEngine

class ImageLoadSignals(QObject):
    finished = pyqtSignal(str, object)
    error = pyqtSignal(str, str)

class ImageLoadTask(QRunnable):
    """
    Downloads and decodes image data into a pre-scaled QImage in the background.
    Performs all network I/O, format decoding, and Lanczos downscaling on worker threads,
    keeping the main GUI thread at 60 FPS without any frame drops.
    """
    def __init__(self, primary_url: str, fallback_url: Optional[str] = None) -> None:
        super().__init__()
        self.primary_url = primary_url
        self.fallback_url = fallback_url
        self.url = primary_url
        self.signals = ImageLoadSignals()
        self.setAutoDelete(True)
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    def run(self) -> None:
        if self._cancelled:
            return
        try:
            raw_bytes = IconEngine.download_image(self.primary_url, timeout=(2.0, 3.5))
            if (not raw_bytes or len(raw_bytes) == 0) and self.fallback_url and self.fallback_url != self.primary_url:
                raw_bytes = IconEngine.download_image(self.fallback_url, timeout=(2.0, 3.5))
            if self._cancelled:
                return
            if not raw_bytes or len(raw_bytes) == 0:
                self.signals.error.emit(self.url, "Empty response")
                return

            # Background decode & ensure transparent background without white halos
            qimg = None
            try:
                from PIL import Image
                import io
                pil_im = Image.open(io.BytesIO(raw_bytes))
                # Ensure transparent background and clean defringe BEFORE downsampling
                # so downsampling filter never blends white edges
                pil_im = IconEngine.ensure_transparent_background(pil_im)
                if pil_im.width > 72 or pil_im.height > 72:
                    pil_im.thumbnail((72, 72), Image.Resampling.LANCZOS)
                raw_rgba = pil_im.tobytes("raw", "RGBA")
                qimg = QtGui.QImage(raw_rgba, pil_im.width, pil_im.height, QtGui.QImage.Format_RGBA8888)
            except Exception:
                qimg = QtGui.QImage()
                if qimg.loadFromData(raw_bytes) and (qimg.width() > 72 or qimg.height() > 72):
                    qimg = qimg.scaled(72, 72, Qt.KeepAspectRatio, Qt.SmoothTransformation)

            if qimg and not qimg.isNull() and not self._cancelled:
                self.signals.finished.emit(self.url, qimg)
            elif not self._cancelled:
                self.signals.error.emit(self.url, "Could not decode image")
        except Exception as e:
            if not self._cancelled:
                self.signals.error.emit(self.url, str(e))

class IconCard(QtWidgets.QFrame):
    """
    Neumorphic-styled icon card widget with soft rounded borders,
    dark transparency checkerboard, hover elevation, and async image rendering.
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

        # Precompute modern dark checkerboard pattern
        self._checkerboard = self._create_checkerboard_pattern()

    @staticmethod
    def _create_checkerboard_pattern() -> QtGui.QPixmap:
        pm = QtGui.QPixmap(16, 16)
        p = QtGui.QPainter(pm)
        p.fillRect(0, 0, 8, 8, QtGui.QColor("#222534"))
        p.fillRect(8, 0, 8, 8, QtGui.QColor("#1a1c28"))
        p.fillRect(0, 8, 8, 8, QtGui.QColor("#1a1c28"))
        p.fillRect(8, 8, 8, 8, QtGui.QColor("#222534"))
        p.end()
        return pm

    def set_pixmap(self, pixmap: QtGui.QPixmap) -> None:
        if sip.isdeleted(self):
            return
        target_size = 72
        if pixmap.width() > target_size or pixmap.height() > target_size:
            self.pixmap = pixmap.scaled(
                target_size, target_size,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
        else:
            self.pixmap = pixmap
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

        rect = self.rect().adjusted(3, 3, -3, -3)

        # 1. Background checkerboard clipped to rounded rect
        painter.save()
        path = QtGui.QPainterPath()
        path.addRoundedRect(QtCore.QRectF(rect), 14, 14)
        painter.setClipPath(path)
        painter.drawTiledPixmap(rect, self._checkerboard)
        painter.restore()

        # 2. Draw centered image
        if self.pixmap and not self.pixmap.isNull():
            x = (self.width() - self.pixmap.width()) // 2
            y = (self.height() - self.pixmap.height()) // 2
            painter.drawPixmap(x, y, self.pixmap)
        else:
            painter.setPen(QtGui.QColor("#5d617a"))
            painter.drawText(rect, Qt.AlignCenter, "...")

        # 3. Draw border & selection glow
        if self.is_selected:
            painter.setPen(QtGui.QPen(QtGui.QColor("#7c5cfc"), 2.5))
            painter.drawRoundedRect(QtCore.QRectF(rect), 14, 14)
        elif self.is_hovered or self.hasFocus():
            painter.setPen(QtGui.QPen(QtGui.QColor("#9061f9"), 1.8))
            painter.drawRoundedRect(QtCore.QRectF(rect), 14, 14)
        else:
            painter.setPen(QtGui.QPen(QtGui.QColor("#2d3044"), 1.0))
            painter.drawRoundedRect(QtCore.QRectF(rect), 14, 14)

class IconGrid(QtWidgets.QScrollArea):
    """
    Scrollable, dynamically responsive grid that arranges icon cards.
    Reflows columns automatically when the window is resized.
    """
    iconSelected = pyqtSignal(object)   # Emits IconResult on single-click / enter
    iconActivated = pyqtSignal(object)  # Emits IconResult on double-click

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.cards: List[IconCard] = []
        self.tasks: List[ImageLoadTask] = []
        self.selected_index: int = -1
        self.current_cols: int = 5
        self.card_size: int = 100
        self.spacing: int = 12

        self.thread_pool = QThreadPool(self)
        self.thread_pool.setMaxThreadCount(24)

        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setStyleSheet("background-color: transparent; border: none;")

        self.container = QtWidgets.QWidget()
        self.container.setStyleSheet("background-color: transparent;")
        self.flow_layout = QtWidgets.QGridLayout(self.container)
        self.flow_layout.setContentsMargins(6, 6, 6, 6)
        self.flow_layout.setSpacing(self.spacing)
        self.flow_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        self.setWidget(self.container)

    def calculate_columns(self) -> int:
        viewport_w = self.viewport().width()
        if viewport_w <= 100:
            viewport_w = self.width() if self.width() > 100 else 700
        # Account for container margins (12px) and scrollbar (~16px)
        available_w = max(100, viewport_w - 28)
        cols = max(2, (available_w + self.spacing) // (self.card_size + self.spacing))
        return cols

    def _relayout_cards(self, force: bool = False) -> None:
        if not self.cards:
            return
        cols = self.calculate_columns()
        if cols == self.current_cols and not force and self.flow_layout.count() > 0:
            return

        self.current_cols = cols
        for idx, card in enumerate(self.cards):
            if not sip.isdeleted(card):
                self.flow_layout.removeWidget(card)
                row = idx // cols
                col = idx % cols
                self.flow_layout.addWidget(card, row, col, Qt.AlignCenter)

    def showEvent(self, event: QtGui.QShowEvent) -> None:
        super().showEvent(event)
        self._relayout_cards(force=True)

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        super().resizeEvent(event)
        self._relayout_cards()

    def set_results(self, results: List[IconResult]) -> None:
        self.clear()
        if not results:
            return

        self.current_cols = self.calculate_columns()
        for idx, result in enumerate(results):
            card = IconCard(result)
            card.clicked.connect(self._on_card_clicked)
            card.doubleClicked.connect(self._on_card_double_clicked)

            row = idx // self.current_cols
            col = idx % self.current_cols
            self.flow_layout.addWidget(card, row, col, Qt.AlignCenter)
            self.cards.append(card)

            primary_url = result.image_url or result.thumb_url
            fallback_url = result.thumb_url if result.thumb_url != primary_url else None
            if not primary_url:
                continue

            # 1. Instant cache check: Render immediately with 0ms delay if previously cached
            cached_bytes = IconEngine.get_cached_image(primary_url)
            if not cached_bytes and fallback_url:
                cached_bytes = IconEngine.get_cached_image(fallback_url)

            if cached_bytes:
                try:
                    from PIL import Image
                    import io
                    pil_im = Image.open(io.BytesIO(cached_bytes))
                    pil_im = IconEngine.ensure_transparent_background(pil_im)
                    if pil_im.width > 72 or pil_im.height > 72:
                        pil_im.thumbnail((72, 72), Image.Resampling.LANCZOS)
                    raw_rgba = pil_im.tobytes("raw", "RGBA")
                    qimg = QtGui.QImage(raw_rgba, pil_im.width, pil_im.height, QtGui.QImage.Format_RGBA8888)
                    card.set_pixmap(QtGui.QPixmap.fromImage(qimg))
                    continue
                except Exception:
                    qimg = QtGui.QImage()
                    if qimg.loadFromData(cached_bytes):
                        scaled = qimg.scaled(72, 72, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        card.set_pixmap(QtGui.QPixmap.fromImage(scaled))
                        continue

            # 2. Async concurrent download via thread pool (primary transparent PNG with fallback)
            task = ImageLoadTask(primary_url, fallback_url=fallback_url)
            task.signals.finished.connect(self._make_image_callback(card))
            self.tasks.append(task)
            self.thread_pool.start(task)

        if self.cards:
            self.set_selected_index(0)

    def _make_image_callback(self, card: IconCard):
        def on_image_loaded(url: str, img_obj: object) -> None:
            if sip.isdeleted(card):
                return
            try:
                if isinstance(img_obj, QtGui.QImage):
                    pixmap = QtGui.QPixmap.fromImage(img_obj)
                elif isinstance(img_obj, bytes):
                    pixmap = QtGui.QPixmap()
                    pixmap.loadFromData(img_obj)
                elif isinstance(img_obj, QtGui.QPixmap):
                    pixmap = img_obj
                else:
                    return
                card.set_pixmap(pixmap)
            except Exception:
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
        cols = self.current_cols
        if key == Qt.Key_Right:
            self.set_selected_index(self.selected_index + 1)
            event.accept()
        elif key == Qt.Key_Left:
            self.set_selected_index(self.selected_index - 1)
            event.accept()
        elif key == Qt.Key_Down:
            self.set_selected_index(self.selected_index + cols)
            event.accept()
        elif key == Qt.Key_Up:
            self.set_selected_index(self.selected_index - cols)
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
        for task in self.tasks:
            task.cancel()
        self.tasks.clear()
        self.thread_pool.clear()
        self.thread_pool.waitForDone(300)
