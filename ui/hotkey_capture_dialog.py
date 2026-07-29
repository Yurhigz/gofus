"""Boîte de dialogue de capture de raccourci clavier, basée sur QKeySequenceEdit
(widget Qt natif -- plus fiable que de mélanger la lib `keyboard` avec les
événements de la fenêtre, qui pouvait désynchroniser modificateurs et touche
dans la v1 du projet)."""
from __future__ import annotations

from typing import Optional

from PyQt6.QtGui import QKeySequence
from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QKeySequenceEdit, QLabel, QVBoxLayout


class HotkeyCaptureDialog(QDialog):
    def __init__(self, parent=None, current: str = "") -> None:
        super().__init__(parent)
        self.setWindowTitle("Définir un raccourci")
        self.setModal(True)
        self.setMinimumWidth(320)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Appuie sur la combinaison souhaitée :"))

        self.edit = QKeySequenceEdit(self)
        if current:
            self.edit.setKeySequence(QKeySequence(_normalize_for_qt(current)))
        layout.addWidget(self.edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def hotkey_string(self) -> str:
        """Retourne le raccourci au format 'ctrl+shift+tab' utilisé par le reste de l'app."""
        sequence = self.edit.keySequence()
        if sequence.isEmpty():
            return ""
        # QKeySequenceEdit peut en théorie enchaîner plusieurs combinaisons ;
        # on ne garde que la première ici, c'est tout ce dont on a besoin.
        text = sequence.toString(QKeySequence.SequenceFormat.PortableText)
        first = text.split(",")[0].strip()
        return first.lower().replace(" ", "")


def _normalize_for_qt(hotkey: str) -> str:
    """Convertit 'ctrl+shift+tab' vers le format attendu par QKeySequence ('Ctrl+Shift+Tab')."""
    parts = [p.strip() for p in hotkey.split("+") if p.strip()]
    return "+".join(part.capitalize() for part in parts)


def capture_hotkey(parent=None, current: str = "") -> Optional[str]:
    """Ouvre le dialogue et retourne le raccourci choisi, ou None si annulé."""
    dialog = HotkeyCaptureDialog(parent, current)
    if dialog.exec() == QDialog.DialogCode.Accepted:
        return dialog.hotkey_string()
    return None
