from typing import Optional, Any
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, pyqtSignal, QPoint, QEasingCurve, QPropertyAnimation
from PyQt5.QtWidgets import QGraphicsOpacityEffect

from icon_changer.ui.icons import (
    create_folder_icon,
    create_reset_icon,
    create_gear_icon,
)
from icon_changer.core.config import config
from icon_changer.core.permissions import PermissionManager

class AnimatedHamburgerMenu(QtWidgets.QWidget):
    """
    Sleek, dark, animated floating dropdown menu for options,
    icon resolution selection, browsing local files, and restoring defaults.
    """
    resolutionChanged = pyqtSignal(object)
    browseLocalRequested = pyqtSignal()
    restoreDefaultRequested = pyqtSignal()
    openSettingsRequested = pyqtSignal()

    def __init__(self, current_res: Any = 256, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(None, Qt.Popup | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.current_res = current_res

        self._setup_ui()
        self._setup_animation()

    def _setup_ui(self) -> None:
        outer_layout = QtWidgets.QVBoxLayout(self)
        outer_layout.setContentsMargins(8, 8, 8, 8)

        # Main Card Container
        self.card = QtWidgets.QFrame()
        self.card.setObjectName("menuCard")
        self.card.setStyleSheet("""
            QFrame#menuCard {
                background-color: #1a1c28;
                border: 1px solid #2d3042;
                border-radius: 16px;
            }
            QLabel {
                color: #8b8ea4;
                font-size: 11px;
                font-weight: 700;
                letter-spacing: 0.5px;
                text-transform: uppercase;
                background: transparent;
                border: none;
            }
            QPushButton.menuItem {
                background-color: transparent;
                color: #e2e8f0;
                border: none;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 13px;
                font-weight: 600;
                text-align: left;
            }
            QPushButton.menuItem:hover {
                background-color: #272a3c;
                color: #ffffff;
            }
            QPushButton.menuItem:pressed {
                background-color: #1f2130;
            }
            QComboBox {
                background-color: #222534;
                color: #ffffff;
                border: 1px solid #32364c;
                border-radius: 8px;
                padding: 6px 12px;
                font-size: 12px;
                font-weight: 600;
            }
            QComboBox:hover {
                border-color: #7c5cfc;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox QAbstractItemView {
                background-color: #1e202e;
                color: #ffffff;
                selection-background-color: #7c5cfc;
                selection-color: #ffffff;
                border: 1px solid #2d3042;
                border-radius: 8px;
                padding: 4px;
            }
        """)

        layout = QtWidgets.QVBoxLayout(self.card)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        # 1. Resolution Header & Dropdown
        res_label = QtWidgets.QLabel("ICON RESOLUTION")
        layout.addWidget(res_label)

        self.res_combo = QtWidgets.QComboBox()
        self.res_combo.addItem("256x256 (Extra Large / Crisp)", 256)
        self.res_combo.addItem("128x128 (Large)", 128)
        self.res_combo.addItem("96x96 (Medium-Large)", 96)
        self.res_combo.addItem("64x64 (Medium)", 64)
        self.res_combo.addItem("48x48 (Standard)", 48)
        self.res_combo.addItem("32x32 (Compact)", 32)
        self.res_combo.addItem("16x16 (Small)", 16)
        self.res_combo.addItem("Multi-Size .ICO (All Views)", "multi")

        idx = self.res_combo.findData(self.current_res)
        if idx >= 0:
            self.res_combo.setCurrentIndex(idx)
        self.res_combo.currentIndexChanged.connect(self._on_res_changed)
        layout.addWidget(self.res_combo)

        # Divider
        divider = QtWidgets.QFrame()
        divider.setFrameShape(QtWidgets.QFrame.HLine)
        divider.setStyleSheet("background-color: #26293a; max-height: 1px; border: none; margin: 4px 0px;")
        layout.addWidget(divider)

        # 2. Quick Actions Header
        actions_label = QtWidgets.QLabel("ACTIONS")
        layout.addWidget(actions_label)

        # Browse Local Button
        self.browse_btn = QtWidgets.QPushButton("Browse Local Icon...")
        self.browse_btn.setProperty("class", "menuItem")
        self.browse_btn.setIcon(create_folder_icon(18, "#8b5cf6"))
        self.browse_btn.setIconSize(QtCore.QSize(18, 18))
        self.browse_btn.clicked.connect(self._on_browse)
        layout.addWidget(self.browse_btn)

        # Restore Default Button
        self.restore_btn = QtWidgets.QPushButton("Restore Default Icon")
        self.restore_btn.setProperty("class", "menuItem")
        self.restore_btn.setIcon(create_reset_icon(18, "#ef4444"))
        self.restore_btn.setIconSize(QtCore.QSize(18, 18))
        self.restore_btn.clicked.connect(self._on_restore)
        layout.addWidget(self.restore_btn)

        outer_layout.addWidget(self.card)

    def _setup_animation(self) -> None:
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)

        self.anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.anim.setDuration(160)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.setEasingCurve(QEasingCurve.OutCubic)

    def _on_res_changed(self, idx: int) -> None:
        val = self.res_combo.currentData()
        self.current_res = val
        self.resolutionChanged.emit(val)

    def _on_browse(self) -> None:
        self.close()
        self.browseLocalRequested.emit()

    def _on_restore(self) -> None:
        self.close()
        self.restoreDefaultRequested.emit()

    def popup_at(self, target_rect: QtCore.QRect) -> None:
        """Pops up the menu anchored below the target rectangle with animation."""
        self.adjustSize()
        x = target_rect.right() - self.width() + 10
        y = target_rect.bottom() + 6

        # Screen boundary safety
        screen = QtWidgets.QApplication.screenAt(QPoint(x, y)) or QtWidgets.QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            x = max(geo.left() + 10, min(x, geo.right() - self.width() - 10))
            y = max(geo.top() + 10, min(y, geo.bottom() - self.height() - 10))

        self.move(x, y)
        self.show()
        self.anim.start()
