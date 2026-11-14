"""Command line interface."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer
from pydantic import ValidationError

from .adapters import import_messages
from .compare import compare
from .models import dump_trace, load_trace, read_json

app = typer.Typer(no_args_is_help=True)


@app.command("validate")
def validate_command(traces: Annotated[list[Path], typer.Argument()],
                     json_output: Annotated[bool, typer.Option("--json")] = False) -> None:
    """Validate one or more traces against the supported versioned format."""
    failed = False
    results: list[dict[str, object]] = []
    for trace in traces:
        try:
            parsed = load_trace(trace)
        except (OSError, ValueError, ValidationError) as exc:
            results.append({"path": str(trace), "valid": False, "error": str(exc)})
            if not json_output:
                typer.secho(f"Error: {trace}: {exc}", fg=typer.colors.RED, err=True)
            failed = True
            continue
        results.append({"path": str(trace), "valid": True, "schema_version": parsed.schema_version,
                        "step_count": len(parsed.steps)})
        if not json_output:
            typer.secho(
                f"PASS: {trace}: schema version {parsed.schema_version}, {len(parsed.steps)} steps",
                fg=typer.colors.GREEN,
            )
    if json_output:
        typer.echo(json.dumps({"valid": not failed, "results": results}, indent=2))
    if failed:
        raise typer.Exit(2)


@app.command("compare")
def compare_command(expected: Path, actual: Path, loose: bool = False,
                    ignore: Annotated[list[str] | None, typer.Option()] = None,
                    optional: Annotated[list[str] | None, typer.Option()] = None,
                    json_report: Path | None = None) -> None:
    """Compare two traces; ACTUAL must come from an independently observed run."""
    try:
        report = compare(load_trace(expected), load_trace(actual),
                         "loose" if loose else "strict", set(ignore or []), set(optional or []))
        if json_report:
            payload = {"passed": report.passed, **report.model_dump()}
            json_report.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        if report.passed:
            typer.secho("PASS: traces match", fg=typer.colors.GREEN)
        else:
            for diff in report.differences:
                typer.secho(f"{diff.path}: {diff.reason}", fg=typer.colors.RED)
                typer.echo(f"  expected: {diff.expected!r}\n  actual:   {diff.actual!r}")
            raise typer.Exit(1)
    except (OSError, ValueError, ValidationError) as exc:
        typer.secho(f"Error: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(2) from exc


@app.command("import")
def import_command(provider: str, source: Path, output: Path) -> None:
    """Import a JSON array of provider messages into a trace."""
    try:
        dump_trace(import_messages(provider, read_json(source)), output)
    except (OSError, ValueError, ValidationError) as exc:
        typer.secho(f"Error: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(2) from exc
