"""
Modern Neumorphic Dark Theme Stylesheet for Windows Icon Changer.
Inspired by high-end design systems: Deep slate-navy surfaces (#141520),
rounded pill controls, bold modern typography, and vibrant violet accents (#7c5cfc).
"""

DARK_THEME_QSS = """
/* Global Styling */
QWidget {
    background-color: transparent;
    color: #e2e8f0;
    font-family: 'Segoe UI Variable Display', 'Segoe UI', 'Inter', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
    font-size: 13px;
    font-weight: 500;
    selection-background-color: #7c5cfc;
    selection-color: #ffffff;
}

/* Frameless Window Container */
QFrame#mainFrame {
    background-color: #161722;
    border: 1px solid #282b3c;
    border-radius: 20px;
}

/* Top Header Bar */
QFrame#headerBar {
    background-color: transparent;
    border: none;
    padding: 2px 4px;
}

QLabel#targetTitle {
    color: #ffffff;
    font-size: 14px;
    font-weight: 700;
}

/* Header Action Buttons (Gear, Hamburger, Close) */
QPushButton.headerBtn {
    background-color: #212332;
    color: #a2a5b8;
    border: 1px solid #2d3044;
    border-radius: 16px;
    padding: 6px;
    min-width: 32px;
    min-height: 32px;
    max-width: 32px;
    max-height: 32px;
}

QPushButton.headerBtn:hover {
    background-color: #2c2f44;
    border-color: #7c5cfc;
    color: #ffffff;
}

QPushButton.headerBtn:pressed {
    background-color: #1a1c28;
}

QPushButton#closeBtn {
    background-color: #261e24;
    border: 1px solid #3d252e;
    color: #ef4444;
    border-radius: 16px;
    min-width: 32px;
    min-height: 32px;
    max-width: 32px;
    max-height: 32px;
}

QPushButton#closeBtn:hover {
    background-color: #ef4444;
    border-color: #dc2626;
    color: #ffffff;
}

QPushButton#closeBtn:pressed {
    background-color: #b91c1c;
}

/* Search Bar Container */
QFrame#searchContainer {
    background-color: #1e202e;
    border: 1px solid #2c3044;
    border-radius: 22px;
    padding: 2px 6px;
}

QFrame#searchContainer:focus-within {
    border: 1px solid #7c5cfc;
}

QLineEdit#searchInput {
    background-color: transparent;
    color: #ffffff;
    border: none;
    padding: 8px 12px;
    font-size: 13px;
    font-weight: 600;
}

QLineEdit#searchInput:focus {
    outline: none;
}

/* Provider Icon Toggle Buttons (G, 8, API) */
QPushButton.providerToggle,
QPushButton#providerToggleWeb,
QPushButton#providerToggleIcons8,
QPushButton#providerToggleApi {
    background-color: #242738;
    color: #8e92a8;
    border: 1px solid #2e334a;
    border-radius: 15px;
    min-width: 30px;
    min-height: 30px;
    max-width: 30px;
    max-height: 30px;
    padding: 4px;
}

QPushButton.providerToggle:hover,
QPushButton#providerToggleWeb:hover,
QPushButton#providerToggleIcons8:hover,
QPushButton#providerToggleApi:hover {
    background-color: #2e324a;
    border-color: #7c5cfc;
    color: #ffffff;
}

QPushButton.providerToggle:checked,
QPushButton.providerToggle[checked="true"],
QPushButton#providerToggleWeb:checked,
QPushButton#providerToggleIcons8:checked,
QPushButton#providerToggleApi:checked {
    background-color: #7c5cfc;
    border-color: #9061f9;
    color: #ffffff;
}

QPushButton.providerToggle:checked:hover,
QPushButton#providerToggleWeb:checked:hover,
QPushButton#providerToggleIcons8:checked:hover,
QPushButton#providerToggleApi:checked:hover {
    background-color: #8b5cf6;
    border-color: #a78bfa;
    color: #ffffff;
}

/* Search Action Button */
QPushButton#searchIconBtn {
    background-color: #7c5cfc;
    color: #ffffff;
    border: 1px solid #9061f9;
    border-radius: 18px;
    min-width: 36px;
    min-height: 36px;
    max-width: 36px;
    max-height: 36px;
    padding: 6px;
}

QPushButton#searchIconBtn:hover {
    background-color: #8b5cf6;
    border-color: #a78bfa;
}

QPushButton#searchIconBtn:pressed {
    background-color: #6d28d9;
}

/* Compact Pagination Buttons */
QPushButton.pageArrowBtn {
    background-color: #212332;
    color: #ffffff;
    border: 1px solid #2d3044;
    border-radius: 15px;
    min-width: 30px;
    min-height: 30px;
    max-width: 30px;
    max-height: 30px;
    padding: 2px;
    font-size: 16px;
    font-weight: 700;
}

QPushButton.pageArrowBtn:hover {
    background-color: #2c2f44;
    border-color: #7c5cfc;
}

QPushButton.pageArrowBtn:disabled {
    background-color: #1a1c27;
    border-color: #222433;
    color: #4b4e64;
}

QLabel#pagePill {
    background-color: #7c5cfc;
    color: #ffffff;
    border-radius: 13px;
    padding: 4px 14px;
    font-size: 12px;
    font-weight: 700;
    min-width: 24px;
}

/* General Buttons */
QPushButton {
    background-color: #242738;
    color: #f1f5f9;
    border: 1px solid #2e334a;
    border-radius: 10px;
    padding: 8px 18px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: #2d3249;
    border-color: #7c5cfc;
    color: #ffffff;
}

QPushButton:pressed {
    background-color: #1c1e2c;
}

QPushButton:disabled {
    background-color: #1a1b26;
    color: #555870;
    border-color: #222433;
}

QPushButton#primaryButton {
    background-color: #7c5cfc;
    color: #ffffff;
    border: 1px solid #9061f9;
    font-weight: 700;
}

QPushButton#primaryButton:hover {
    background-color: #8b5cf6;
    border-color: #a78bfa;
}

QPushButton#dangerButton {
    background-color: #2a1b24;
    color: #f87171;
    border: 1px solid #4a2432;
    font-weight: 600;
}

QPushButton#dangerButton:hover {
    background-color: #ef4444;
    color: #ffffff;
    border-color: #dc2626;
}

/* Tabs */
QTabWidget::pane {
    border: 1px solid #282b3c;
    background-color: #161722;
    border-radius: 14px;
    top: -1px;
}

QTabBar::tab {
    background-color: #1e202e;
    color: #8b8ea4;
    padding: 10px 24px;
    border-top-left-radius: 12px;
    border-top-right-radius: 12px;
    margin-right: 4px;
    font-weight: 700;
    font-size: 13px;
    border: 1px solid transparent;
}

QTabBar::tab:hover {
    background-color: #252839;
    color: #ffffff;
}

QTabBar::tab:selected {
    background-color: #161722;
    color: #a78bfa;
    border: 1px solid #282b3c;
    border-bottom: 1px solid #161722;
}

/* Badges */
QLabel#badgeActive {
    background-color: #064e3b;
    color: #34d399;
    border: 1px solid #059669;
    border-radius: 10px;
    padding: 4px 10px;
    font-weight: 700;
    font-size: 11px;
}

QLabel#badgeInactive {
    background-color: #272a3b;
    color: #94a3b8;
    border: 1px solid #33384e;
    border-radius: 10px;
    padding: 4px 10px;
    font-weight: 700;
    font-size: 11px;
}

/* Scrollbars */
QScrollBar:vertical {
    border: none;
    background: transparent;
    width: 6px;
    margin: 4px 0 4px 0;
}

QScrollBar::handle:vertical {
    background: #33364c;
    min-height: 24px;
    border-radius: 3px;
}

QScrollBar::handle:vertical:hover {
    background: #7c5cfc;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
"""
