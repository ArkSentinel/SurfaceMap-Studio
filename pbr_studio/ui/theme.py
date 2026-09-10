"""
PBR Studio Modern Dark Theme & Stylesheet
Professional dark UI theme optimized for creative 3D and graphics tools.
"""

DARK_THEME = """
/* Global styling */
QWidget {
    background-color: #1a1b1e;
    color: #e4e5e7;
    font-family: "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    font-size: 13px;
    selection-background-color: #3b82f6;
    selection-color: #ffffff;
}

QMainWindow, QDialog {
    background-color: #141517;
}

/* ToolBar & Menu */
QMenuBar {
    background-color: #141517;
    border-bottom: 1px solid #2c2e33;
    padding: 2px 4px;
}
QMenuBar::item {
    background: transparent;
    padding: 6px 12px;
    border-radius: 4px;
}
QMenuBar::item:selected {
    background: #2c2e33;
}
QMenu {
    background-color: #1e1f23;
    border: 1px solid #373a40;
    border-radius: 6px;
    padding: 4px;
}
QMenu::item {
    padding: 6px 24px 6px 12px;
    border-radius: 4px;
}
QMenu::item:selected {
    background-color: #2563eb;
    color: #ffffff;
}
QMenu::separator {
    height: 1px;
    background: #2c2e33;
    margin: 4px 6px;
}

QToolBar {
    background-color: #18191c;
    border-bottom: 1px solid #27292e;
    spacing: 6px;
    padding: 4px 8px;
}

/* Tabs */
QTabWidget::pane {
    border: 1px solid #27292e;
    background-color: #18191c;
    border-radius: 6px;
}
QTabBar::tab {
    background: #1e1f23;
    color: #909296;
    padding: 7px 16px;
    margin-right: 2px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    font-weight: 500;
}
QTabBar::tab:selected {
    background: #25262b;
    color: #60a5fa;
    border-bottom: 2px solid #3b82f6;
}
QTabBar::tab:hover:!selected {
    background: #25262b;
    color: #c1c2c5;
}

/* Buttons */
QPushButton {
    background-color: #25262b;
    border: 1px solid #373a40;
    color: #e4e5e7;
    padding: 6px 14px;
    border-radius: 5px;
    font-weight: 500;
}
QPushButton:hover {
    background-color: #2c2e33;
    border-color: #494e57;
}
QPushButton:pressed {
    background-color: #1c1d20;
}
QPushButton:disabled {
    background-color: #18191c;
    color: #5c5f66;
    border-color: #25262b;
}

QPushButton#PrimaryButton {
    background-color: #2563eb;
    border: 1px solid #3b82f6;
    color: #ffffff;
    font-weight: 600;
}
QPushButton#PrimaryButton:hover {
    background-color: #1d4ed8;
    border-color: #60a5fa;
}
QPushButton#PrimaryButton:pressed {
    background-color: #1e40af;
}

/* Inputs & Combos */
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background-color: #202124;
    border: 1px solid #373a40;
    border-radius: 5px;
    padding: 5px 8px;
    color: #f1f3f5;
}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
    border: 1px solid #3b82f6;
    background-color: #25262b;
}
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 24px;
    border-left: 1px solid #373a40;
}
QComboBox QAbstractItemView {
    background-color: #1e1f23;
    border: 1px solid #373a40;
    selection-background-color: #2563eb;
    color: #f1f3f5;
    border-radius: 4px;
}

/* Sliders */
QSlider::groove:horizontal {
    border: 1px solid #2c2e33;
    height: 6px;
    background: #25262b;
    border-radius: 3px;
}
QSlider::sub-page:horizontal {
    background: #3b82f6;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background: #e4e5e7;
    border: 2px solid #3b82f6;
    width: 14px;
    margin-top: -5px;
    margin-bottom: -5px;
    border-radius: 7px;
}
QSlider::handle:horizontal:hover {
    background: #ffffff;
    border-color: #60a5fa;
    transform: scale(1.1);
}

/* Checkboxes & Radios */
QCheckBox, QRadioButton {
    spacing: 8px;
    color: #c1c2c5;
}
QCheckBox::indicator, QRadioButton::indicator {
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 1px solid #373a40;
    background-color: #202124;
}
QRadioButton::indicator {
    border-radius: 8px;
}
QCheckBox::indicator:checked, QRadioButton::indicator:checked {
    background-color: #2563eb;
    border-color: #3b82f6;
}

/* ScrollBars */
QScrollBar:vertical {
    border: none;
    background: #141517;
    width: 8px;
    border-radius: 4px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: #2c2e33;
    min-height: 20px;
    border-radius: 4px;
}
QScrollBar::handle:vertical:hover {
    background: #494e57;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QScrollBar:horizontal {
    border: none;
    background: #141517;
    height: 8px;
    border-radius: 4px;
}
QScrollBar::handle:horizontal {
    background: #2c2e33;
    min-width: 20px;
    border-radius: 4px;
}
QScrollBar::handle:horizontal:hover {
    background: #494e57;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

/* Splitter */
QSplitter::handle {
    background-color: #27292e;
}
QSplitter::handle:hover {
    background-color: #3b82f6;
}

/* GroupBox */
QGroupBox {
    font-weight: 600;
    border: 1px solid #2c2e33;
    border-radius: 6px;
    margin-top: 10px;
    padding-top: 14px;
    background-color: #18191c;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 10px;
    padding: 0 4px;
    color: #909296;
}

/* Status Bar */
QStatusBar {
    background-color: #141517;
    border-top: 1px solid #27292e;
    color: #909296;
    font-size: 12px;
}
"""
