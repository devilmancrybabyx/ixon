"""
Modern Dark Theme Stylesheet for Windows Icon Changer.
Fluent Design-inspired colors, rounded borders, and sleek controls.
"""

DARK_THEME_QSS = """
/* Global Window */
QWidget {
    background-color: #1a1a1c;
    color: #e0e0e0;
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
    font-size: 13px;
    selection-background-color: #0078d4;
    selection-color: #ffffff;
}

/* Main Window & Dialogs */
QMainWindow, QDialog {
    background-color: #141416;
}

/* Tab Widget */
QTabWidget::pane {
    border: 1px solid #2d2d32;
    background-color: #1a1a1c;
    border-radius: 8px;
    top: -1px;
}

QTabBar::tab {
    background-color: #212124;
    color: #a0a0a5;
    padding: 10px 24px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    margin-right: 4px;
    font-weight: 600;
    border: 1px solid transparent;
}

QTabBar::tab:hover {
    background-color: #2a2a2f;
    color: #ffffff;
}

QTabBar::tab:selected {
    background-color: #1a1a1c;
    color: #38a6ff;
    border: 1px solid #2d2d32;
    border-bottom: 1px solid #1a1a1c;
}

/* Inputs & Search Bars */
QLineEdit {
    background-color: #242428;
    color: #ffffff;
    border: 1px solid #38383e;
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 13px;
}

QLineEdit:focus {
    border: 1px solid #0078d4;
    background-color: #28282e;
}

/* Buttons */
QPushButton {
    background-color: #2b2b30;
    color: #f0f0f0;
    border: 1px solid #3c3c44;
    border-radius: 6px;
    padding: 7px 16px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #36363d;
    border-color: #4f4f5a;
    color: #ffffff;
}

QPushButton:pressed {
    background-color: #202024;
}

QPushButton:disabled {
    background-color: #1e1e22;
    color: #606066;
    border-color: #28282c;
}

/* Accent Button */
QPushButton#primaryButton {
    background-color: #0078d4;
    color: #ffffff;
    border: 1px solid #1084d8;
    font-weight: 600;
}

QPushButton#primaryButton:hover {
    background-color: #198ae6;
    border-color: #2b95ec;
}

QPushButton#primaryButton:pressed {
    background-color: #0066b3;
}

/* Danger / Reset Button */
QPushButton#dangerButton {
    background-color: #3a1e22;
    color: #ff7b88;
    border: 1px solid #5a2a30;
}

QPushButton#dangerButton:hover {
    background-color: #4a242a;
    color: #ffa1ab;
}

/* Combo Box */
QComboBox {
    background-color: #242428;
    color: #ffffff;
    border: 1px solid #38383e;
    border-radius: 6px;
    padding: 6px 12px;
    min-width: 100px;
}

QComboBox:hover {
    border-color: #4f4f5a;
}

QComboBox:on {
    border-color: #0078d4;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 24px;
    border-left: none;
}

QComboBox QAbstractItemView {
    background-color: #242428;
    color: #ffffff;
    border: 1px solid #38383e;
    selection-background-color: #0078d4;
    selection-color: #ffffff;
    padding: 4px;
}

/* Scroll Area */
QScrollArea {
    border: none;
    background-color: transparent;
}

QScrollBar:vertical {
    border: none;
    background: #18181a;
    width: 8px;
    border-radius: 4px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background: #333338;
    min-height: 24px;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background: #4a4a52;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* Labels */
QLabel {
    color: #d0d0d5;
}

QLabel#titleLabel {
    font-size: 16px;
    font-weight: 700;
    color: #ffffff;
}

QLabel#subtitleLabel {
    font-size: 12px;
    color: #8c8c94;
}

/* Status Badges */
QLabel#badgeActive {
    background-color: #143522;
    color: #4ee085;
    border: 1px solid #205c36;
    border-radius: 12px;
    padding: 3px 10px;
    font-size: 11px;
    font-weight: 600;
}

QLabel#badgeInactive {
    background-color: #382414;
    color: #e0984e;
    border: 1px solid #5c3820;
    border-radius: 12px;
    padding: 3px 10px;
    font-size: 11px;
    font-weight: 600;
}

/* Group Boxes / Frames */
QGroupBox {
    border: 1px solid #2d2d32;
    border-radius: 8px;
    margin-top: 18px;
    padding-top: 14px;
    font-weight: 600;
    color: #a0a0a5;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    left: 12px;
}

/* Progress Bar */
QProgressBar {
    border: 1px solid #2d2d32;
    border-radius: 4px;
    text-align: center;
    background-color: #202024;
    height: 10px;
}

QProgressBar::chunk {
    background-color: #0078d4;
    border-radius: 3px;
}
"""
