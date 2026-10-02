import os
import time
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
from icon_changer.ui.settings_tab import SettingsTab
from icon_changer.ui.quick_picker import SearchWorker

class DropTargetArea(QtWidgets.QFrame):
    """Drag & Drop zone for selecting files, folders, or shortcuts."""
    targetDropped = pyqtSignal(str)

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setStyleSheet("""
            DropTargetArea {
                border: 2px dashed #3c3c44;
                border-radius: 8px;
                background-color: #1e1e22;
                padding: 16px;
            }
            DropTargetArea:hover {
                border-color: #0078d4;
                background-color: #222228;
            }
        """)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        self.icon_label = QtWidgets.QLabel()
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.text_label = QtWidgets.QLabel("Drag and drop any Folder, File, or Shortcut here\nor use the buttons below")
        self.text_label.setAlignment(Qt.AlignCenter)
        self.text_label.setStyleSheet("color: #a0a0a8; font-size: 13px; font-weight: 500;")
        layout.addWidget(self.icon_label)
        layout.addWidget(self.text_label)

    def set_target_display(self, path_str: str) -> None:
        p = Path(path_str)
        info = QtCore.QFileInfo(path_str)
        icon = QtWidgets.QFileIconProvider().icon(info)
        self.icon_label.setPixmap(icon.pixmap(32, 32))
        self.text_label.setText(f"<b>Selected:</b> {p.name}<br><span style='color: #707078; font-size: 11px;'>{p}</span>")

    def dragEnterEvent(self, event: QtGui.QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QtGui.QDropEvent) -> None:
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if os.path.exists(file_path):
                self.set_target_display(file_path)
                self.targetDropped.emit(file_path)
                break
        event.acceptProposedAction()

