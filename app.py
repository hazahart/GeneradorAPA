"""
Generador de Citas APA — GVTeam  v3.2.0
pip install PyQt6 qtawesome
"""
import sys, json, os, ctypes, time, urllib.request, webbrowser
from ctypes import c_int, byref, sizeof
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QCheckBox, QTextEdit,
    QTabWidget, QFrame, QScrollArea, QFileDialog, QMessageBox,
    QInputDialog, QDialog, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QToolButton, QGridLayout, QGroupBox,
    QSizePolicy, QSpacerItem, QDateEdit
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize, QTimer, QSettings, QDate
from PyQt6.QtGui  import QFont, QTextCharFormat, QCursor, QAction, QFontMetrics, QIcon

try:
    import qtawesome as qta
    _QTA = True
except ImportError:
    _QTA = False

from main import obtener_metadatos, generar_apa

try:
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("gvteam.generadorapa.app.3")
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

def _dwm(hwnd, attr, val):
    try:
        ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, attr, byref(c_int(val)), sizeof(c_int))
        return True
    except Exception:
        return False

def apply_mica(hwnd, dark=False):
    _dwm(hwnd, 20, 1 if dark else 0)                                         
    if not _dwm(hwnd, 38, 2):                                                            
        _dwm(hwnd, 1029, 1)                                                       

def is_system_dark():
    try:
        s = QSettings(
            r"HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
            QSettings.Format.NativeFormat)
        return s.value("AppsUseLightTheme", 1) == 0
    except Exception:
        return False

def _pal(dark: bool) -> dict:

    if dark:
        return dict(
            BG_WIN      = "#191A1B",
            BG_SURFACE  = "#222426",
            BG_CARD     = "#262829",
            BG_ELEVATED = "#2C2E30",
            BG_INPUT    = "#2A2C2E",
            BORDER      = "#3A3C3E",
            BORDER_FOCUS= "#5B8DD9",
            ACCENT      = "#5B8DD9",
            ACCENT_HOVER= "#7AA3E3",
            ACCENT_PRESS= "#4070BF",
            ACCENT_TEXT = "#FFFFFF",
            TEXT1       = "#F0F0F0",
            TEXT2       = "#A8AAAC",
            TEXTH       = "#606468",
            SUCCESS     = "#4EC97B",
            DANGER      = "#F27474",
            WARNING     = "#F5A623",
            SEL_BG          = "rgba(91,141,217, 22)",
            TAB_SEL_BG      = "rgba(91,141,217, 12)",
            TAB_SEL_SOLID   = "#263345",
            TAB_HOVER_SOLID = "#2A2F38",
        )
    else:
        return dict(
            BG_WIN      = "#F3F3F3",
            BG_SURFACE  = "#FFFFFF",
            BG_CARD     = "#FFFFFF",
            BG_ELEVATED = "#F7F7F7",
            BG_INPUT    = "#FFFFFF",
            BORDER      = "#E0E0E0",
            BORDER_FOCUS= "#1B396A",
            ACCENT      = "#1B396A",
            ACCENT_HOVER= "#254E93",
            ACCENT_PRESS= "#122649",
            ACCENT_TEXT = "#FFFFFF",
            TEXT1       = "#1A1A1A",
            TEXT2       = "#5E5E5E",
            TEXTH       = "#B0B0B0",
            SUCCESS     = "#0D7A0D",
            DANGER      = "#B52B2B",
            WARNING     = "#8A5A00",
            SEL_BG          = "rgba(27,57,106, 18)",
            TAB_SEL_BG      = "rgba(27,57,106, 10)",
            TAB_SEL_SOLID   = "#E8EDF5",
            TAB_HOVER_SOLID = "#F0F3F8",
        )

