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
            IconResult(title="Test 1", image_url="https://example.com/1.png", thumb_url="https://example.com/1.png", source="Test"),
            IconResult(title="Test 2", image_url="https://example.com/2.png", thumb_url="https://example.com/2.png", source="Test")
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
            picker = QuickPickerWindow(str(temp_dir))
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
            picker = QuickPickerWindow(str(temp_dir))
            self.assertEqual(picker.current_page, 1)
            picker._next_page()
            self.assertEqual(picker.current_page, 2)
            picker._prev_page()
            self.assertEqual(picker.current_page, 1)
            picker.close()
        finally:
            if temp_dir.exists():
                try:
                    temp_dir.rmdir()
                except OSError:
                    pass

if __name__ == "__main__":
    unittest.main()
