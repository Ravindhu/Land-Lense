import json
from datetime import date

import pytest
from shapely.geometry import LineString

from tn_highway_intel.domain.models import NoticeDot
from tn_highway_intel.engine.dot_snapper import snap_dots
from tn_highway_intel.engine.gazette_parser import (
    GeminiOcrClient,
    OcrRecord,
    parse_gazette,
    to_notice_dots,
)
from tn_highway_intel.engine.ocr_cache import OcrCache, cache_key
from tn_highway_intel.services.review_queue import ReviewQueue


class FakeClient:
    engine = "fake"
    model = "m1"

    def __init__(self, raw):
        self.raw = raw
        self.calls = 0

    def extract(self, pdf_bytes, prompt):
        self.calls += 1
        return self.raw, {"prompt_tokens": 100}


def _good(conf=0.95):
    return json.dumps({"records": [{
        "district": "Erode", "taluk": "Perundurai", "village": "Ingur",
        "survey_no": "12/3", "stage": "3D", "page": 2, "confidence": conf,
    }]})


def test_valid_output_becomes_records(tmp_path):
    result = parse_gazette(b"%PDF-1 a", "raw/a.pdf", FakeClient(_good()), OcrCache(tmp_path))
    assert len(result.records) == 1
    assert result.review == []
    assert result.cache_hit is False


def test_second_run_hits_cache_and_skips_model(tmp_path):
    cache = OcrCache(tmp_path)
    client = FakeClient(_good())
    parse_gazette(b"%PDF-1 a", "raw/a.pdf", client, cache)
    result = parse_gazette(b"%PDF-1 a", "raw/a.pdf", client, cache)
    assert client.calls == 1
    assert result.cache_hit is True
    assert len(result.records) == 1


def test_cache_key_changes_with_prompt_version():
    assert cache_key(b"x", "gemini", "m", "v1") != cache_key(b"x", "gemini", "m", "v2")


def test_invalid_json_goes_to_review(tmp_path):
    result = parse_gazette(b"%PDF-1 a", "raw/a.pdf", FakeClient("not json"), OcrCache(tmp_path))
    assert result.records == []
    assert result.review[0].reason == "ocr_output_invalid"


def test_schema_violation_goes_to_review(tmp_path):
    bad = json.dumps({"records": [{"village": "Ingur", "stage": "15(2)", "page": 1, "confidence": 0.9}]})
    result = parse_gazette(b"%PDF-1 a", "raw/a.pdf", FakeClient(bad), OcrCache(tmp_path))
    assert result.records == []
    assert result.review[0].reason == "ocr_output_invalid"


def test_low_confidence_goes_to_review_not_map(tmp_path):
    result = parse_gazette(b"%PDF-1 a", "raw/a.pdf", FakeClient(_good(conf=0.5)), OcrCache(tmp_path))
    assert result.records == []
    assert result.review[0].reason == "low_confidence"


def test_unmatched_record_goes_to_review():
    rec = OcrRecord(district="Erode", taluk="P", village="Ingur", survey_no="99", stage="3D", page=1, confidence=0.9)
    dots, review = to_notice_dots([rec], {"source_pdf": "a.pdf", "gazette_id": "G1", "gazette_date": date(2026, 3, 1)}, centroids={})
    assert dots == []
    assert review[0].reason == "no_parcel_match"


def test_matched_record_becomes_dot_with_source():
    rec = OcrRecord(district="Erode", taluk="P", village="Ingur", survey_no="12/3", stage="3D", page=2, confidence=0.9)
    dots, _ = to_notice_dots(
        [rec],
        {"source_pdf": "raw/a.pdf", "gazette_id": "G1", "gazette_date": "2026-03-01"},
        centroids={("Ingur", "12/3"): (1000.0, 2000.0)},
    )
    assert dots[0].source_pdf == "raw/a.pdf"
    assert dots[0].source_page == 2
    assert dots[0].gazette_date == date(2026, 3, 1)


def _dot(x, y, survey="1"):
    return NoticeDot(
        dot_id=f"d{survey}", district="E", taluk="P", village="V", survey_no=survey, stage="3D",
        gazette_id="G1", gazette_date=date(2026, 3, 1), source_pdf="a.pdf", source_page=1,
        coords=(x, y), confidence=0.9,
    )


def test_snap_moves_near_dot_onto_line_and_flags_far_dot():
    line = LineString([(0, 0), (1000, 0)])
    mapped, review = snap_dots([_dot(100, 10, "1"), _dot(200, 500, "2")], line, tolerance_m=50)
    assert len(mapped) == 1
    assert mapped[0].coords == (100.0, 0.0)
    assert mapped[0].snap_distance_m == pytest.approx(10.0)
    assert len(review) == 1
    assert review[0].status == "review"


def test_review_queue_stores_reason_and_rejects_unknown(tmp_path):
    queue = ReviewQueue(tmp_path / "review.json")
    queue.add_raw("low_confidence", "raw/a.pdf", 2, {"confidence": 0.5})
    assert queue.all()[0]["reason"] == "low_confidence"
    with pytest.raises(ValueError):
        queue.add_raw("made_up", "raw/a.pdf", 1, {})


def test_gemini_client_builds_request_and_parses_response():
    class Resp:
        def __init__(self, payload):
            self._p = payload

        def raise_for_status(self):
            pass

        def json(self):
            return self._p

    class Sess:
        def __init__(self):
            self.kwargs = None

        def post(self, url, **kwargs):
            self.kwargs = dict(url=url, **kwargs)
            return Resp({
                "candidates": [{"content": {"parts": [{"text": _good()}]}}],
                "usageMetadata": {"promptTokenCount": 10},
            })

    sess = Sess()
    client = GeminiOcrClient("KEY-NOT-REAL", "gemini-2.5-flash", sess)
    text, usage = client.extract(b"%PDF-1 a", "prompt")
    assert json.loads(text)["records"][0]["village"] == "Ingur"
    assert usage["promptTokenCount"] == 10
    assert sess.kwargs["headers"]["x-goog-api-key"] == "KEY-NOT-REAL"
    assert "inline_data" in sess.kwargs["data"]
    assert sess.kwargs["timeout"] == 120