def _css(p: dict) -> str:
    return f"""
/* ─ Global ─ */
* {{
    color: {p['TEXT1']};
    font-family: 'Segoe UI Variable', 'Segoe UI', sans-serif;
    font-size: 13px;
    outline: 0;
}}
QMainWindow, QDialog, QWidget {{
    background: {p['BG_WIN']};
}}
/* ─ Scroll area transparente ─ */
QScrollArea, QScrollArea > QWidget > QWidget {{
    background: transparent;
    border: none;
}}
/* ─ Tabs ─ */
QTabWidget::pane {{
    border: 1px solid {p['BORDER']};
    border-radius: 10px;
    background: {p['BG_WIN']};
    top: -1px;
}}
QTabBar::tab {{
    background: transparent;
    color: {p['TEXT2']};
    padding: 9px 20px;
    margin-right: 2px;
    border-bottom: 2px solid transparent;
    font-size: 13px;
    font-weight: 500;
    min-width: 80px;
}}
QTabBar::tab:selected {{
    color: {p['ACCENT']};
    border-bottom: 2px solid {p['ACCENT']};
    background: {p['TAB_SEL_SOLID']};
    font-weight: 600;
}}
QTabBar::tab:hover:!selected {{
    color: {p['TEXT1']};
    background: {p['TAB_HOVER_SOLID']};
    border-radius: 6px 6px 0 0;
}}
/* ─ GroupBox ─ */
QGroupBox {{
    font-weight: 700;
    font-size: 11px;
    letter-spacing: 0.7px;
    color: {p['TEXT2']};
    border: 1px solid {p['BORDER']};
    border-radius: 10px;
    margin-top: 20px;
    padding: 20px 12px 10px 12px;
    background: {p['BG_CARD']};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 10px;
    top: 0px;
    padding: 3px 8px;
    background: {p['ACCENT']};
    color: {p['ACCENT_TEXT']};
    border-radius: 5px;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1px;
}}
/* ─ LineEdit ─ */
QLineEdit {{
    background: {p['BG_INPUT']};
    border: 1px solid {p['BORDER']};
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 13px;
    color: {p['TEXT1']};
    selection-background-color: {p['SEL_BG']};
}}
QLineEdit:focus {{
    border: 2px solid {p['BORDER_FOCUS']};
    padding: 5px 9px;
}}
QLineEdit:disabled {{
    background: {p['BG_ELEVATED']};
    color: {p['TEXTH']};
    border-color: {p['BORDER']};
}}
/* ─ ComboBox ─ */
QComboBox {{
    background: {p['BG_INPUT']};
    border: 1px solid {p['BORDER']};
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 13px;
    color: {p['TEXT1']};
}}
QComboBox:focus {{ border: 2px solid {p['BORDER_FOCUS']}; padding: 5px 9px; }}
QComboBox::drop-down {{ border: none; width: 26px; }}
QComboBox::down-arrow {{
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid {p['TEXT2']};
    margin-right: 8px;
}}
QComboBox QAbstractItemView {{
    background: {p['BG_CARD']};
    border: 1px solid {p['BORDER']};
    border-radius: 8px;
    selection-background-color: {p['SEL_BG']};
    color: {p['TEXT1']};
    padding: 4px;
    outline: 0;
}}
/* ─ Buttons (base) ─ */
QPushButton {{
    background: {p['BG_ELEVATED']};
    color: {p['TEXT1']};
    border: 1px solid {p['BORDER']};
    border-radius: 6px;
    padding: 6px 14px;
    font-size: 13px;
    font-weight: 500;
    min-height: 28px;
}}
QPushButton:hover  {{ background: {p['BG_CARD']}; border-color: {p['BORDER_FOCUS']}; }}
QPushButton:pressed{{ background: {p['SEL_BG']}; }}
QPushButton:disabled {{ color: {p['TEXTH']}; border-color: {p['BORDER']}; }}
/* ─ ToolButton ─ */
QToolButton {{
    background: transparent;
    border: none;
    border-radius: 5px;
    padding: 4px;
}}
QToolButton:hover  {{ background: {p['SEL_BG']}; }}
QToolButton:pressed{{ background: {p['BORDER']}; }}
/* ─ Checkbox ─ */
QCheckBox {{
    spacing: 8px;
    font-size: 13px;
    color: {p['TEXT1']};
    background: transparent;
}}
QCheckBox::indicator {{
    width: 17px; height: 17px;
    border: 1.5px solid {p['BORDER']};
    border-radius: 4px;
    background: {p['BG_INPUT']};
}}
QCheckBox::indicator:checked {{
    background: {p['ACCENT']};
    border-color: {p['ACCENT']};
}}
QCheckBox::indicator:hover {{ border-color: {p['ACCENT']}; }}
/* ─ TextEdit ─ */
QTextEdit {{
    background: {p['BG_INPUT']};
    border: 1px solid {p['BORDER']};
    border-radius: 6px;
    padding: 6px 8px;
    font-size: 13px;
    color: {p['TEXT1']};
    selection-background-color: {p['SEL_BG']};
}}
QTextEdit:focus {{ border: 2px solid {p['BORDER_FOCUS']}; padding: 5px 7px; }}
/* ─ Table ─ */
QTableWidget {{
    background: {p['BG_CARD']};
    border: 1px solid {p['BORDER']};
    border-radius: 8px;
    gridline-color: {p['BORDER']};
    alternate-background-color: {p['BG_ELEVATED']};
    selection-background-color: {p['SEL_BG']};
    selection-color: {p['TEXT1']};
    outline: 0;
}}
QTableWidget::item {{ padding: 7px 10px; border: none; }}
QTableWidget::item:selected {{
    background: {p['SEL_BG']};
    color: {p['TEXT1']};
}}
QHeaderView::section {{
    background: {p['BG_ELEVATED']};
    color: {p['TEXT2']};
    font-weight: 700; font-size: 11px;
    letter-spacing: 0.4px;
    padding: 7px 10px;
    border: none;
    border-bottom: 1px solid {p['BORDER']};
    border-right: 1px solid {p['BORDER']};
}}
QHeaderView::section:last {{ border-right: none; }}
QHeaderView {{ background: transparent; border-radius: 8px; }}
/* ─ Scrollbars ─ */
QScrollBar:vertical {{
    background: transparent; width: 8px; margin: 4px 2px;
    border-radius: 4px;
}}
QScrollBar::handle:vertical {{
    background: {p['BORDER']};
    border-radius: 4px; min-height: 28px;
}}
QScrollBar::handle:vertical:hover {{ background: {p['TEXT2']}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{
    background: transparent; height: 8px; margin: 2px 4px;
    border-radius: 4px;
}}
QScrollBar::handle:horizontal {{
    background: {p['BORDER']};
    border-radius: 4px; min-width: 28px;
}}
/* ─ Status bar ─ */
QStatusBar {{
    background: {p['BG_ELEVATED']};
    border-top: 1px solid {p['BORDER']};
    color: {p['TEXT2']};
    font-size: 12px;
    padding: 2px 8px;
    min-height: 26px;
}}
QStatusBar QLabel {{ color: {p['TEXT2']}; font-size: 12px; background: transparent; }}
/* ─ Menu bar ─ */
QMenuBar {{
    background: {p['BG_WIN']};
    color: {p['TEXT1']};
    border-bottom: 1px solid {p['BORDER']};
    padding: 2px 4px;
    font-size: 13px;
}}
QMenuBar::item {{ padding: 5px 11px; border-radius: 5px; background: transparent; }}
QMenuBar::item:selected {{ background: {p['SEL_BG']}; }}
QMenu {{
    background: {p['BG_CARD']};
    border: 1px solid {p['BORDER']};
    border-radius: 10px;
    padding: 5px;
    font-size: 13px;
}}
QMenu::item {{ padding: 7px 26px 7px 12px; border-radius: 5px; color: {p['TEXT1']}; }}
QMenu::item:selected {{ background: {p['SEL_BG']}; }}
QMenu::separator {{ height: 1px; background: {p['BORDER']}; margin: 4px 8px; }}
/* ─ MessageBox / InputDialog ─ */
QMessageBox {{
    background: {p['BG_CARD']};
    border: 1px solid {p['BORDER']};
    border-radius: 10px;
    min-width: 320px;
}}
QMessageBox QLabel {{
    color: {p['TEXT1']};
    font-size: 13px;
    background: transparent;
    padding: 4px;
    min-width: 260px;
}}
QMessageBox QPushButton {{
    min-width: 80px;
    padding: 6px 18px;
    font-size: 13px;
}}
QInputDialog {{
    background: {p['BG_CARD']};
    border: 1px solid {p['BORDER']};
    border-radius: 10px;
}}
QInputDialog QLabel {{ color: {p['TEXT1']}; font-size: 13px; background: transparent; }}
QInputDialog QLineEdit {{ font-size: 13px; }}
QInputDialog QPushButton {{ min-width: 72px; padding: 6px 16px; font-size: 13px; }}
/* ─ Labels semánticos ─ */
QLabel#sectionTitle {{
    font-size: 11px;
    font-weight: 700;
    color: {p['TEXT2']};
    letter-spacing: 0.5px;
    background: transparent;
}}
QLabel#indicador {{
    font-size: 12px;
    color: {p['ACCENT']};
    font-style: italic;
    background: transparent;
}}
QLabel#statusOk      {{ color: {p['SUCCESS']}; font-weight: 600; font-size: 12px; }}
QLabel#statusWarn    {{ color: {p['WARNING']}; font-weight: 600; font-size: 12px; }}
QLabel#statusErr     {{ color: {p['DANGER']};  font-weight: 600; font-size: 12px; }}
/* ─ Frame card ─ */
QFrame#card {{
    background: {p['BG_CARD']};
    border: 1px solid {p['BORDER']};
    border-radius: 10px;
}}
"""

