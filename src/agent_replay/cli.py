"""Command line interface."""
from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from pydantic import ValidationError

from .adapters import import_messages
from .compare import compare
from .models import dump_trace, load_trace, read_json

app = typer.Typer(no_args_is_help=True)


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
            json_report.write_text(report.model_dump_json(indent=2) + "\n", encoding="utf-8")
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
