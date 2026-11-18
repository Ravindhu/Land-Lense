from datetime import date

import numpy as np
import pytest
from shapely.geometry import LineString

from tn_highway_intel.collectors.central_egazette import (
    BadDocument,
    CentralEgazetteCollector,
    CollectorDisabled,
)
from tn_highway_intel.domain.settings import CollectorSettings
from tn_highway_intel.engine.official_map import (
    GeoreferenceError,
    check_accuracy,
    fit_affine,
    load_alignment,
    save_alignment,
    transform_polyline,
)


# ---- official map -----------------------------------------------------------

def _pairs_for(matrix, pixels):
    out = []
    for px, py in pixels:
        x = matrix[0][0] * px + matrix[0][1] * py + matrix[0][2]
        y = matrix[1][0] * px + matrix[1][1] * py + matrix[1][2]
        out.append(((px, py), (x, y)))
    return out


def test_affine_fit_recovers_known_transform():
    matrix = [[0.5, 0.01, 300000.0], [-0.02, 0.5, 1500000.0]]
    pairs = _pairs_for(matrix, [(0, 0), (1000, 0), (0, 1000), (900, 800)])
    fit = fit_affine(pairs)
    assert np.allclose(fit.matrix, np.array(matrix), atol=1e-6)
    assert fit.rms_m == pytest.approx(0, abs=1e-3)  # 1 mm; coordinates are ~1.5e6 m


def test_affine_fit_needs_three_points():
    pairs = _pairs_for([[1, 0, 0], [0, 1, 0]], [(0, 0), (1, 0)])
    with pytest.raises(GeoreferenceError):
        fit_affine(pairs)


def test_affine_fit_rejects_collinear_points():
    pairs = _pairs_for([[1, 0, 0], [0, 1, 0]], [(0, 0), (1, 1), (2, 2)])
    with pytest.raises(GeoreferenceError):
        fit_affine(pairs)


def test_accuracy_gate_rejects_large_residual():
    fit = fit_affine(_pairs_for([[1, 0, 0], [0, 1, 0]], [(0, 0), (10, 0), (0, 10)]))
    fit = type(fit)(matrix=fit.matrix, rms_m=12.0, n_points=3)
    with pytest.raises(GeoreferenceError):
        check_accuracy(fit, max_rms_m=5.0)


def test_alignment_round_trip(tmp_path):
    line = LineString([(0, 0), (100, 10), (200, 20)])
    path = tmp_path / "official_alignment.geojson"
    save_alignment(line, path, source={"map_id": "sheet-1", "control_points": 3})
    loaded = load_alignment(path)
    assert list(loaded.coords) == list(line.coords)


def test_transform_polyline_applies_fit():
    fit = fit_affine(_pairs_for([[2, 0, 10], [0, 2, 20]], [(0, 0), (5, 0), (0, 5)]))
    line = transform_polyline(fit, [(0, 0), (5, 5)])
    assert list(line.coords)[1] == pytest.approx((20.0, 30.0))


# ---- central gazette collector ----------------------------------------------

class _Resp:
    def __init__(self, content: bytes, status: int = 200):
        self.content = content
        self.status_code = status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"http {self.status_code}")


class _Session:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def get(self, url, timeout):
        self.calls.append((url, timeout))
        return self.responses.pop(0)


class _Clock:
    def __init__(self):
        self.now = 0.0
        self.slept = []

    def __call__(self):
        return self.now

    def sleep(self, seconds):
        self.slept.append(seconds)
        self.now += seconds


def _enabled():
    return CollectorSettings(enabled=True, terms_cleared=True, min_interval_s=5)


def test_collector_refuses_when_terms_not_cleared(tmp_path):
    settings = CollectorSettings(enabled=True, terms_cleared=False)
    collector = CentralEgazetteCollector(settings, tmp_path, session=_Session([]))
    with pytest.raises(CollectorDisabled):
        collector.fetch("https://egazette.gov.in/x.pdf", "G1", date(2026, 3, 1))


def test_collector_stores_pdf_and_manifest(tmp_path):
    session = _Session([_Resp(b"%PDF-1.4 notice one")])
    collector = CentralEgazetteCollector(_enabled(), tmp_path, session=session)
    entry = collector.fetch("https://egazette.gov.in/a.pdf", "G1", date(2026, 3, 1))
    assert entry is not None
    assert (tmp_path / entry.path).read_bytes() == b"%PDF-1.4 notice one"
    manifest = collector.load_manifest()
    assert manifest[0]["gazette_id"] == "G1"
    assert manifest[0]["sha256"] == entry.sha256
    assert session.calls[0][1] == 30  # timeout always set


def test_collector_skips_identical_content(tmp_path):
    body = b"%PDF-1.4 same"
    session = _Session([_Resp(body), _Resp(body)])
    collector = CentralEgazetteCollector(_enabled(), tmp_path, session=session)
    first = collector.fetch("https://egazette.gov.in/a.pdf", "G1", date(2026, 3, 1))
    second = collector.fetch("https://egazette.gov.in/b.pdf", "G1", date(2026, 3, 1))
    assert first is not None
    assert second is None
    assert len(collector.load_manifest()) == 1


def test_collector_rejects_non_pdf(tmp_path):
    session = _Session([_Resp(b"<html>login</html>")])
    collector = CentralEgazetteCollector(_enabled(), tmp_path, session=session)
    with pytest.raises(BadDocument):
        collector.fetch("https://egazette.gov.in/a.pdf", "G1", date(2026, 3, 1))


def test_collector_rejects_plain_http(tmp_path):
    collector = CentralEgazetteCollector(_enabled(), tmp_path, session=_Session([]))
    with pytest.raises(BadDocument):
        collector.fetch("http://egazette.gov.in/a.pdf", "G1", date(2026, 3, 1))


def test_collector_throttles_between_requests(tmp_path):
    clock = _Clock()
    session = _Session([_Resp(b"%PDF-1 one"), _Resp(b"%PDF-1 two")])
    collector = CentralEgazetteCollector(
        _enabled(), tmp_path, session=session, clock=clock, sleep=clock.sleep
    )
    collector.fetch("https://egazette.gov.in/a.pdf", "G1", date(2026, 3, 1))
    collector.fetch("https://egazette.gov.in/b.pdf", "G2", date(2026, 3, 2))
    assert clock.slept == [5]
