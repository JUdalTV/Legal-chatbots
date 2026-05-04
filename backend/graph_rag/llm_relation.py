"""
llm_relation.py — Trích quan hệ giữa các thực thể bằng LLM (Qwen3.5-9B).

Input  : 1 chunk (text) + danh sách entity từ NER (đã filter còn NODE)
Output : list edge dict
   {
     "from_id":   "<id node nguồn>",
     "to_id":     "<id node đích>",
     "type":      "REQUIRES" | "REQUIRES_LICENSE" | ...,
     "modality":  "OBLIGATION" | "PROHIBITION" | "PERMISSION" | None,
     "condition": str | None,
     "exception": str | None,
     "scope":     str | None,
     "time":      str | None,
     "evidence":  "<đoạn text gốc minh chứng>",
   }

Endpoint: OpenAI-compatible chat/completions (vLLM / llama.cpp / LM Studio).
"""
from __future__ import annotations

import json
import os
import re
from typing import Optional

import requests

from .ontology import RELATION_CATALOG, EDGE_MODALITY, LOGIC_ROLE_OF, EDGE_GOVERNANCE


DEFAULT_ENDPOINT = "http://100.119.186.48:8000/v1/chat/completions"
DEFAULT_MODEL    = "Qwen/Qwen3.5-9B"
DEFAULT_TIMEOUT  = 120
DEFAULT_DISABLE_THINKING = os.getenv("LLM_DISABLE_THINKING", "1").lower() not in {"0", "false", "no"}


