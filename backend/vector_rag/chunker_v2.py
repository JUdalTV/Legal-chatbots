"""
chunker_v2.py — Hierarchical semantic chunking cho văn bản pháp luật.

Pipeline:
  raw text  →  parse_to_articles(text, law_id)
            →  chunk_legal_document(articles, ...)
            →  list[LegalChunk]

Với mỗi Điều, sinh ra:
  • 1  article_summary chunk (cho câu hỏi "Điều X nói về gì")
  • N  clause chunks (gộp khoản ngắn / chunk khoản vừa / split điểm khoản dài)

Cùng tồn tại với `chunker.py` cũ — chunker.py vẫn được Graph RAG dùng để giữ
cầu nối `LawChunk.neo4j_id`. `LegalChunk.article` ở đây CŨNG = neo4j_id để
Vector RAG nối được sang Neo4j khi cần.
"""
from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from typing import Callable, Optional

from .chunker import CHUONG_PATTERN, DIEU_PATTERN, LAW_META


# ════════════════════════════════════════════════════════════════════
# Data classes
# ════════════════════════════════════════════════════════════════════
@dataclass
class LegalChunk:
    chunk_id:    str
    law_id:      str                    # "LuatAnNinhMang2025"
    chapter:     Optional[str]          # "Chương II"
    article:     str                    # "LuatAnNinhMang2025_dieu_11"  (= neo4j_id)
    clause:      Optional[str]          # "Khoản 2"
    points:      list[str]              # ["a", "b"] nếu chunk gộp điểm
    content:     str                    # text đưa vào embed/LLM
    token_count: int
    chunk_type:  str                    # "clause" | "article_summary" | "point_group"
    refs:        list[str]              # ["LuatAnNinhMang2025_dieu_10"] cross-refs
    metadata:    dict = field(default_factory=dict)


# Internal AST format từ parse_to_articles()
@dataclass
class _PointAST:
    label:   str   # "điểm a"
    so:      str   # "a"
    content: str   # "Bảo đảm an toàn ..."


@dataclass
class _ClauseAST:
    id:               str             # "khoan_2"
    label:            str             # "Khoản 2"
    so:               str             # "2"
    content:          str
    points:           list[_PointAST]
    is_continuation:  bool = False
    parent_header:    str = ""
    modality:         Optional[str] = None    # OBLIGATION/PROHIBITION/PERMISSION
    header:           str = ""                # dòng dẫn "có trách nhiệm sau đây:"


@dataclass
class _ArticleAST:
    id:       str               # "LuatAnNinhMang2025_dieu_15"
    label:    str               # "Điều 15. Trách nhiệm ..."
    so:       str               # "15"
    chapter:  Optional[str]
    content:  str               # full text Điều
    clauses:  list[_ClauseAST]


# ════════════════════════════════════════════════════════════════════
# Public entry
# ════════════════════════════════════════════════════════════════════
def chunk_legal_document(
    articles: list[_ArticleAST],
    *,
    law_id: str,
    count_tokens: Callable[[str], int],
    min_tokens: int = 80,
    max_tokens: int = 400,
    overlap_context: bool = True,
) -> list[LegalChunk]:
    """Hierarchical chunking — xem header file."""
    chunks: list[LegalChunk] = []
    law_meta = LAW_META.get(law_id, {})
    law_label = law_meta.get("ten", law_id)

    for art in articles:
        # ── Bước 1: article_summary ───────────────────────────────
        summary_text = _build_article_summary(art, law_label)
        chunks.append(LegalChunk(
            chunk_id    = _mk_id(law_id, f"{art.id}_summary"),
            law_id      = law_id,
            chapter     = art.chapter,
            article     = art.id,
            clause      = None,
            points      = [],
            content     = summary_text,
            token_count = count_tokens(summary_text),
            chunk_type  = "article_summary",
            refs        = _extract_refs(summary_text, law_id),
            metadata    = {"article_label": art.label, "law_label": law_label},
        ))

        # ── Bước 2: clauses ──────────────────────────────────────
        pending: list[_ClauseAST] = []
        pending_tokens = 0

        def _flush() -> None:
            nonlocal pending, pending_tokens
            if not pending:
                return
            chunks.append(_make_grouped_chunk(
                pending, art, law_id, law_label,
                count_tokens, overlap_context,
            ))
            pending = []
            pending_tokens = 0

        for cl in art.clauses:
            cl_tok = count_tokens(cl.content)

            # A. khoản quá dài → split theo điểm hoặc giữ nguyên
            if cl_tok > max_tokens:
                _flush()
                if cl.points:
                    chunks.extend(_chunk_by_points(
                        cl, art, law_id, law_label,
                        count_tokens, max_tokens, overlap_context,
                    ))
                else:
                    chunks.append(_make_clause_chunk(
                        cl, art, law_id, law_label,
                        count_tokens, overlap_context,
                    ))

            # B. khoản quá ngắn → gộp
            elif cl_tok < min_tokens:
                pending.append(cl)
                pending_tokens += cl_tok
                if pending_tokens >= min_tokens:
                    _flush()

            # C. khoản vừa
            else:
                _flush()
                chunks.append(_make_clause_chunk(
                    cl, art, law_id, law_label,
                    count_tokens, overlap_context,
                ))

        _flush()

    return chunks


