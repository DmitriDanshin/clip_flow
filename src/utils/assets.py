from __future__ import annotations

from pathlib import Path
import sys


def _find_project_root(start: Path | None = None) -> Path:
    here = (start or Path(__file__)).resolve()
    for parent in here.parents:
        if parent.name == "src":
            return parent.parent

    try:
        return here.parents[2]
    except Exception:
        return Path.cwd()


def assets_dir() -> Path:
    # Для PyInstaller - проверяем временную папку
    if hasattr(sys, "_MEIPASS"):
        # Собранное приложение
        bundled_assets = Path(sys._MEIPASS) / "assets"
        if bundled_assets.exists():
            return bundled_assets

    # Обычный режим разработки
    root = _find_project_root()
    candidates = [root / "assets", Path.cwd() / "assets"]
    for d in candidates:
        if d.exists():
            return d
    return candidates[0]


def asset_uri(filename: str) -> str | None:
    path = assets_dir() / filename
    if path.exists():
        return path.resolve().as_uri()
    return None
