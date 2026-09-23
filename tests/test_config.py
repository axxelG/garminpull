from garminpull.config import (
    ACTIVITY_PRESETS,
    FORMATS,
    coarse_category,
    resolve_type_keys,
)


def test_pool_swim_preset_maps_to_lap_swimming():
    assert resolve_type_keys("pool-swim") == frozenset({"lap_swimming"})


def test_all_preset_is_empty_meaning_no_filter():
    assert resolve_type_keys("all") == ACTIVITY_PRESETS["all"] == frozenset()


def test_raw_typekey_passes_through():
    assert resolve_type_keys("indoor_rowing") == frozenset({"indoor_rowing"})


def test_fit_format_is_zip_wrapped():
    assert FORMATS["fit"].is_zip is True
    assert FORMATS["fit"].extension == "fit"


def test_non_fit_formats_are_plain_files():
    assert FORMATS["tcx"].is_zip is False


def test_coarse_category_shared_parent():
    # pool + open water both live under "swimming"
    assert coarse_category(frozenset({"lap_swimming", "open_water_swimming"})) == "swimming"


def test_coarse_category_none_when_empty():
    assert coarse_category(frozenset()) is None


def test_coarse_category_none_when_spanning_categories():
    assert coarse_category(frozenset({"lap_swimming", "running"})) is None


def test_coarse_category_none_for_unmapped_typekey():
    assert coarse_category(frozenset({"indoor_rowing"})) is None
