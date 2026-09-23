"""Command-line interface for garminpull."""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

import typer
from dotenv import load_dotenv

from . import client as garmin_client
from . import downloader
from .config import (
    ACTIVITY_PRESETS,
    DEFAULT_ACTIVITY,
    DEFAULT_FORMAT,
    FORMATS,
    resolve_type_keys,
)

def _parse_date(value: str | None) -> date | None:
    if value is None:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:  # pragma: no cover - user input validation
        raise typer.BadParameter(f"Dates must be YYYY-MM-DD, got {value!r}") from exc


def pull(
    activity: str = typer.Option(
        DEFAULT_ACTIVITY,
        "--activity",
        "-a",
        help=(
            "Activity preset ("
            + ", ".join(ACTIVITY_PRESETS)
            + ") or a raw Garmin typeKey (e.g. lap_swimming)."
        ),
    ),
    fmt: str = typer.Option(
        DEFAULT_FORMAT,
        "--format",
        "-f",
        help="Output format: " + ", ".join(FORMATS) + ".",
    ),
    output_dir: Path = typer.Option(
        Path("downloads"),
        "--output-dir",
        "-o",
        help="Directory to write activity files into.",
    ),
    since: str = typer.Option(None, "--since", help="Start date, inclusive (YYYY-MM-DD)."),
    until: str = typer.Option(None, "--until", help="End date, inclusive (YYYY-MM-DD)."),
    limit: int = typer.Option(None, "--limit", "-n", help="Maximum activities to download."),
    overwrite: bool = typer.Option(False, "--overwrite", help="Re-download existing files."),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="List matching activities without downloading."
    ),
) -> None:
    """Download activities matching the selected type and date range."""

    load_dotenv()

    if fmt not in FORMATS:
        raise typer.BadParameter(f"Unknown format {fmt!r}. Choose from: {', '.join(FORMATS)}")
    output_format = FORMATS[fmt]
    type_keys = resolve_type_keys(activity)

    typer.echo("Authenticating with Garmin Connect...")
    client = garmin_client.login()

    activities = downloader.list_activities(
        client,
        type_keys=type_keys,
        start_date=_parse_date(since),
        end_date=_parse_date(until),
        limit=limit,
    )

    label = "all activities" if not type_keys else activity
    typer.echo(f"Found {len(activities)} matching '{label}'.")

    if dry_run:
        for act in activities:
            typer.echo(f"  {downloader.target_path(act, output_format, output_dir).name}")
        return

    saved = 0
    skipped = 0
    for act in activities:
        dest = downloader.target_path(act, output_format, output_dir)
        if dest.exists() and not overwrite:
            typer.echo(f"  skip:  {dest}")
            skipped += 1
            continue
        downloader.download_activity(client, act, output_format, output_dir, overwrite=overwrite)
        typer.echo(f"  saved: {dest}")
        saved += 1

    typer.echo(f"Done. {saved} saved, {skipped} skipped in {output_dir}/")


def main() -> None:
    """Console-script entry point: a single command, no subcommand name."""
    typer.run(pull)


if __name__ == "__main__":
    main()