class MainWindow(QtWidgets.QMainWindow):
    """
    Main Application Window with Full Workspace, History Manager, and Settings.
    """

    def __init__(self, initial_target: str = "") -> None:
        super().__init__()
        self.current_target: Optional[str] = initial_target if (initial_target and os.path.exists(initial_target)) else None
        self.selected_result: Optional[IconResult] = None
        self.worker: Optional[SearchWorker] = None
        self.current_page = 1

        self._setup_ui()
        if self.current_target:
            self._set_target(self.current_target)

    def _setup_ui(self) -> None:
        self.setWindowTitle("Icon Changer — Windows Icon Customizer")
        self.setStyleSheet(DARK_THEME_QSS)
        self.resize(900, 700)

        # Set window icon
        app_icon_path = Path(__file__).resolve().parent.parent.parent / "assets" / "app_icon.ico"
        if app_icon_path.exists():
            self.setWindowIcon(QtGui.QIcon(str(app_icon_path)))

        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QtWidgets.QVBoxLayout(central_widget)
        main_layout.setContentsMargins(14, 14, 14, 14)

        # Tab Widget
        self.tabs = QtWidgets.QTabWidget()
        self.tabs.addTab(self._create_customizer_tab(), "Customizer")
        self.tabs.addTab(self._create_history_tab(), "History")
        self.tabs.addTab(SettingsTab(), "Settings")

        main_layout.addWidget(self.tabs)

        # Status Bar
        self.statusBar().showMessage("Ready")

    def _create_customizer_tab(self) -> QtWidgets.QWidget:
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(tab)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # 1. Target Selector Section
        self.drop_area = DropTargetArea()
        self.drop_area.targetDropped.connect(self._set_target)
        layout.addWidget(self.drop_area)

        # Browse buttons row
        browse_row = QtWidgets.QHBoxLayout()
        browse_folder_btn = QtWidgets.QPushButton("Browse Folder...")
        browse_folder_btn.clicked.connect(self._browse_folder)
        browse_row.addWidget(browse_folder_btn)

        browse_shortcut_btn = QtWidgets.QPushButton("Browse Shortcut (.lnk)...")
        browse_shortcut_btn.clicked.connect(self._browse_shortcut)
        browse_row.addWidget(browse_shortcut_btn)

        browse_file_btn = QtWidgets.QPushButton("Browse Any File...")
        browse_file_btn.clicked.connect(self._browse_file)
        browse_row.addWidget(browse_file_btn)

        self.restore_btn = QtWidgets.QPushButton("Restore Default Icon")
        self.restore_btn.setObjectName("dangerButton")
        self.restore_btn.clicked.connect(self._restore_current_target)
        self.restore_btn.setEnabled(False)
        browse_row.addWidget(self.restore_btn)

        layout.addLayout(browse_row)

        # 2. Search Controls
        search_box = QtWidgets.QGroupBox("Search & Select New Icon")
        s_layout = QtWidgets.QVBoxLayout(search_box)
        s_layout.setSpacing(10)

        s_row = QtWidgets.QHBoxLayout()
        self.search_input = QtWidgets.QLineEdit()
        self.search_input.setPlaceholderText("Search icon (e.g. gta v \"icon png\")...")
        self.search_input.returnPressed.connect(lambda: self.perform_search(reset_page=True))
        s_row.addWidget(self.search_input, stretch=3)

        self.provider_combo = QtWidgets.QComboBox()
        self.provider_combo.addItem("Google & Web", "web")
        self.provider_combo.addItem("Icons8 Library", "icons8")
        self.provider_combo.addItem("Google Custom API", "google_api")
        idx = self.provider_combo.findData(config.get("default_provider", "web"))
        if idx >= 0:
            self.provider_combo.setCurrentIndex(idx)
        self.provider_combo.currentIndexChanged.connect(lambda: self.perform_search(reset_page=True))
        s_row.addWidget(self.provider_combo)

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
        s_row.addWidget(self.res_combo)

        self.search_btn = QtWidgets.QPushButton("Search")
        self.search_btn.setObjectName("primaryButton")
        self.search_btn.clicked.connect(lambda: self.perform_search(reset_page=True))
        s_row.addWidget(self.search_btn)

        self.browse_local_btn = QtWidgets.QPushButton("Local File...")
        self.browse_local_btn.clicked.connect(self._browse_local_icon)
        s_row.addWidget(self.browse_local_btn)

        s_layout.addLayout(s_row)

        self.search_status = QtWidgets.QLabel("Select a target or enter search terms above.")
        self.search_status.setStyleSheet("color: #8c8c94; font-size: 11px;")
        s_layout.addWidget(self.search_status)

        # 3. Grid of Icons
        self.grid = IconGrid()
        self.grid.iconSelected.connect(self._on_icon_selected)
        self.grid.iconActivated.connect(self._on_icon_activated)
        s_layout.addWidget(self.grid, stretch=1)

        # 4. Pagination Bar
        page_row = QtWidgets.QHBoxLayout()
        self.prev_btn = QtWidgets.QPushButton("< Previous")
        self.prev_btn.setEnabled(False)
        self.prev_btn.clicked.connect(self._prev_page)
        page_row.addWidget(self.prev_btn)

        page_row.addStretch()
        self.page_label = QtWidgets.QLabel("Page 1")
        self.page_label.setStyleSheet("color: #a0a0a8; font-size: 12px; font-weight: 500;")
        page_row.addWidget(self.page_label)
        page_row.addStretch()

        self.next_btn = QtWidgets.QPushButton("Next >")
        self.next_btn.setEnabled(False)
        self.next_btn.clicked.connect(self._next_page)
        page_row.addWidget(self.next_btn)

        s_layout.addLayout(page_row)

        # 5. Action Bar
        action_row = QtWidgets.QHBoxLayout()
        self.selected_info = QtWidgets.QLabel("No icon selected.")
        self.selected_info.setStyleSheet("color: #a0a0a5; font-size: 12px;")
        action_row.addWidget(self.selected_info)
        action_row.addStretch()

        self.apply_btn = QtWidgets.QPushButton("Apply Selected Icon")
        self.apply_btn.setObjectName("primaryButton")
        self.apply_btn.setEnabled(False)
        self.apply_btn.clicked.connect(self._apply_current_selection)
        action_row.addWidget(self.apply_btn)

        s_layout.addLayout(action_row)
        layout.addWidget(search_box, stretch=1)

        return tab

    def _create_history_tab(self) -> QtWidgets.QWidget:
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header_row = QtWidgets.QHBoxLayout()
        title = QtWidgets.QLabel("Customized Items on this PC")
        title.setObjectName("titleLabel")
        header_row.addWidget(title)
        header_row.addStretch()

        refresh_btn = QtWidgets.QPushButton("Refresh History")
        refresh_btn.clicked.connect(self._refresh_history_table)
        header_row.addWidget(refresh_btn)
        layout.addLayout(header_row)

        self.history_table = QtWidgets.QTableWidget()
        self.history_table.setColumnCount(5)
        self.history_table.setHorizontalHeaderLabels(["Icon", "Name", "Target Path", "Date", "Actions"])
        self.history_table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        self.history_table.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        self.history_table.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
        self.history_table.horizontalHeader().setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeToContents)
        self.history_table.horizontalHeader().setSectionResizeMode(4, QtWidgets.QHeaderView.ResizeToContents)
        self.history_table.verticalHeader().setDefaultSectionSize(48)
        self.history_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        layout.addWidget(self.history_table)

        self._refresh_history_table()
        return tab

    def _set_target(self, path_str: str) -> None:
        self.current_target = path_str
        self.drop_area.set_target_display(path_str)
        self.restore_btn.setEnabled(True)

        target_name = Path(path_str).stem
        query = config.build_search_query(target_name)
        self.search_input.setText(query)
        self.perform_search()

    def _browse_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select Folder to Change Icon")
        if folder:
            self._set_target(folder)

    def _browse_shortcut(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Shortcut", "", "Shortcuts (*.lnk)")
        if file_path:
            self._set_target(file_path)

    def _browse_file(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Any File", "", "All Files (*.*)")
        if file_path:
            self._set_target(file_path)

    def perform_search(self, reset_page: bool = False) -> None:
        if reset_page:
            self.current_page = 1

        query = self.search_input.text().strip()
        if not query:
            return

        provider_name = self.provider_combo.currentData()
        self.search_status.setText(f"Searching for '{query}' (Page {self.current_page})...")
        self.search_btn.setEnabled(False)
        self.prev_btn.setEnabled(False)
        self.next_btn.setEnabled(False)
        self.page_label.setText(f"Page {self.current_page}")

        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.worker.wait(400)

        max_res = config.get("max_results", 30)
        self.worker = SearchWorker(query, provider_name, max_results=max_res, page=self.current_page)
        self.worker.resultsReady.connect(self._on_search_results)
        self.worker.errorOccurred.connect(self._on_search_error)
        self.worker.start()

    def _prev_page(self) -> None:
        if self.current_page > 1:
            self.current_page -= 1
            self.perform_search(reset_page=False)

    def _next_page(self) -> None:
        self.current_page += 1
        self.perform_search(reset_page=False)

    def _on_search_results(self, results: List[IconResult]) -> None:
        self.search_btn.setEnabled(True)
        self.prev_btn.setEnabled(self.current_page > 1)
        self.next_btn.setEnabled(len(results) >= config.get("max_results", 30))
        self.page_label.setText(f"Page {self.current_page}")

        if not results:
            self.search_status.setText("No icons found. Modify search query or switch provider.")
            self.grid.clear()
            return

        self.search_status.setText(f"Found {len(results)} icons (Page {self.current_page}).")
        self.grid.set_results(results)

    def _on_search_error(self, err: str) -> None:
        self.search_btn.setEnabled(True)
        self.prev_btn.setEnabled(self.current_page > 1)
        self.search_status.setText(f"Search error: {err}")

    def _on_icon_selected(self, result: IconResult) -> None:
        self.selected_result = result
        self.selected_info.setText(f"Selected: <b>{result.title}</b> ({result.source})")
        self.apply_btn.setEnabled(bool(self.current_target))

    def _on_icon_activated(self, result: IconResult) -> None:
        self._on_icon_selected(result)
        self._apply_current_selection()

    def _apply_current_selection(self) -> None:
        if not self.current_target:
            QMessageBox.warning(self, "No Target", "Please select a folder, file, or shortcut first.")
            return
        if not self.selected_result:
            QMessageBox.warning(self, "No Icon", "Please select an icon from the grid first.")
            return

        self.statusBar().showMessage("Downloading and applying icon...")
        QtWidgets.QApplication.processEvents()

        try:
            resolution = self.res_combo.currentData()
            target_stem = Path(self.current_target).stem
            ico_path = IconEngine.create_icon_for_target(
                image_data=self.selected_result.image_url,
                target_name=target_stem,
                resolution=resolution
            )

            success, msg = IconApplicator.apply_icon(self.current_target, str(ico_path))
            if success:
                history.add_entry(self.current_target, str(ico_path), title=self.selected_result.title)
                self.statusBar().showMessage(msg, 5000)
                QMessageBox.information(self, "Success", f"{msg}\n\nIcon saved to:\n{ico_path}")
                self._refresh_history_table()
            else:
                QMessageBox.critical(self, "Error", msg)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to apply icon:\n{e}")

    def _browse_local_icon(self) -> None:
        if not self.current_target:
            QMessageBox.warning(self, "No Target", "Please select a target folder/shortcut first.")
            return

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
                target_stem = Path(self.current_target).stem
                ico_path = IconEngine.create_icon_for_target(
                    image_data=file_path,
                    target_name=target_stem,
                    resolution=resolution
                )

            success, msg = IconApplicator.apply_icon(self.current_target, str(ico_path))
            if success:
                history.add_entry(self.current_target, str(ico_path), title=p.name)
                QMessageBox.information(self, "Success", msg)
                self._refresh_history_table()
            else:
                QMessageBox.critical(self, "Error", msg)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to set local icon:\n{e}")

    def _restore_current_target(self) -> None:
        if not self.current_target:
            return
        p = Path(self.current_target)
        reply = QMessageBox.question(
            self,
            "Restore Default Icon",
            f"Are you sure you want to restore the default Windows icon for:\n{p.name}?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                if p.is_dir():
                    IconApplicator.restore_folder_icon(str(p))
                elif p.suffix.lower() == ".lnk":
                    IconApplicator.restore_shortcut_icon(str(p))
                history.remove_entry(str(p))
                QMessageBox.information(self, "Success", "Default icon restored.")
                self._refresh_history_table()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to restore icon:\n{e}")

    def _refresh_history_table(self) -> None:
        entries = history.get_all()
        self.history_table.setRowCount(len(entries))

        for row, item in enumerate(entries):
            # Column 0: Icon Thumbnail
            icon_cell = QtWidgets.QLabel()
            icon_cell.setAlignment(Qt.AlignCenter)
            ico_p = item.get("ico_path", "")
            if os.path.exists(ico_p):
                pm = QtGui.QPixmap(ico_p).scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                icon_cell.setPixmap(pm)
            self.history_table.setCellWidget(row, 0, icon_cell)

            # Column 1: Name
            name_item = QtWidgets.QTableWidgetItem(item.get("target_name", ""))
            self.history_table.setItem(row, 1, name_item)

            # Column 2: Target Path
            path_item = QtWidgets.QTableWidgetItem(item.get("target_path", ""))
            self.history_table.setItem(row, 2, path_item)

            # Column 3: Date
            ts = item.get("timestamp", 0)
            date_str = time.strftime("%Y-%m-%d %H:%M", time.localtime(ts)) if ts else "-"
            date_item = QtWidgets.QTableWidgetItem(date_str)
            self.history_table.setItem(row, 3, date_item)

            # Column 4: Actions
            actions_widget = QtWidgets.QWidget()
            a_layout = QtWidgets.QHBoxLayout(actions_widget)
            a_layout.setContentsMargins(4, 2, 4, 2)
            a_layout.setSpacing(6)

            re_btn = QtWidgets.QPushButton("Change")
            re_btn.clicked.connect(self._make_rechange_callback(item.get("target_path", "")))
            a_layout.addWidget(re_btn)

            rst_btn = QtWidgets.QPushButton("Restore")
            rst_btn.setObjectName("dangerButton")
            rst_btn.clicked.connect(self._make_restore_callback(item.get("target_path", "")))
            a_layout.addWidget(rst_btn)

            self.history_table.setCellWidget(row, 4, actions_widget)

    def _make_rechange_callback(self, path_str: str):
        def on_rechange():
            if os.path.exists(path_str):
                self.tabs.setCurrentIndex(0)
                self._set_target(path_str)
            else:
                QMessageBox.warning(self, "Not Found", f"Path no longer exists:\n{path_str}")
        return on_rechange

    def _make_restore_callback(self, path_str: str):
        def on_restore():
            if not os.path.exists(path_str):
                history.remove_entry(path_str)
                self._refresh_history_table()
                return

            p = Path(path_str)
            if p.is_dir():
                IconApplicator.restore_folder_icon(path_str)
            elif p.suffix.lower() == ".lnk":
                IconApplicator.restore_shortcut_icon(path_str)
            history.remove_entry(path_str)
            self._refresh_history_table()
            QMessageBox.information(self, "Success", f"Default icon restored for:\n{p.name}")
        return on_restore

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        """Safely stops any ongoing search worker and image tasks before window closes."""
        self.grid.stop()
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.worker.wait(400)
        super().closeEvent(event)
        QtWidgets.QApplication.quit()
