# Migration Notes - Professional Structure

## What Changed

The project has been reorganized from a single-file structure to a professional modular architecture.

## New Structure

- **`smart_glass/`** - Main package with all core functionality
  - **`hardware/`** - Hardware interfaces (GPIO, Camera, Ultrasonic)
  - **`modes/`** - Mode implementations (Time, Text Recognition, Object Detection, Distance)
  - **`audio/`** - Audio handling (TTS, Audio Queue)
  - **`utils/`** - Utility functions (Logging)
  - **`main.py`** - Main orchestrator

- **`tests/`** - All test files
- **`scripts/`** - Utility scripts
- **`docs/`** - Documentation files

## How to Use

### Old Way (deprecated)
```bash
python3 smart_glass.py
```

### New Way (recommended)
```bash
python3 run.py
# or
python3 -m smart_glass.main
# or (after pip install -e .)
smart-glass
```

## Benefits

1. **Modularity**: Each component is in its own module
2. **Maintainability**: Easy to find and modify specific features
3. **Testability**: Tests separated from main code
4. **Scalability**: Easy to add new modes or features
5. **Professional**: Follows Python package best practices

## Old Files

The following files are kept for reference but are no longer used:
- `smart_glass.py` - Original monolithic file
- `smart_glassb_boxes.py` - Alternative version
- `smart_glass_web.py` - Web version
- `smart_glass_simple.py` - Simplified version

These are ignored by git (see `.gitignore`).

## Configuration

The `config.py` file in the root directory is still supported and will be automatically loaded if present.

## Testing

All test files have been moved to `tests/` directory:
- `tests/test_buttons.py`
- `tests/test_camera.py`
- `tests/test_display.py`

Run them the same way:
```bash
python3 tests/test_buttons.py
```

