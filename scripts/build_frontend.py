from __future__ import annotations

from pathlib import Path
import shutil


def copytree(src: Path, dst: Path) -> None:
    if not src.exists():
        raise SystemExit(f"Source not found: {src}")
    dst.mkdir(parents=True, exist_ok=True)
    for path in src.rglob("*"):
        rel = path.relative_to(src)
        target = dst / rel
        if path.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    src_dir = root / "frontend"
    dst_dir = root / "assets"

    print(f"Building frontend: {src_dir} -> {dst_dir}")
    copytree(src_dir, dst_dir)
    print("Done.")


if __name__ == "__main__":
    main()
