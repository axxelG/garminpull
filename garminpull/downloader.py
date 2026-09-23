"""Listing and downloading activities from an authenticated Garmin client."""

from __future__ import annotations

import io
import re
import zipfile
from datetime import date
from pathlib import Path

from garminconnect import Garmin

from .config import OutputFormat


def _typekey(activity: dict) -> str:
    return (activity.get("activityType") or {}).get("typeKey", "")


def list_activities(
    client: Garmin,
    type_keys: frozenset[str],
    start_date: date | None = None,
    end_date: date | None = None,
    limit: int | None = None,
) -> list[dict]:
    """Return activities matching ``type_keys`` (empty set = all types).

    When a date range is given, uses Garmin's date query; otherwise pages through the
    most recent activities. Results are always filtered client-side on the precise
    ``typeKey`` for accuracy, then capped at ``limit`` if provided.
    """

    if start_date or end_date:
        start = (start_date or date.min).isoformat()
        end = (end_date or date.today()).isoformat()
        activities = client.get_activities_by_date(start, end)
    else:
        activities = _recent_activities(client, limit, type_keys)

    if type_keys:
        activities = [a for a in activities if _typekey(a) in type_keys]

    if limit is not None:
        activities = activities[:limit]
    return activities


def _recent_activities(
    client: Garmin, limit: int | None, type_keys: frozenset[str]
) -> list[dict]:
    """Page through recent activities until we have enough matches (or run out)."""

    page_size = 100
    collected: list[dict] = []
    start = 0
    while True:
        batch = client.get_activities(start, page_size)
        if not batch:
            break
        collected.extend(batch)
        matching = [a for a in collected if not type_keys or _typekey(a) in type_keys]
        if limit is not None and len(matching) >= limit:
            break
        if len(batch) < page_size:
            break
        start += page_size
    return collected


def _safe_name(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", text).strip("_") or "activity"


def target_path(activity: dict, fmt: OutputFormat, output_dir: Path) -> Path:
    """Build a stable, human-readable output path for an activity file."""

    activity_id = activity.get("activityId", "unknown")
    started = (activity.get("startTimeLocal") or "").split(" ")[0] or "nodate"
    name = _safe_name(activity.get("activityName") or _typekey(activity) or "activity")
    filename = f"{started}_{activity_id}_{name}.{fmt.extension}"
    return output_dir / filename


def download_activity(
    client: Garmin,
    activity: dict,
    fmt: OutputFormat,
    output_dir: Path,
    overwrite: bool = False,
) -> Path:
    """Download a single activity to ``output_dir`` and return the written path.

    If the file already exists and ``overwrite`` is False, the download is skipped.
    ZIP-wrapped formats (``fit``) are unpacked to the requested extension.
    """

    dest = target_path(activity, fmt, output_dir)
    if dest.exists() and not overwrite:
        return dest

    output_dir.mkdir(parents=True, exist_ok=True)
    data = client.download_activity(activity["activityId"], dl_fmt=fmt.download_fmt)

    if fmt.is_zip:
        _write_from_zip(data, dest, fmt.extension)
    else:
        dest.write_bytes(data)
    return dest


def _write_from_zip(data: bytes, dest: Path, extension: str) -> None:
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        members = archive.namelist()
        chosen = next(
            (m for m in members if m.lower().endswith(f".{extension}")),
            members[0] if members else None,
        )
        if chosen is None:
            raise ValueError("Garmin returned an empty archive for this activity")
        dest.write_bytes(archive.read(chosen))
