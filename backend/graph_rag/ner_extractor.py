"""
ner_extractor.py — Wrapper cho NER fine-tuned model (NlpHUST/electra-vi).

Pipeline ĐÚNG với khi train (xem notebooks/finetune_ner.ipynb §12):
    raw text
      → underthesea.word_tokenize  (giữ '_' cho từ ghép)
      → merge_tokens               (gộp số+đơn vị, struct, standards…)
      → tokenizer(is_split_into_words=True)
      → model.argmax → BIO → merge entity → replace '_'→' '

Output mỗi entity:
    {
      "type":           "LEGAL_ACTOR",
      "text":           "doanh nghiệp viễn thông",
      "score":          0.987,
      "char_start":     12,        # vị trí trong text gốc
      "char_end":       35,
      "sentence_idx":   0,         # index câu trong chunk (0-based)
      "source":         "model",   # | "rule" | "whitelist"
      "subclass":       "TELECOM_OPERATOR"  # optional
    }
"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Optional

import numpy as np
import torch
from transformers import AutoModelForTokenClassification, AutoTokenizer
from underthesea import word_tokenize as _ut_word_tokenize


# ── Default config ───────────────────────────────────────────────────
_DEFAULT_MODEL_DIR = Path(__file__).resolve().parents[2] / "ner_models"
MAX_LENGTH         = 512
SCORE_THRESHOLD    = 0.6


# =====================================================================
# Tokenization (must match train pipeline)
# =====================================================================
_TIME_UNITS   = {"giờ", "ngày", "tháng", "năm", "tuần", "phút", "giây"}
_MONEY_UNITS  = {"triệu", "tỷ", "nghìn", "trăm"}
_TECH_UNITS   = {"Gbps", "Mbps", "MB", "GB", "TB", "KB", "GHz", "MHz", "ms", "bps"}
_CURRENCIES   = {"USD", "EUR", "VND", "GBP", "JPY"}
_STRUCT_WORDS = {"Điều", "Khoản", "Điểm", "Mục", "Chương", "Phần"}
_STANDARDS    = {"ISO", "IEC", "NIST", "OWASP", "CWE", "CVE", "CVSS",
                 "PCI", "ETSI", "TCVN", "QCVN"}


def merge_tokens(tokens: list[str]) -> list[str]:
    """Gộp các token nhỏ thành cụm đơn nhất (số+đơn vị, struct+số, standard+code)."""
    out, i, n = [], 0, len(tokens)
    digit = re.compile(r"^\d[\d,\.]*$")
    while i < n:
        t = tokens[i]
        nxt = tokens[i + 1] if i + 1 < n else None
        # số + thời gian (kèm "làm_việc")
        if nxt and digit.match(t) and nxt in _TIME_UNITS:
            m = f"{t}_{nxt}"; i += 2
            if i < n and tokens[i] == "làm_việc":
                m += "_làm_việc"; i += 1
            out.append(m); continue
        # số + tiền (kèm "đồng")
        if nxt and digit.match(t) and nxt in _MONEY_UNITS:
            m = f"{t}_{nxt}"; i += 2
            if i < n and tokens[i] == "đồng":
                m += "_đồng"; i += 1
            out.append(m); continue
        # số + %
        if nxt and digit.match(t) and nxt == "%":
            out.append(f"{t}%"); i += 2; continue
        # số + tech / currency / lần
        if nxt and digit.match(t) and nxt in _TECH_UNITS:
            out.append(f"{t}_{nxt}"); i += 2; continue
        if nxt and digit.match(t) and nxt in _CURRENCIES:
            out.append(f"{t}_{nxt}"); i += 2; continue
        if nxt and re.match(r"^\d+$", t) and nxt == "lần":
            out.append(f"{t}_lần"); i += 2; continue
        # struct + số/chữ cái
        if t in _STRUCT_WORDS and nxt and re.match(r"^\d+$|^[a-zđ]$", nxt):
            out.append(f"{t}_{nxt}"); i += 2; continue
        # standards
        if t in _STANDARDS and nxt:
            if re.match(r"^\d[\d\-\.]*$|^SP$|^DSS$|^MASVS$", nxt):
                m = f"{t}_{nxt}"; i += 2
                if i + 1 < n and tokens[i] == ":" and re.match(r"^\d+$", tokens[i + 1]):
                    m += f":{tokens[i + 1]}"; i += 2
                out.append(m); continue
            if nxt == "/" and i + 2 < n and tokens[i + 2] in _STANDARDS:
                m = f"{t}/{tokens[i + 2]}"; i += 3
                if i < n and re.match(r"^\d[\d\-\.]*$", tokens[i]):
                    m += f"_{tokens[i]}"; i += 1
                out.append(m); continue
        # CVE-YYYY-NNNN
        if t == "CVE" and nxt == "-" and i + 2 < n and re.match(r"^\d{4}$", tokens[i + 2]):
            m = f"CVE-{tokens[i + 2]}"; i += 3
            if i + 1 < n and tokens[i] == "-":
                m += f"-{tokens[i + 1]}"; i += 2
            out.append(m); continue
        # Tier I / II / 1
        if t == "Tier" and nxt and re.match(r"^(I{1,3}|IV|V|\d+)$", nxt):
            out.append(f"Tier_{nxt}"); i += 2; continue
        # cấp độ N
        if t == "cấp" and nxt in ("độ", "_độ") and i + 2 < n and re.match(r"^\d+$", tokens[i + 2]):
            out.append(f"cấp_độ_{tokens[i + 2]}"); i += 3; continue
        out.append(t); i += 1
    return out


def word_tokenize(text: str) -> list[str]:
    return merge_tokens(_ut_word_tokenize(text, format="text").split())


# =====================================================================
# Sentence splitter — theo dấu kết câu, tránh "Đ.", "Khoản 1.", v.v.
# =====================================================================
_SENT_SPLIT = re.compile(r"(?<=[\.!?\?])\s+(?=[A-ZĐÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚĂŨƠƯ\d])")


def split_sentences(text: str) -> list[tuple[int, int, str]]:
    """Trả list (char_start, char_end, sentence_text)."""
    out = []
    pos = 0
    for piece in _SENT_SPLIT.split(text):
        if not piece.strip():
            continue
        idx = text.find(piece, pos)
        if idx < 0:
            idx = pos
        out.append((idx, idx + len(piece), piece))
        pos = idx + len(piece)
    return out


def _sentence_idx_of(char_pos: int, sentences: list[tuple[int, int, str]]) -> int:
    for i, (s, e, _) in enumerate(sentences):
        if s <= char_pos < e:
            return i
    return max(0, len(sentences) - 1)


# =====================================================================
# Rule-based structural (PART/CHAPTER/SECTION/POINT/APPENDIX)
# =====================================================================
_STRUCTURAL_PATTERNS = [
    (r"(?<!\w)(Phần\s+(?:[IVX]+|\d+))(?!\w)",              "PART"),
    (r"(?<!\w)(Chương\s+(?:[IVX]+|\d+))(?!\w)",            "CHAPTER"),
    (r"(?<!\w)(Mục\s+\d+)(?!\w)",                           "SECTION"),
    (r"(?<!\w)([Đđ]iểm\s+[a-zđ])(?!\w)",                   "POINT"),
    (r"(?<!\w)(Phụ\s+lục\s+(?:[IVX]+|[A-Z]|\d+))(?!\w)",  "APPENDIX"),
]


def _rule_structural(text: str) -> list[dict]:
    found = []
    for pat, etype in _STRUCTURAL_PATTERNS:
        for m in re.finditer(pat, text, re.IGNORECASE):
            found.append({
                "type":       etype,
                "text":       m.group(1).strip(),
                "score":      1.0,
                "char_start": m.start(1),
                "char_end":   m.end(1),
                "source":     "rule",
            })
    return found


# =====================================================================
# Post-fixes (giữ từ pipeline cũ, đã chứng minh tốt)
# =====================================================================
_COND_TRIGGERS = {"khi", "nếu", "trường_hợp", "khi_có", "khi có", "trong_trường_hợp"}


def _fix_yeu_cau(entities: list[dict], words: list[str]) -> list[dict]:
    """OBLIGATION 'yêu cầu' đứng sau 'khi/nếu' → là CONDITION, không phải nghĩa vụ."""
    wl = [w.lower() for w in words]
    out = []
    for e in entities:
        if (e["type"] == "OBLIGATION"
                and e["text"].lower().strip() in ("yêu cầu", "yêu_cầu")):
            s = e.get("word_start", 0)
            prev  = set(wl[max(0, s - 3):s])
            after = set(wl[e.get("word_end", s + 1):e.get("word_end", s + 1) + 2])
            if prev & _COND_TRIGGERS or s <= 1 or after & {"bằng_văn_bản", "bằng"}:
                out.append({**e, "type": "CONDITION"})
                continue
        out.append(e)
    return out


def _fix_telecom(entities: list[dict]) -> list[dict]:
    """TELECOM_OPERATOR là sub-class của LEGAL_ACTOR."""
    return [
        {**e, "type": "LEGAL_ACTOR", "subclass": "TELECOM_OPERATOR"}
        if e["type"] == "TELECOM_OPERATOR" else e
        for e in entities
    ]


_DATA_WHITELIST = {
    "dữ liệu cá nhân", "dữ liệu cá nhân nhạy cảm", "dữ liệu sinh trắc học",
    "dữ liệu sức khỏe", "dữ liệu tài chính", "dữ liệu y tế", "dữ liệu nhạy cảm",
    "dữ liệu hành vi cá nhân", "dữ liệu di truyền", "dữ liệu vị trí",
    "dữ liệu người sử dụng", "dữ liệu người dùng", "dữ liệu thuê bao",
    "nhật ký truy cập", "nhật ký hoạt động", "thông tin cá nhân",
    "thông tin người dùng", "thông tin thuê bao", "thông tin đăng ký",
    "dữ liệu bí mật nhà nước", "thông tin bảo mật",
}


def _fix_data_type(entities: list[dict], text: str) -> list[dict]:
    out = list(entities)
    tl = text.lower()
    seen = {e["text"].lower().replace("_", " ").strip() for e in out}
    for e in out:
        if (e["type"] in ("DATA_TYPE", "DATA")
                and e["text"].lower().replace("_", " ").strip() in _DATA_WHITELIST):
            e["score"] = max(e["score"], 0.85)
    for phrase in sorted(_DATA_WHITELIST, key=len, reverse=True):
        if phrase not in seen and phrase in tl:
            idx = tl.find(phrase)
            out.append({
                "type":       "DATA_TYPE",
                "text":       text[idx:idx + len(phrase)],
                "score":      0.85,
                "char_start": idx,
                "char_end":   idx + len(phrase),
                "source":     "whitelist",
            })
            seen.add(phrase)
    return out


# =====================================================================
# LOCATION + SYSTEM whitelist (cell 12 demo §3b)
# =====================================================================
_LOCATION_PHRASES = sorted([
    "ngoài lãnh thổ Việt Nam", "lãnh thổ Việt Nam",
    "trong lãnh thổ Việt Nam", "Việt Nam",
    "nước ngoài", "trong nước", "quốc tế",
    "Hà Nội", "TP. Hồ Chí Minh", "TP.HCM", "Hồ Chí Minh",
    "Đà Nẵng", "Cần Thơ", "Hải Phòng",
], key=len, reverse=True)


def _rule_location(text: str) -> list[dict]:
    found: list[dict] = []
    used: list[tuple[int, int]] = []
    tl = text.lower()
    for phrase in _LOCATION_PHRASES:
        sp = phrase.lower()
        idx = 0
        while True:
            pos = tl.find(sp, idx)
            if pos < 0:
                break
            end = pos + len(phrase)
            if not any(s <= pos < e or s < end <= e for s, e in used):
                found.append({
                    "type":       "LOCATION",
                    "text":       text[pos:end],
                    "score":      1.0,
                    "char_start": pos,
                    "char_end":   end,
                    "source":     "rule",
                })
                used.append((pos, end))
            idx = pos + 1
    return found


_SYSTEM_PHRASES = sorted([
    "hệ thống thông tin", "hệ thống máy chủ", "hệ thống mạng",
    "hệ thống lõi", "hệ thống giám sát", "hệ thống phát hiện xâm nhập",
    "cơ sở dữ liệu", "máy chủ", "hạ tầng thông tin", "hạ tầng số",
    "hạ tầng kỹ thuật số", "nền tảng số", "điện toán đám mây",
    "đám mây", "phần mềm độc hại", "tường lửa", "phần mềm",
    "ứng dụng di động", "thiết bị đầu cuối",
], key=len, reverse=True)


def _rule_system(text: str, existing: list[dict]) -> list[dict]:
    """Bắt SYSTEM bị model bỏ sót — không chồng span với entity đã có."""
    existing_texts = {
        e["text"].lower().replace("_", " ").strip()
        for e in existing if e["type"] == "SYSTEM"
    }
    used = [(e.get("char_start", -1), e.get("char_end", -1)) for e in existing]
    found: list[dict] = []
    tl = text.lower()
    for phrase in _SYSTEM_PHRASES:
        if phrase in existing_texts:
            continue
        idx = 0
        while True:
            pos = tl.find(phrase, idx)
            if pos < 0:
                break
            end = pos + len(phrase)
            if not any(s != -1 and s <= pos < e for s, e in used):
                found.append({
                    "type":       "SYSTEM",
                    "text":       text[pos:end],
                    "score":      0.9,
                    "char_start": pos,
                    "char_end":   end,
                    "source":     "rule",
                })
                used.append((pos, end))
                existing_texts.add(phrase)
            idx = pos + 1
    return found


# =====================================================================
# Main extractor
# =====================================================================
class NerExtractor:
    def __init__(self, model_dir: Optional[str | Path] = None,
                 device: Optional[str] = None):
        self.model_dir = Path(model_dir) if model_dir else _DEFAULT_MODEL_DIR
        self.device = torch.device(
            device or ("cuda" if torch.cuda.is_available() else "cpu")
        )
        self.tok = AutoTokenizer.from_pretrained(str(self.model_dir), use_fast=True)
        self.mdl = (AutoModelForTokenClassification
                    .from_pretrained(str(self.model_dir))
                    .eval()
                    .to(self.device))

        label_path = self.model_dir / "label_mapping.json"
        if label_path.exists():
            mp = json.loads(label_path.read_text(encoding="utf-8"))
            self.id2label = {int(k): v for k, v in mp["id2label"].items()}
        else:
            self.id2label = {int(k): v for k, v in self.mdl.config.id2label.items()}

    # ----------------------------------------------------------------
    @torch.no_grad()
    def _model_predict(self, text: str) -> tuple[list[str], list[dict]]:
        words = word_tokenize(text)
        enc = self.tok(
            words,
            is_split_into_words=True,
            return_tensors="pt",
            truncation=True,
            max_length=MAX_LENGTH,
            return_offsets_mapping=False,
        ).to(self.device)

        logits = self.mdl(**enc).logits[0]
        probs  = torch.softmax(logits, dim=-1).cpu().numpy()
        pred_ids = probs.argmax(-1)
        word_ids = enc.word_ids(0)

        word_label = [None] * len(words)
        word_score = [0.0]  * len(words)
        seen = set()
        for j, wid in enumerate(word_ids):
            if wid is None or wid in seen:
                continue
            seen.add(wid)
            word_label[wid] = self.id2label[int(pred_ids[j])]
            word_score[wid] = float(probs[j, pred_ids[j]])

        # Map word_idx → char position trong text gốc
        word_char_start = self._map_words_to_char(text, words)

        entities: list[dict] = []
        cur: dict | None = None

        def flush():
            nonlocal cur
            if cur is None:
                return
            cs = word_char_start[cur["word_start"]][0]
            ce = word_char_start[cur["word_end"] - 1][1]
            entities.append({
                "type":       cur["type"],
                "text":       " ".join(cur["tokens"]).replace("_", " "),
                "score":      round(sum(cur["scores"]) / len(cur["scores"]), 4),
                "char_start": cs,
                "char_end":   ce,
                "word_start": cur["word_start"],
                "word_end":   cur["word_end"],
                "source":     "model",
            })
            cur = None

        for i, (w, lab, s) in enumerate(zip(words, word_label, word_score)):
            if lab is None or lab == "O":
                flush(); continue
            prefix, _, etype = lab.partition("-")
            if prefix == "B" or cur is None or cur["type"] != etype:
                flush()
                cur = {"type": etype, "tokens": [w], "scores": [s],
                       "word_start": i, "word_end": i + 1}
            else:
                cur["tokens"].append(w); cur["scores"].append(s)
                cur["word_end"] = i + 1
        flush()
        return words, entities

    @staticmethod
    def _map_words_to_char(text: str, words: list[str]) -> list[tuple[int, int]]:
        """Best-effort map word index → (char_start, char_end) trong text gốc."""
        spans = []
        cursor = 0
        for w in words:
            surface = w.replace("_", " ")
            idx = text.find(surface, cursor)
            if idx < 0:
                # fallback: skip mismatch (giữ cursor)
                spans.append((cursor, cursor + len(surface)))
            else:
                spans.append((idx, idx + len(surface)))
                cursor = idx + len(surface)
        return spans

    # ----------------------------------------------------------------
    def extract(self, text: str, score_threshold: float = SCORE_THRESHOLD) -> list[dict]:
        """Trả list entity. Mỗi entity đã có sentence_idx tính sẵn theo char_start."""
        words, model_ents = self._model_predict(text)
        # filter low-confidence trước fix
        model_ents = [e for e in model_ents if e["score"] >= score_threshold]
        # bỏ structural từ model (đã có rule riêng, ổn định hơn)
        model_ents = [
            e for e in model_ents
            if e["type"] not in {"PART", "CHAPTER", "SECTION", "POINT", "APPENDIX"}
        ]

        # rule-based enrichment (structural + location)
        entities = model_ents + _rule_structural(text) + _rule_location(text)
        entities = _fix_yeu_cau(entities, words)
        entities = _fix_telecom(entities)
        entities = _fix_data_type(entities, text)
        # SYSTEM whitelist sau cùng — không chồng span với entity đã có
        entities += _rule_system(text, entities)

        # dedup keep-best-score (giống cell 12 demo)
        best: dict[tuple[str, str], dict] = {}
        for e in entities:
            key = (e["type"], e["text"].lower().replace("_", " ").strip())
            if key not in best or e["score"] > best[key]["score"]:
                best[key] = e
        deduped = sorted(best.values(), key=lambda e: e.get("char_start", 0))

        # gắn sentence_idx
        sents = split_sentences(text)
        for e in deduped:
            e["sentence_idx"] = _sentence_idx_of(e.get("char_start", 0), sents)
        return deduped


# ── Module-level singleton (lazy) ────────────────────────────────────
@lru_cache(maxsize=1)
def get_ner_extractor(model_dir: Optional[str] = None) -> NerExtractor:
    return NerExtractor(model_dir=model_dir)
