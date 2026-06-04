# 🤝 Contributing to Volume Monitor

Hey, thanks for wanting to help out! Whether you're fixing a bug, adding a feature, or just poking around the code — contributions are very welcome.

---

## 🚀 Setting Up Your Dev Environment

### 1. Clone the repo

```bash
git clone https://github.com/Tech127x/volume-monitor.git
cd volume-monitor
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv .venv
source .venv/bin/activate
```

Then install the package in editable mode with dev dependencies:

```bash
pip install --editable ".[dev]"
```

This installs Volume Monitor plus all the tools you'll need: pytest, ruff, black, mypy, and pre-commit.

### 3. Or go straight with pipx

```bash
pipx install --editable .
```

Great for testing the CLI as your users would use it — no virtual environment needed. Just remember you won't have the dev tools available globally unless you install them separately.

### 4. Verify it works

```bash
volume-monitor --help
```

---

## 🧪 Running Tests

### With the test venv (recommended during development)

```bash
# Activate your venv first, then:
pytest
```

### Without the test venv

If you just have pipx but no venv, you can install test dependencies:

```bash
pip install pytest pytest-cov pytest-mock
pytest
```

### Run just a specific test file

```bash
pytest tests/test_config.py -v
```

### Run with coverage

```bash
pytest --cov=volume_monitor --cov-report=term-missing
```

Coverage reports are always shown by default (check `pyproject.toml`), but the `--cov-report=term-missing` flag adds the extra detail of which lines weren't hit.

---

## 🧹 Code Quality Tools

We keep things tidy with three tools. Run them before pushing:

### Ruff (linting with automatic fixing)

```bash
ruff check src/ tests/
ruff check src/ tests/ --fix   # Auto-fix what it can
```

### Black (formatting)

```bash
black src/ tests/
```

We use `line-length = 100` — Black will enforce it for you.

### Mypy (type checking)

```bash
mypy src/
```

We're progressively adding type hints, so don't worry if some files aren't fully typed yet. Just don't *remove* existing annotations.

### One-liner to run all three

```bash
ruff check src/ tests/ && black --check src/ tests/ && mypy src/
```

Or use `--check` on Black if you just want to see what would change without reformatting.

---

## 📁 Project Structure

```
volume-monitor/
├── src/
│   └── volume_monitor/          # Main package
│       ├── __init__.py
│       ├── __main__.py          # Entry point
│       ├── cli.py               # CLI argument parsing & dispatch
│       ├── cli_utils.py         # CLI helper utilities
│       ├── config.py            # Config management
│       ├── constants.py         # Shared constants
│       ├── fish_support.py      # Fish shell integration
│       ├── logging_setup.py     # Logging configuration
│       ├── audio/               # Audio backend (PipeWire/WirePlumber)
│       ├── companion/           # BitFocus Companion API client
│       ├── monitors/            # Polling & event monitors
│       └── utils/               # Shared utilities & helpers
├── tests/                       # Test suite (mirrors src layout)
│   ├── conftest.py
│   ├── test_audio_devices.py
│   ├── test_audio_pipewire.py
│   ├── test_companion_client.py
│   ├── test_config.py
│   ├── test_end_to_end.py
│   ├── test_fish_support.py
│   ├── test_integration.py
│   ├── test_package_structure.py
│   └── test_utils_normalization.py
├── docs/                        # Documentation & wiki resources
├── scripts/                     # Helper scripts
├── pyproject.toml               # Project config & tool settings
├── Makefile                     # Common task shortcuts
├── README.md                    # You are here
└── CONTRIBUTING.md              # This file
```

### Subpackage breakdown

| Subpackage | What lives there |
|---|---|
| `audio/` | PipeWire discovery, device/stream listing, volume control |
| `companion/` | HTTP client for BitFocus Companion's TCP API |
| `monitors/` | Background pollers that detect audio/device changes |
| `utils/` | Normalization helpers, format utilities, shared helpers |

Tests live in `tests/` and follow the naming convention `test_<module>.py`.

---

## 🔧 Making a Pull Request

1. **Fork** the repo on GitHub.
2. **Create a branch** with a descriptive name:
   ```bash
   git checkout -b fix/volume-memory-off-by-one
   ```
   Branch prefixes: `fix/`, `feat/`, `docs/`, `refactor/`, `chore/`.
3. **Make your changes** — keep them focused on one thing.
4. **Run the quality checks**:
   ```bash
   ruff check src/ tests/
   black src/ tests/
   mypy src/
   pytest
   ```
5. **Commit** with a clear message:
   ```bash
   git commit -m "fix: off-by-one error in volume memory for new apps"
   ```
6. **Push** and open a PR against `main`.

### What we look for in a PR

- One logical change per PR. Small PRs get reviewed faster.
- Tests for new functionality or bug fixes.
- Existing tests still pass (obviously).
- Type hints on any new public functions (we're lenient inside private helpers).
- Matching the existing style (see below).

---

## 📐 Style Guide Notes

- **Line length**: 100 characters. Black enforces this, so just let it do its thing.
- **Python version**: 3.9+ — no walrus operators, no `match`/`case`, no `str.removeprefix` without a compat helper.
- **Type hints**: Strongly encouraged for public APIs, optional but welcome everywhere else. We use `mypy` with `--warn-return-any` to catch obvious gaps.
- **Imports**: Use Ruff with the "I" ruleset to keep them sorted. Run `ruff check --fix` to auto-sort.
- **Naming**: `snake_case` for functions and variables, `UPPER_CASE` for constants, `PascalCase` for classes. No surprises.
- **Docstrings**: Use triple double-quotes (`"""..."""`). Brief is better than verbose — explain *why*, not *what*.
- **Error messages**: User-facing errors should be actionable. Instead of "Error: invalid config", say "Config file not found at ~/.volume_monitor_config.json. Run `volume-monitor --configure` to create one."
- **Logging**: Use the `logging_setup` module. Debug logs can be chatty, info logs should be meaningful, error logs should include context.

---

## ❓ Questions?

Open a [discussion](https://github.com/Tech127x/volume-monitor/discussions) or an [issue](https://github.com/Tech127x/volume-monitor/issues). We're friendly!

Happy hacking! 🎛️