# ════════════════════════════════════════════════════════════════════
# Builders
# ════════════════════════════════════════════════════════════════════
def _build_article_summary(art: _ArticleAST, law_label: str) -> str:
    """Tóm tắt: tiêu đề Điều + dòng đầu mỗi khoản (max ~80 ký tự)."""
    lines = [f"{art.label} — {law_label}"]
    for cl in art.clauses[:8]:
        first_sent = cl.content.split(".", 1)[0].strip()
        if first_sent:
            lines.append(f"{cl.label}: {first_sent[:120]}")
    return "\n".join(lines)


def _make_clause_chunk(
    cl: _ClauseAST, art: _ArticleAST, law_id: str, law_label: str,
    count_tokens: Callable[[str], int], overlap_context: bool,
) -> LegalChunk:
    breadcrumb = f"{art.label}, {cl.label} — {law_label}\n"
    parent = (cl.parent_header + "\n") if (overlap_context and cl.is_continuation and cl.parent_header) else ""
    content = breadcrumb + parent + cl.content
    return LegalChunk(
        chunk_id    = _mk_id(law_id, f"{art.id}_{cl.id}"),
        law_id      = law_id,
        chapter     = art.chapter,
        article     = art.id,
        clause      = cl.label,
        points      = [],
        content     = content,
        token_count = count_tokens(content),
        chunk_type  = "clause",
        refs        = _extract_refs(cl.content, law_id),
        metadata    = {
            "modality":      cl.modality,
            "article_label": art.label,
            "clause_label":  cl.label,
        },
    )


def _make_grouped_chunk(
    group: list[_ClauseAST], art: _ArticleAST, law_id: str, law_label: str,
    count_tokens: Callable[[str], int], overlap_context: bool,
) -> LegalChunk:
    """Gộp ≥ 2 khoản ngắn thành 1 chunk."""
    if len(group) == 1:
        return _make_clause_chunk(group[0], art, law_id, law_label, count_tokens, overlap_context)
    breadcrumb = f"{art.label} — {law_label}\n"
    body = "\n".join(f"{cl.label}. {cl.content}" for cl in group)
    content = breadcrumb + body
    so_list = "_".join(cl.so for cl in group)
    refs = sorted({r for cl in group for r in _extract_refs(cl.content, law_id)})
    return LegalChunk(
        chunk_id    = _mk_id(law_id, f"{art.id}_grouped_{so_list}"),
        law_id      = law_id,
        chapter     = art.chapter,
        article     = art.id,
        clause      = ",".join(cl.label for cl in group),
        points      = [],
        content     = content,
        token_count = count_tokens(content),
        chunk_type  = "clause",
        refs        = refs,
        metadata    = {"article_label": art.label},
    )


