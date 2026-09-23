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
reused automatically — no credentials needed until they expire.

By default garminpull just **prompts** for your email and password on that first run, so
no setup is required. If you'd rather not be prompted, put them in an optional `.env`:

```bash
cp .env.example .env   # then edit GARMIN_EMAIL / GARMIN_PASSWORD
```

## Usage

The activity is a required positional argument. Running with no arguments prints help.

```bash
# All pool swims as FIT files into ./downloads
poetry run garminpull pool-swim

# Every activity in a date range, as TCX
poetry run garminpull all --format tcx --since 2026-01-01 --until 2026-09-23

# Last 10 runs, into a custom folder
poetry run garminpull run --limit 10 --output-dir ~/runs

# See what would be downloaded without fetching anything
poetry run garminpull pool-swim --dry-run

# Any Garmin activity typeKey works even without a preset
poetry run garminpull indoor_rowing
```

Run `poetry run garminpull --help` for all options.

### Activity presets

`pool-swim`, `open-water-swim`, `swim`, `run`, `bike`, `all`. Anything else is treated as
a raw Garmin `typeKey`.

### Formats

`fit` (default), `tcx`, `gpx`, `kml`, `csv`.

## Development

```bash
poetry install
poetry run pytest      # run tests (no network needed — Garmin is faked)
poetry run ruff check .
```
