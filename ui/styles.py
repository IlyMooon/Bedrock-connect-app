"""Modern Phenomenon Studio / DailyMe Inspired Theme for Bedrock DirectConnect."""

DARK_THEME_QSS = """
/* Global Window & Fonts */
QMainWindow, QDialog, QWidget {
    background-color: #0c1017;
    color: #e2e8f0;
    font-family: "Helvetica Neue", Arial;
    font-size: 13px;
}

/* Scroll Area & Container */
QScrollArea {
    background-color: #0c1017;
    border: none;
}
QWidget#ContentWidget {
    background-color: #0c1017;
}

/* Sleek Slim ScrollBars */
QScrollBar:vertical {
    border: none;
    background: transparent;
    width: 6px;
    margin: 4px 1px 4px 1px;
    border-radius: 3px;
}
QScrollBar::handle:vertical {
    background: #232b3e;
    min-height: 25px;
    border-radius: 3px;
}
QScrollBar::handle:vertical:hover {
    background: #334155;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QScrollBar:horizontal {
    height: 0px;
}

/* DailyMe Modern Cards & Containers */
QFrame#Card {
    background-color: #151b26;
    border: 1px solid #232b3e;
    border-radius: 16px;
}
QFrame#HeroCard {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #182233, stop:1 #131a26);
    border: 1px solid #2a3850;
    border-radius: 18px;
}
QFrame#SubCard {
    background-color: #0e131d;
    border: 1px solid #1c2436;
    border-radius: 12px;
}
QFrame#StatChip {
    background-color: #121824;
    border: 1px solid #1e273a;
    border-radius: 10px;
}

/* Header Labels */
QLabel#TitleLabel {
    font-size: 18px;
    font-weight: 800;
    color: #ffffff;
    letter-spacing: -0.3px;
}
QLabel#SubtitleLabel {
    font-size: 12px;
    color: #8da2be;
}
QLabel#SectionTitle {
    font-size: 12px;
    font-weight: 700;
    color: #10b981;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}
QLabel#FieldLabel {
    font-size: 11px;
    font-weight: 600;
    color: #94a3b8;
    margin-bottom: 1px;
}

/* DailyMe Pill Badges */
QLabel#StatusPill {
    background-color: rgba(16, 185, 129, 0.12);
    color: #34d399;
    border: 1px solid rgba(16, 185, 129, 0.25);
    border-radius: 12px;
    padding: 3px 10px;
    font-size: 11px;
    font-weight: 700;
}
QLabel#StatusPillInactive {
    background-color: rgba(148, 163, 184, 0.1);
    color: #94a3b8;
    border: 1px solid rgba(148, 163, 184, 0.2);
    border-radius: 12px;
    padding: 3px 10px;
    font-size: 11px;
    font-weight: 700;
}

/* Input Fields */
QLineEdit, QSpinBox {
    background-color: #0e131d;
    border: 1px solid #232b3e;
    border-radius: 10px;
    padding: 8px 12px;
    color: #ffffff;
    font-size: 13px;
    selection-background-color: #10b981;
}
QLineEdit:focus, QSpinBox:focus {
    border: 1.5px solid #10b981;
    background-color: #111722;
}
QLineEdit:hover, QSpinBox:hover {
    border: 1px solid #334155;
}

/* ComboBox dropdown */
QComboBox {
    background-color: #0e131d;
    border: 1px solid #232b3e;
    border-radius: 10px;
    padding: 8px 12px;
    color: #ffffff;
    font-size: 13px;
    min-height: 18px;
}
QComboBox:focus {
    border: 1.5px solid #10b981;
    background-color: #111722;
}
QComboBox:hover {
    border: 1px solid #334155;
}
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: center right;
    width: 24px;
    border-left: none;
}
QComboBox QAbstractItemView {
    background-color: #151b26;
    border: 1px solid #232b3e;
    border-radius: 10px;
    color: #ffffff;
    selection-background-color: #10b981;
    selection-color: #ffffff;
    padding: 4px;
}

/* Standard Buttons */
QPushButton {
    background-color: #1a2232;
    border: 1px solid #2a364e;
    border-radius: 12px;
    padding: 8px 14px;
    color: #e2e8f0;
    font-weight: 600;
    font-size: 12px;
}
QPushButton:hover {
    background-color: #232d42;
    border-color: #3b4c6e;
    color: #ffffff;
}
QPushButton:pressed {
    background-color: #141b27;
}

/* Primary DailyMe Pill Start Button */
QPushButton#StartButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10b981, stop:1 #059669);
    border: none;
    border-radius: 20px;
    padding: 12px 20px;
    color: #ffffff;
    font-size: 14px;
    font-weight: 800;
    letter-spacing: 0.3px;
}
QPushButton#StartButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #34d399, stop:1 #10b981);
}
QPushButton#StartButton:pressed {
    background: #047857;
}

/* DailyMe Pill Stop Button */
QPushButton#StopButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ef4444, stop:1 #dc2626);
    border: none;
    border-radius: 20px;
    padding: 12px 20px;
    color: #ffffff;
    font-size: 14px;
    font-weight: 800;
    letter-spacing: 0.3px;
}
QPushButton#StopButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #f87171, stop:1 #ef4444);
}
QPushButton#StopButton:pressed {
    background: #b91c1c;
}

/* Secondary Action Button (Tester) */
QPushButton#TestButton {
    background-color: #141d2b;
    border: 1px solid #24334c;
    border-radius: 10px;
    color: #38bdf8;
    font-weight: 700;
    font-size: 12px;
    padding: 8px 14px;
}
QPushButton#TestButton:hover {
    background-color: #1a2638;
    border-color: #38bdf8;
    color: #ffffff;
}

/* Terminal Log View */
QTextEdit#LogView {
    background-color: #0a0d14;
    border: 1px solid #1a2233;
    border-radius: 12px;
    padding: 8px 10px;
    color: #94a3b8;
    font-family: Menlo, Monaco, "Courier New";
    font-size: 11px;
    line-height: 1.4;
}

/* Guide Button */
QPushButton#GuideButton {
    background-color: transparent;
    border: 1px solid #232b3e;
    border-radius: 10px;
    color: #94a3b8;
    font-size: 11px;
    font-weight: 600;
    padding: 5px 10px;
}
QPushButton#GuideButton:hover {
    background-color: #151b26;
    color: #e2e8f0;
    border-color: #38bdf8;
}

/* Disabled/Locked Input Fields */
QLineEdit:disabled, QSpinBox:disabled {
    background-color: #0b0e14;
    border: 1px dashed #232d3f;
    color: #64748b;
}

/* Mobile Bottom Navigation Bar */
QFrame#BottomNavBar {
    background-color: #0d121b;
    border-top: 1px solid #1e2638;
    min-height: 60px;
    max-height: 60px;
}

QPushButton#NavTab {
    background-color: transparent;
    border: none;
    border-radius: 10px;
    color: #8da2be;
    font-size: 12px;
    font-weight: 700;
    padding: 6px 12px;
}
QPushButton#NavTab:hover {
    background-color: #161e2b;
    color: #cbd5e1;
}

QPushButton#NavTabActive {
    background-color: rgba(16, 185, 129, 0.14);
    border: 1px solid rgba(16, 185, 129, 0.3);
    border-radius: 10px;
    color: #34d399;
    font-size: 12px;
    font-weight: 800;
    padding: 6px 12px;
}

/* Partner Server Cards */
QFrame#PartnerCard {
    background-color: #141a24;
    border: 1px solid #222c3d;
    border-radius: 12px;
}
QFrame#PartnerCard:hover {
    background-color: #18202d;
    border-color: #334155;
}

QFrame#PartnerCardSelected {
    background-color: rgba(16, 185, 129, 0.08);
    border: 1.5px solid #10b981;
    border-radius: 12px;
}

/* Favorite Server Cards */
QFrame#FavoriteCard {
    background-color: #141a24;
    border: 1px solid #222c3d;
    border-radius: 12px;
}
QFrame#FavoriteCard:hover {
    background-color: #18202d;
    border-color: #38bdf8;
}

QPushButton#FavDeleteBtn {
    background-color: rgba(239, 68, 68, 0.12);
    border: 1px solid rgba(239, 68, 68, 0.25);
    border-radius: 8px;
    color: #f87171;
    font-size: 13px;
    font-weight: bold;
    padding: 0px;
}
QPushButton#FavDeleteBtn:hover {
    background-color: #ef4444;
    color: #ffffff;
    border-color: #ef4444;
}

/* Favorite Add Button (Yellow/Amber accent) */
QPushButton#FavAddButton {
    background-color: #1e2638;
    border: 1px solid #334155;
    border-radius: 14px;
    color: #fbbf24;
    font-weight: 700;
    font-size: 12px;
    padding: 10px 14px;
}
QPushButton#FavAddButton:hover {
    background-color: #27334a;
    border-color: #fbbf24;
    color: #fef08a;
}
QPushButton#FavAddButton:pressed {
    background-color: #171e2c;
}

/* Top Left Back Button */
QPushButton#BackButton {
    background-color: #151b26;
    border: 1px solid #28354a;
    border-radius: 10px;
    color: #94a3b8;
    font-size: 12px;
    font-weight: 700;
    padding: 6px 12px;
}
QPushButton#BackButton:hover {
    background-color: #1e2738;
    border-color: #38bdf8;
    color: #ffffff;
}

/* Big Navigation Buttons inside Infos Menu */
QPushButton#MenuNavCard {
    background-color: #141a24;
    border: 1px solid #222c3d;
    border-radius: 14px;
    text-align: left;
    padding: 14px 16px;
    font-size: 14px;
    font-weight: 700;
    color: #ffffff;
}
QPushButton#MenuNavCard:hover {
    background-color: #1a2230;
    border-color: #3b4c6e;
    color: #38bdf8;
}

/* Badges */
QLabel#PartnerBadge {
    background-color: rgba(56, 189, 248, 0.12);
    border: 1px solid rgba(56, 189, 248, 0.3);
    border-radius: 6px;
    color: #38bdf8;
    font-size: 9px;
    font-weight: 800;
    padding: 2px 6px;
}

QLabel#PlayerBadge {
    background-color: rgba(52, 211, 153, 0.12);
    border: 1px solid rgba(52, 211, 153, 0.25);
    border-radius: 6px;
    color: #34d399;
    font-size: 11px;
    font-weight: 700;
    padding: 2px 6px;
}

/* iOS Segmented Slider Container */
QFrame#IOSSliderContainer {
    background-color: #101622;
    border: 1px solid #1f2a3c;
    border-radius: 23px;
}

/* iOS Segmented Slider Animated Thumb Pill */
QFrame#IOSSliderThumb {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #27364b, stop:1 #1d293a);
    border: 1px solid #3b4d6a;
    border-radius: 19px;
}

/* iOS Slider Buttons */
QPushButton#IOSSliderText {
    background-color: transparent;
    border: none;
    color: #8da2be;
    font-size: 12px;
    font-weight: 600;
    padding: 0px;
}
QPushButton#IOSSliderText:hover {
    color: #cbd5e1;
}

QPushButton#IOSSliderTextActive {
    background-color: transparent;
    border: none;
    color: #ffffff;
    font-size: 12px;
    font-weight: 800;
    padding: 0px;
}

"""

