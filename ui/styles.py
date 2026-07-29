"""Feuille de style QSS - thème sombre moderne pour l'application."""

ACCENT = "#5B8CFF"
ACCENT_HOVER = "#7AA2FF"
BG_DARK = "#14171F"
BG_PANEL = "#1B1F2A"
BG_ELEVATED = "#242938"
BORDER = "#2E3446"
TEXT_PRIMARY = "#E7E9F0"
TEXT_SECONDARY = "#9BA1B4"
DANGER = "#E55A5A"

STYLESHEET = f"""
QWidget {{
    background-color: {BG_DARK};
    color: {TEXT_PRIMARY};
    font-family: "Poppins";
    font-size: 13px;
}}

QMainWindow {{
    background-color: {BG_DARK};
}}

QLabel#Title {{
    font-size: 19px;
    font-weight: 600;
    color: {TEXT_PRIMARY};
}}

QLabel#Subtitle {{
    color: {TEXT_SECONDARY};
    font-size: 12px;
    font-weight: 400;
}}

QLabel#FieldLabel {{
    font-weight: 600;
    color: {TEXT_PRIMARY};
}}

QPushButton {{
    background-color: {BG_ELEVATED};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 8px 16px;
    color: {TEXT_PRIMARY};
}}
QPushButton:hover {{
    background-color: {BORDER};
}}
QPushButton:pressed {{
    background-color: {BG_PANEL};
}}

QPushButton#PrimaryButton {{
    background-color: {ACCENT};
    border: none;
    color: #0B0D12;
    font-weight: 600;
}}
QPushButton#PrimaryButton:hover {{
    background-color: {ACCENT_HOVER};
}}

QPushButton#DangerButton {{
    background-color: transparent;
    border: 1px solid {DANGER};
    color: {DANGER};
}}
QPushButton#DangerButton:hover {{
    background-color: {DANGER};
    color: #0B0D12;
}}

QLineEdit, QSpinBox, QComboBox, QKeySequenceEdit {{
    background-color: {BG_ELEVATED};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 6px 10px;
    color: {TEXT_PRIMARY};
}}
QLineEdit:focus, QSpinBox:focus, QComboBox:focus, QKeySequenceEdit:focus {{
    border: 1px solid {ACCENT};
}}

QComboBox::drop-down {{
    border: none;
    width: 24px;
}}

QTableWidget {{
    background-color: {BG_PANEL};
    border: 1px solid {BORDER};
    border-radius: 8px;
    gridline-color: {BORDER};
    selection-background-color: {ACCENT};
    selection-color: #0B0D12;
}}
QHeaderView::section {{
    background-color: {BG_ELEVATED};
    color: {TEXT_SECONDARY};
    padding: 8px;
    border: none;
    border-bottom: 1px solid {BORDER};
    font-weight: 600;
}}
QTableWidget::item {{
    padding: 6px;
}}

QScrollBar:vertical {{
    background: transparent;
    width: 10px;
}}
QScrollBar::handle:vertical {{
    background: {BORDER};
    border-radius: 5px;
    min-height: 24px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QStatusBar {{
    color: {TEXT_SECONDARY};
}}

QMenu {{
    background-color: {BG_ELEVATED};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 4px;
}}
QMenu::item {{
    padding: 6px 20px;
    border-radius: 4px;
}}
QMenu::item:selected {{
    background-color: {ACCENT};
    color: #0B0D12;
}}
"""
