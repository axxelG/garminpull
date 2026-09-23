# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
poetry install                       # set up the venv and dependencies
poetry run pytest                    # run all tests (offline — Garmin is faked)
poetry run pytest tests/test_downloader.py::test_download_fit_unpacks_zip  # single test
poetry run ruff check .              # lint
poetry run garminpull pull --help   # CLI entry point
poetry run garminpull pull --dry-run  # list matches without downloading (safe, but still hits Garmin auth)
```

## Architecture

A small CLI that authenticates to Garmin Connect, lists activities, and downloads them
locally. Flow: `cli.py` → `client.login()` → `downloader.list_activities()` →
`downloader.download_activity()`. The `garminconnect` library (backed by `garth`) is the
only Garmin API surface; we never call Garmin's HTTP endpoints directly.

- **`config.py`** — the extension point. `FORMATS` maps friendly format names to a
  `garminconnect` download format + file extension; `ACTIVITY_PRESETS` maps preset names
  to sets of Garmin `typeKey` values. Adding a format or preset is a one-line change here
  and the CLI picks it up automatically. `resolve_type_keys()` falls through to treating
  an unknown argument as a raw `typeKey`, so any Garmin activity type works without a preset.
- **`client.py`** — token-first auth. Resumes from cached OAuth tokens
  (`~/.garminconnect`, override with `GARMINTOKENS`); only falls back to email/password
  (+ interactive MFA prompt) when no valid tokens exist, then persists new ones.
- **`downloader.py`** — pure, network-light logic. Filtering is two-level: for date-range
  queries it pre-narrows on Garmin's **coarse** server-side category (`coarse_category()`,
  only when all requested types share one parent, e.g. pool + open water -> "swimming"),
  then always applies the exact **client-side** `typeKey` filter because Garmin's category
  filter can't distinguish pool from open water. `is_zip` formats (`fit`) come as a ZIP
  that gets unpacked to the target extension.
- **`cli.py`** — Typer app; the console script `garminpull` maps to `cli:app`. Loads
  `.env` before auth.

## Conventions specific to this repo

- Keep `downloader.py` and `config.py` free of network calls and Typer so they stay unit-
  testable. Tests use a `FakeClient` implementing only `get_activities`,
  `get_activities_by_date`, and `download_activity` — mirror that surface when extending.
- Defaults encode the primary use case: pool swims (`pool-swim`) as `fit`. Preserve those
  defaults unless asked otherwise.
- `typer` must be `>=0.15` — earlier versions break against the installed `click` 8.5.
