"""Gestion des hotkeys globaux via l'API Win32 (RegisterHotKey), avec repli sur
la librairie `keyboard` si un raccourci est déjà pris par une autre application."""
from __future__ import annotations

import queue
import threading
from typing import Any, Callable, Dict, List, Optional, Tuple

import keyboard
import win32api
import win32con
import win32gui

_KEY_MAP = {
    "tab": 0x09, "enter": 0x0D, "return": 0x0D, "esc": 0x1B, "escape": 0x1B,
    "space": 0x20, "left": 0x25, "up": 0x26, "right": 0x27, "down": 0x28,
    "home": 0x24, "end": 0x23, "pageup": 0x21, "pagedown": 0x22,
    "insert": 0x2D, "delete": 0x2E,
    **{f"f{i}": 0x6F + i for i in range(1, 13)},  # f1..f12 -> 0x70..0x7B
}


def parse_hotkey(hotkey: str) -> Optional[Tuple[int, int]]:
    """Convertit une chaîne type 'ctrl+shift+tab' en (modifiers, virtual_key_code)."""
    if not hotkey:
        return None

    parts = [p.strip().lower() for p in hotkey.split("+") if p.strip()]
    if not parts:
        return None

    key = parts[-1]
    modifiers = 0
    for part in parts[:-1]:
        if part in ("ctrl", "control"):
            modifiers |= win32con.MOD_CONTROL
        elif part == "shift":
            modifiers |= win32con.MOD_SHIFT
        elif part in ("alt", "menu"):
            modifiers |= win32con.MOD_ALT
        elif part in ("win", "windows", "cmd"):
            modifiers |= win32con.MOD_WIN

    vk = _KEY_MAP.get(key)
    if vk is None:
        if len(key) == 1 and key.isalnum():
            vk = ord(key.upper())
        else:
            return None

    return modifiers, vk


class HotkeyManager:
    """Gère les hotkeys globaux dans un thread dédié avec sa propre boucle de messages Win32.

    RegisterHotKey nécessite une fenêtre (même invisible) et une vraie boucle de
    messages GetMessage/PeekMessage pour recevoir WM_HOTKEY -- d'où ce thread isolé,
    séparé du thread Qt principal.
    """

    def __init__(self) -> None:
        self._callbacks: Dict[int, Callable[[], None]] = {}
        self._hotkey_ids: List[int] = []
        self._fallback_handles: List[Any] = []
        self._next_id = 1
        self._hwnd: Optional[int] = None
        self._ready = threading.Event()
        self._commands: "queue.Queue[Tuple[str, Any]]" = queue.Queue()
        self._thread = threading.Thread(target=self._message_loop, daemon=True)
        self._thread.start()
        self._ready.wait(timeout=2)

    # -- Thread interne -------------------------------------------------

    def _message_loop(self) -> None:
        class_name = "DofusHotkeyWindowClass"
        wc = win32gui.WNDCLASS()
        wc.lpfnWndProc = {win32con.WM_HOTKEY: self._on_hotkey}
        wc.lpszClassName = class_name
        wc.hInstance = win32api.GetModuleHandle(None)

        try:
            win32gui.RegisterClass(wc)
        except Exception:
            pass  # déjà enregistrée (relance dans le même process, tests...)

        self._hwnd = win32gui.CreateWindowEx(
            0, class_name, class_name, 0, 0, 0, 0, 0, 0, 0, wc.hInstance, None
        )
        self._ready.set()

        running = True
        while running:
            try:
                command, payload = self._commands.get(timeout=0.05)
            except queue.Empty:
                pass
            else:
                running = self._handle_command(command, payload)

            # Vide complètement la file de messages Windows en attente.
            # Un seul PeekMessage par itération peut en perdre si plusieurs
            # WM_HOTKEY arrivent d'un coup (bug de la v1).
            while win32gui.PeekMessage(None, 0, 0, win32con.PM_REMOVE):
                win32gui.PumpWaitingMessages()

        if self._hwnd is not None:
            win32gui.DestroyWindow(self._hwnd)
            self._hwnd = None

    def _handle_command(self, command: str, payload: Any) -> bool:
        if command == "register":
            hotkey_id, modifiers, vk, callback, response = payload
            success = False
            try:
                success = bool(win32gui.RegisterHotKey(self._hwnd, hotkey_id, modifiers, vk))
            except Exception:
                success = False
            if success:
                self._callbacks[hotkey_id] = callback
                self._hotkey_ids.append(hotkey_id)
            response.put(success)
        elif command == "unregister":
            hotkey_id = payload
            try:
                win32gui.UnregisterHotKey(self._hwnd, hotkey_id)
            except Exception:
                pass
            self._callbacks.pop(hotkey_id, None)
            if hotkey_id in self._hotkey_ids:
                self._hotkey_ids.remove(hotkey_id)
        elif command == "exit":
            return False
        return True

    def _on_hotkey(self, hwnd: int, msg: int, wparam: int, lparam: int) -> int:
        callback = self._callbacks.get(wparam)
        if callback:
            callback()
        return 0

    # -- API publique -----------------------------------------------------

    def register_hotkey(self, hotkey: str, callback: Callable[[], None]) -> bool:
        """Enregistre un hotkey global. Retombe sur la lib `keyboard` si Win32 échoue
        (raccourci déjà pris par une autre appli, par ex.). Retourne True si l'un des
        deux mécanismes a fonctionné, False sinon (permet à l'appelant d'avertir
        l'utilisateur d'un conflit plutôt que d'échouer silencieusement)."""
        parsed = parse_hotkey(hotkey)
        if parsed and self._hwnd is not None:
            modifiers, vk = parsed
            hotkey_id = self._next_id
            self._next_id += 1
            response: "queue.Queue[bool]" = queue.Queue()
            self._commands.put(("register", (hotkey_id, modifiers, vk, callback, response)))
            try:
                if response.get(timeout=1):
                    return True
            except queue.Empty:
                pass

        try:
            handle = keyboard.add_hotkey(hotkey, callback)
            self._fallback_handles.append(handle)
            return True
        except Exception:
            return False

    def clear_hotkeys(self) -> None:
        for hotkey_id in list(self._hotkey_ids):
            self._commands.put(("unregister", hotkey_id))
        for handle in self._fallback_handles:
            try:
                keyboard.remove_hotkey(handle)
            except Exception:
                pass
        self._fallback_handles.clear()

    def stop(self) -> None:
        self.clear_hotkeys()
        self._commands.put(("exit", None))
        self._thread.join(timeout=1)
