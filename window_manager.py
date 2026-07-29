"""Détection et manipulation des fenêtres du jeu Dofus (API Win32)."""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List

import win32api
import win32con
import win32gui
import win32process

# Mots-clés à exclure même si le process ressemble à Dofus (launcher, panneau
# Ankama, etc.) -- ces fenêtres ne sont pas des instances de jeu jouables.
_EXCLUDED_TITLE_KEYWORDS = ("launcher", "ankama", "panel", "settings", "zaap")


@dataclass
class DofusWindow:
    hwnd: int
    title: str


def _process_name(hwnd: int) -> str:
    """Nom (sans extension) de l'exécutable propriétaire de la fenêtre, ou "" si échec."""
    try:
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        handle = win32api.OpenProcess(
            win32con.PROCESS_QUERY_INFORMATION | win32con.PROCESS_VM_READ,
            False,
            pid,
        )
    except Exception:
        return ""

    try:
        path = win32process.GetModuleFileNameEx(handle, 0) or ""
        return os.path.splitext(os.path.basename(path))[0].lower()
    except Exception:
        return ""
    finally:
        win32api.CloseHandle(handle)


def _is_dofus_window(hwnd: int) -> bool:
    if not win32gui.IsWindowVisible(hwnd):
        return False
    if win32gui.GetWindow(hwnd, win32con.GW_OWNER) != 0:
        return False
    if win32gui.GetParent(hwnd) != 0:
        return False

    title = (win32gui.GetWindowText(hwnd) or "").strip()
    if not title:
        return False

    lower_title = title.lower()
    if any(keyword in lower_title for keyword in _EXCLUDED_TITLE_KEYWORDS):
        return False

    # Le nom du process est la source de vérité : le format du titre de fenêtre
    # peut changer d'une version du jeu à l'autre, contrairement au nom de l'exe.
    name = _process_name(hwnd)
    return name.startswith("dofus") and "launcher" not in name


def find_dofus_windows() -> List[DofusWindow]:
    """Énumère toutes les fenêtres visibles appartenant à un process Dofus."""
    windows: List[DofusWindow] = []

    def _callback(hwnd: int, _extra) -> bool:
        if _is_dofus_window(hwnd):
            windows.append(DofusWindow(hwnd=hwnd, title=win32gui.GetWindowText(hwnd) or ""))
        return True

    win32gui.EnumWindows(_callback, None)
    return windows


def is_window_valid(hwnd: int) -> bool:
    return bool(hwnd) and win32gui.IsWindow(hwnd) and win32gui.IsWindowVisible(hwnd)


def activate_window(hwnd: int) -> bool:
    """Donne le focus à une fenêtre.

    Windows empêche par défaut un process de "voler" le focus à un autre :
    il faut attacher temporairement le thread courant à celui de la fenêtre
    cible (AttachThreadInput) pour que SetForegroundWindow fonctionne de
    façon fiable, y compris quand le focus est actuellement ailleurs.
    """
    if not is_window_valid(hwnd):
        return False

    current_thread_id = win32api.GetCurrentThreadId()
    window_thread_id, _ = win32process.GetWindowThreadProcessId(hwnd)
    attached = False

    try:
        if current_thread_id != window_thread_id:
            attached = win32process.AttachThreadInput(current_thread_id, window_thread_id, True)

        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        win32gui.BringWindowToTop(hwnd)
        win32gui.SetForegroundWindow(hwnd)
        return True
    except Exception:
        return False
    finally:
        if attached:
            win32process.AttachThreadInput(current_thread_id, window_thread_id, False)
