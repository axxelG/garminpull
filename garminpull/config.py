"""Format and activity-type definitions shared across the app.

Keeping these tables in one place is what makes garminpull flexible: adding a new
output format or a new activity-type preset is a one-line change here, and the CLI
picks it up automatically.
"""

from __future__ import annotations

from dataclasses import dataclass

from garminconnect import Garmin


@dataclass(frozen=True)
class OutputFormat:
    """A downloadable representation of an activity.

    ``download_fmt`` is what Garmin serves. ``ORIGINAL`` returns a ZIP archive that
    contains the raw uploaded file (a ``.fit`` for most devices); ``is_zip`` tells the
    downloader to unpack it. Everything else is served as a single plain file.
    """

    name: str
    download_fmt: object
    extension: str
    is_zip: bool = False


# Friendly format name -> how to fetch and store it.
FORMATS: dict[str, OutputFormat] = {
    "fit": OutputFormat("fit", Garmin.ActivityDownloadFormat.ORIGINAL, "fit", is_zip=True),
    "tcx": OutputFormat("tcx", Garmin.ActivityDownloadFormat.TCX, "tcx"),
    "gpx": OutputFormat("gpx", Garmin.ActivityDownloadFormat.GPX, "gpx"),
    "kml": OutputFormat("kml", Garmin.ActivityDownloadFormat.KML, "kml"),
    "csv": OutputFormat("csv", Garmin.ActivityDownloadFormat.CSV, "csv"),
}

DEFAULT_FORMAT = "fit"


# Preset name -> the set of Garmin ``typeKey`` values it matches. Garmin's own
# category filter is coarse (e.g. "swimming" covers pool and open water), so we filter
# client-side on the precise ``typeKey`` for accuracy. ``ALL_ACTIVITIES`` (empty set)
# means "do not filter".
ALL_ACTIVITIES: frozenset[str] = frozenset()

ACTIVITY_PRESETS: dict[str, frozenset[str]] = {
    "pool-swim": frozenset({"lap_swimming"}),
    "open-water-swim": frozenset({"open_water_swimming"}),
    "swim": frozenset({"lap_swimming", "open_water_swimming"}),
    "run": frozenset({"running", "treadmill_running", "trail_running"}),
    "bike": frozenset({"cycling", "road_biking", "mountain_biking", "indoor_cycling"}),
    "all": ALL_ACTIVITIES,
}


def resolve_type_keys(preset_or_type: str) -> frozenset[str]:
    """Resolve a CLI activity argument to the set of matching Garmin ``typeKey`` values.

    Accepts either a preset name from :data:`ACTIVITY_PRESETS` or a raw Garmin
    ``typeKey`` (e.g. ``lap_swimming``) for anything not covered by a preset.
    """

    if preset_or_type in ACTIVITY_PRESETS:
        return ACTIVITY_PRESETS[preset_or_type]
    return frozenset({preset_or_type})


# Precise ``typeKey`` -> Garmin's coarse parent category, which is the value the list
# endpoints accept as a server-side ``activitytype`` filter. We can only pre-narrow on
# the server when every requested ``typeKey`` shares one parent (see
# :func:`coarse_category`); the exact ``typeKey`` filtering still happens client-side.
TYPEKEY_CATEGORY: dict[str, str] = {
    "lap_swimming": "swimming",
    "open_water_swimming": "swimming",
    "running": "running",
    "treadmill_running": "running",
    "trail_running": "running",
    "cycling": "cycling",
    "road_biking": "cycling",
    "mountain_biking": "cycling",
    "indoor_cycling": "cycling",
}


def coarse_category(type_keys: frozenset[str]) -> str | None:
    """Return the shared Garmin parent category for a server-side pre-filter, or None.

    Returns None when ``type_keys`` is empty (means "all types"), when any key is
    unknown to :data:`TYPEKEY_CATEGORY` (e.g. a raw ``typeKey`` we can't map), or when
    the keys span more than one parent category. In every None case the caller must fall
    back to fetching all activities and filtering client-side.
    """

    if not type_keys:
        return None
    categories = {TYPEKEY_CATEGORY.get(key) for key in type_keys}
    if None in categories or len(categories) != 1:
        return None
    return next(iter(categories))