# ── Prompt ────────────────────────────────────────────────────────────
_SYSTEM_PROMPT = """Bạn là chuyên gia trích xuất quan hệ pháp lý từ văn bản luật Việt Nam.

=== ĐẦU VÀO ===
- `text`: đoạn văn bản pháp luật (1 điều/khoản)
- `entities`: danh sách thực thể đã nhận diện, mỗi thực thể có `id` và `type`

=== NHIỆM VỤ ===
Tìm các QUAN HỆ có căn cứ rõ ràng trong `text` giữa các thực thể trong `entities`.

=== RELATION TYPES (chỉ dùng các type sau) ===

Nhóm cấu trúc:
  HAS_PART · HAS_CHAPTER · HAS_ARTICLE · HAS_CLAUSE · HAS_POINT · PART_OF

Nhóm ngữ nghĩa pháp lý:
  DEFINES · GOVERNS · APPLIES_TO · REQUIRES · PROHIBITS
  GRANTS · ALLOWS · CREATES_RIGHT · IMPOSES_OBLIGATION

Nhóm vi phạm & chế tài:
  VIOLATES · LEADS_TO_SANCTION · ENFORCED_BY

Nhóm quản trị:
  REQUIRES_LICENSE · ISSUED_BY · REVOKED_BY · AUTHORIZES
  SUPERVISES · AUDITS · INSPECTS · COMPLIES_WITH · SUPERVISED_BY_AGENCY

Nhóm hành động:
  DETECTS · RESPONDS_TO · PREVENTS · MITIGATES · CAUSES
  TARGETS · PROCESSES · STORES · USES · MANAGES · OPERATES
  PROVIDES_SERVICE · DEVELOPS

Nhóm cross-law:
  REFERS_TO · AMENDS · SUPERSEDES

=== QUY TẮC BẮT BUỘC ===

R1. CHỈ tạo edge giữa 2 thực thể CÓ TRONG `entities` — không bịa entity mới.
R2. `from_id` và `to_id` phải khớp chính xác `id` trong `entities`.
R3. `type` phải là một trong các RELATION TYPES liệt kê ở trên.
R4. DIRECTION: `from` là CHỦ THỂ thực hiện hành động, `to` là ĐỐI TƯỢNG chịu tác động.
    VÍ DỤ ĐÚNG:  Bộ Công an —SUPERVISES→ hệ thống thông tin
    VÍ DỤ SAI:   Bộ Công an —SUPERVISED_BY→ hệ thống thông tin  ← ngược chiều
R5. `modality`: ghi "OBLIGATION" / "PERMISSION" / "PROHIBITION" nếu text dùng
    "có trách nhiệm", "phải", "được phép", "bị cấm", "không được" — null nếu không rõ.
R6. `condition`: trích nguyên văn mệnh đề "nếu...", "khi...", "trong trường hợp..." (≤ 120 ký tự).
R7. `exception`: trích nguyên văn mệnh đề "trừ...", "ngoại trừ...", "không áp dụng..." (≤ 120 ký tự).
R8. `scope`: trích nguyên văn phạm vi áp dụng nếu có (≤ 80 ký tự).
R9. `evidence`: trích nguyên văn câu/mệnh đề làm căn cứ — ưu tiên trích trọn câu, tối đa 300 ký tự.
R10. Nếu không tìm được quan hệ nào có căn cứ rõ ràng → trả về `{"edges": []}`.
R11. Không tạo edge trùng lặp (cùng from_id, to_id, type).
R12. Mỗi edge phải có `evidence` — không được để null.

=== VÍ DỤ (few-shot) ===

Input:
{
  "text": "Bộ Công an có trách nhiệm thẩm định an ninh mạng, giám sát an ninh mạng đối với hệ thống thông tin quan trọng về an ninh quốc gia, trừ hệ thống thông tin quân sự.",
  "entities": [
    {"id": "actor_bo_cong_an", "type": "LEGAL_ACTOR", "label": "Bộ Công an"},
    {"id": "sys_httt_quoc_gia", "type": "SYSTEM", "label": "hệ thống thông tin quan trọng về an ninh quốc gia"},
    {"id": "sys_httt_quan_su", "type": "SYSTEM", "label": "hệ thống thông tin quân sự"}
  ]
}

Output:
{"edges": [
  {
    "from_id": "actor_bo_cong_an",
    "to_id": "sys_httt_quoc_gia",
    "type": "SUPERVISES",
    "modality": "OBLIGATION",
    "condition": null,
    "exception": "trừ hệ thống thông tin quân sự",
    "scope": "hệ thống thông tin quan trọng về an ninh quốc gia",
    "time": null,
    "evidence": "Bộ Công an có trách nhiệm thẩm định an ninh mạng, giám sát an ninh mạng đối với hệ thống thông tin quan trọng về an ninh quốc gia"
  },
  {
    "from_id": "actor_bo_cong_an",
    "to_id": "sys_httt_quoc_gia",
    "type": "AUDITS",
    "modality": "OBLIGATION",
    "condition": null,
    "exception": "trừ hệ thống thông tin quân sự",
    "scope": "hệ thống thông tin quan trọng về an ninh quốc gia",
    "time": null,
    "evidence": "Bộ Công an có trách nhiệm thẩm định an ninh mạng, giám sát an ninh mạng đối với hệ thống thông tin quan trọng về an ninh quốc gia"
  }
]}

=== OUTPUT FORMAT ===
Trả về CHỈ JSON hợp lệ, không markdown, không giải thích, không prefix.
Schema bắt buộc cho mỗi edge:
{
  "from_id":   string,         // id trong entities
  "to_id":     string,         // id trong entities
  "type":      string,         // từ RELATION TYPES
  "modality":  string | null,  // OBLIGATION | PERMISSION | PROHIBITION | null
  "condition": string | null,
  "exception": string | null,
  "scope":     string | null,
  "time":      string | null,
  "evidence":  string          // bắt buộc, trích nguyên văn
}
"""

def _build_user_prompt(chunk_text: str, entities: list[dict]) -> str:
    rel_block = "\n".join(
        f"- {group}: {', '.join(rels)}"
        for group, rels in RELATION_CATALOG.items()
    )
    ent_block = "\n".join(
        f'- {{"id":"{e["id"]}", "type":"{e["type"]}", "label":"{e["label"]}"}}'
        for e in entities
    )
    return f"""RELATION_TYPES (chỉ dùng các type này):
{rel_block}

EDGE_ATTR cho phép:
- modality:   {sorted(EDGE_MODALITY)}
- logic keys: {sorted(LOGIC_ROLE_OF.values())}
- governance type: {sorted(EDGE_GOVERNANCE)}

ENTITIES (danh sách hợp lệ — chỉ dùng các id này):
{ent_block}

TEXT:
\"\"\"{chunk_text}\"\"\"
"""


# ── JSON extraction ───────────────────────────────────────────────────
_JSON_BLOCK = re.compile(r"\{[\s\S]*\}")


def _parse_json(content: str) -> dict:
    """Best-effort parse — bóc JSON object đầu tiên trong chuỗi."""
    content = content.strip()
    # bỏ ```json fence nếu có
    if content.startswith("```"):
        content = re.sub(r"^```(?:json)?", "", content).rstrip("`").strip()
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        m = _JSON_BLOCK.search(content)
        if not m:
            raise
        return json.loads(m.group(0))


