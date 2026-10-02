import os
import sys
from pathlib import Path
from typing import Optional, List
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, pyqtSignal, QThread, QPoint
from PyQt5.QtWidgets import QFileDialog, QMessageBox

from icon_changer.core.config import config
from icon_changer.core.history import history
from icon_changer.providers import search_icons, IconResult
from icon_changer.ui.styles import DARK_THEME_QSS
from icon_changer.ui.widgets import IconGrid
from icon_changer.ui.animated_success import SuccessCheckmarkOverlay
from icon_changer.ui.hamburger_menu import AnimatedHamburgerMenu
from icon_changer.ui.icons import (
    create_google_icon,
    create_icons8_icon,
    create_api_icon,
    create_search_icon,
    create_gear_icon,
    create_hamburger_icon,
    create_close_icon,
    create_chevron_left_icon,
    create_chevron_right_icon,
)

class SearchWorker(QThread):
    """Background worker to fetch search results with pagination without blocking UI."""
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
    Neumorphic-styled minimalist context-menu popup window for instant icon customization.
    Frameless, rounded corners, vector icons, animated hamburger menu,
    responsive reflowing icon grid, and animated green circle checkmark on apply.
    """

    def __init__(self, target_path: str, parent: Optional[QtWidgets.QWidget] = None, auto_search: bool = True) -> None:
        super().__init__(parent)
        self.target_path = str(Path(target_path).resolve())
        self.target_name = Path(target_path).name
        self.target_stem = Path(target_path).stem
        self.is_dir = Path(target_path).is_dir()
        self.is_lnk = str(target_path).lower().endswith(".lnk")

        self.current_page = 1
        self.current_provider = config.get("default_provider", "web")
        self.current_resolution = config.get("icon_resolution", 256)
        self.worker: Optional[SearchWorker] = None
        self.tray_icon: Optional[QtWidgets.QSystemTrayIcon] = None
        self.hamburger_menu: Optional[AnimatedHamburgerMenu] = None
        self._drag_pos: Optional[QPoint] = None

        self._setup_ui()
        self._setup_tray()
        self._apply_position()

        # Trigger initial search if enabled
        if auto_search:
            self.perform_search(reset_page=True)

    def _setup_tray(self) -> None:
        """Shows program in system tray (minimized section) while active."""
        if QtWidgets.QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon = QtWidgets.QSystemTrayIcon(self)
            app_icon_path = Path(__file__).resolve().parent.parent.parent / "assets" / "app_icon.png"
            if app_icon_path.exists():
                self.tray_icon.setIcon(QtGui.QIcon(str(app_icon_path)))
            else:
                pm = QtGui.QPixmap(16, 16)
                pm.fill(QtCore.Qt.transparent)
                p = QtGui.QPainter(pm)
                p.setRenderHint(QtGui.QPainter.Antialiasing)
                p.setBrush(QtGui.QBrush(QtGui.QColor("#7c5cfc")))
                p.setPen(QtCore.Qt.NoPen)
                p.drawRoundedRect(1, 1, 14, 14, 3, 3)
                p.end()
                self.tray_icon.setIcon(QtGui.QIcon(pm))

            self.tray_icon.setToolTip(f"Icon Changer - {self.target_name}")
            self.tray_icon.show()

    def _setup_ui(self) -> None:
        self.setWindowTitle(f"Change Icon - {self.target_name}")
        self.setStyleSheet(DARK_THEME_QSS)
        self.resize(720, 580)
        self.setMinimumSize(480, 400)

        # Frameless tool window without taskbar clutter
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowSystemMenuHint | Qt.Tool)

        # Set window icon
        app_icon_path = Path(__file__).resolve().parent.parent.parent / "assets" / "app_icon.ico"
        if app_icon_path.exists():
            self.setWindowIcon(QtGui.QIcon(str(app_icon_path)))

        outer_layout = QtWidgets.QVBoxLayout(self)
        outer_layout.setContentsMargins(6, 6, 6, 6)

        # Main Neumorphic Card Container
        self.main_card = QtWidgets.QFrame()
        self.main_card.setObjectName("mainFrame")
        card_layout = QtWidgets.QVBoxLayout(self.main_card)
        card_layout.setContentsMargins(14, 14, 14, 14)
        card_layout.setSpacing(12)

        # -------------------------------------------------------------
        # 1. Minimal Header Bar (Target info on Left, Actions on Right)
        # -------------------------------------------------------------
        header = QtWidgets.QFrame()
        header.setObjectName("headerBar")
        header_layout = QtWidgets.QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(10)

        # Target system icon
        target_icon_label = QtWidgets.QLabel()
        file_info = QtCore.QFileInfo(self.target_path)
        sys_icon = QtWidgets.QFileIconProvider().icon(file_info)
        target_icon_label.setPixmap(sys_icon.pixmap(24, 24))
        header_layout.addWidget(target_icon_label)

        # Bold target title
        target_info = QtWidgets.QLabel(self.target_name)
        target_info.setObjectName("targetTitle")
        header_layout.addWidget(target_info)

        header_layout.addStretch()

        # Gear Icon Button (Open Full Program)
        self.gear_btn = QtWidgets.QPushButton()
        self.gear_btn.setProperty("class", "headerBtn")
        self.gear_btn.setIcon(create_gear_icon(18, "#a2a5b8"))
        self.gear_btn.setIconSize(QtCore.QSize(18, 18))
        self.gear_btn.setToolTip("Open Full Program Window")
        self.gear_btn.setAutoDefault(False)
        self.gear_btn.setDefault(False)
        self.gear_btn.clicked.connect(self._open_full_program)
        header_layout.addWidget(self.gear_btn)

        # Hamburger Menu Button (Options & Resolution)
        self.hamburger_btn = QtWidgets.QPushButton()
        self.hamburger_btn.setProperty("class", "headerBtn")
        self.hamburger_btn.setIcon(create_hamburger_icon(18, "#a2a5b8"))
        self.hamburger_btn.setIconSize(QtCore.QSize(18, 18))
        self.hamburger_btn.setToolTip("Options, Resolution & Local Browse")
        self.hamburger_btn.setAutoDefault(False)
        self.hamburger_btn.setDefault(False)
        self.hamburger_btn.clicked.connect(self._toggle_hamburger_menu)
        header_layout.addWidget(self.hamburger_btn)

        # Minimal Red Close Button
        self.close_btn = QtWidgets.QPushButton()
        self.close_btn.setObjectName("closeBtn")
        self.close_btn.setIcon(create_close_icon(16, "#ef4444"))
        self.close_btn.setIconSize(QtCore.QSize(16, 16))
        self.close_btn.setToolTip("Close")
        self.close_btn.setAutoDefault(False)
        self.close_btn.setDefault(False)
        self.close_btn.clicked.connect(self.reject)
        header_layout.addWidget(self.close_btn)

        card_layout.addWidget(header)

        # -------------------------------------------------------------
        # 2. Sleek Unified Search & Provider Toolbar
        # -------------------------------------------------------------
        search_container = QtWidgets.QFrame()
        search_container.setObjectName("searchContainer")
        s_layout = QtWidgets.QHBoxLayout(search_container)
        s_layout.setContentsMargins(6, 4, 6, 4)
        s_layout.setSpacing(6)

        # Search Input Field
        default_query = config.build_search_query(self.target_stem)
        self.search_input = QtWidgets.QLineEdit(default_query)
        self.search_input.setObjectName("searchInput")
        self.search_input.setPlaceholderText("Search icon (e.g. gta v \"icon png\")...")
        self.search_input.returnPressed.connect(lambda: self.perform_search(reset_page=True))
        s_layout.addWidget(self.search_input, stretch=1)

        # Provider Toggle Buttons (Google, Icons8, API)
        self.provider_group = QtWidgets.QButtonGroup(self)
        self.provider_group.setExclusive(True)

        self.btn_web = QtWidgets.QPushButton()
        self.btn_web.setObjectName("providerToggleWeb")
        self.btn_web.setProperty("class", "providerToggle")
        self.btn_web.setIcon(create_google_icon(18))
        self.btn_web.setIconSize(QtCore.QSize(18, 18))
        self.btn_web.setCheckable(True)
        self.btn_web.setToolTip("Google & Web Search")
        self.btn_web.setAutoDefault(False)
        self.btn_web.setDefault(False)
        self.provider_group.addButton(self.btn_web, 0)
        s_layout.addWidget(self.btn_web)

        self.btn_icons8 = QtWidgets.QPushButton()
        self.btn_icons8.setObjectName("providerToggleIcons8")
        self.btn_icons8.setProperty("class", "providerToggle")
        self.btn_icons8.setIcon(create_icons8_icon(18))
        self.btn_icons8.setIconSize(QtCore.QSize(18, 18))
        self.btn_icons8.setCheckable(True)
        self.btn_icons8.setToolTip("Icons8 Icon Library")
        self.btn_icons8.setAutoDefault(False)
        self.btn_icons8.setDefault(False)
        self.provider_group.addButton(self.btn_icons8, 1)
        s_layout.addWidget(self.btn_icons8)

        self.btn_api = QtWidgets.QPushButton()
        self.btn_api.setObjectName("providerToggleApi")
        self.btn_api.setProperty("class", "providerToggle")
        self.btn_api.setIcon(create_api_icon(18))
        self.btn_api.setIconSize(QtCore.QSize(18, 18))
        self.btn_api.setCheckable(True)
        self.btn_api.setToolTip("Google Custom Search API")
        self.btn_api.setAutoDefault(False)
        self.btn_api.setDefault(False)
        self.provider_group.addButton(self.btn_api, 2)
        s_layout.addWidget(self.btn_api)

        # Sync initial provider check state
        if self.current_provider == "icons8":
            self.btn_icons8.setChecked(True)
        elif self.current_provider == "google_api":
            self.btn_api.setChecked(True)
        else:
            self.btn_web.setChecked(True)

        self.provider_group.buttonClicked.connect(self._on_provider_toggled)

        # Search Vector Button
        self.search_btn = QtWidgets.QPushButton()
        self.search_btn.setObjectName("searchIconBtn")
        self.search_btn.setIcon(create_search_icon(18, "#ffffff"))
        self.search_btn.setIconSize(QtCore.QSize(18, 18))
        self.search_btn.setToolTip("Search")
        self.search_btn.setAutoDefault(False)
        self.search_btn.setDefault(False)
        self.search_btn.clicked.connect(lambda: self.perform_search(reset_page=True))
        s_layout.addWidget(self.search_btn)

        card_layout.addWidget(search_container)

        # -------------------------------------------------------------
        # 3. Responsive Icon Grid (Reflows on resize, uncluttered)
        # -------------------------------------------------------------
        self.grid = IconGrid()
        self.grid.iconSelected.connect(self._on_icon_selected)
        self.grid.iconActivated.connect(self._on_icon_selected)
        card_layout.addWidget(self.grid, stretch=1)

        # -------------------------------------------------------------
        # 4. Compact Centered Pagination Bar
        # -------------------------------------------------------------
        page_layout = QtWidgets.QHBoxLayout()
        page_layout.setContentsMargins(0, 4, 0, 0)
        page_layout.setSpacing(8)
        page_layout.addStretch()

        self.prev_btn = QtWidgets.QPushButton()
        self.prev_btn.setProperty("class", "pageArrowBtn")
        self.prev_btn.setIcon(create_chevron_left_icon(14, "#ffffff"))
        self.prev_btn.setIconSize(QtCore.QSize(14, 14))
        self.prev_btn.setEnabled(False)
        self.prev_btn.setAutoDefault(False)
        self.prev_btn.setDefault(False)
        self.prev_btn.clicked.connect(self._prev_page)
        page_layout.addWidget(self.prev_btn)

        self.page_pill = QtWidgets.QLabel("1")
        self.page_pill.setObjectName("pagePill")
        self.page_pill.setAlignment(Qt.AlignCenter)
        page_layout.addWidget(self.page_pill)

        self.next_btn = QtWidgets.QPushButton()
        self.next_btn.setProperty("class", "pageArrowBtn")
        self.next_btn.setIcon(create_chevron_right_icon(14, "#ffffff"))
        self.next_btn.setIconSize(QtCore.QSize(14, 14))
        self.next_btn.setEnabled(False)
        self.next_btn.setAutoDefault(False)
        self.next_btn.setDefault(False)
        self.next_btn.clicked.connect(self._next_page)
        page_layout.addWidget(self.next_btn)

        page_layout.addStretch()
        card_layout.addLayout(page_layout)

        outer_layout.addWidget(self.main_card)

        # -------------------------------------------------------------
        # 5. Success Checkmark Overlay (Animated circle + tick)
        # -------------------------------------------------------------
        self.success_overlay = SuccessCheckmarkOverlay(self.main_card)
        self.success_overlay.animationFinished.connect(self.accept)

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

    def _on_provider_toggled(self, button: QtWidgets.QAbstractButton) -> None:
        if button == self.btn_icons8:
            new_provider = "icons8"
        elif button == self.btn_api:
            new_provider = "google_api"
        else:
            new_provider = "web"

        if new_provider == self.current_provider and self.grid.cards:
            return

        self.current_provider = new_provider
        config.set("default_provider", self.current_provider)

        # Force style re-polish to ensure immediate visual highlight update
        for btn in (self.btn_web, self.btn_icons8, self.btn_api):
            btn.style().unpolish(btn)
            btn.style().polish(btn)
            btn.update()

        self.perform_search(reset_page=True)

    def _toggle_hamburger_menu(self) -> None:
        if self.hamburger_menu and self.hamburger_menu.isVisible():
            self.hamburger_menu.close()
            return

        self.hamburger_menu = AnimatedHamburgerMenu(current_res=self.current_resolution, parent=self)
        self.hamburger_menu.resolutionChanged.connect(self._on_resolution_changed)
        self.hamburger_menu.browseLocalRequested.connect(self._on_browse_local)
        self.hamburger_menu.restoreDefaultRequested.connect(self._on_restore_default)

        # Compute button geometry in global screen space
        btn_geo = self.hamburger_btn.rect()
        top_left = self.hamburger_btn.mapToGlobal(btn_geo.topLeft())
        global_rect = QtCore.QRect(top_left, self.hamburger_btn.size())

        self.hamburger_menu.popup_at(global_rect)

    def _on_resolution_changed(self, new_res: object) -> None:
        self.current_resolution = new_res
        config.set("icon_resolution", new_res)

    def perform_search(self, reset_page: bool = False) -> None:
        if reset_page:
            self.current_page = 1

        query = self.search_input.text().strip()
        if not query:
            return

        self.search_btn.setEnabled(False)
        self.prev_btn.setEnabled(False)
        self.next_btn.setEnabled(False)
        self.page_pill.setText(str(self.current_page))

        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.worker.wait(300)

        max_res = config.get("max_results", 30)
        self.worker = SearchWorker(query, self.current_provider, max_results=max_res, page=self.current_page)
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
        self.page_pill.setText(str(self.current_page))

        if not results:
            self.grid.clear()
            return

        self.grid.set_results(results)

    def _on_search_error(self, err_msg: str) -> None:
        self.search_btn.setEnabled(True)
        self.prev_btn.setEnabled(self.current_page > 1)

    def _on_icon_selected(self, result: IconResult) -> None:
        """Downloads selected icon, converts to multi-resolution ICO, applies, and plays tick animation."""
        from icon_changer.core.icon_engine import IconEngine
        from icon_changer.core.icon_applicator import IconApplicator
        try:
            try:
                ico_path = IconEngine.create_icon_for_target(
                    image_data=result.image_url,
                    target_name=self.target_stem,
                    resolution=self.current_resolution
                )
            except Exception:
                if result.thumb_url and result.thumb_url != result.image_url:
                    ico_path = IconEngine.create_icon_for_target(
                        image_data=result.thumb_url,
                        target_name=self.target_stem,
                        resolution=self.current_resolution
                    )
                else:
                    raise

            success, msg = IconApplicator.apply_icon(self.target_path, str(ico_path))
            if success:
                history.add_entry(self.target_path, str(ico_path), title=result.title)
                # Play animated green circle + tick animation
                self.success_overlay.play()
            else:
                QMessageBox.critical(self, "Error", f"Failed to apply icon:\n{msg}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to apply icon:\n{e}")

    def _on_browse_local(self) -> None:
        """Allows selecting .ico, .png, .exe, .dll, or .lnk files from PC."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Icon, Executable, or Image",
            "",
            "All Supported (*.ico *.png *.jpg *.jpeg *.webp *.exe *.dll *.lnk);;"
            "Icons (*.ico);;"
            "Executables & DLLs (*.exe *.dll);;"
            "Shortcuts (*.lnk);;"
            "Images (*.png *.webp *.jpg);;"
            "All Files (*.*)"
        )
        if not file_path:
            return

        from icon_changer.core.icon_engine import IconEngine
        from icon_changer.core.icon_applicator import IconApplicator
        try:
            p = Path(file_path)
            if p.suffix.lower() == ".ico":
                ico_path = p
            else:
                ico_path = IconEngine.create_icon_for_target(
                    image_data=file_path,
                    target_name=self.target_stem,
                    resolution=self.current_resolution
                )

            success, msg = IconApplicator.apply_icon(self.target_path, str(ico_path))
            if success:
                history.add_entry(self.target_path, str(ico_path), title=p.name)
                self.success_overlay.play()
            else:
                QMessageBox.critical(self, "Error", f"Failed to apply icon:\n{msg}")
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
            from icon_changer.core.icon_applicator import IconApplicator
            try:
                if self.is_dir:
                    IconApplicator.restore_folder_icon(self.target_path)
                elif self.is_lnk:
                    IconApplicator.restore_shortcut_icon(self.target_path)
                history.remove_entry(self.target_path)
                self.success_overlay.play()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to restore icon:\n{e}")

    def _open_full_program(self) -> None:
        """Opens full application window and closes quick picker."""
        self.close()
        from icon_changer.ui.main_window import MainWindow
        self.main_win = MainWindow(initial_target=self.target_path)
        self.main_win.show()

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
        if event.buttons() == Qt.LeftButton and self._drag_pos:
            self.move(event.globalPos() - self._drag_pos)
            event.accept()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:
        self._drag_pos = None
        super().mouseReleaseEvent(event)

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        super().resizeEvent(event)
        if hasattr(self, "success_overlay") and self.success_overlay:
            self.success_overlay.resize(self.main_card.size())

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        if event.key() == Qt.Key_Escape:
            self.reject()
        elif event.key() in (Qt.Key_Return, Qt.Key_Enter):
            if self.search_input.hasFocus():
                self.perform_search(reset_page=True)
                event.accept()
            else:
                # If a card in the grid is selected, apply it
                selected = self.grid.get_selected_result()
                if selected:
                    self._on_icon_selected(selected)
                event.accept()
        elif event.key() == Qt.Key_F5:
            self.perform_search(reset_page=True)
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        if self.tray_icon:
            self.tray_icon.hide()
            self.tray_icon = None
        self.grid.stop()
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.worker.wait(300)
        super().closeEvent(event)
        QtWidgets.QApplication.quit()

    def reject(self) -> None:
        if self.tray_icon:
            self.tray_icon.hide()
            self.tray_icon = None
        self.grid.stop()
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.worker.wait(300)
        super().reject()
        QtWidgets.QApplication.quit()

    def accept(self) -> None:
        if self.tray_icon:
            self.tray_icon.hide()
            self.tray_icon = None
        self.grid.stop()
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.worker.wait(300)
        super().accept()
        QtWidgets.QApplication.quit()
