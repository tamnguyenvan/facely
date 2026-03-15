"""Theme and styling for Facely UI using Qt."""

COLORS = {
    # Backgrounds
    "bg_root": "#0D0F11",
    "bg_panel": "#141618",
    "bg_card": "#1C1F23",
    "bg_elevated": "#23272C",
    
    # Borders
    "border": "#2A2F36",
    "border_focus": "#00B4D8",
    
    # Text
    "text_primary": "#E8EDF2",
    "text_secondary": "#7A8899",
    "text_muted": "#4A5568",
    "text_accent": "#00B4D8",
    
    # Status
    "success": "#2DD4BF",
    "warning": "#F59E0B",
    "danger": "#EF4444",
    "info": "#60A5FA",
    
    # Interactive
    "btn_primary": "#00B4D8",
    "btn_primary_hover": "#0096B5",
    "btn_danger": "#DC2626",
    "btn_danger_hover": "#B91C1C",
    "btn_surface": "#23272C",
    "btn_surface_hover": "#2D3340",
    
    # Camera overlay
    "bbox_match": "#2DD4BF",
    "bbox_unknown": "#EF4444",
    "label_bg": "#000000",
}

FONTS = {
    "display": ("Segoe UI", 13, "bold"),
    "label": ("Segoe UI", 11),
    "small": ("Segoe UI", 9),
    "mono": ("Consolas", 11),
    "mono_large": ("Consolas", 14),
    "status": ("Consolas", 10),
}

SPACING = {
    "xs": 4,
    "sm": 8,
    "md": 12,
    "lg": 20,
    "xl": 32,
}


def get_stylesheet() -> str:
    """Get Qt stylesheet for the application."""
    return f"""
    QMainWindow {{
        background-color: {COLORS['bg_root']};
    }}
    
    QWidget {{
        background-color: {COLORS['bg_panel']};
        color: {COLORS['text_primary']};
        font-family: 'Segoe UI';
        font-size: 11pt;
    }}
    
    QPushButton {{
        background-color: {COLORS['btn_surface']};
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['border']};
        border-radius: 4px;
        padding: 8px 16px;
        font-size: 11pt;
    }}
    
    QPushButton:hover {{
        background-color: {COLORS['btn_surface_hover']};
    }}
    
    QPushButton:pressed {{
        background-color: {COLORS['bg_elevated']};
    }}
    
    QPushButton#primaryButton {{
        background-color: {COLORS['btn_primary']};
        color: #000000;
        font-weight: bold;
    }}
    
    QPushButton#primaryButton:hover {{
        background-color: {COLORS['btn_primary_hover']};
    }}
    
    QPushButton#dangerButton {{
        background-color: {COLORS['btn_danger']};
        color: #FFFFFF;
    }}
    
    QPushButton#dangerButton:hover {{
        background-color: {COLORS['btn_danger_hover']};
    }}
    
    QLineEdit {{
        background-color: {COLORS['bg_elevated']};
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['border']};
        border-radius: 4px;
        padding: 6px;
        font-family: 'Consolas';
        font-size: 11pt;
    }}
    
    QLineEdit:focus {{
        border: 1px solid {COLORS['border_focus']};
    }}
    
    QComboBox {{
        background-color: {COLORS['bg_elevated']};
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['border']};
        border-radius: 4px;
        padding: 6px;
        font-family: 'Consolas';
        font-size: 11pt;
    }}
    
    QComboBox:hover {{
        border: 1px solid {COLORS['border_focus']};
    }}
    
    QComboBox::drop-down {{
        border: none;
        width: 20px;
    }}
    
    QComboBox::down-arrow {{
        image: none;
        border-left: 4px solid transparent;
        border-right: 4px solid transparent;
        border-top: 6px solid {COLORS['text_primary']};
        margin-right: 6px;
    }}
    
    QComboBox QAbstractItemView {{
        background-color: {COLORS['bg_elevated']};
        color: {COLORS['text_primary']};
        selection-background-color: {COLORS['btn_primary']};
        border: 1px solid {COLORS['border']};
    }}
    
    QLabel {{
        background-color: transparent;
        color: {COLORS['text_primary']};
    }}
    
    QLabel#mutedLabel {{
        color: {COLORS['text_muted']};
    }}
    
    QLabel#accentLabel {{
        color: {COLORS['text_accent']};
        font-family: 'Consolas';
    }}
    
    QLabel#titleLabel {{
        font-size: 13pt;
        font-weight: bold;
    }}
    
    QTreeWidget {{
        background-color: {COLORS['bg_card']};
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['border']};
        border-radius: 4px;
        alternate-background-color: {COLORS['bg_panel']};
    }}
    
    QTreeWidget::item {{
        padding: 4px;
    }}
    
    QTreeWidget::item:selected {{
        background-color: {COLORS['bg_elevated']};
        color: {COLORS['text_accent']};
    }}
    
    QTreeWidget::item:hover {{
        background-color: {COLORS['btn_surface']};
    }}
    
    QHeaderView::section {{
        background-color: {COLORS['bg_panel']};
        color: {COLORS['text_secondary']};
        padding: 6px;
        border: none;
        border-bottom: 1px solid {COLORS['border']};
        font-size: 9pt;
    }}
    
    QScrollBar:vertical {{
        background-color: {COLORS['bg_panel']};
        width: 12px;
        border-radius: 6px;
    }}
    
    QScrollBar::handle:vertical {{
        background-color: {COLORS['bg_elevated']};
        border-radius: 6px;
        min-height: 20px;
    }}
    
    QScrollBar::handle:vertical:hover {{
        background-color: {COLORS['btn_surface']};
    }}
    
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    
    QProgressBar {{
        background-color: {COLORS['bg_elevated']};
        border: none;
        border-radius: 2px;
        text-align: center;
        height: 4px;
    }}
    
    QProgressBar::chunk {{
        background-color: {COLORS['success']};
        border-radius: 2px;
    }}
    
    QFrame#cardFrame {{
        background-color: {COLORS['bg_card']};
        border: 1px solid {COLORS['border']};
        border-radius: 6px;
    }}
    
    QFrame#panelFrame {{
        background-color: {COLORS['bg_panel']};
        border: none;
    }}
    """
