"""Point d'entrée de l'application."""
import sys
from pathlib import Path

# Garantit que le dossier du projet est dans sys.path, peu importe le
# répertoire courant depuis lequel `uv run` / `python` est invoqué.
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from PyQt6.QtGui import QFont, QFontDatabase
from PyQt6.QtWidgets import QApplication

from ui.main_window import MainWindow

FONTS_DIR = PROJECT_ROOT / "assets" / "fonts"
FONT_FILES = ["Poppins-Regular.ttf", "Poppins-Medium.ttf", "Poppins-SemiBold.ttf", "Poppins-Bold.ttf"]


def _load_bundled_fonts() -> None:
    """Charge Poppins depuis les fichiers embarqués (pas d'installation système requise)."""
    for filename in FONT_FILES:
        font_path = FONTS_DIR / filename
        if font_path.exists():
            QFontDatabase.addApplicationFont(str(font_path))


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # base neutre sur laquelle le QSS s'applique proprement
    _load_bundled_fonts()
    app.setFont(QFont("Poppins", 10))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
