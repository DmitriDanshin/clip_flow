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

    schema_file = project_root / "settings_schema.json"
    if schema_file.exists():
        cmd.extend(["--add-data", f"{schema_file}{ os.pathsep}."])
        print(f"Including data file: {schema_file}")
    else:
        print("Warning: settings_schema.json not found at project root; skipping --add-data")

    print("Building clip-flow with PyInstaller...")
    print(f"Command: {' '.join(cmd)}")

    try:
        subprocess.run(cmd, check=True, cwd=project_root)

        print("\nBuild completed successfully!")
        print(f"Executable created: {project_root / 'dist' / 'clip-flow.exe'}")
    except subprocess.CalledProcessError as e:
        print(f"\nBuild failed with exit code {e.returncode}")
        sys.exit(1)
    except FileNotFoundError:
        print(
            "\nPyInstaller not found. Make sure it's installed in the dev dependencies."
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
