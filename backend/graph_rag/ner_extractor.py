"""
NER extractor for Actor nodes:
- CoQuanNhaNuoc
- DoanhNghiep
- ToChucKhac
- ChucDanh
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Optional


CO_QUAN_KW = {
    "bộ", "cục", "tổng cục", "vụ", "ủy ban", "chính phủ", "quốc hội",
    "viện", "tòa án", "kiểm sát", "nhà nước", "sở", "phòng", "ban",
    "trung tâm", "văn phòng", "thanh tra", "cơ quan", "lực lượng",
}
DOANH_NGHIEP_KW = {
    "doanh nghiệp", "công ty", "tập đoàn", "tổng công ty",
    "nhà cung cấp", "nhà mạng", "đại lý",
}
TO_CHUC_KW = {
    "tổ chức", "hội", "hiệp hội", "liên minh", "đảng", "đoàn",
    "quỹ", "trường", "trung tâm",
}


def _normalize_text(text: str) -> str:
    norm = unicodedata.normalize("NFKD", text)
    norm = "".join(ch for ch in norm if not unicodedata.combining(ch))
    return norm.lower().strip()


def _classify_org(text: str) -> str:
    t = text.lower()
    if any(kw in t for kw in CO_QUAN_KW):
        return "CoQuanNhaNuoc"
    if any(kw in t for kw in DOANH_NGHIEP_KW):
        return "DoanhNghiep"
    if any(kw in t for kw in TO_CHUC_KW):
        return "ToChucKhac"
    if re.match(r"^(bộ|ban|cục|sở)\s", t):
        return "CoQuanNhaNuoc"

    # Fallback accent-insensitive check.
    t_norm = _normalize_text(text)
    if any(kw in t_norm for kw in {
        "bo", "cuc", "tong cuc", "uy ban", "chinh phu", "quoc hoi",
        "vien", "toa an", "kiem sat", "nha nuoc", "so", "phong", "ban",
        "trung tam", "van phong", "thanh tra", "co quan", "luc luong",
    }):
        return "CoQuanNhaNuoc"
    if any(kw in t_norm for kw in {
        "doanh nghiep", "cong ty", "tap doan", "tong cong ty",
        "nha cung cap", "nha mang", "dai ly",
    }):
        return "DoanhNghiep"
    if any(kw in t_norm for kw in {
        "to chuc", "hoi", "hiep hoi", "lien minh", "dang", "doan",
        "quy", "truong", "trung tam",
    }):
        return "ToChucKhac"
    if re.match(r"^(bo|ban|cuc|so)\s", t_norm):
        return "CoQuanNhaNuoc"

    return "ToChucKhac"


class NERExtractor:
    MODEL_NAME = "NlpHUST/ner-vietnamese-electra-base"
    SCORE_THRESHOLD = 0.80
    MIN_TEXT_LEN = 3

    def __init__(self):
        self._pipe = None
        self._tokenizer = None

    def _load(self):
        if self._pipe is not None:
            return
        try:
            from transformers import (
                pipeline,
                AutoTokenizer,
                AutoModelForTokenClassification,
            )
        except ImportError:
            raise ImportError("pip install transformers torch")

        tokenizer = AutoTokenizer.from_pretrained(self.MODEL_NAME)
        model = AutoModelForTokenClassification.from_pretrained(self.MODEL_NAME)
        self._pipe = pipeline(
            "ner",
            model=model,
            tokenizer=tokenizer,
            aggregation_strategy="simple",
            device=-1,
        )
        self._tokenizer = tokenizer

    def extract_actors(self, text: str, dieu_id: str) -> list[dict]:
        self._load()

        tokens = self._tokenizer(
            text, truncation=True, max_length=512, return_tensors="pt"
        )
        decoded = self._tokenizer.decode(
            tokens["input_ids"][0], skip_special_tokens=True
        )

        results = self._pipe(decoded)
        seen: set[tuple[str, str]] = set()
        actors: list[dict] = []

        for r in results:
            tag = r.get("entity_group")
            if tag not in ("ORG", "PER"):
                continue
            if float(r.get("score", 0)) < self.SCORE_THRESHOLD:
                continue

            text_clean = str(r.get("word", "")).strip().title()
            if len(text_clean) < self.MIN_TEXT_LEN:
                continue

            label = "ChucDanh" if tag == "PER" else _classify_org(text_clean)
            key = (text_clean, label)
            if key in seen:
                continue
            seen.add(key)

            actors.append(
                {
                    "text": text_clean,
                    "label": label,
                    "score": round(float(r["score"]), 3),
                    "source_dieu_id": dieu_id,
                }
            )

        # Fallback to regex extractor if model returns empty.
        if not actors:
            actors = self._fallback_extract(text, dieu_id)

        return actors

    def _fallback_extract(self, text: str, dieu_id: str) -> list[dict]:
        patterns = [
            (
                re.compile(
                    r"\b(?:Thủ tướng|Thu tuong|Phó thủ tướng|Pho thu tuong|"
                    r"Bộ trưởng|Bo truong|Chủ tịch Quốc hội|Chu tich Quoc hoi|"
                    r"Chủ tịch nước|Chu tich nuoc)\b",
                    flags=re.IGNORECASE,
                ),
                "ChucDanh",
            ),
            (
                re.compile(
                    r"\b(?:Bộ|Bo|Cục|Cuc|Tổng cục|Tong cuc|Ủy ban|Uy ban|"
                    r"Chính phủ|Chinh phu|Quốc hội|Quoc hoi|Viện|Vien|"
                    r"Tòa án|Toa an|Sở|So)\s+[^\n,.;:]{2,80}",
                    flags=re.IGNORECASE,
                ),
                "ORG",
            ),
            (
                re.compile(
                    r"\b(?:Công ty|Cong ty|Doanh nghiệp|Doanh nghiep|"
                    r"Tập đoàn|Tap doan|Tổng công ty|Tong cong ty)\s+[^\n,.;:]{2,80}",
                    flags=re.IGNORECASE,
                ),
                "ORG",
            ),
        ]

        actors: list[dict] = []
        seen: set[tuple[str, str]] = set()

        for pattern, entity_type in patterns:
            for match in pattern.finditer(text):
                text_clean = match.group(0).strip().title()
                if len(text_clean) < self.MIN_TEXT_LEN:
                    continue

                label = "ChucDanh" if entity_type == "ChucDanh" else _classify_org(text_clean)
                key = (text_clean, label)
                if key in seen:
                    continue
                seen.add(key)

                actors.append(
                    {
                        "text": text_clean,
                        "label": label,
                        "score": 0.5,
                        "source_dieu_id": dieu_id,
                    }
                )

        return actors


_ner_extractor: Optional[NERExtractor] = None


def get_ner_extractor() -> NERExtractor:
    global _ner_extractor
    if _ner_extractor is None:
        _ner_extractor = NERExtractor()
    return _ner_extractor


def _read_docx_paragraphs(docx_path: str) -> list[str]:
    from docx import Document

    doc = Document(docx_path)
    return [p.text.strip() for p in doc.paragraphs if p.text and p.text.strip()]


def _chunk_paragraphs(paragraphs: list[str], max_chars: int = 1200) -> list[str]:
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for para in paragraphs:
        para_len = len(para) + 1
        if current and current_len + para_len > max_chars:
            chunks.append("\n".join(current))
            current = [para]
            current_len = para_len
        else:
            current.append(para)
            current_len += para_len

    if current:
        chunks.append("\n".join(current))
    return chunks


def extract_actors_from_docx(docx_path: str, max_chars: int = 1200) -> list[dict]:
    paragraphs = _read_docx_paragraphs(docx_path)
    chunks = _chunk_paragraphs(paragraphs, max_chars=max_chars)
    ner = get_ner_extractor()

    all_actors: list[dict] = []
    seen: set[tuple[str, str]] = set()

    for idx, chunk in enumerate(chunks, start=1):
        actors = ner.extract_actors(chunk, f"chunk_{idx}")
        for actor in actors:
            key = (actor["text"], actor["label"])
            if key in seen:
                continue
            seen.add(key)
            all_actors.append(actor)

    return all_actors


def _print_result(actors: list[dict], limit: int) -> None:
    counts = Counter(a["label"] for a in actors)
    print(f"Tong actor: {len(actors)}")
    print("Thong ke theo label:")
    for label, count in sorted(counts.items()):
        print(f"  - {label}: {count}")

    sample = actors[:limit] if limit > 0 else actors
    print(f"\nTop {len(sample)} actors (JSON):")
    try:
        print(json.dumps(sample, ensure_ascii=False, indent=2))
    except UnicodeEncodeError:
        print(json.dumps(sample, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    os.environ.setdefault("PYTHONUTF8", "1")
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass

    default_docx = Path(__file__).resolve().parents[1] / "data" / "raw" / "luatanm2025.docx"

    parser = argparse.ArgumentParser(description="Run NER for a law .docx file.")
    parser.add_argument("--docx", type=str, default=str(default_docx), help="Path to .docx input file")
    parser.add_argument("--max-chars", type=int, default=1200, help="Chunk size by characters")
    parser.add_argument("--limit", type=int, default=50, help="How many actors to print")
    args = parser.parse_args()

    try:
        output = extract_actors_from_docx(args.docx, max_chars=args.max_chars)
        _print_result(output, limit=args.limit)
    except Exception as exc:
        print(f"[ERROR] {exc}")
        sys.exit(1)
