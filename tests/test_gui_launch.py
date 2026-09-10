"""
Test headless initialization of GUI components
"""
import os
import sys
import unittest

os.environ["QT_QPA_PLATFORM"] = "offscreen"

class TestGUILaunch(unittest.TestCase):
    def test_main_window_init(self):
        from PyQt6.QtWidgets import QApplication
        from pbr_studio.ui.main_window import MainWindow

        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        window = MainWindow()
        self.assertIsNotNone(window)
        self.assertEqual(window.windowTitle(), "SurfaceMap Studio - Generador de Mapas PBR y Superficies")
        window.close()


if __name__ == "__main__":
    unittest.main()