def _extract_message_content(data: dict) -> Optional[str]:
    """Handle small response-shape differences across OpenAI-compatible servers."""
    choices = data.get("choices")
    if not choices:
        return None
    choice = choices[0]
    message = choice.get("message") if isinstance(choice, dict) else None
    if isinstance(message, dict):
        content = message.get("content")
        if isinstance(content, str) and content.strip():
            return content
        reasoning = message.get("reasoning_content")
        if isinstance(reasoning, str) and reasoning.strip():
            return reasoning
    text = choice.get("text") if isinstance(choice, dict) else None
    if isinstance(text, str) and text.strip():
        return text
    return None


# ── Validation ────────────────────────────────────────────────────────
_VALID_RELATIONS = {r for rs in RELATION_CATALOG.values() for r in rs}
_VALID_MODALITY  = EDGE_MODALITY
_LOGIC_KEYS      = set(LOGIC_ROLE_OF.values())


def _validate_edges(raw_edges: list[dict],
                    valid_ids: set[str]) -> list[dict]:
    out = []
    for e in raw_edges:
        if not isinstance(e, dict):
            continue
        fid, tid = e.get("from_id"), e.get("to_id")
        rtype    = e.get("type")
        if not (fid and tid and rtype):
            continue
        if fid not in valid_ids or tid not in valid_ids:
            continue
        if fid == tid:
            continue
        if rtype not in _VALID_RELATIONS:
            continue
        edge = {
            "from_id":  fid,
            "to_id":    tid,
            "type":     rtype,
            "modality": e.get("modality") if e.get("modality") in _VALID_MODALITY else None,
            "evidence": (e.get("evidence") or "")[:200],
        }
        for k in _LOGIC_KEYS:
            v = e.get(k)
            edge[k] = (str(v)[:200] if v else None)
        out.append(edge)
    return out


# ── Main class ────────────────────────────────────────────────────────
class LlmRelationExtractor:
    def __init__(self,
                 endpoint: str = DEFAULT_ENDPOINT,
                 model:    str = DEFAULT_MODEL,
                 api_key:  Optional[str] = None,
                 timeout:  int = DEFAULT_TIMEOUT,
                 temperature: float = 0.0,
                 max_tokens:  int = 4096,
                 disable_thinking: bool = DEFAULT_DISABLE_THINKING):
        self.endpoint    = endpoint
        self.model       = model
        self.api_key     = api_key
        self.timeout     = timeout
        self.temperature = temperature
        self.max_tokens  = max_tokens
        self.disable_thinking = disable_thinking

    # ----------------------------------------------------------------
    def extract(self, chunk_text: str, entities: list[dict]) -> list[dict]:
        """
        entities: list dict CÓ field 'id', 'type', 'label' (đã filter là NODE).
        Trả list edge đã validate.
        """
        if len(entities) < 2:
            return []

        valid_ids = {e["id"] for e in entities}

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user",   "content": _build_user_prompt(chunk_text, entities)},
            ],
            "temperature": self.temperature,
            "max_tokens":  self.max_tokens,
            "response_format": {"type": "json_object"},  # vLLM/Qwen hỗ trợ
        }
        if self.disable_thinking:
            # Qwen thinking models may return only message.reasoning and leave
            # message.content as null unless thinking is disabled.
            payload["chat_template_kwargs"] = {"enable_thinking": False}

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            resp = requests.post(
                self.endpoint, headers=headers,
                json=payload, timeout=self.timeout,
            )
            resp.raise_for_status()
            data = resp.json()
            content = _extract_message_content(data)
            if content is None:
                print(
                    "[llm_relation] LLM response has no text content. "
                    f"Raw response: {json.dumps(data, ensure_ascii=False)[:500]}"
                )
                return []
        except requests.HTTPError as ex:
            body = (ex.response.text or "")[:500] if ex.response is not None else ""
            print(f"[llm_relation] LLM call failed: {ex}. Response body: {body}")
            return []
        except (requests.RequestException, KeyError, IndexError, ValueError) as ex:
            print(f"[llm_relation] LLM call failed: {ex}")
            return []

        try:
            data = _parse_json(content)
        except (json.JSONDecodeError, TypeError) as ex:
            print(f"[llm_relation] JSON parse failed: {ex}\n--- raw ---\n{content[:500]}")
            return []

        edges = data.get("edges", []) if isinstance(data, dict) else []
        return _validate_edges(edges, valid_ids)
