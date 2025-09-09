import os
import subprocess
import sys
from pathlib import Path


def main():
    project_root = Path(__file__).parent.parent
    main_script = project_root / "main.py"

    if not main_script.exists():
        print(f"Error: {main_script} not found!")
        sys.exit(1)

    cmd = [
        "pyinstaller",
        "--onefile",  # Create a single executable file
        "--windowed",  # Hide console window (GUI app)
        "--name",
        "clip-flow",  # Set executable name
        "--clean",  # Clean PyInstaller cache
        str(main_script),
    ]

    
    assets_dir = project_root / "assets"
    if assets_dir.exists():
        cmd.extend(["--add-data", f"{assets_dir}{os.pathsep}assets"])
        print(f"Including assets directory: {assets_dir}")
    else:
        print("Warning: assets directory not found; skipping assets")

    print("Building Python application with PyInstaller...")
    print(f"Command: {' '.join(cmd)}")

    try:
        subprocess.run(cmd, check=True, cwd=project_root)

        print("\nPython build completed successfully!")
        print(f"Executable created: {project_root / 'dist' / 'clip-flow.exe'}")
    except subprocess.CalledProcessError as e:
        print(f"\nPython build failed with exit code {e.returncode}")
        sys.exit(1)
    except FileNotFoundError:
        print(
            "\nPyInstaller not found. Make sure it's installed in the dev dependencies."
        )
        sys.exit(1)


if __name__ == "__main__":
    main()