def _chunk_by_points(
    cl: _ClauseAST, art: _ArticleAST, law_id: str, law_label: str,
    count_tokens: Callable[[str], int], max_tokens: int, overlap_context: bool,
) -> list[LegalChunk]:
    """Khoản dài có nhiều điểm → gộp điểm tới gần max_tokens."""
    out: list[LegalChunk] = []
    group: list[_PointAST] = []
    g_tok = 0
    header = cl.header or cl.content.split("\n", 1)[0]

    def _emit() -> None:
        nonlocal group, g_tok
        if not group:
            return
        breadcrumb = f"{art.label}, {cl.label} — {law_label}\n"
        body = header + "\n" + "\n".join(f"{p.label}) {p.content}" for p in group)
        content = breadcrumb + body
        so_list = "".join(p.so for p in group)
        out.append(LegalChunk(
            chunk_id    = _mk_id(law_id, f"{art.id}_{cl.id}_pts_{so_list}"),
            law_id      = law_id,
            chapter     = art.chapter,
            article     = art.id,
            clause      = cl.label,
            points      = [p.so for p in group],
            content     = content,
            token_count = count_tokens(content),
            chunk_type  = "point_group",
            refs        = _extract_refs(body, law_id),
            metadata    = {
                "modality":      cl.modality,
                "article_label": art.label,
                "clause_label":  cl.label,
            },
        ))
        group = []
        g_tok = 0

    for pt in cl.points:
        pt_tok = count_tokens(pt.content)
        if g_tok + pt_tok > max_tokens and group:
            _emit()
        group.append(pt)
        g_tok += pt_tok
    _emit()
    return out


# ════════════════════════════════════════════════════════════════════
# parse_to_articles — text → list[_ArticleAST]
# ════════════════════════════════════════════════════════════════════
_KHOAN_START = re.compile(r"^(\d+)\.\s+(.+)", re.DOTALL)
_POINT_START = re.compile(r"^([a-zđ])\)\s+(.+)", re.DOTALL)
_HEADER_TAIL = re.compile(r":\s*$")  # khoản kết thúc bằng ":" → có header

_MODALITY_RULES = [
    ("PROHIBITION", re.compile(r"\b(không\s+được|nghiêm\s+cấm|cấm)\b", re.IGNORECASE)),
    ("OBLIGATION",  re.compile(r"\b(phải|có\s+trách\s+nhiệm|có\s+nghĩa\s+vụ|bắt\s+buộc)\b", re.IGNORECASE)),
    ("PERMISSION",  re.compile(r"\b(được\s+phép|có\s+quyền|được\s+quyền)\b", re.IGNORECASE)),
]

_REF_LOCAL = re.compile(
    r"[ĐĐđ]iều\s+(\d+[a-z]?)(?!\s*(?:của\s+)?(?:Luật|Nghị\s+định|Pháp\s+lệnh))",
    re.IGNORECASE,
)


def parse_to_articles(text: str, law_id: str) -> list[_ArticleAST]:
    """Parse raw text → AST `list[_ArticleAST]` để feed `chunk_legal_document`."""
    chapters = _split_chapters(text)
    out: list[_ArticleAST] = []
    for ch in chapters:
        chap_label = ch["label"]
        for art_dict in _split_articles(ch["content"]):
            so   = art_dict["so"]
            ten  = art_dict["ten"]
            body = art_dict["body"]
            clauses = _split_clauses(body)
            out.append(_ArticleAST(
                id      = f"{law_id}_dieu_{so}",
                label   = f"Điều {so}. {ten}".rstrip(),
                so      = so,
                chapter = chap_label,
                content = body,
                clauses = clauses,
            ))
    return out


def _split_chapters(text: str) -> list[dict]:
    matches = list(CHUONG_PATTERN.finditer(text))
    if not matches:
        return [{"label": None, "content": text}]
    out: list[dict] = []
    for i, m in enumerate(matches):
        so  = m.group(1).upper()
        ten = (m.group(2) or "").strip().title()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        label = f"Chương {so}" + (f" {ten}" if ten else "")
        out.append({"label": label, "content": text[m.end():end]})
    return out


