import sys
import unittest
from pathlib import Path
from PyQt5 import QtCore, QtWidgets

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from icon_changer.ui.quick_picker import QuickPickerWindow
from icon_changer.ui.main_window import MainWindow
from icon_changer.ui.settings_tab import SettingsTab
from icon_changer.ui.widgets import IconCard, IconGrid
from icon_changer.providers.base import IconResult

app = QtWidgets.QApplication.instance()
if not app:
    app = QtWidgets.QApplication([])

class TestUIComponents(unittest.TestCase):

    def test_settings_tab(self):
        tab = SettingsTab()
        self.assertIsNotNone(tab.suffix_input.text())
        self.assertIsNotNone(tab.template_input.text())

    def test_icon_card_and_grid(self):
        grid = IconGrid()
        res = [
            IconResult(title="Test 1", image_url="", thumb_url="", source="Test"),
            IconResult(title="Test 2", image_url="", thumb_url="", source="Test")
        ]
        grid.set_results(res)
        self.assertEqual(len(grid.cards), 2)
        grid.set_selected_index(1)
        self.assertEqual(grid.selected_index, 1)
        grid.stop()

    def test_quick_picker_init(self):
        # Test QuickPicker with a dummy folder
        temp_dir = Path(root_dir) / "test_gui_folder"
        temp_dir.mkdir(exist_ok=True)
        try:
            picker = QuickPickerWindow(str(temp_dir), auto_search=False)
            self.assertEqual(picker.target_name, "test_gui_folder")
            self.assertIn("test_gui_folder", picker.search_input.text())
            picker.close()
        finally:
            if temp_dir.exists():
                try:
                    temp_dir.rmdir()
                except OSError:
                    pass

    def test_main_window_init(self):
        win = MainWindow()
        self.assertEqual(win.tabs.count(), 3)
        self.assertEqual(win.current_page, 1)

    def test_quick_picker_pagination(self):
        temp_dir = Path(root_dir) / "test_gui_folder_page"
        temp_dir.mkdir(exist_ok=True)
        try:
            picker = QuickPickerWindow(str(temp_dir), auto_search=False)
            self.assertEqual(picker.current_page, 1)
            picker.current_page = 2
            self.assertEqual(picker.current_page, 2)
            picker.current_page = 1
            self.assertEqual(picker.current_page, 1)
            picker.close()
        finally:
            if temp_dir.exists():
                try:
                    temp_dir.rmdir()
                except OSError:
                    pass

    def test_animated_hamburger_menu(self):
        from icon_changer.ui.hamburger_menu import AnimatedHamburgerMenu
        menu = AnimatedHamburgerMenu(current_res=256)
        self.assertEqual(menu.res_combo.currentData(), 256)
        menu.close()

    def test_success_checkmark_overlay(self):
        from icon_changer.ui.animated_success import SuccessCheckmarkOverlay
        overlay = SuccessCheckmarkOverlay()
        overlay.play()
        self.assertTrue(overlay.anim.state() == QtCore.QAbstractAnimation.Running or overlay.isVisible())
        overlay.anim.stop()

    def test_exe_icon_extraction(self):
        from icon_changer.core.icon_engine import IconEngine
        # Test extraction from Windows notepad.exe or explorer.exe
        target = r"C:\Windows\explorer.exe"
        if Path(target).exists():
            data = IconEngine.extract_file_icon_bytes(target)
            self.assertIsNotNone(data)
            self.assertGreater(len(data), 100)

    def test_provider_toggle(self):
        temp_dir = Path(root_dir) / "test_gui_provider"
        temp_dir.mkdir(exist_ok=True)
        try:
            picker = QuickPickerWindow(str(temp_dir), auto_search=False)
            # Test switching to Icons8
            picker.btn_icons8.click()
            self.assertTrue(picker.btn_icons8.isChecked())
            self.assertFalse(picker.btn_web.isChecked())
            self.assertEqual(picker.current_provider, "icons8")

            # Test switching back to Google/Web
            picker.btn_web.click()
            self.assertTrue(picker.btn_web.isChecked())
            self.assertFalse(picker.btn_icons8.isChecked())
            self.assertEqual(picker.current_provider, "web")

            # Test switching to API
            picker.btn_api.click()
            self.assertTrue(picker.btn_api.isChecked())
            self.assertEqual(picker.current_provider, "google_api")
            picker.close()
        finally:
            if temp_dir.exists():
                try:
                    temp_dir.rmdir()
                except OSError:
                    pass

    def test_grid_centering(self):
        grid = IconGrid()
        # Verify horizontal center alignment is set
        align = grid.flow_layout.alignment()
        self.assertTrue(bool(align & QtCore.Qt.AlignHCenter))
        cols = grid.calculate_columns()
        self.assertGreaterEqual(cols, 2)
        grid.stop()

if __name__ == "__main__":
    unittest.main()
