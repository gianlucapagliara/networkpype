# Contributing

## Development Setup

Clone the repository and install dependencies:

```bash
git clone https://github.com/gianlucapagliara/networkpype.git
cd networkpype
uv sync
```

## Running Tests

```bash
uv run pytest
```

With coverage:

```bash
uv run pytest --cov=networkpype --cov-report=term-missing
```

## Code Quality

### Linting and Formatting

```bash
# Check code style
uv run ruff check .

# Auto-fix issues
uv run ruff check --fix .

# Format code
uv run ruff format .
```

### Type Checking

```bash
uv run mypy networkpype
```

The project uses MyPy in strict mode. All public functions must have type annotations.

### Pre-commit Hooks

Install hooks to run checks automatically before each commit:

```bash
uv run pre-commit install
```

Run all hooks manually:

```bash
uv run pre-commit run --all-files
```

## Project Structure

```
networkpype/
├── networkpype/
│   ├── __init__.py
│   ├── auth.py                        # Auth abstract base class
│   ├── factory.py                     # ConnectionsFactory, ConnectionManagersFactory
│   ├── time_synchronizer.py           # TimeSynchronizer
│   ├── rest/
│   │   ├── __init__.py
│   │   ├── connection.py              # RESTConnection
│   │   ├── manager.py                 # RESTManager
│   │   ├── method.py                  # RESTMethod enum
│   │   ├── request.py                 # RESTRequest dataclass
│   │   ├── response.py                # RESTResponse
│   │   └── processor/
│   │       ├── base.py                # RESTPreProcessor, RESTPostProcessor
│   │       └── time_synchronizer.py   # TimeSynchronizerRESTPreProcessor
│   ├── websocket/
│   │   ├── __init__.py
│   │   ├── connection.py              # WebSocketConnection
│   │   ├── manager.py                 # WebSocketManager
│   │   ├── request.py                 # WebSocketRequest, WebSocketJSONRequest, WebSocketPlainTextRequest
│   │   ├── response.py                # WebSocketResponse
│   │   └── processor/
│   │       └── base.py                # WebSocketPreProcessor, WebSocketPostProcessor
│   └── throttler/
│       ├── __init__.py
│       ├── context.py                 # AsyncRequestContext
│       ├── rate_limit.py              # RateLimit, LinkedLimitWeightPair, TaskLog
│       └── throttler.py               # AsyncThrottler
├── tests/
│   ├── conftest.py
│   ├── rest/
│   │   └── ...
│   └── websocket/
│       └── ...
├── docs/                              # Documentation (mkdocs)
└── pyproject.toml
```

## Building Documentation

Install docs dependencies and run the mkdocs development server:

```bash
uv sync --group docs
uv run mkdocs serve
```

Build the static site:

```bash
uv run mkdocs build --strict
```

## Releasing

Releases are tagged on `main` and published to PyPI via the GitHub Actions `publish.yml` workflow.

1. Bump the version in `pyproject.toml`
2. Commit with message `chore: bump version to X.Y.Z`
3. Create and push a git tag: `git tag vX.Y.Z && git push origin vX.Y.Z`
4. Create a GitHub release from the tag — this triggers the publish workflow

## CI/CD

- **CI** runs on every push and PR to `main`: linting (ruff), type checking (mypy), and tests with coverage
- **Publish** runs on GitHub release creation: tests, build, and publish to PyPI
- **Docs** deploys to GitHub Pages on every push to `main`
