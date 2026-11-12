# Contributing

Use Python 3.11+ and uv. Run `uv sync --all-groups --no-editable`, `uv run --no-editable ruff check .`, `uv run --no-editable mypy src`, `uv run --no-editable pytest --cov=agent_replay --cov-report=term-missing`, and `uv build`. Add focused tests for behavior and failure cases. Use synthetic traces, never secrets. Discuss format changes and preserve version compatibility. Submit small, documented pull requests.