def _split_articles(chap_text: str) -> list[dict]:
    matches = list(DIEU_PATTERN.finditer(chap_text))
    if not matches:
        return []
    out: list[dict] = []
    for i, m in enumerate(matches):
        so = m.group(1)
        end = matches[i + 1].start() if i + 1 < len(matches) else len(chap_text)
        block = chap_text[m.start():end].strip()

        # Tên Điều: dòng đầu sau "Điều X. "
        first_line = block.split("\n", 1)[0]
        h = re.match(r"^[ĐĐ]iều\s+\d+[a-z]?\.\s+(.+)", first_line)
        ten = ""
        if h:
            raw = h.group(1)
            for stop in (" 1. ", "\n1.", "Trong Luật", "Luật này"):
                idx = raw.find(stop)
                if idx > 5:
                    raw = raw[:idx]; break
            ten = raw.strip().rstrip(".")[:120]

        # Body = block không có dòng "Điều X."
        body = block
        out.append({"so": so, "ten": ten, "body": body})
    return out


def _split_clauses(body: str) -> list[_ClauseAST]:
    """Tách body Điều thành các khoản. Body có thể chứa cả tên Điều ở dòng đầu."""
    # Bỏ dòng "Điều X. ..." nếu có
    lines = body.split("\n")
    if lines and re.match(r"^[ĐĐ]iều\s+\d+[a-z]?\.\s+", lines[0]):
        lines = lines[1:]

    # Gom theo "N. " (đầu dòng)
    raw_groups: list[tuple[str, list[str]]] = []
    current_so: Optional[str] = None
    current_lines: list[str] = []
    for ln in lines:
        m = re.match(r"^(\d+)\.\s+(.+)", ln)
        if m:
            if current_so is not None:
                raw_groups.append((current_so, current_lines))
            current_so = m.group(1)
            current_lines = [m.group(2)]
        else:
            if current_so is not None:
                current_lines.append(ln)

    if current_so is not None:
        raw_groups.append((current_so, current_lines))

    # Trường hợp Điều không có khoản (1 đoạn duy nhất)
    if not raw_groups:
        text = "\n".join(lines).strip()
        if not text:
            return []
        return [_ClauseAST(
            id="khoan_1", label="Khoản 1", so="1",
            content=text, points=[], modality=_detect_modality(text),
        )]

    clauses: list[_ClauseAST] = []
    for so, ln_list in raw_groups:
        clause_text = "\n".join(ln_list).strip()
        first = clause_text.split("\n", 1)[0].strip()
        # Nếu khoản kết thúc câu đầu bằng ":" → câu đầu là header dẫn cho
        # các điểm a/b/c CÙNG KHOẢN (chunker dùng khi split theo điểm)
        header = first if _HEADER_TAIL.search(first) else ""
        clauses.append(_ClauseAST(
            id              = f"khoan_{so}",
            label           = f"Khoản {so}",
            so              = so,
            content         = clause_text,
            points          = _split_points(clause_text),
            is_continuation = False,
            parent_header   = "",
            modality        = _detect_modality(clause_text),
            header          = header,
        ))
    return clauses


def _split_points(clause_text: str) -> list[_PointAST]:
    """Tách điểm a) b) c) trong nội dung khoản."""
    out: list[_PointAST] = []
    for m in re.finditer(r"(?m)^([a-zđ])\)\s+(.+?)(?=\n[a-zđ]\)|\Z)",
                          clause_text, re.DOTALL):
        out.append(_PointAST(
            label   = f"điểm {m.group(1)}",
            so      = m.group(1),
            content = m.group(2).strip(),
        ))
    return out


def _detect_modality(text: str) -> Optional[str]:
    for tag, rx in _MODALITY_RULES:
        if rx.search(text):
            return tag
    return None


def _extract_refs(text: str, law_id: str) -> list[str]:
    refs: list[str] = []
    for m in _REF_LOCAL.finditer(text):
        refs.append(f"{law_id}_dieu_{m.group(1)}")
    # dedup giữ thứ tự
    seen: set[str] = set()
    out: list[str] = []
    for r in refs:
        if r not in seen:
            seen.add(r)
            out.append(r)
    return out


def _mk_id(law_id: str, raw: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{law_id}::{raw}"))
