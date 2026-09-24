import os
import sys
from pathlib import Path
from typing import Optional, List
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, pyqtSignal, QThread
from PyQt5.QtWidgets import QFileDialog, QMessageBox

from icon_changer.core.config import config
from icon_changer.core.icon_engine import IconEngine
from icon_changer.core.icon_applicator import IconApplicator
from icon_changer.core.history import history
from icon_changer.providers import search_icons, IconResult
from icon_changer.ui.styles import DARK_THEME_QSS
from icon_changer.ui.widgets import IconGrid

class SearchWorker(QThread):
    """Background worker to fetch search results with pagination without blocking the UI."""
    resultsReady = pyqtSignal(list)
    errorOccurred = pyqtSignal(str)

    def __init__(self, query: str, provider_name: str, max_results: int = 30, page: int = 1) -> None:
        super().__init__()
        self.query = query
        self.provider_name = provider_name
        self.max_results = max_results
        self.page = page
        self._is_cancelled = False

    def cancel(self) -> None:
        self._is_cancelled = True

    def run(self) -> None:
        try:
            results = search_icons(self.query, self.provider_name, self.max_results, page=self.page)
            if not self._is_cancelled:
                self.resultsReady.emit(results)
        except Exception as e:
            if not self._is_cancelled:
                self.errorOccurred.emit(str(e))

