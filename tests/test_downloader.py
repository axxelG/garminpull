import io
import zipfile
from datetime import date
from pathlib import Path

from garminpull import downloader
from garminpull.config import FORMATS


def _activity(activity_id, type_key, name="Morning Swim", start="2026-09-20 07:15:00"):
    return {
        "activityId": activity_id,
        "activityName": name,
        "startTimeLocal": start,
        "activityType": {"typeKey": type_key},
    }


class FakeClient:
    """Stand-in for garminconnect.Garmin covering only what the downloader calls."""

    def __init__(self, activities, payloads=None):
        self._activities = activities
        self._payloads = payloads or {}
        self.last_activitytype = "unset"

    def get_activities(self, start, limit):
        return self._activities[start : start + limit]

    def get_activities_by_date(self, start, end, activitytype=None):
        self.last_activitytype = activitytype
        return self._activities

    def download_activity(self, activity_id, dl_fmt):
        return self._payloads[activity_id]


def test_list_activities_filters_by_typekey():
    acts = [_activity(1, "lap_swimming"), _activity(2, "running")]
    client = FakeClient(acts)
    result = downloader.list_activities(client, type_keys=frozenset({"lap_swimming"}))
    assert [a["activityId"] for a in result] == [1]


def test_list_activities_empty_typekeys_returns_all():
    acts = [_activity(1, "lap_swimming"), _activity(2, "running")]
    client = FakeClient(acts)
    result = downloader.list_activities(client, type_keys=frozenset())
    assert len(result) == 2


def test_date_range_prenarrows_to_coarse_category():
    acts = [_activity(1, "lap_swimming")]
    client = FakeClient(acts)
    downloader.list_activities(
        client,
        type_keys=frozenset({"lap_swimming"}),
        start_date=date(2026, 1, 1),
        end_date=date(2026, 9, 23),
    )
    assert client.last_activitytype == "swimming"


def test_date_range_no_prefilter_when_categories_span():
    acts = [_activity(1, "lap_swimming")]
    client = FakeClient(acts)
    downloader.list_activities(
        client,
        type_keys=frozenset({"lap_swimming", "running"}),
        start_date=date(2026, 1, 1),
    )
    assert client.last_activitytype is None


def test_list_activities_respects_limit():
    acts = [_activity(i, "lap_swimming") for i in range(5)]
    client = FakeClient(acts)
    result = downloader.list_activities(client, type_keys=frozenset(), limit=2)
    assert len(result) == 2


def test_target_path_is_readable_and_sanitized():
    act = _activity(42, "lap_swimming", name="Pool / Swim!")
    path = downloader.target_path(act, FORMATS["fit"], Path("out"))
    assert path.name == "2026-09-20_42_Pool_Swim.fit"


def test_download_fit_unpacks_zip(tmp_path):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("12345.fit", b"FIT-BYTES")
    act = _activity(42, "lap_swimming")
    client = FakeClient([act], payloads={42: buf.getvalue()})

    dest = downloader.download_activity(client, act, FORMATS["fit"], tmp_path)

    assert dest.read_bytes() == b"FIT-BYTES"
    assert dest.suffix == ".fit"


def test_download_skips_existing_without_overwrite(tmp_path):
    act = _activity(42, "lap_swimming")
    client = FakeClient([act], payloads={42: b"data"})
    dest = downloader.target_path(act, FORMATS["tcx"], tmp_path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(b"original")

    downloader.download_activity(client, act, FORMATS["tcx"], tmp_path, overwrite=False)

    assert dest.read_bytes() == b"original"
