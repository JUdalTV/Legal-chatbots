# -*- coding: utf-8 -*-
"""
Test don gian cho graph_rag/ner_extractor.py.
Muc tieu: de doc, de chay, khong loi chuoi tieng Viet.
"""

import os
import sys
import json
from unittest.mock import MagicMock


BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

import graph_rag.ner_extractor as ner_module
from graph_rag.ner_extractor import NERExtractor, _classify_org, get_ner_extractor


class FakeTokenizer:
    def __call__(self, text, truncation=True, max_length=512, return_tensors="pt"):
        return {"input_ids": [[1, 2, 3]]}

    def decode(self, input_ids, skip_special_tokens=True):
        return "van ban da decode"


def make_extractor(mock_results):
    extractor = NERExtractor()
    extractor._tokenizer = FakeTokenizer()
    extractor._pipe = MagicMock(return_value=mock_results)
    return extractor


def test_classify_org_basic():
    assert _classify_org("Bộ Tư pháp") == "CoQuanNhaNuoc"
    assert _classify_org("Công ty ABC") == "DoanhNghiep"
    assert _classify_org("Hiệp hội Luật gia") == "ToChucKhac"


def test_extract_actors_filters_and_maps():
    raw = [
        {"entity_group": "ORG", "word": "bộ tài chính", "score": 0.92},
        {"entity_group": "PER", "word": "thủ tướng", "score": 0.91},
        {"entity_group": "LOC", "word": "Hà Nội", "score": 0.99},
        {"entity_group": "ORG", "word": "AB", "score": 0.99},
        {"entity_group": "ORG", "word": "Công ty XYZ", "score": 0.79},
    ]
    ext = make_extractor(raw)
    actors = ext.extract_actors("Văn bản tiếng Việt có dấu.", "dieu_01")

    assert len(actors) == 2
    assert actors[0]["label"] == "CoQuanNhaNuoc"
    assert actors[0]["text"] == "Bộ Tài Chính"
    assert actors[1]["label"] == "ChucDanh"
    assert actors[1]["text"] == "Thủ Tướng"
    assert all(x["source_dieu_id"] == "dieu_01" for x in actors)


def test_extract_actors_deduplicate():
    raw = [
        {"entity_group": "ORG", "word": "Bộ Y tế", "score": 0.93},
        {"entity_group": "ORG", "word": "Bộ Y tế", "score": 0.95},
    ]
    ext = make_extractor(raw)
    actors = ext.extract_actors("Bộ Y tế phối hợp Bộ Y tế.", "dieu_02")
    assert len(actors) == 1


def test_get_ner_extractor_singleton():
    ner_module._ner_extractor = None
    a = get_ner_extractor()
    b = get_ner_extractor()
    assert a is b


def demo_print_extract_output():
    """In ket qua xu ly va kieu du lieu dau ra cua extract_actors."""
    raw = [
        {"entity_group": "ORG", "word": "bo tai chinh", "score": 0.92},
        {"entity_group": "PER", "word": "thu tuong", "score": 0.91},
    ]
    ext = make_extractor(raw)
    actors = ext.extract_actors("van ban demo", "dieu_demo")

    print("\n=== DEMO extract_actors output ===")
    print("type(actors):", type(actors).__name__)
    if actors:
        print("type(actors[0]):", type(actors[0]).__name__)
        for key in ["text", "label", "score", "source_dieu_id"]:
            print(f"type(actors[0]['{key}']):", type(actors[0][key]).__name__)

    print("value:")
    print(json.dumps(actors, ensure_ascii=False, indent=2))
    print("=== END DEMO ===\n")


if __name__ == "__main__":
    # Print UTF-8 friendly output on Windows terminal.
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    os.environ.setdefault("PYTHONUTF8", "1")

    demo_print_extract_output()
    try:
        import pytest

    except ImportError:
        print("[WARN] Chua cai pytest. Dang chay fallback mode...")
        test_funcs = [
            test_classify_org_basic,
            test_extract_actors_filters_and_maps,
            test_extract_actors_deduplicate,
            test_get_ner_extractor_singleton,
        ]
        passed = 0
        failed = 0

        for fn in test_funcs:
            try:
                fn()
                passed += 1
                print(f"[PASS] {fn.__name__}")
                print(fn)
            except Exception as exc:
                failed += 1
                print(f"[FAIL] {fn.__name__}: {exc}")

        total = passed + failed
        print(f"\nTong ket: {passed}/{total} PASS, {failed} FAIL")
        sys.exit(0 if failed == 0 else 1)

    # Preferred path: run pytest and print full result.
    demo_print_extract_output()
    rc = pytest.main([__file__, "-v", "--tb=short"])
    print(f"\nPytest exit code: {rc}")
    sys.exit(rc)
