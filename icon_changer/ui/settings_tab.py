import os
import shutil
from pathlib import Path
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMessageBox

from icon_changer.core.config import config, ICONS_DIR, CACHE_DIR
from icon_changer.core.shell_manager import ShellManager
from icon_changer.core.icon_applicator import IconApplicator
from icon_changer.core.permissions import PermissionManager

class SettingsTab(QtWidgets.QWidget):
    """Configuration interface for context menu, administrator permissions, search templates, providers, and cache."""

    def __init__(self, parent: QtWidgets.QWidget = None) -> None:
        super().__init__(parent)
        self._setup_ui()
        self.load_settings()

    def _setup_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        container = QtWidgets.QWidget()
        c_layout = QtWidgets.QVBoxLayout(container)
        c_layout.setSpacing(18)

        # --- 1. Context Menu Integration ---
        ctx_group = QtWidgets.QGroupBox("Windows Context Menu Integration")
        ctx_layout = QtWidgets.QVBoxLayout(ctx_group)
        ctx_layout.setSpacing(10)

        status_row = QtWidgets.QHBoxLayout()
        status_row.addWidget(QtWidgets.QLabel("Integration Status:"))
        self.ctx_badge = QtWidgets.QLabel()
        status_row.addWidget(self.ctx_badge)
        status_row.addStretch()

        self.install_ctx_btn = QtWidgets.QPushButton("Install to Context Menu")
        self.install_ctx_btn.setObjectName("primaryButton")
        self.install_ctx_btn.clicked.connect(self._toggle_context_menu)
        status_row.addWidget(self.install_ctx_btn)
        ctx_layout.addLayout(status_row)

        desc_label = QtWidgets.QLabel(
            "Enables right-clicking any Folder, File, or Shortcut (.lnk) in Windows Explorer "
            "to open the quick 'Change Icon' picker."
        )
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #8c8c94; font-size: 11px;")
        ctx_layout.addWidget(desc_label)

        c_layout.addWidget(ctx_group)

        # --- 2. Administrator & Full Permission Settings ---
        perm_group = QtWidgets.QGroupBox("Administrator & Full Permissions")
        perm_layout = QtWidgets.QVBoxLayout(perm_group)
        perm_layout.setSpacing(10)

        perm_status_row = QtWidgets.QHBoxLayout()
        perm_status_row.addWidget(QtWidgets.QLabel("Current Session Privilege:"))
        self.perm_status_badge = QtWidgets.QLabel()
        perm_status_row.addWidget(self.perm_status_badge)
        perm_status_row.addStretch()

        self.relaunch_admin_btn = QtWidgets.QPushButton("Relaunch as Administrator")
        self.relaunch_admin_btn.clicked.connect(self._relaunch_as_admin)
        perm_status_row.addWidget(self.relaunch_admin_btn)
        perm_layout.addLayout(perm_status_row)

        # Full Permission Checkbox
        self.admin_checkbox = QtWidgets.QCheckBox(
            "Always run Icon Changer and Context Menu with Full Administrator Permissions"
        )
        self.admin_checkbox.setStyleSheet("font-weight: 600; color: #ffffff;")
        self.admin_checkbox.toggled.connect(self._on_admin_permission_toggled)
        perm_layout.addWidget(self.admin_checkbox)

        perm_desc = QtWidgets.QLabel(
            "Registers an official Windows Compatibility flag (~ RUNASADMIN) and UAC shield on the context menu. "
            "Guarantees unrestricted permissions to customize Windows protected folders, system directories, "
            "and Public Desktop shortcuts (e.g. C:\\Users\\Public\\Desktop) without access denied errors."
        )
        perm_desc.setWordWrap(True)
        perm_desc.setStyleSheet("color: #8c8c94; font-size: 11px;")
        perm_layout.addWidget(perm_desc)

        c_layout.addWidget(perm_group)

        # --- 3. Search & Template Settings ---
        search_group = QtWidgets.QGroupBox("Search Options & Query Customization")
        search_layout = QtWidgets.QFormLayout(search_group)
        search_layout.setSpacing(12)
        search_layout.setLabelAlignment(Qt.AlignLeft)

        # Search Suffix
        self.suffix_input = QtWidgets.QLineEdit()
        self.suffix_input.setPlaceholderText("e.g. icon png, transparent icon, logo png")
        suffix_help = QtWidgets.QLabel("Appended to the target name. Example: Searching 'gta v' + 'icon png' -> 'gta v icon png'.")
        suffix_help.setStyleSheet("color: #8c8c94; font-size: 11px;")
        suffix_vbox = QtWidgets.QVBoxLayout()
        suffix_vbox.addWidget(self.suffix_input)
        suffix_vbox.addWidget(suffix_help)
        search_layout.addRow("Search Suffix:", suffix_vbox)

        # Template
        self.template_input = QtWidgets.QLineEdit()
        self.template_input.setPlaceholderText("{name} {suffix}")
        template_help = QtWidgets.QLabel("Format: {name} will be replaced by folder/file name, {suffix} by the suffix above.")
        template_help.setStyleSheet("color: #8c8c94; font-size: 11px;")
        template_vbox = QtWidgets.QVBoxLayout()
        template_vbox.addWidget(self.template_input)
        template_vbox.addWidget(template_help)
        search_layout.addRow("Query Template:", template_vbox)

        # Default Provider
        self.provider_combo = QtWidgets.QComboBox()
        self.provider_combo.addItem("Google & Web Images (Direct Transparent PNG)", "web")
        self.provider_combo.addItem("Icons8 Icon Library (Millions of Clean Icons)", "icons8")
        self.provider_combo.addItem("Google Custom Search JSON API", "google_api")
        search_layout.addRow("Default Provider:", self.provider_combo)

        # Default Resolution
        self.res_combo = QtWidgets.QComboBox()
        self.res_combo.addItem("256x256 (Extra Large / Crisp - Recommended)", 256)
        self.res_combo.addItem("128x128 (Large)", 128)
        self.res_combo.addItem("96x96 (Medium-Large)", 96)
        self.res_combo.addItem("64x64 (Medium)", 64)
        self.res_combo.addItem("48x48 (Standard)", 48)
        self.res_combo.addItem("32x32 (Compact)", 32)
        self.res_combo.addItem("16x16 (Small)", 16)
        self.res_combo.addItem("Multi-Size .ICO (All Explorer Views)", "multi")
        search_layout.addRow("Default Resolution:", self.res_combo)

        c_layout.addWidget(search_group)

        # --- 4. Google Custom Search API (Optional) ---
        api_group = QtWidgets.QGroupBox("Google Custom Search API Credentials (Optional)")
        api_layout = QtWidgets.QFormLayout(api_group)
        api_layout.setSpacing(10)

        self.api_key_input = QtWidgets.QLineEdit()
        self.api_key_input.setEchoMode(QtWidgets.QLineEdit.Password)
        self.api_key_input.setPlaceholderText("Paste your Google Cloud API Key...")
        api_layout.addRow("API Key:", self.api_key_input)

        self.cx_input = QtWidgets.QLineEdit()
        self.cx_input.setPlaceholderText("Paste your Search Engine ID (CX)...")
        api_layout.addRow("Search Engine ID (CX):", self.cx_input)

        api_note = QtWidgets.QLabel(
            "Optional: If provided, enables official Google Images API queries (100 free queries/day). "
            "Without this, the app uses direct web transparent image search and Icons8 automatically."
        )
        api_note.setWordWrap(True)
        api_note.setStyleSheet("color: #8c8c94; font-size: 11px;")
        api_layout.addRow("", api_note)

        c_layout.addWidget(api_group)

        # --- 5. Cache & Maintenance ---
        cache_group = QtWidgets.QGroupBox("Storage & Icon Cache")
        cache_layout = QtWidgets.QHBoxLayout(cache_group)

        self.cache_stats_label = QtWidgets.QLabel("Calculating storage...")
        cache_layout.addWidget(self.cache_stats_label)
        cache_layout.addStretch()

        self.open_icons_btn = QtWidgets.QPushButton("Open Icons Folder")
        self.open_icons_btn.clicked.connect(self._open_icons_folder)
        cache_layout.addWidget(self.open_icons_btn)

        self.clear_cache_btn = QtWidgets.QPushButton("Clear Cache")
        self.clear_cache_btn.clicked.connect(self._clear_cache)
        cache_layout.addWidget(self.clear_cache_btn)

        self.refresh_shell_btn = QtWidgets.QPushButton("Refresh Shell Cache")
        self.refresh_shell_btn.clicked.connect(self._refresh_shell_cache)
        cache_layout.addWidget(self.refresh_shell_btn)

        c_layout.addWidget(cache_group)

        # --- Save Button ---
        btn_row = QtWidgets.QHBoxLayout()
        btn_row.addStretch()
        self.save_btn = QtWidgets.QPushButton("Save Settings")
        self.save_btn.setObjectName("primaryButton")
        self.save_btn.clicked.connect(self.save_settings)
        btn_row.addWidget(self.save_btn)
        c_layout.addLayout(btn_row)

        scroll.setWidget(container)
        layout.addWidget(scroll)

    def load_settings(self) -> None:
        self.suffix_input.setText(config.get("search_suffix", "icon png"))
        self.template_input.setText(config.get("search_template", "{name} {suffix}"))

        prov = config.get("default_provider", "web")
        idx = self.provider_combo.findData(prov)
        if idx >= 0:
            self.provider_combo.setCurrentIndex(idx)

        res = config.get("icon_resolution", 256)
        res_idx = self.res_combo.findData(res)
        if res_idx >= 0:
            self.res_combo.setCurrentIndex(res_idx)

        self.api_key_input.setText(config.get("google_api_key", ""))
        self.cx_input.setText(config.get("google_cx", ""))

        # Admin permission state
        full_perm = PermissionManager.is_full_permission_enabled() or config.get("run_as_admin", False)
        self.admin_checkbox.blockSignals(True)
        self.admin_checkbox.setChecked(full_perm)
        self.admin_checkbox.blockSignals(False)

        self._update_admin_status()
        self._update_context_menu_status()
        self._update_cache_stats()

    def _update_admin_status(self) -> None:
        is_admin = PermissionManager.is_running_as_admin()
        if is_admin:
            self.perm_status_badge.setText(" ADMINISTRATOR (ELEVATED) ")
            self.perm_status_badge.setObjectName("badgeActive")
            self.relaunch_admin_btn.setEnabled(False)
            self.relaunch_admin_btn.setText("Already Elevated")
        else:
            self.perm_status_badge.setText(" STANDARD USER ")
            self.perm_status_badge.setObjectName("badgeInactive")
            self.relaunch_admin_btn.setEnabled(True)
            self.relaunch_admin_btn.setText("Relaunch as Administrator")

        self.perm_status_badge.setStyleSheet(self.perm_status_badge.styleSheet())

    def _on_admin_permission_toggled(self, checked: bool) -> None:
        ok, msg = PermissionManager.set_full_permission(checked)
        config.set("run_as_admin", checked)
        if ok:
            QMessageBox.information(self, "Permissions Updated", msg)
        else:
            QMessageBox.warning(self, "Warning", msg)
            self.admin_checkbox.blockSignals(True)
            self.admin_checkbox.setChecked(not checked)
            self.admin_checkbox.blockSignals(False)

    def _relaunch_as_admin(self) -> None:
        reply = QMessageBox.question(
            self,
            "Relaunch as Administrator",
            "This will close the current session and request Windows Administrator elevation.\nProceed?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            PermissionManager.relaunch_as_admin()

    def _update_context_menu_status(self) -> None:
        installed = ShellManager.is_installed()
        if installed:
            self.ctx_badge.setText(" ACTIVE (INSTALLED) ")
            self.ctx_badge.setObjectName("badgeActive")
            self.install_ctx_btn.setText("Uninstall Context Menu")
            self.install_ctx_btn.setObjectName("dangerButton")
        else:
            self.ctx_badge.setText(" NOT INSTALLED ")
            self.ctx_badge.setObjectName("badgeInactive")
            self.install_ctx_btn.setText("Install to Context Menu")
            self.install_ctx_btn.setObjectName("primaryButton")

        self.ctx_badge.setStyleSheet(self.ctx_badge.styleSheet())
        self.install_ctx_btn.setStyleSheet(self.install_ctx_btn.styleSheet())

    def _toggle_context_menu(self) -> None:
        if ShellManager.is_installed():
            ok, msg = ShellManager.uninstall()
            if ok:
                QMessageBox.information(self, "Success", msg)
            else:
                QMessageBox.warning(self, "Warning", msg)
        else:
            ok, msg = ShellManager.install(menu_label=config.get("context_menu_label", "Change Icon"))
            if ok:
                QMessageBox.information(self, "Success", msg)
            else:
                QMessageBox.warning(self, "Warning", msg)
        self._update_context_menu_status()

    def _update_cache_stats(self) -> None:
        try:
            ico_count = len(list(ICONS_DIR.glob("*.ico")))
            cache_files = list(CACHE_DIR.glob("*.*"))
            cache_size_mb = sum(f.stat().st_size for f in cache_files) / (1024 * 1024)
            self.cache_stats_label.setText(f"{ico_count} icons saved | {len(cache_files)} cached ({cache_size_mb:.1f} MB)")
        except Exception:
            self.cache_stats_label.setText("Icon storage active")

    def _open_icons_folder(self) -> None:
        os.startfile(str(ICONS_DIR))

    def _clear_cache(self) -> None:
        reply = QMessageBox.question(
            self,
            "Clear Cache",
            "This will delete temporary image downloads from cache. Your customized folder icons will remain safe.\nProceed?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            for item in CACHE_DIR.glob("*.*"):
                try:
                    item.unlink()
                except Exception:
                    pass
            self._update_cache_stats()
            QMessageBox.information(self, "Success", "Cache cleared successfully.")

    def _refresh_shell_cache(self) -> None:
        IconApplicator.notify_shell()
        QMessageBox.information(self, "Shell Notified", "Windows Explorer icon cache refresh signal broadcasted.")

    def save_settings(self) -> None:
        config.set("search_suffix", self.suffix_input.text().strip() or "icon png")
        config.set("search_template", self.template_input.text().strip() or "{name} {suffix}")
        config.set("default_provider", self.provider_combo.currentData())
        config.set("icon_resolution", self.res_combo.currentData())
        config.set("google_api_key", self.api_key_input.text().strip())
        config.set("google_cx", self.cx_input.text().strip())

        QMessageBox.information(self, "Saved", "Settings updated successfully!")
