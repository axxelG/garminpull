# garminpull

Pull your activities from [Garmin Connect](https://connect.garmin.com) and save them
locally. Defaults to downloading **pool swim** sessions as **FIT** files, but the
activity type, date range, and output format are all selectable — so you can grab a
single sport or your entire history in whatever format you need.

## Install

```bash
poetry install
```

## Authenticate

The first run needs your Garmin credentials (and an MFA code if your account uses
two-factor auth). After that, OAuth tokens are cached under `~/.garminconnect` and
reused automatically.

```bash
cp .env.example .env   # then edit GARMIN_EMAIL / GARMIN_PASSWORD
```

## Usage

```bash
# Default: all pool swims as FIT files into ./downloads
poetry run garminpull pull

# Every activity in a date range, as TCX
poetry run garminpull pull --activity all --format tcx --since 2026-01-01 --until 2026-09-23

# Last 10 runs, into a custom folder
poetry run garminpull pull --activity run --limit 10 --output-dir ~/runs

# See what would be downloaded without fetching anything
poetry run garminpull pull --dry-run

# Any Garmin activity typeKey works even without a preset
poetry run garminpull pull --activity indoor_rowing
```

Run `poetry run garminpull pull --help` for all options.

### Activity presets

`pool-swim` (default), `open-water-swim`, `swim`, `run`, `bike`, `all`. Anything else is
treated as a raw Garmin `typeKey`.

### Formats

`fit` (default), `tcx`, `gpx`, `kml`, `csv`.

## Development

```bash
poetry install
poetry run pytest      # run tests (no network needed — Garmin is faked)
poetry run ruff check .
```
