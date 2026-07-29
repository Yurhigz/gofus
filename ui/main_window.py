"""Fenêtre principale de l'application (PyQt6)."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCloseEvent, QIcon
from PyQt6.QtWidgets import (
    QComboBox, QHBoxLayout, QHeaderView, QInputDialog, QLabel, QLineEdit,
    QMainWindow, QMenu, QMessageBox, QPushButton, QSpinBox, QSystemTrayIcon,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from config import AppConfig, ProfileConfig, WindowConfig, load_config, save_config
from hotkey_manager import HotkeyManager
from window_manager import activate_window, find_dofus_windows, is_window_valid
from ui.hotkey_capture_dialog import capture_hotkey
from ui.styles import STYLESHEET

DEFAULT_CYCLE_HOTKEY = "ctrl+shift+tab"
COLUMNS = ["Titre", "Alias", "Initiative", "Hotkey"]

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
APP_ICON_PATH = ASSETS_DIR / "icons" / "app_icon.ico"
TRAY_ICON_PATH = ASSETS_DIR / "icons" / "tray_icon.png"
MIN_WINDOW_SIZE = (760, 480)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Dofus Window Manager")
        self.resize(900, 580)
        self.setMinimumSize(*MIN_WINDOW_SIZE)
        if APP_ICON_PATH.exists():
            self.setWindowIcon(QIcon(str(APP_ICON_PATH)))
        self.setStyleSheet(STYLESHEET)

        self.config: AppConfig = load_config()
        self.active_profile: ProfileConfig = self._get_profile(self.config.selected_profile)
        self._refresh_windows_from_os()
        save_config(self.config)

        self.hotkeys = HotkeyManager()
        self.alias_visible = True

        self._build_ui()
        self._populate_profiles()
        self._reload_table()
        self._rebind_hotkeys()
        self._build_tray_icon()

    # ------------------------------------------------------------------ UI

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(14)

        # -- Barre du haut : titre + profil --------------------------------
        top_bar = QWidget()
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(0, 0, 0, 0)
        title_box = QVBoxLayout()
        title_box.addWidget(QLabel("Dofus Window Manager", objectName="Title"))
        title_box.addWidget(QLabel("Navigue entre tes fenêtres en un raccourci", objectName="Subtitle"))
        top_layout.addLayout(title_box)
        top_layout.addStretch()

        top_layout.addWidget(QLabel("Profil", objectName="FieldLabel"))
        self.profile_combo = QComboBox()
        self.profile_combo.currentTextChanged.connect(self._on_profile_changed)
        top_layout.addWidget(self.profile_combo)

        new_profile_btn = QPushButton("Nouveau")
        new_profile_btn.clicked.connect(self._on_new_profile)
        top_layout.addWidget(new_profile_btn)

        delete_profile_btn = QPushButton("Supprimer profil", objectName="DangerButton")
        delete_profile_btn.clicked.connect(self._on_delete_profile)
        top_layout.addWidget(delete_profile_btn)

        root.addWidget(top_bar)

        # -- Cycle hotkey ------------------------------------------------------
        cycle_row = QHBoxLayout()
        cycle_row.addWidget(QLabel("Raccourci de cycle (fenêtre suivante)", objectName="FieldLabel"))
        self.cycle_hotkey_edit = QLineEdit()
        self.cycle_hotkey_edit.setReadOnly(True)
        cycle_row.addWidget(self.cycle_hotkey_edit)
        cycle_pick_btn = QPushButton("Modifier")
        cycle_pick_btn.clicked.connect(self._on_pick_cycle_hotkey)
        cycle_row.addWidget(cycle_pick_btn)
        cycle_row.addStretch()
        root.addLayout(cycle_row)

        # -- Table des fenêtres ---------------------------------------------
        self.table = QTableWidget(0, len(COLUMNS))
        self.table.setHorizontalHeaderLabels(COLUMNS)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self._on_row_selected)
        root.addWidget(self.table, stretch=1)

        # -- Panneau d'édition -------------------------------------------------
        edit_panel = QWidget()
        edit_layout = QHBoxLayout(edit_panel)
        edit_layout.setContentsMargins(0, 0, 0, 0)

        edit_layout.addWidget(QLabel("Alias", objectName="FieldLabel"))
        self.alias_edit = QLineEdit()
        edit_layout.addWidget(self.alias_edit)

        edit_layout.addWidget(QLabel("Initiative", objectName="FieldLabel"))
        self.initiative_edit = QSpinBox()
        self.initiative_edit.setRange(0, 9999)
        edit_layout.addWidget(self.initiative_edit)

        edit_layout.addWidget(QLabel("Hotkey", objectName="FieldLabel"))
        self.hotkey_edit = QLineEdit()
        self.hotkey_edit.setReadOnly(True)
        edit_layout.addWidget(self.hotkey_edit)

        pick_hotkey_btn = QPushButton("Définir")
        pick_hotkey_btn.clicked.connect(self._on_pick_window_hotkey)
        edit_layout.addWidget(pick_hotkey_btn)

        update_btn = QPushButton("Mettre à jour", objectName="PrimaryButton")
        update_btn.clicked.connect(self._on_update_window)
        edit_layout.addWidget(update_btn)

        delete_btn = QPushButton("Supprimer", objectName="DangerButton")
        delete_btn.clicked.connect(self._on_delete_window)
        edit_layout.addWidget(delete_btn)

        root.addWidget(edit_panel)

        # -- Barre du bas --------------------------------------------------------
        bottom_bar = QHBoxLayout()
        refresh_btn = QPushButton("Rafraîchir les fenêtres")
        refresh_btn.clicked.connect(self._on_refresh)
        bottom_bar.addWidget(refresh_btn)

        toggle_alias_btn = QPushButton("Afficher/Masquer alias")
        toggle_alias_btn.clicked.connect(self._on_toggle_alias)
        bottom_bar.addWidget(toggle_alias_btn)

        bottom_bar.addStretch()

        save_btn = QPushButton("Sauvegarder", objectName="PrimaryButton")
        save_btn.clicked.connect(self._on_save)
        bottom_bar.addWidget(save_btn)

        root.addLayout(bottom_bar)

        self.statusBar().showMessage("Prêt.")

    def _build_tray_icon(self) -> None:
        self.tray = QSystemTrayIcon(self)
        icon_path = TRAY_ICON_PATH if TRAY_ICON_PATH.exists() else APP_ICON_PATH
        self.tray.setIcon(QIcon(str(icon_path)) if icon_path.exists() else self.windowIcon())
        menu = QMenu()
        show_action = menu.addAction("Afficher")
        show_action.triggered.connect(self.showNormal)
        menu.addSeparator()
        quit_action = menu.addAction("Quitter")
        quit_action.triggered.connect(self.close)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._on_tray_activated)
        self.tray.show()

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.showNormal()
            self.activateWindow()

    # ------------------------------------------------------------- Profils

    def _get_profile(self, name: str) -> ProfileConfig:
        for profile in self.config.profiles:
            if profile.name == name:
                return profile
        new_profile = ProfileConfig(name=name or "Default")
        self.config.profiles.append(new_profile)
        return new_profile

    def _populate_profiles(self) -> None:
        self.profile_combo.blockSignals(True)
        self.profile_combo.clear()
        self.profile_combo.addItems([p.name for p in self.config.profiles])
        self.profile_combo.setCurrentText(self.active_profile.name)
        self.profile_combo.blockSignals(False)
        self.cycle_hotkey_edit.setText(self.active_profile.cycle_hotkey or DEFAULT_CYCLE_HOTKEY)

    def _on_profile_changed(self, name: str) -> None:
        if not name:
            return
        self.active_profile = self._get_profile(name)
        self.config.selected_profile = name
        self.cycle_hotkey_edit.setText(self.active_profile.cycle_hotkey or DEFAULT_CYCLE_HOTKEY)
        self._reload_table()
        save_config(self.config)
        self._rebind_hotkeys()

    def _on_new_profile(self) -> None:
        name, ok = QInputDialog.getText(self, "Nouveau profil", "Nom du profil :")
        if ok and name.strip():
            self.active_profile = self._get_profile(name.strip())
            self.config.selected_profile = self.active_profile.name
            self._populate_profiles()
            self._reload_table()
            save_config(self.config)
            self._rebind_hotkeys()

    def _on_delete_profile(self) -> None:
        if len(self.config.profiles) <= 1:
            QMessageBox.warning(self, "Impossible", "Il doit rester au moins un profil.")
            return
        confirm = QMessageBox.question(
            self, "Confirmer", f"Supprimer le profil '{self.active_profile.name}' ?"
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        self.config.profiles = [p for p in self.config.profiles if p.name != self.active_profile.name]
        self.active_profile = self.config.profiles[0]
        self.config.selected_profile = self.active_profile.name
        self._populate_profiles()
        self._reload_table()
        save_config(self.config)
        self._rebind_hotkeys()

    # --------------------------------------------------------------- Table

    def _reload_table(self) -> None:
        windows = sorted(self.active_profile.windows, key=lambda w: w.initiative)
        self.table.setRowCount(len(windows))
        for row, window in enumerate(windows):
            alias_text = window.alias if self.alias_visible else ""
            values = [window.title, alias_text, str(window.initiative), window.hotkey]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row, col, item)

    def _selected_window(self) -> Optional[WindowConfig]:
        row = self.table.currentRow()
        if row < 0:
            return None
        windows = sorted(self.active_profile.windows, key=lambda w: w.initiative)
        if 0 <= row < len(windows):
            return windows[row]
        return None

    def _on_row_selected(self) -> None:
        window = self._selected_window()
        if window is None:
            return
        self.alias_edit.setText(window.alias)
        self.initiative_edit.setValue(window.initiative)
        self.hotkey_edit.setText(window.hotkey)

    def _on_update_window(self) -> None:
        window = self._selected_window()
        if window is None:
            QMessageBox.information(self, "Info", "Sélectionne une fenêtre dans le tableau.")
            return
        window.alias = self.alias_edit.text() or window.alias
        window.initiative = self.initiative_edit.value()
        window.hotkey = self.hotkey_edit.text()
        save_config(self.config)
        self._reload_table()
        self._rebind_hotkeys()
        self.statusBar().showMessage(f"Fenêtre '{window.title}' mise à jour.", 3000)

    def _on_delete_window(self) -> None:
        window = self._selected_window()
        if window is None:
            return
        self.active_profile.windows = [w for w in self.active_profile.windows if w.window_id != window.window_id]
        save_config(self.config)
        self._reload_table()
        self._rebind_hotkeys()

    def _on_toggle_alias(self) -> None:
        self.alias_visible = not self.alias_visible
        self._reload_table()

    # ------------------------------------------------------------- Hotkeys

    def _on_pick_window_hotkey(self) -> None:
        result = capture_hotkey(self, current=self.hotkey_edit.text())
        if result is not None:
            self.hotkey_edit.setText(result)

    def _on_pick_cycle_hotkey(self) -> None:
        result = capture_hotkey(self, current=self.cycle_hotkey_edit.text())
        if result:
            self.cycle_hotkey_edit.setText(result)
            self.active_profile.cycle_hotkey = result
            save_config(self.config)
            self._rebind_hotkeys()

    def _rebind_hotkeys(self) -> None:
        self.hotkeys.clear_hotkeys()

        cycle_key = self.active_profile.cycle_hotkey or DEFAULT_CYCLE_HOTKEY
        if not self.hotkeys.register_hotkey(cycle_key, self._cycle_windows):
            self.statusBar().showMessage(
                f"⚠ Impossible d'enregistrer le raccourci de cycle '{cycle_key}'.", 5000
            )

        for window in self.active_profile.windows:
            if not window.hotkey:
                continue
            bound_hwnd = window.window_id
            success = self.hotkeys.register_hotkey(window.hotkey, lambda h=bound_hwnd: activate_window(h))
            if not success:
                self.statusBar().showMessage(
                    f"⚠ Raccourci '{window.hotkey}' déjà utilisé (conflit possible).", 5000
                )

    def _cycle_windows(self) -> None:
        import win32gui  # import local : uniquement utile ici pour la fenêtre active

        valid = [w for w in self.active_profile.windows if is_window_valid(w.window_id)]
        if not valid:
            return
        ordered = sorted(valid, key=lambda w: w.initiative)
        active_hwnd = win32gui.GetForegroundWindow()
        current_index = next((i for i, w in enumerate(ordered) if w.window_id == active_hwnd), -1)
        next_index = 0 if current_index in (-1, len(ordered) - 1) else current_index + 1
        activate_window(ordered[next_index].window_id)

    # --------------------------------------------------------- Refresh / Save

    def _refresh_windows_from_os(self) -> None:
        found = find_dofus_windows()
        found_by_hwnd = {w.hwnd: w for w in found}
        found_by_title = {w.title: w for w in found}

        for saved in self.active_profile.windows:
            if saved.window_id in found_by_hwnd:
                found_by_title.pop(found_by_hwnd[saved.window_id].title, None)
                continue
            match = found_by_title.pop(saved.title, None)
            if match:
                saved.window_id = match.hwnd

        for remaining in found_by_title.values():
            self.active_profile.windows.append(
                WindowConfig(window_id=remaining.hwnd, title=remaining.title, alias=remaining.title)
            )

    def _on_refresh(self) -> None:
        self._refresh_windows_from_os()
        save_config(self.config)
        self._reload_table()
        self._rebind_hotkeys()
        self.statusBar().showMessage("Fenêtres rafraîchies.", 3000)

    def _on_save(self) -> None:
        self.config.selected_profile = self.active_profile.name
        save_config(self.config)
        self.statusBar().showMessage("Configuration sauvegardée.", 3000)

    # --------------------------------------------------------------- Fermeture

    def closeEvent(self, event: QCloseEvent) -> None:
        self.hotkeys.stop()
        self.tray.hide()
        super().closeEvent(event)
