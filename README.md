# Clip Flow

A clipboard history manager with search functionality.

## Installation

1. Clone the repository
2. Install dependencies using uv:
   ```bash
   uv sync
   ```

## Usage

Run the application:
```bash
uv run python main.py
```

### Frontend

- Source HTML lives under `frontend/`.
- Build/copy to `assets/`:
  ```bash
  uv run python scripts/build_frontend.py
  # or
  python scripts/build_frontend.py
  ```
- The app loads pages from `assets/` only (no inline fallback).

## Development

### Linting and Formatting

Format code with Ruff:
```bash
uvx ruff format .
```

Check code style:
```bash
uvx ruff check .
```

## TODO

### DevOps & Quality
- [ ] Set up comprehensive linting configuration
- [ ] Configure CI/CD pipeline
- [ ] Set up semantic release automation
- [ ] Add pre-commit hooks
- [ ] Set up test coverage reporting
- [ ] Add Windows Installer

### Configuration & Settings
- [ ] Extract settings to configuration file
- [ ] Add configurable settings interface
- [ ] Add hotkey customization
- [ ] Add clipboard size limits configuration

### Features
- [ ] Favorites/pin: pin items to top
- [ ] Deduplication: merge duplicates; show occurrence count
- [ ] Multi-select: bulk actions (copy/delete)
- [ ] Search highlight: highlight matches in list
- [ ] Ignore list: exclude apps/patterns from history
- [ ] App exceptions: skip clipboard from sensitive apps
- [ ] Resize/persist: remember window size/position
- [ ] Support image clipboard history
- [ ] Support files clipboard history
- [ ] Right-click context menu on history items (with Delete) or using the Del key

### Platform Support
- [ ] Create installer packages
- [ ] Add auto-update functionality
