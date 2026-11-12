# Agent Replay development guide

## Architecture

The Python package contains versioned trace models, provider import adapters, deterministic replay and comparison, a Typer CLI, and pytest integration. Examples use synthetic data only.

## Conventions

- Support Python 3.11 and later; use typed public APIs and Pydantic validation.
- Keep replay offline and deterministic; never execute tools from untrusted traces.
- Preserve user data and never commit credentials or private traces.
- Changes to trace format require explicit version handling and tests.
- Tests should cover real behavior and failure cases; target 80% core coverage.

## Commands

- Install: `uv sync --all-groups --no-editable`
- Test: `uv run --no-editable pytest --cov=agent_replay --cov-report=term-missing`
- Lint: `uv run --no-editable ruff check .`
- Typecheck: `uv run --no-editable mypy src`
- Build: `uv build`

## Future tasks

Keep changes small and reviewable. Run relevant checks, document user-visible changes, and avoid publishing packages or modifying external services without authorization.

## Replay and matching

Trace comparisons compare supplied data; only an agent run wired to the mock replay can reveal new behavior. Never import or execute tools named in trace files. Strict matching compares JSON values exactly, including key order; loose matching ignores object key order and configured keys, and allows only explicitly declared optional extra argument fields. Keep provider adapters limited to documented message subsets and reject incomplete pairs. CI must run Ruff, mypy, pytest with coverage, and build.
