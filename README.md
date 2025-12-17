# ODIN API

OdinAPI was rewritten 2023 to run in AWS, using ECS Fargate, S3, and posgresql hosted on Chalmers.

## Preparing the development environment

### Python environment

Python dependencies are managed with **uv** and declared in `pyproject.toml`.

Create and populate a virtual environment with development dependencies:

```bash
uv sync
```

### Node.js environment

```bash
npm install
```

```bash
npm run build
```

```bash
npm test
```


## Running tests locally

To run all tests, this requires correct AWS credentials, and running mongodb and postgresql docker containers.

```bash
uv run pytest
```

There are some markers defined for tests:
- `aws`: tests that require access to AWS S3
- `slow`: tests that are slow to run (e.g., integration tests)
- `system`: tests that require the full system to be running.

to run only unittests:

```bash
uv run pytest -m "not (slow or system or aws)"
```

## Linting

```bash
uv run black --check .
```
```bash
uv run ruff check .
```

## Type checking
```bash
uv run mypy .
```

## Running the API

```bash
uv run flask --app odinapi.api:run run
```

