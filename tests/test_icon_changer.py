import os
import sys
import unittest
from pathlib import Path
from PIL import Image

# Add root directory to sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from icon_changer.core.config import ConfigManager, DEFAULT_CONFIG
from icon_changer.core.icon_engine import IconEngine, STANDARD_ICO_SIZES
from icon_changer.core.icon_applicator import IconApplicator
from icon_changer.core.shell_manager import ShellManager
from icon_changer.core.history import HistoryManager
from icon_changer.providers import search_icons, get_provider

class TestIconChanger(unittest.TestCase):

    def setUp(self):
        self.test_dir = root_dir / "test_sandbox"
        self.test_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        # Clean up test sandbox
        if self.test_dir.exists():
            import shutil
            # Remove read-only attribute if folder had it
            import ctypes
            ctypes.windll.kernel32.SetFileAttributesW(str(self.test_dir), 0x80)
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_config_query_builder(self):
        cfg = ConfigManager()
        query = cfg.build_search_query("gta v", custom_suffix="icon png")
        self.assertEqual(query, "gta v icon png")

        query2 = cfg.build_search_query("Steam", custom_suffix="logo transparent")
        self.assertEqual(query2, "Steam logo transparent")

    def test_ico_generation(self):
        # Create a test RGBA PNG
        img = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
        # Add a colored square in center
        for x in range(32, 96):
            for y in range(32, 96):
                img.putpixel((x, y), (50, 150, 250, 200))

        png_path = self.test_dir / "test.png"
        img.save(png_path, format="PNG")

        ico_path = self.test_dir / "test.ico"
        result_ico = IconEngine.convert_to_ico(png_path, ico_path, resolution=256)
        
        self.assertTrue(result_ico.exists())
        self.assertGreater(result_ico.stat().st_size, 1000)

        # Verify ICO can be opened and contains sizes
        with Image.open(result_ico) as ico_img:
            self.assertEqual(ico_img.format, "ICO")

    def test_folder_customization(self):
        # Create dummy folder
        sub_folder = self.test_dir / "sample_folder"
        sub_folder.mkdir(parents=True, exist_ok=True)

        # Create dummy ico
        ico_path = self.test_dir / "sample.ico"
        img = Image.new("RGBA", (64, 64), (255, 0, 0, 255))
        img.save(ico_path, format="ICO")

        # Apply icon
        success, msg = IconApplicator.apply_icon(str(sub_folder), str(ico_path))
        self.assertTrue(success)
        
        desktop_ini = sub_folder / "desktop.ini"
        self.assertTrue(desktop_ini.exists())
        
        with open(desktop_ini, "r", encoding="utf-16le") as f:
            content = f.read()
            self.assertIn("IconResource=", content)
            self.assertIn(str(ico_path), content)

        # Restore folder icon
        restored = IconApplicator.restore_folder_icon(str(sub_folder))
        self.assertTrue(restored)
        self.assertFalse(desktop_ini.exists())

    def test_shell_manager_registry(self):
        # Test registry install and uninstall
        ok_install, msg_install = ShellManager.install(menu_label="Test Change Icon")
        self.assertTrue(ok_install)
        self.assertTrue(ShellManager.is_installed())

        ok_uninstall, msg_uninstall = ShellManager.uninstall()
        self.assertTrue(ok_uninstall)
        self.assertFalse(ShellManager.is_installed())

    def test_icons8_provider(self):
        provider = get_provider("icons8")
        results = provider.search("folder", max_results=5)
        self.assertIsInstance(results, list)
        if results:
            self.assertTrue(results[0].image_url.startswith("http"))
            self.assertEqual(results[0].source, "Icons8")

    def test_web_provider(self):
        provider = get_provider("web")
        results = provider.search("gta v icon png", max_results=5)
        self.assertIsInstance(results, list)
        if results:
            self.assertTrue(results[0].image_url.startswith("http"))
            self.assertEqual(results[0].source, "Web")

if __name__ == "__main__":
    unittest.main()
