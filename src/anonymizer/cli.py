from __future__ import annotations

import time
from pathlib import Path
from typing import Optional

import typer

from .audit import make_audit_record, write_audit
from .keymgmt import load_keyfile
from .pipeline import run_pipeline
from .profile import load_profile

app = typer.Typer(add_completion=False, no_args_is_help=True, help="On-premise CSV anonymizer")

EXIT_OK = 0
EXIT_PROFILE_INVALID = 2
EXIT_IO = 3
EXIT_KEY = 4
EXIT_TRANSFORM = 5
EXIT_AUDIT = 6


@app.command()
def run(
    input: Path = typer.Option(..., exists=True, dir_okay=False, help="Input CSV file"),
    output: Path = typer.Option(..., dir_okay=False, help="Output CSV file"),
    profile: Path = typer.Option(..., exists=True, dir_okay=False, help="YAML profile"),
    keyfile: Path = typer.Option(..., exists=True, dir_okay=False, help="Keyfile JSON or raw bytes"),
    audit: Optional[Path] = typer.Option(Path("audit/audit-log.jsonl"), help="Audit JSONL path"),
) -> None:
    """Run a complete anonymization job."""
    started_at = time.time()
    prof = None
    key_material = None
    stats = None

    try:
        prof = load_profile(profile)
    except Exception as exc:
        typer.secho(f"Profile invalid: {exc}", err=True, fg=typer.colors.RED)
        raise typer.Exit(EXIT_PROFILE_INVALID)

    try:
        key_material = load_keyfile(keyfile)
        if key_material.version != prof.key_version:
            raise ValueError(f"key version mismatch: profile expects {prof.key_version}, keyfile has {key_material.version}")
    except Exception as exc:
        typer.secho(f"Key error: {exc}", err=True, fg=typer.colors.RED)
        if audit:
            try:
                write_audit(
                    make_audit_record(
                        input_file=input,
                        output_file=output,
                        profile=prof,
                        key_version=-1,
                        rows_in=None,
                        rows_out=None,
                        operations={},
                        exit_code=EXIT_KEY,
                        started_at=started_at,
                        error=str(exc),
                    ),
                    audit,
                )
            except Exception:
                pass
        raise typer.Exit(EXIT_KEY)

    try:
        stats = run_pipeline(input, output, prof, key_material.key)
    except OSError as exc:
        typer.secho(f"IO error: {exc}", err=True, fg=typer.colors.RED)
        code = EXIT_IO
        err = str(exc)
    except Exception as exc:
        typer.secho(f"Transform error: {exc}", err=True, fg=typer.colors.RED)
        code = EXIT_TRANSFORM
        err = str(exc)
    else:
        code = EXIT_OK
        err = None
        typer.secho(f"OK: {input} -> {output}", fg=typer.colors.GREEN)
        if stats.warnings:
            for warning in stats.warnings:
                typer.secho(f"Warning: {warning}", err=True, fg=typer.colors.YELLOW)

    if audit:
        try:
            write_audit(
                make_audit_record(
                    input_file=input,
                    output_file=output,
                    profile=prof,
                    key_version=key_material.version,
                    rows_in=stats.rows_in if stats else None,
                    rows_out=stats.rows_out if stats else None,
                    operations=stats.operations if stats else {},
                    exit_code=code,
                    started_at=started_at,
                    error=err,
                ),
                audit,
            )
        except Exception as exc:
            typer.secho(f"Audit error: {exc}", err=True, fg=typer.colors.RED)
            raise typer.Exit(EXIT_AUDIT)

    raise typer.Exit(code)


if __name__ == "__main__":
    app()