def _accent_css(p):
    return f"""
    QPushButton {{
        background: {p['ACCENT']}; color: {p['ACCENT_TEXT']};
        border: 1px solid {p['ACCENT']}; border-radius: 6px;
        padding: 6px 16px; font-size: 13px; font-weight: 600; min-height: 28px;
    }}
    QPushButton:hover  {{ background: {p['ACCENT_HOVER']}; border-color: {p['ACCENT_HOVER']}; }}
    QPushButton:pressed{{ background: {p['ACCENT_PRESS']}; }}
    QPushButton:disabled {{ background: {p['BG_ELEVATED']}; color: {p['TEXTH']}; border-color: {p['BORDER']}; }}
"""

def _danger_css(p):
    return f"""
    QPushButton {{
        background: transparent; color: {p['DANGER']};
        border: 1px solid {p['DANGER']}; border-radius: 6px;
        padding: 6px 14px; font-size: 13px; min-height: 28px;
    }}
    QPushButton:hover  {{ background: {p['SEL_BG']}; }}
    QPushButton:pressed{{ background: {p['BORDER']}; }}
"""

def _icon(name, color="#888"):
    from PyQt6.QtGui import QIcon
    if _QTA:
        try: return qta.icon(name, color=color)
        except Exception: pass
    from PyQt6.QtGui import QIcon
    return QIcon()

def _tbtn(icon_name, tooltip, color="#888"):
    b = QToolButton()
    b.setIcon(_icon(icon_name, color)); b.setIconSize(QSize(16, 16))
    b.setToolTip(tooltip)
    b.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
    return b

def _btn(text, icon_name=None, style="normal", p=None):
    b = QPushButton(text)
    if icon_name and p:
        ic = p["ACCENT_TEXT"] if style == "accent" else p["TEXT2"]
        b.setIcon(_icon(icon_name, ic)); b.setIconSize(QSize(14, 14))
    b.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
    if   style == "accent" and p: b.setStyleSheet(_accent_css(p))
    elif style == "danger" and p: b.setStyleSheet(_danger_css(p))
    return b

def _lbl(text, obj="sectionTitle"):
    l = QLabel(text); l.setObjectName(obj); return l

def _sep():
    """Línea separadora horizontal."""
    f = QFrame()
    f.setFrameShape(QFrame.Shape.HLine)
    f.setFrameShadow(QFrame.Shadow.Sunken)
    return f

class _Combo(QComboBox):
    """QComboBox que solo consume el scroll wheel cuando está desplegado.
    Si está cerrado, propaga el evento al widget padre para que el
    QScrollArea siga scrolleando normalmente."""
    def wheelEvent(self, e):
        if self.view().isVisible():
            super().wheelEvent(e)                                       
        else:
            e.ignore()                                                 

class ExtractWorker(QThread):
    done = pyqtSignal(object)
    def __init__(self, url): super().__init__(); self.url = url
    def run(self): self.done.emit(obtener_metadatos(self.url))

class UpdateWorker(QThread):
    result = pyqtSignal(str, bool)
    def __init__(self, ver, url): super().__init__(); self.ver = ver; self.url = url
    def run(self):
        try:
            req = urllib.request.Request(f"{self.url}?t={int(time.time())}",
                                         headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=5) as r:
                remote = r.read().decode().strip()
            vr = [int(x) for x in remote.split(".") if x.isdigit()]
            va = [int(x) for x in self.ver.split(".")    if x.isdigit()]
            self.result.emit(remote, vr > va)
        except Exception:
            self.result.emit("", False)

class ResultBox(QFrame):
    def __init__(self, title, on_copy, p, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 8, 10, 8)
        lay.setSpacing(5)

        hdr = QHBoxLayout()
        hdr.addWidget(_lbl(title))
        hdr.addStretch()
        cb = _tbtn("fa5s.copy", "Copiar", p["ACCENT"])
        cb.clicked.connect(on_copy)
        hdr.addWidget(cb)
        lay.addLayout(hdr)

        self.te = QTextEdit()
        self.te.setReadOnly(True)
        self.te.setMinimumHeight(52)
        self.te.setMaximumHeight(72)
        self.te.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        lay.addWidget(self.te)

    def set_tuplas(self, tuplas):
        self.te.clear()
        cur = self.te.textCursor()
        nf = QTextCharFormat(); nf.setFont(QFont("Segoe UI Variable", 11))
        if_ = QTextCharFormat(); if_.setFont(QFont("Segoe UI Variable", 11)); if_.setFontItalic(True)
        for t, s in tuplas:
            cur.insertText(t, if_ if s == "italic" else nf)