class QuickPickerWindow(QtWidgets.QDialog):
    """
    Fast, lightweight context-menu popup window for instant icon customization.
    Renders as a tool utility window without cluttering the taskbar, and shows in the system tray.
    """

    def __init__(self, target_path: str, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.target_path = str(Path(target_path).resolve())
        self.target_name = Path(target_path).name
        self.target_stem = Path(target_path).stem
        self.is_dir = Path(target_path).is_dir()
        self.is_lnk = str(target_path).lower().endswith(".lnk")

        self.current_page = 1
        self.worker: Optional[SearchWorker] = None
        self.tray_icon: Optional[QtWidgets.QSystemTrayIcon] = None

        self._setup_ui()
        self._setup_tray()
        self._apply_position()

        # Trigger initial search
        self.perform_search(reset_page=True)

    def _setup_tray(self) -> None:
        """Adds program to the system tray (minimized section) while active."""
        if QtWidgets.QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon = QtWidgets.QSystemTrayIcon(self)
            
            # Use official app logo for system tray
            app_icon_path = Path(__file__).resolve().parent.parent.parent / "assets" / "app_icon.png"
            if app_icon_path.exists():
                self.tray_icon.setIcon(QtGui.QIcon(str(app_icon_path)))
            else:
                pm = QtGui.QPixmap(16, 16)
                pm.fill(QtCore.Qt.transparent)
                painter = QtGui.QPainter(pm)
                painter.setRenderHint(QtGui.QPainter.Antialiasing)
                painter.setBrush(QtGui.QBrush(QtGui.QColor("#0078d4")))
                painter.setPen(QtCore.Qt.NoPen)
                painter.drawRoundedRect(1, 1, 14, 14, 3, 3)
                painter.end()
                self.tray_icon.setIcon(QtGui.QIcon(pm))

            self.tray_icon.setToolTip(f"Icon Changer - {self.target_name}")
            self.tray_icon.show()

    def _setup_ui(self) -> None:
        self.setWindowTitle(f"Change Icon - {self.target_name}")
        self.setStyleSheet(DARK_THEME_QSS)
        self.resize(720, 560)

        # Set window icon
        app_icon_path = Path(__file__).resolve().parent.parent.parent / "assets" / "app_icon.ico"
        if app_icon_path.exists():
            self.setWindowIcon(QtGui.QIcon(str(app_icon_path)))

        # Qt.Tool removes the window from the main Windows taskbar
        self.setWindowFlags(Qt.Tool | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(10)

        # 1. Header with Target Info
        header_layout = QtWidgets.QHBoxLayout()
        target_icon_label = QtWidgets.QLabel()
        file_info = QtCore.QFileInfo(self.target_path)
        icon_provider = QtWidgets.QFileIconProvider()
        sys_icon = icon_provider.icon(file_info)
        target_icon_label.setPixmap(sys_icon.pixmap(24, 24))
        header_layout.addWidget(target_icon_label)

        target_info = QtWidgets.QLabel(f"<b>Target:</b> {self.target_name}")
        target_info.setStyleSheet("font-size: 13px; color: #ffffff;")
        header_layout.addWidget(target_info)
        header_layout.addStretch()

        self.reset_btn = QtWidgets.QPushButton("Restore Default")
        self.reset_btn.setObjectName("dangerButton")
        self.reset_btn.setToolTip("Restore default Windows icon for this item")
        self.reset_btn.clicked.connect(self._on_restore_default)
        header_layout.addWidget(self.reset_btn)

        self.browse_btn = QtWidgets.QPushButton("Browse Local...")
        self.browse_btn.setToolTip("Choose an .ico, .png, .exe, or .dll file from your PC")
        self.browse_btn.clicked.connect(self._on_browse_local)
        header_layout.addWidget(self.browse_btn)

        main_layout.addLayout(header_layout)

        # 2. Search Toolbar
        search_layout = QtWidgets.QHBoxLayout()
        search_layout.setSpacing(8)

        default_query = config.build_search_query(self.target_stem)
        self.search_input = QtWidgets.QLineEdit(default_query)
        self.search_input.setPlaceholderText("Search icon (e.g. gta v \"icon png\")...")
        self.search_input.returnPressed.connect(lambda: self.perform_search(reset_page=True))
        search_layout.addWidget(self.search_input, stretch=3)

        self.provider_combo = QtWidgets.QComboBox()
        self.provider_combo.addItem("Google & Web", "web")
        self.provider_combo.addItem("Icons8 Library", "icons8")
        self.provider_combo.addItem("Google Custom API", "google_api")
        idx = self.provider_combo.findData(config.get("default_provider", "web"))
        if idx >= 0:
            self.provider_combo.setCurrentIndex(idx)
        self.provider_combo.currentIndexChanged.connect(lambda: self.perform_search(reset_page=True))
        self.provider_combo.setToolTip("Switch icon source")
        search_layout.addWidget(self.provider_combo)

        self.res_combo = QtWidgets.QComboBox()
        self.res_combo.addItem("256x256 (Extra Large / Crisp)", 256)
        self.res_combo.addItem("128x128 (Large)", 128)
        self.res_combo.addItem("96x96 (Medium-Large)", 96)
        self.res_combo.addItem("64x64 (Medium)", 64)
        self.res_combo.addItem("48x48 (Standard)", 48)
        self.res_combo.addItem("32x32 (Compact)", 32)
        self.res_combo.addItem("16x16 (Small)", 16)
        self.res_combo.addItem("Multi-Size .ICO (All Views)", "multi")
        res_idx = self.res_combo.findData(config.get("icon_resolution", 256))
        if res_idx >= 0:
            self.res_combo.setCurrentIndex(res_idx)
        self.res_combo.setToolTip("Output icon resolution")
        search_layout.addWidget(self.res_combo)

        self.search_btn = QtWidgets.QPushButton("Search")
        self.search_btn.setObjectName("primaryButton")
        self.search_btn.clicked.connect(lambda: self.perform_search(reset_page=True))
        search_layout.addWidget(self.search_btn)

        main_layout.addLayout(search_layout)

        # 3. Status label
        self.status_label = QtWidgets.QLabel("Ready")
        self.status_label.setStyleSheet("color: #8c8c94; font-size: 11px;")
        main_layout.addWidget(self.status_label)

        # 4. Icon Results Grid
        self.grid = IconGrid()
        self.grid.iconSelected.connect(self._on_icon_selected)
        self.grid.iconActivated.connect(self._on_icon_selected)
        main_layout.addWidget(self.grid, stretch=1)

        # 5. Pagination Bar
        page_layout = QtWidgets.QHBoxLayout()
        self.prev_btn = QtWidgets.QPushButton("< Previous")
        self.prev_btn.setEnabled(False)
        self.prev_btn.clicked.connect(self._prev_page)
        page_layout.addWidget(self.prev_btn)

        page_layout.addStretch()
        self.page_label = QtWidgets.QLabel("Page 1")
        self.page_label.setStyleSheet("color: #a0a0a8; font-size: 12px; font-weight: 500;")
        page_layout.addWidget(self.page_label)
        page_layout.addStretch()

        self.next_btn = QtWidgets.QPushButton("Next >")
        self.next_btn.setEnabled(False)
        self.next_btn.clicked.connect(self._next_page)
        page_layout.addWidget(self.next_btn)

        main_layout.addLayout(page_layout)

        # 6. Footer Instructions & Full App Button
        footer_layout = QtWidgets.QHBoxLayout()
        hint = QtWidgets.QLabel("Click an icon to apply • Arrow keys to navigate • Esc to close")
        hint.setStyleSheet("color: #707078; font-size: 11px;")
        footer_layout.addWidget(hint)
        footer_layout.addStretch()

        self.full_app_btn = QtWidgets.QPushButton("Open Full Program")
        self.full_app_btn.clicked.connect(self._open_full_program)
        footer_layout.addWidget(self.full_app_btn)

        main_layout.addLayout(footer_layout)

    def _apply_position(self) -> None:
        """Positions window near cursor with screen boundary safety."""
        cursor_pos = QtGui.QCursor.pos()
        screen = QtWidgets.QApplication.screenAt(cursor_pos) or QtWidgets.QApplication.primaryScreen()
        if not screen:
            return
        screen_geo = screen.availableGeometry()

        x = cursor_pos.x() - self.width() // 2
        y = cursor_pos.y() - self.height() // 2

        x = max(screen_geo.left() + 20, min(x, screen_geo.right() - self.width() - 20))
        y = max(screen_geo.top() + 20, min(y, screen_geo.bottom() - self.height() - 20))

        self.move(x, y)

    def perform_search(self, reset_page: bool = False) -> None:
        if reset_page:
            self.current_page = 1

        query = self.search_input.text().strip()
        if not query:
            return

        provider_name = self.provider_combo.currentData()
        self.status_label.setText(f"Searching for '{query}' (Page {self.current_page})...")
        self.search_btn.setEnabled(False)
        self.prev_btn.setEnabled(False)
        self.next_btn.setEnabled(False)
        self.page_label.setText(f"Page {self.current_page}")

        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.worker.wait(400)

        max_res = config.get("max_results", 30)
        self.worker = SearchWorker(query, provider_name, max_results=max_res, page=self.current_page)
        self.worker.resultsReady.connect(self._on_results_ready)
        self.worker.errorOccurred.connect(self._on_search_error)
        self.worker.start()

    def _prev_page(self) -> None:
        if self.current_page > 1:
            self.current_page -= 1
            self.perform_search(reset_page=False)

    def _next_page(self) -> None:
        self.current_page += 1
        self.perform_search(reset_page=False)

    def _on_results_ready(self, results: List[IconResult]) -> None:
        self.search_btn.setEnabled(True)
        self.prev_btn.setEnabled(self.current_page > 1)
        self.next_btn.setEnabled(len(results) >= config.get("max_results", 30))
        self.page_label.setText(f"Page {self.current_page}")

        if not results:
            self.status_label.setText("No icons found. Modify search terms or switch provider.")
            self.grid.clear()
            return

        self.status_label.setText(f"Found {len(results)} icons (Page {self.current_page}). Click an icon to apply.")
        self.grid.set_results(results)

    def _on_search_error(self, err_msg: str) -> None:
        self.search_btn.setEnabled(True)
        self.prev_btn.setEnabled(self.current_page > 1)
        self.status_label.setText(f"Search error: {err_msg}")

    def _on_icon_selected(self, result: IconResult) -> None:
        """Downloads selected icon, converts to ICO with alpha channel, and applies to target."""
        self.status_label.setText(f"Applying icon from {result.source}...")
        QtWidgets.QApplication.processEvents()

        try:
            resolution = self.res_combo.currentData()
            ico_path = IconEngine.create_icon_for_target(
                image_data=result.image_url,
                target_name=self.target_stem,
                resolution=resolution
            )

            success, msg = IconApplicator.apply_icon(self.target_path, str(ico_path))
            if success:
                history.add_entry(self.target_path, str(ico_path), title=result.title)
                self.status_label.setText(msg)
                QtCore.QTimer.singleShot(600, self.accept)
            else:
                self.status_label.setText(f"Error: {msg}")
        except Exception as e:
            self.status_label.setText(f"Error applying icon: {e}")
            QMessageBox.critical(self, "Error", f"Failed to apply icon:\n{e}")

    def _on_browse_local(self) -> None:
        """Allows picking a local image or icon file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Icon or Image",
            "",
            "Icon & Image Files (*.ico *.png *.jpg *.jpeg *.webp *.exe *.dll);;All Files (*.*)"
        )
        if not file_path:
            return

        try:
            p = Path(file_path)
            if p.suffix.lower() == ".ico":
                ico_path = p
            else:
                resolution = self.res_combo.currentData()
                ico_path = IconEngine.create_icon_for_target(
                    image_data=file_path,
                    target_name=self.target_stem,
                    resolution=resolution
                )

            success, msg = IconApplicator.apply_icon(self.target_path, str(ico_path))
            if success:
                history.add_entry(self.target_path, str(ico_path), title=p.name)
                self.status_label.setText(msg)
                QtCore.QTimer.singleShot(600, self.accept)
            else:
                self.status_label.setText(f"Error: {msg}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to set local icon:\n{e}")

    def _on_restore_default(self) -> None:
        """Restores default Windows icon."""
        reply = QMessageBox.question(
            self,
            "Restore Default Icon",
            f"Restore default Windows icon for:\n{self.target_name}?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                if self.is_dir:
                    IconApplicator.restore_folder_icon(self.target_path)
                elif self.is_lnk:
                    IconApplicator.restore_shortcut_icon(self.target_path)
                history.remove_entry(self.target_path)
                self.status_label.setText("Default icon restored.")
                QtCore.QTimer.singleShot(600, self.accept)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to restore icon:\n{e}")

    def _open_full_program(self) -> None:
        """Opens the full application window."""
        self.close()
        from icon_changer.ui.main_window import MainWindow
        self.main_win = MainWindow(initial_target=self.target_path)
        self.main_win.show()

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        """Ensures worker thread, tray icon, and image tasks are safely stopped."""
        if self.tray_icon:
            self.tray_icon.hide()
        self.grid.stop()
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.worker.wait(400)
        super().closeEvent(event)

    def reject(self) -> None:
        if self.tray_icon:
            self.tray_icon.hide()
        self.grid.stop()
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.worker.wait(400)
        super().reject()

    def accept(self) -> None:
        if self.tray_icon:
            self.tray_icon.hide()
        super().accept()

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        if event.key() == Qt.Key_Escape:
            self.reject()
        elif event.key() == Qt.Key_F5:
            self.perform_search(reset_page=True)
        else:
            super().keyPressEvent(event)
