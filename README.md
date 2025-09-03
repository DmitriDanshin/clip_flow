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

### Configuration & Settings
- [ ] Extract settings to configuration file
- [ ] Add configurable settings interface
- [ ] Add hotkey customization
- [ ] Add clipboard size limits configuration

### Features
- [ ] Add clipboard item favorites
- [ ] Support image clipboard history
- [ ] Support files clipboard history

### Platform Support
- [ ] Create installer packages
- [ ] Add auto-update functionality