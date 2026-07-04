from __future__ import annotations

from datetime import datetime

from bson import ObjectId

from utils.mongo_utils import convert_objectid_to_str, parse_object_id
from utils.static_content_utils import normalize_static_rel_path
from utils.test_utils import build_available_tests_filter, parse_expiration_datetime


def test_parse_object_id_and_convert_objectid_to_str() -> None:
    oid = ObjectId()
    parsed = parse_object_id(str(oid))
    assert parsed == oid
    assert parse_object_id("invalid-id") is None

    payload = {"_id": oid, "nested": [oid]}
    converted = convert_objectid_to_str(payload)
    assert converted["_id"] == str(oid)
    assert converted["nested"] == [str(oid)]


def test_normalize_static_rel_path_strips_prefixes() -> None:
    assert normalize_static_rel_path("Legacy Json Qs/lessons/math.json") == "lessons/math.json"
    assert normalize_static_rel_path("./backend/data/Update.json") == "Update.json"
    assert normalize_static_rel_path("mongo://json:teachers.json") == "teachers.json"


def test_build_available_tests_filter_contains_required_sections() -> None:
    mongo_filter = build_available_tests_filter(standard=9, user_id="u1", division="A")
    assert "$and" in mongo_filter
    assert mongo_filter["$and"][0]["standard"] == 9
    assert mongo_filter["$and"][0]["completed_by"]["$ne"] == "u1"
    assert any(cond.get("division") == "A" for cond in mongo_filter["$and"][1]["$or"])


def test_parse_expiration_datetime() -> None:
    valid = datetime.now().isoformat().replace("+00:00", "Z")
    parsed = parse_expiration_datetime(valid)
    assert parsed is not None
    assert parse_expiration_datetime("not-a-date") is None
