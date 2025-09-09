import subprocess
import sys
from pathlib import Path


def run_script(script_path: Path) -> bool:
    try:
        subprocess.run(
            [sys.executable, str(script_path)], 
            check=True,
            cwd=script_path.parent.parent
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running {script_path.name}: exit code {e.returncode}")
        return False
    except Exception as e:
        print(f"Unexpected error running {script_path.name}: {e}")
        return False


def main():
    scripts_dir = Path(__file__).parent
    
    build_frontend_script = scripts_dir / "build_frontend.py"
    build_python_script = scripts_dir / "build_python.py"
    
    print("Starting complete build process...")
    print("=" * 50)
    
    print("\n1. Building frontend...")
    if not build_frontend_script.exists():
        print(f"Error: {build_frontend_script} not found!")
        sys.exit(1)
    
    if not run_script(build_frontend_script):
        print("Frontend build failed!")
        sys.exit(1)
    
    print("Frontend build completed successfully!")
    
    print("\n2. Building Python application...")
    if not build_python_script.exists():
        print(f"Error: {build_python_script} not found!")
        sys.exit(1)
    
    if not run_script(build_python_script):
        print("Python build failed!")
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("Complete build process finished successfully!")
    project_root = Path(__file__).parent.parent
    print(f"Executable created: {project_root / 'dist' / 'clip-flow.exe'}")


if __name__ == "__main__":
    main()
