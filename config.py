"""Gestion de la configuration de l'application (profils, fenêtres, hotkeys)."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import List

CONFIG_PATH = Path(__file__).parent / "config.json"
DEFAULT_CYCLE_HOTKEY = "ctrl+shift+tab"


@dataclass
class WindowConfig:
    window_id: int
    title: str
    alias: str = ""
    initiative: int = 0
    hotkey: str = ""


@dataclass
class ProfileConfig:
    name: str
    windows: List[WindowConfig] = field(default_factory=list)
    cycle_hotkey: str = DEFAULT_CYCLE_HOTKEY


@dataclass
class AppConfig:
    profiles: List[ProfileConfig] = field(default_factory=lambda: [ProfileConfig(name="Default")])
    selected_profile: str = "Default"


def _window_from_dict(raw: dict) -> WindowConfig:
    return WindowConfig(
        window_id=int(raw.get("window_id", 0)),
        title=str(raw.get("title", "")),
        alias=str(raw.get("alias", "")),
        initiative=int(raw.get("initiative", 0)),
        hotkey=str(raw.get("hotkey", "")),
    )


def _profile_from_dict(raw: dict) -> ProfileConfig:
    return ProfileConfig(
        name=str(raw.get("name", "Default")),
        windows=[_window_from_dict(w) for w in raw.get("windows", [])],
        cycle_hotkey=str(raw.get("cycle_hotkey", DEFAULT_CYCLE_HOTKEY)),
    )


def load_config(path: Path = CONFIG_PATH) -> AppConfig:
    """Charge la config depuis le disque. Retourne une config par défaut si absente ou corrompue."""
    if not path.exists():
        return AppConfig()

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return AppConfig()

    try:
        if "profiles" in raw:
            profiles = [_profile_from_dict(p) for p in raw.get("profiles", [])]
            if not profiles:
                profiles = [ProfileConfig(name="Default")]
            selected = raw.get("selected_profile", profiles[0].name)
            if selected not in {p.name for p in profiles}:
                selected = profiles[0].name
            return AppConfig(profiles=profiles, selected_profile=selected)

        # Migration automatique depuis l'ancien format (une seule liste de fenêtres à plat)
        legacy_windows = [_window_from_dict(w) for w in raw.get("windows", [])]
        legacy_profile = ProfileConfig(
            name="Default",
            windows=legacy_windows,
            cycle_hotkey=str(raw.get("cycle_hotkey", DEFAULT_CYCLE_HOTKEY)),
        )
        return AppConfig(profiles=[legacy_profile], selected_profile="Default")
    except (KeyError, TypeError, ValueError):
        return AppConfig()


def save_config(config: AppConfig, path: Path = CONFIG_PATH) -> None:
    """Sauvegarde la config sur disque de façon atomique.

    Écrire dans un fichier temporaire puis le renommer évite de se retrouver
    avec un config.json à moitié écrit (et donc corrompu) si l'app crashe ou
    perd l'alimentation pendant la sauvegarde.
    """
    tmp_path = path.with_suffix(".tmp")
    tmp_path.write_text(
        json.dumps(asdict(config), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    tmp_path.replace(path)
