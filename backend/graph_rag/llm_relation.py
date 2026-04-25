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
import re
from typing import Optional

import requests

from .ontology import RELATION_CATALOG, EDGE_MODALITY, LOGIC_ROLE_OF, EDGE_GOVERNANCE


DEFAULT_ENDPOINT = "http://localhost:8000/v1/chat/completions"
DEFAULT_MODEL    = "Qwen3.5-9B"
DEFAULT_TIMEOUT  = 120


# ── Prompt ────────────────────────────────────────────────────────────
_SYSTEM_PROMPT = """Bạn là chuyên gia trích xuất quan hệ pháp lý.
Đầu vào: 1 đoạn văn bản pháp luật + danh sách thực thể (đã được nhận diện sẵn).
Nhiệm vụ: tìm các QUAN HỆ giữa các thực thể, BÁM SÁT ontology dưới đây.

Quy tắc bắt buộc:
1. CHỈ tạo edge giữa 2 thực thể CÓ TRONG danh sách entities — không bịa thực thể mới.
2. `from_id` và `to_id` PHẢI khớp chính xác `id` trong danh sách entities.
3. `type` phải nằm trong RELATION_TYPES được liệt kê.
4. Nếu quan hệ mang sắc thái OBLIGATION/PROHIBITION/PERMISSION → ghi vào `modality`.
5. CONDITION/EXCEPTION/SCOPE/TIME → ghi text gốc vào field tương ứng (string ngắn).
6. `evidence` là TRÍCH NGUYÊN VĂN từ đoạn input (≤ 200 ký tự), KHÔNG paraphrase.
7. Trả về CHỈ JSON, không markdown, không giải thích.

OUTPUT FORMAT (JSON strict):
{"edges": [
  {"from_id":"...", "to_id":"...", "type":"REQUIRES_LICENSE",
   "modality":"OBLIGATION", "condition":null, "exception":null,
   "scope":null, "time":null, "evidence":"..."}
]}
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
                 max_tokens:  int = 2048):
        self.endpoint    = endpoint
        self.model       = model
        self.api_key     = api_key
        self.timeout     = timeout
        self.temperature = temperature
        self.max_tokens  = max_tokens

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
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            resp = requests.post(
                self.endpoint, headers=headers,
                json=payload, timeout=self.timeout,
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
        except (requests.RequestException, KeyError, IndexError) as ex:
            print(f"[llm_relation] LLM call failed: {ex}")
            return []

        try:
            data = _parse_json(content)
        except json.JSONDecodeError as ex:
            print(f"[llm_relation] JSON parse failed: {ex}\n--- raw ---\n{content[:500]}")
            return []

        edges = data.get("edges", []) if isinstance(data, dict) else []
        return _validate_edges(edges, valid_ids)