class GeneradorAPA(QMainWindow):
    VERSION      = "2.0.0"
    URL_VERSION  = "https://raw.githubusercontent.com/hazahart/GeneradorAPA/main/version.txt"
    URL_DESCARGA = "https://github.com/hazahart/GeneradorAPA/releases/latest"

    def __init__(self):
        super().__init__()
        self._dark = is_system_dark()
        self._p    = _pal(self._dark)

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setWindowTitle(f"Generador de Citas APA  ·  GVTeam  v{self.VERSION}")

        _ico_path = Path(__file__).parent / "icono.ico"
        if _ico_path.exists():
            self.setWindowIcon(QIcon(str(_ico_path)))
        self.setMinimumSize(640, 480)

        self.showMaximized()

        self.config_file       = Path.home() / ".generador_apa_config.json"
        self.archivo_datos     = self._get_data_path()
        self.colecciones       = {"General": []}
        self.col_actual        = "General"
        self.ultima_ref        = []
        self.ultima_cita_p     = []
        self.ultima_cita_n     = []
        self.ultimos_datos_gui = {}
        self.ultimo_tipo       = ""
        self.ultimo_formato    = ""
        self.ultimo_corp       = False

        QApplication.instance().setStyleSheet(_css(self._p))

        self._build_menu()
        self._build_ui()
        self._build_statusbar()
        self._load_data()
        self._check_updates(silent=True)

    def showEvent(self, ev):
        super().showEvent(ev)
        apply_mica(int(self.winId()), self._dark)

    def _apply_theme(self):
        """Aplica nuevo tema a toda la app incluyendo widgets con estilos inline."""
        p = self._p

        QApplication.instance().setStyleSheet(_css(p))

        apply_mica(int(self.winId()), self._dark)

        for w, style in self._styled_widgets:
            if   style == "accent": w.setStyleSheet(_accent_css(p))
            elif style == "danger": w.setStyleSheet(_danger_css(p))

        self._theme_btn.setIcon(_icon(
            "fa5s.moon" if not self._dark else "fa5s.sun", p["TEXT2"]))

        self.status_lbl.setStyleSheet("")

    def _toggle_theme(self):
        self._dark = not self._dark
        self._p    = _pal(self._dark)
        self._apply_theme()
        self.flash_status("Tema actualizado.", self._p["ACCENT"])

    def _get_data_path(self):
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    p = json.load(f).get("db_path", "")
                    if p and Path(p).parent.exists(): return p
            except Exception: pass
        folder = Path.home() / "Documents" / "GeneradorAPA"
        folder.mkdir(parents=True, exist_ok=True)
        return str(folder / "coleccion_apa.json")

    def _save_config(self, path):
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump({"db_path": path}, f)
        except Exception: pass

    def _load_data(self):
        if os.path.exists(self.archivo_datos):
            try:
                with open(self.archivo_datos, "r", encoding="utf-8") as f:
                    d = json.load(f)
                if isinstance(d, list):              self.colecciones = {"General": d}
                elif isinstance(d, dict) and d:      self.colecciones = d
            except Exception:                        self.colecciones = {"General": []}
        if self.col_actual not in self.colecciones:
            self.col_actual = list(self.colecciones.keys())[0]
        self._refresh_col_ui()

    def _save_data(self):
        try:
            with open(self.archivo_datos, "w", encoding="utf-8") as f:
                json.dump(self.colecciones, f, ensure_ascii=False, indent=4)
        except Exception: pass

    def _build_menu(self):
        p = self._p
        mb = self.menuBar()
        arch = mb.addMenu("Archivo")
        arch.addAction(self._act("Cambiar ubicación de guardado…", "fa5s.folder-open", self._change_path))
        arch.addSeparator()
        arch.addAction(self._act("Importar colección…",  "fa5s.file-import", self._import_data))
        arch.addAction(self._act("Exportar colección…",  "fa5s.file-export", self._export_data))
        ay = mb.addMenu("Ayuda")
        ay.addAction(self._act("Buscar actualizaciones…", "fa5s.sync-alt",
                               lambda: self._check_updates(silent=False)))
        ay.addSeparator()
        ay.addAction(self._act("Acerca de…", "fa5s.info-circle", self._about))

    def _act(self, text, icon_name, slot):
        a = QAction(_icon(icon_name, self._p["TEXT2"]), text, self)
        a.triggered.connect(slot)
        return a

    def _build_statusbar(self):
        sb = self.statusBar()
        self.status_lbl = QLabel(f"Generador APA v{self.VERSION}  ·  GVTeam")
        sb.addWidget(self.status_lbl)

        self._theme_btn = _tbtn(
            "fa5s.moon" if not self._dark else "fa5s.sun",
            "Cambiar tema claro / oscuro", self._p["TEXT2"])
        self._theme_btn.clicked.connect(self._toggle_theme)
        sb.addPermanentWidget(self._theme_btn)

        self.path_lbl = QLabel()
        self.path_lbl.setStyleSheet(f"color:{self._p['TEXTH']}; font-size:11px;")
        sb.addPermanentWidget(self.path_lbl)
        self._upd_path()

    def _upd_path(self):
        self.path_lbl.setText(f"  {self.archivo_datos}  ")

    def flash_status(self, msg, color=None, ms=3500):
        c = color or self._p["SUCCESS"]
        self.status_lbl.setText(msg)
        self.status_lbl.setStyleSheet(f"color:{c}; font-weight:600; font-size:12px;")
        QTimer.singleShot(ms, lambda: (
            self.status_lbl.setText(f"Generador APA v{self.VERSION}  ·  GVTeam"),
            self.status_lbl.setStyleSheet("")
        ))

    def _build_ui(self):
        self._styled_widgets = []                                                           

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(14, 10, 14, 10)
        root.setSpacing(0)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        root.addWidget(self.tabs)

        self.tabs.addTab(self._build_tab_gen(), "  Generador  ")
        self.tabs.addTab(self._build_tab_col(), "  Mis Colecciones  ")

        if _QTA:
            self.tabs.setTabIcon(0, _icon("fa5s.magic",       self._p["ACCENT"]))
            self.tabs.setTabIcon(1, _icon("fa5s.layer-group", self._p["ACCENT"]))

    def _build_tab_gen(self):
        p = self._p
        tab = QWidget()
        scroll = QScrollArea()
        scroll.setWidget(tab)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        lay = QVBoxLayout(tab)
        lay.setContentsMargins(16, 14, 16, 18)
        lay.setSpacing(12)

        ext = QGroupBox("1. EXTRACCIÓN AUTOMÁTICA")
        eh  = QHBoxLayout(ext); eh.setSpacing(8)
        self.inp_url = QLineEdit()
        self.inp_url.setPlaceholderText("Pega una URL o ruta de PDF aquí…")
        eh.addWidget(self.inp_url, stretch=1)

        b_pdf = _btn("", "fa5s.folder-open", p=p)
        b_pdf.setFixedWidth(34); b_pdf.setFixedHeight(32)
        b_pdf.setToolTip("Seleccionar PDF local")
        b_pdf.clicked.connect(self._select_pdf)
        eh.addWidget(b_pdf)

        self.btn_ext = _btn("  Extraer", "fa5s.download", "accent", p)
        self.btn_ext.setFixedHeight(32)
        self.btn_ext.clicked.connect(self._extract)
        eh.addWidget(self.btn_ext)
        self._styled_widgets.append((self.btn_ext, "accent"))
        lay.addWidget(ext)

        tr = QHBoxLayout(); tr.setSpacing(10)
        for lbl_t, attr, items in [
            ("Tipo de Fuente", "cmb_tipo",
             ["Página Web / Documento Genérico", "Revista Académica (Journal)",
              "Noticia / Periódico", "Video / Multimedia", "Libro"]),
            ("Formato de Autor", "cmb_fmt",
             ["Hispano (2 apellidos)", "Internacional (1 apellido)"]),
        ]:
            vb = QVBoxLayout(); vb.setSpacing(4)
            vb.addWidget(_lbl(lbl_t))
            c = _Combo(); c.addItems(items)
            c.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            setattr(self, attr, c); vb.addWidget(c); tr.addLayout(vb)
        lay.addLayout(tr)

        dc = QGroupBox("2. DATOS DE LA REFERENCIA")
        dg = QGridLayout(dc)
        dg.setHorizontalSpacing(10); dg.setVerticalSpacing(8)

        dg.addWidget(_lbl("Autor(es)"), 0, 0)
        self.inp_autor = QLineEdit()
        self.inp_autor.setPlaceholderText("Autor 1 (Nombre Apellido); Autor 2 (Nombre Apellido)")
        dg.addWidget(self.inp_autor, 1, 0)

        self.chk_corp = QCheckBox("Corporativo")
        dg.addWidget(self.chk_corp, 1, 1, Qt.AlignmentFlag.AlignVCenter)

        dg.addWidget(_lbl("Año / Fecha"), 0, 2)
        self.inp_fecha = QLineEdit(); self.inp_fecha.setPlaceholderText("2024")
        self.inp_fecha.setMaximumWidth(130)
        dg.addWidget(self.inp_fecha, 1, 2)

        dg.addWidget(_lbl("Título"), 2, 0)
        self.inp_titulo = QLineEdit()
        dg.addWidget(self.inp_titulo, 3, 0, 1, 3)

        dg.addWidget(_lbl("Sitio / Editorial"), 4, 0)
        self.inp_sitio = QLineEdit()
        self.inp_sitio.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        dg.addWidget(self.inp_sitio, 5, 0)

        dg.addWidget(_lbl("Revista"), 4, 1, 1, 2)
        self.inp_revista = QLineEdit()
        self.inp_revista.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        dg.addWidget(self.inp_revista, 5, 1, 1, 2)

        nh = QHBoxLayout(); nh.setSpacing(8)
        for ph, attr, mw in [("Vol.", "inp_vol", 80), ("Núm.", "inp_num", 80), ("Págs.", "inp_pags", 110)]:
            vb = QVBoxLayout(); vb.setSpacing(4)
            inp = QLineEdit(); inp.setPlaceholderText(ph)
            inp.setMaximumWidth(mw)
            inp.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            setattr(self, attr, inp)
            vb.addWidget(_lbl(ph)); vb.addWidget(inp); nh.addLayout(vb)
        nh.addStretch()
        dg.addLayout(nh, 6, 0, 1, 3)

        dg.addWidget(_lbl("Fecha de Recuperación"), 7, 0)
        recup_row = QHBoxLayout()
        self.chk_recup = QCheckBox("Añadir fecha de recuperación")
        self.chk_recup.toggled.connect(self._toggle_recup)
        recup_row.addWidget(self.chk_recup)
        self.date_recup = QDateEdit(QDate.currentDate())
        self.date_recup.setCalendarPopup(True)
        self.date_recup.setDisplayFormat("dd/MM/yyyy")
        self.date_recup.setEnabled(False)
        self.date_recup.setMaximumWidth(130)
        recup_row.addWidget(self.date_recup)
        self.btn_hoy = _btn("Hoy", "fa5s.calendar-day", p=p)
        self.btn_hoy.setEnabled(False)
        self.btn_hoy.setFixedHeight(30)
        self.btn_hoy.clicked.connect(lambda: self.date_recup.setDate(QDate.currentDate()))
        recup_row.addWidget(self.btn_hoy)
        recup_row.addStretch()
        dg.addLayout(recup_row, 8, 0, 1, 3)

        dg.setColumnStretch(0, 4); dg.setColumnStretch(1, 1); dg.setColumnStretch(2, 3)
        lay.addWidget(dc)

        gr = QHBoxLayout(); gr.addStretch()
        self.btn_gen = _btn("   Generar APA", "fa5s.magic", "accent", p)
        self.btn_gen.setMinimumWidth(160); self.btn_gen.setMinimumHeight(36)
        self.btn_gen.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.btn_gen.clicked.connect(self._generate)
        gr.addWidget(self.btn_gen); gr.addStretch()
        self._styled_widgets.append((self.btn_gen, "accent"))
        lay.addLayout(gr)

        self.box_cp = ResultBox("Cita Parentética", self._copy_cp, p)
        self.box_cn = ResultBox("Cita Narrativa",   self._copy_cn, p)
        cr = QHBoxLayout(); cr.setSpacing(10)
        cr.addWidget(self.box_cp); cr.addWidget(self.box_cn)
        lay.addLayout(cr)

        rh = QHBoxLayout(); rh.setSpacing(8)
        rh.addWidget(_lbl("Referencia Final"))
        self.lbl_ind = _lbl("Guardar en: General", "indicador")
        rh.addWidget(self.lbl_ind); rh.addStretch()

        self.btn_add = _btn("  Añadir a Colección", "fa5s.plus", "accent", p)
        self.btn_add.setMinimumHeight(32)
        self.btn_add.clicked.connect(self._add_to_col)
        rh.addWidget(self.btn_add)
        self._styled_widgets.append((self.btn_add, "accent"))

        cb_ref = _tbtn("fa5s.copy", "Copiar referencia", p["ACCENT"])
        cb_ref.clicked.connect(self._copy_ref)
        rh.addWidget(cb_ref)
        lay.addLayout(rh)

        self.txt_ref = QTextEdit()
        self.txt_ref.setReadOnly(True)
        self.txt_ref.setMinimumHeight(60)
        self.txt_ref.setMaximumHeight(100)
        self.txt_ref.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        lay.addWidget(self.txt_ref)
        lay.addStretch()
        return scroll

    def _build_tab_col(self):
        p = self._p
        tab = QWidget()
        lay = QVBoxLayout(tab)
        lay.setContentsMargins(16, 14, 16, 14)
        lay.setSpacing(10)

        tb = QHBoxLayout(); tb.setSpacing(6)
        tb.addWidget(_lbl("Carpeta:"))
        self.cmb_col = _Combo()
        self.cmb_col.setMinimumWidth(160)
        self.cmb_col.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.cmb_col.setMaximumWidth(280)
        self.cmb_col.currentTextChanged.connect(self._on_col_changed)
        tb.addWidget(self.cmb_col)

        b_nc = _tbtn("fa5s.folder-plus", "Nueva carpeta",    p["SUCCESS"])
        b_dc = _tbtn("fa5s.trash-alt",   "Eliminar carpeta", p["DANGER"])
        b_nc.clicked.connect(self._new_col); b_dc.clicked.connect(self._del_col)
        tb.addWidget(b_nc); tb.addWidget(b_dc); tb.addStretch()

        self.lbl_cnt = QLabel("0 citas")
        self.lbl_cnt.setStyleSheet(
            f"color:{p['TEXT2']}; font-size:12px; font-weight:700; background:transparent;")
        tb.addWidget(self.lbl_cnt)
        lay.addLayout(tb)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Autor(es)", "Año", "Título", "Fuente", "Tipo"])
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        hh.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(0, 160); self.table.setColumnWidth(1, 60)
        self.table.setColumnWidth(3, 130); self.table.setColumnWidth(4, 100)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.table.selectionModel().selectionChanged.connect(self._on_row_sel)
        lay.addWidget(self.table, stretch=1)

        lay.addWidget(_lbl("Vista Previa (APA)"))
        self.txt_prev = QTextEdit()
        self.txt_prev.setReadOnly(True)
        self.txt_prev.setMinimumHeight(56); self.txt_prev.setMaximumHeight(80)
        self.txt_prev.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        lay.addWidget(self.txt_prev)

        acts = QHBoxLayout(); acts.setSpacing(8)
        b_ed  = _btn("  Editar",   "fa5s.edit",  p=p)
        b_del = _btn("  Eliminar", "fa5s.trash", "danger", p)
        b_ed.setMinimumHeight(32); b_del.setMinimumHeight(32)
        b_ed.clicked.connect(self._edit_cit); b_del.clicked.connect(self._del_cit)
        acts.addWidget(b_ed); acts.addWidget(b_del); acts.addStretch()
        self._styled_widgets.append((b_del, "danger"))

        b_vac  = _btn("  Vaciar",        "fa5s.broom", "danger", p)
        b_copy = _btn("  Copiar lista",  "fa5s.copy",  "accent", p)
        b_vac.setMinimumHeight(32); b_copy.setMinimumHeight(32)
        b_vac.clicked.connect(self._empty_col)
        b_copy.clicked.connect(self._copy_all)
        acts.addWidget(b_vac); acts.addWidget(b_copy)
        self._styled_widgets.append((b_vac,  "danger"))
        self._styled_widgets.append((b_copy, "accent"))
        lay.addLayout(acts)
        return tab

    def _select_pdf(self):
        path, _ = QFileDialog.getOpenFileName(self, "Seleccionar PDF", "", "PDFs (*.pdf)")
        if path: self.inp_url.setText(path)

    def _extract(self):
        url = self.inp_url.text().strip()
        if not url:
            self.flash_status("Ingresa una URL o ruta de PDF.", self._p["WARNING"]); return
        self.btn_ext.setEnabled(False); self.btn_ext.setText("Extrayendo…")
        self.worker = ExtractWorker(url)
        self.worker.done.connect(self._on_extracted)
        self.worker.start()

    def _on_extracted(self, datos):
        self.btn_ext.setEnabled(True); self.btn_ext.setText("  Extraer")
        if datos:
            self.inp_autor.setText(datos.get("autor") or "")
            self.inp_titulo.setText(datos.get("titulo") or "")
            self.inp_fecha.setText(datos.get("fecha") or "s. f.")
            self.inp_sitio.setText(datos.get("sitio") or "")
            self.inp_revista.setText(datos.get("revista") or "")
            self.inp_vol.setText(datos.get("volumen") or "")
            self.inp_num.setText(datos.get("numero") or "")
            self.inp_pags.setText(datos.get("paginas") or "")
            if datos.get("tipo_fuente_sugerido"):
                i = self.cmb_tipo.findText(datos["tipo_fuente_sugerido"])
                if i >= 0: self.cmb_tipo.setCurrentIndex(i)
            self.chk_corp.setChecked(datos.get("es_corporativo_sugerido", False))
            self.flash_status("✓  Datos extraídos.", self._p["SUCCESS"])
        else:
            self.flash_status("No se pudieron extraer datos.", self._p["DANGER"])

    def _toggle_recup(self, checked):
        self.date_recup.setEnabled(checked)
        self.btn_hoy.setEnabled(checked)

    def _generate(self):
        datos = {
            "url":     self.inp_url.text().strip(),
            "autor":   self.inp_autor.text().strip(),
            "titulo":  self.inp_titulo.text().strip(),
            "fecha":   self.inp_fecha.text().strip(),
            "sitio":   self.inp_sitio.text().strip(),
            "revista": self.inp_revista.text().strip(),
            "volumen": self.inp_vol.text().strip(),
            "numero":  self.inp_num.text().strip(),
            "paginas": self.inp_pags.text().strip(),
        }
        fmt = "hispano" if "Hispano" in self.cmb_fmt.currentText() else "anglosajon"
        fecha_recup = ""
        if self.chk_recup.isChecked():
            d = self.date_recup.date()
            meses = ["enero","febrero","marzo","abril","mayo","junio",
                     "julio","agosto","septiembre","octubre","noviembre","diciembre"]
            fecha_recup = f"{d.day()} de {meses[d.month()-1]} de {d.year()}"
        res = generar_apa(datos, self.cmb_tipo.currentText(), fecha_recup, fmt, self.chk_corp.isChecked())
        self.ultima_ref    = res["referencia"]
        self.ultima_cita_p = res["cita_parentetica"]
        self.ultima_cita_n = res["cita_narrativa"]
        self.ultimos_datos_gui = datos
        self.ultimo_tipo   = self.cmb_tipo.currentText()
        self.ultimo_formato= self.cmb_fmt.currentText()
        self.ultimo_corp   = self.chk_corp.isChecked()
        self.box_cp.set_tuplas(self.ultima_cita_p)
        self.box_cn.set_tuplas(self.ultima_cita_n)
        self._fill(self.txt_ref, self.ultima_ref)
        self.flash_status("✓  Referencia APA generada.", self._p["SUCCESS"])

    def _fill(self, widget, tuplas):
        widget.clear(); cur = widget.textCursor()
        nf  = QTextCharFormat(); nf.setFont(QFont("Segoe UI Variable", 11))
        if_ = QTextCharFormat(); if_.setFont(QFont("Segoe UI Variable", 11)); if_.setFontItalic(True)
        for t, s in tuplas:
            cur.insertText(t, if_ if s == "italic" else nf)

    def _copy_tuplas(self, tuplas):
        if not tuplas: return
        plain = "".join(t[0] for t in tuplas)
        html_frag = ""
        for t, s in tuplas:
            h = t.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace("\n","<br>")
            html_frag += f"<i>{h}</i>" if s == "italic" else h
        try:
            hs="<html><body><div style='margin-left:40px;text-indent:-40px;'>"
            he="</div></body></html>"
            html_frag=html_frag.replace("<br><br>","</div><div style='margin-left:40px;text-indent:-40px;'>")
            pre="Version:0.9\r\nStartHTML:{0:010d}\r\nEndHTML:{1:010d}\r\nStartFragment:{2:010d}\r\nEndFragment:{3:010d}\r\n"
            fb=html_frag.encode("utf-8"); sb=hs.encode("utf-8"); eb=he.encode("utf-8")
            sh=105; sf=sh+len(sb); ef=sf+len(fb); eh=ef+len(eb)
            hb=pre.format(sh,eh,sf,ef).encode("utf-8")+sb+fb+eb
            u32,k32=ctypes.windll.user32,ctypes.windll.kernel32
            k32.GlobalAlloc.argtypes=[ctypes.c_uint,ctypes.c_size_t]; k32.GlobalAlloc.restype=ctypes.c_void_p
            k32.GlobalLock.argtypes=[ctypes.c_void_p]; k32.GlobalLock.restype=ctypes.c_void_p
            k32.GlobalUnlock.argtypes=[ctypes.c_void_p]
            u32.SetClipboardData.argtypes=[ctypes.c_uint,ctypes.c_void_p]; u32.SetClipboardData.restype=ctypes.c_void_p
            u32.OpenClipboard.argtypes=[ctypes.c_void_p]
            u32.OpenClipboard(None); u32.EmptyClipboard()
            tb=plain.encode("utf-16le")+b"\x00\x00"
            ht=k32.GlobalAlloc(0x0002,len(tb)); ctypes.memmove(k32.GlobalLock(ht),tb,len(tb)); k32.GlobalUnlock(ht)
            u32.SetClipboardData(13,ht)
            CF=u32.RegisterClipboardFormatW("HTML Format")
            hh=k32.GlobalAlloc(0x0002,len(hb)+1); ptr=k32.GlobalLock(hh)
            ctypes.memmove(ptr,hb,len(hb)); ctypes.c_char.from_address(ptr+len(hb)).value=b"\x00"
            k32.GlobalUnlock(hh); u32.SetClipboardData(CF,hh); u32.CloseClipboard()
            self.flash_status("✓  Copiado con formato APA.", self._p["SUCCESS"])
        except Exception:
            QApplication.clipboard().setText(plain)
            self.flash_status("✓  Copiado como texto plano.", self._p["SUCCESS"])

    def _copy_cp(self):  self._copy_tuplas(self.ultima_cita_p)
    def _copy_cn(self):  self._copy_tuplas(self.ultima_cita_n)
    def _copy_ref(self): self._copy_tuplas(self.ultima_ref)

    def _add_to_col(self):
        if not self.ultima_ref:
            self.flash_status("Primero genera una referencia.", self._p["WARNING"]); return
        plain = "".join(t[0] for t in self.ultima_ref).strip().lower()
        act = self.col_actual
        if any(r["plano"] == plain for r in self.colecciones[act]):
            self.flash_status("Esta referencia ya está en la colección.", self._p["WARNING"]); return
        self.colecciones[act].append({
            "plano": plain, "formato": self.ultima_ref,
            "raw_datos": self.ultimos_datos_gui, "raw_tipo": self.ultimo_tipo,
            "raw_formato": self.ultimo_formato, "raw_corp": self.ultimo_corp,
        })
        self.colecciones[act].sort(key=lambda x: x["plano"])
        self._save_data(); self._refresh_col_ui()
        self.flash_status(f"✓  Añadido a «{act}».", self._p["SUCCESS"])

    def _refresh_col_ui(self):
        self.cmb_col.blockSignals(True)
        self.cmb_col.clear(); self.cmb_col.addItems(list(self.colecciones.keys()))
        if self.col_actual in self.colecciones:
            self.cmb_col.setCurrentText(self.col_actual)
        self.cmb_col.blockSignals(False)
        self.lbl_ind.setText(f"Guardar en: {self.col_actual}")
        self._pop_table()

    def _pop_table(self):
        items = self.colecciones.get(self.col_actual, [])
        self.table.setRowCount(0)
        n = len(items)
        self.lbl_cnt.setText(f"{n} cita{'s' if n != 1 else ''}")
        for i, item in enumerate(items):
            rd = item.get("raw_datos", {})
            row = [rd.get("autor","S. A."), rd.get("fecha","s. f."),
                   rd.get("titulo","Sin título"),
                   rd.get("sitio","") or rd.get("revista",""),
                   item.get("raw_tipo","").replace("Página Web / ","")
                                          .replace("Revista Académica","Revista")]
            self.table.insertRow(i)
            for j, v in enumerate(row):
                it = QTableWidgetItem(str(v))
                it.setFlags(it.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(i, j, it)
        self.txt_prev.clear()

    def _on_col_changed(self, text):
        if text and text in self.colecciones:
            self.col_actual = text
            self.lbl_ind.setText(f"Guardar en: {text}")
            self._pop_table()

    def _on_row_sel(self):
        idx = self.table.currentRow()
        items = self.colecciones.get(self.col_actual, [])
        if 0 <= idx < len(items):
            self._fill(self.txt_prev, items[idx]["formato"])

    def _new_col(self):
        name, ok = QInputDialog.getText(self, "Nueva Carpeta", "Nombre:")
        if ok and name.strip() and name.strip() not in self.colecciones:
            self.colecciones[name.strip()] = []
            self.col_actual = name.strip()
            self._save_data(); self._refresh_col_ui()

    def _del_col(self):
        act = self.col_actual
        if len(self.colecciones) <= 1:
            self.flash_status("No puedes eliminar la única colección.", self._p["WARNING"]); return
        if QMessageBox.question(self, "Eliminar Carpeta",
            f"¿Eliminar «{act}» y todas sus citas?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            del self.colecciones[act]
            self.col_actual = list(self.colecciones.keys())[0]
            self._save_data(); self._refresh_col_ui()

    def _empty_col(self):
        if QMessageBox.question(self, "Vaciar Carpeta",
            f"¿Vaciar «{self.col_actual}»?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            self.colecciones[self.col_actual] = []
            self._save_data(); self._pop_table()

    def _edit_cit(self):
        idx = self.table.currentRow()
        items = self.colecciones.get(self.col_actual, [])
        if idx < 0 or idx >= len(items):
            self.flash_status("Selecciona una cita para editar.", self._p["WARNING"]); return
        item = items[idx]
        if "raw_datos" not in item:
            QMessageBox.warning(self, "Error", "Esta cita no tiene datos para edición."); return
        rd = item["raw_datos"]
        self.inp_url.setText(rd.get("url",""));      self.inp_autor.setText(rd.get("autor",""))
        self.inp_titulo.setText(rd.get("titulo","")); self.inp_fecha.setText(rd.get("fecha",""))
        self.inp_sitio.setText(rd.get("sitio",""));   self.inp_revista.setText(rd.get("revista",""))
        self.inp_vol.setText(rd.get("volumen",""));   self.inp_num.setText(rd.get("numero",""))
        self.inp_pags.setText(rd.get("paginas",""))
        ti = self.cmb_tipo.findText(item.get("raw_tipo",""))
        if ti >= 0: self.cmb_tipo.setCurrentIndex(ti)
        fi = self.cmb_fmt.findText(item.get("raw_formato",""))
        if fi >= 0: self.cmb_fmt.setCurrentIndex(fi)
        self.chk_corp.setChecked(item.get("raw_corp", False))
        del self.colecciones[self.col_actual][idx]
        self._save_data(); self._pop_table()
        self.tabs.setCurrentIndex(0)
        self.flash_status("Cita cargada — edita, genera y añade de nuevo.", self._p["WARNING"], 5000)

    def _del_cit(self):
        idx = self.table.currentRow()
        items = self.colecciones.get(self.col_actual, [])
        if idx < 0 or idx >= len(items):
            self.flash_status("Selecciona una cita para eliminar.", self._p["WARNING"]); return
        if QMessageBox.question(self, "Eliminar", "¿Eliminar esta cita?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            del self.colecciones[self.col_actual][idx]
            self._save_data(); self._pop_table()
            self.flash_status("✓  Cita eliminada.", self._p["SUCCESS"])

    def _copy_all(self):
        if not self.colecciones[self.col_actual]:
            self.flash_status("La colección está vacía.", self._p["WARNING"]); return
        all_t = []
        for item in self.colecciones[self.col_actual]:
            all_t.extend(item["formato"]); all_t.append(("\n\n","normal"))
        self._copy_tuplas(all_t)

    def _change_path(self):
        folder = QFileDialog.getExistingDirectory(self, "Carpeta de guardado")
        if folder:
            self.archivo_datos = str(Path(folder) / "coleccion_apa.json")
            self._save_config(self.archivo_datos); self._save_data()
            self._upd_path()
            self.flash_status("✓  Ubicación de guardado actualizada.", self._p["SUCCESS"])

    def _import_data(self):
        path, _ = QFileDialog.getOpenFileName(self, "Importar", "", "JSON (*.json)")
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f: d = json.load(f)
                if isinstance(d, dict):   self.colecciones.update(d)
                elif isinstance(d, list): self.colecciones["Importados"] = d
                self._save_data(); self._refresh_col_ui()
                self.flash_status("✓  Colección importada.", self._p["SUCCESS"])
            except Exception as ex:
                QMessageBox.critical(self, "Error", f"No se pudo importar:\n{ex}")

    def _export_data(self):
        path, _ = QFileDialog.getSaveFileName(self, "Exportar", "Mis_Citas_APA.json", "JSON (*.json)")
        if path:
            if not path.endswith(".json"): path += ".json"
            try:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(self.colecciones, f, ensure_ascii=False, indent=4)
                self.flash_status("✓  Colección exportada.", self._p["SUCCESS"])
            except Exception as ex:
                QMessageBox.critical(self, "Error", f"No se pudo exportar:\n{ex}")

    def _check_updates(self, silent=True):
        self.upd = UpdateWorker(self.VERSION, self.URL_VERSION)
        self.upd.result.connect(lambda v, n: self._on_update(v, n, silent))
        self.upd.start()

    def _on_update(self, remote, newer, silent):
        if newer:
            if QMessageBox.question(self, "¡Actualización disponible!",
                f"Versión actual:  {self.VERSION}\nNueva versión:    {remote}\n\n¿Ir a la página de descarga?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            ) == QMessageBox.StandardButton.Yes:
                webbrowser.open(self.URL_DESCARGA)
        elif not silent:
            QMessageBox.information(self, "Sin actualizaciones",
                f"Ya tienes la última versión  ({self.VERSION}).")

    def _about(self):
        p = self._p
        dlg = QDialog(self)
        dlg.setWindowTitle("Acerca de Generador APA")
        dlg.setMinimumWidth(360)
        dlg.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        lay = QVBoxLayout(dlg)
        lay.setContentsMargins(32, 28, 32, 24); lay.setSpacing(8)

        t = QLabel("Generador de Citas APA")
        t.setAlignment(Qt.AlignmentFlag.AlignCenter)
        t.setStyleSheet(f"font-size:17px; font-weight:700; color:{p['ACCENT']}; background:transparent;")
        lay.addWidget(t)

        v = QLabel(f"Versión {self.VERSION}")
        v.setAlignment(Qt.AlignmentFlag.AlignCenter)
        v.setStyleSheet(f"color:{p['TEXT2']}; font-size:12px; background:transparent;")
        lay.addWidget(v)
        lay.addSpacing(10)

        team = QLabel("Desarrollado por GVTeam:\n\nGustavo Ramírez Mireles")
        team.setAlignment(Qt.AlignmentFlag.AlignCenter)
        team.setStyleSheet(f"color:{p['TEXT2']}; font-size:13px; line-height:1.7; background:transparent;")
        lay.addWidget(team)

        vi_row = QHBoxLayout(); vi_row.setSpacing(5)
        vi_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vic_lbl = QLabel("Victoria Maldonado Patiño")
        vic_lbl.setStyleSheet(f"color:{p['TEXT2']}; font-size:13px; background:transparent;")
        vi_row.addWidget(vic_lbl)
        heart_lbl = QLabel()
        heart_lbl.setPixmap(_icon("fa5s.heart", "#E05555").pixmap(QSize(13, 13)))
        heart_lbl.setStyleSheet("background:transparent;")
        vi_row.addWidget(heart_lbl)
        lay.addLayout(vi_row)
        lay.addStretch()

        btn = _btn("Cerrar", style="accent", p=p)
        btn.setMinimumWidth(100)
        btn.clicked.connect(dlg.accept)
        lay.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)
        dlg.adjustSize()
        dlg.exec()

if __name__ == "__main__":
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

    app = QApplication(sys.argv)
    app.setStyle("windowsvista")
    app.setFont(QFont("Segoe UI Variable", 10))

    win = GeneradorAPA()
    win.show()
    sys.exit(app.exec())