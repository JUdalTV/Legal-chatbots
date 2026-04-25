"""
Legal Knowledge Graph Ontology v1.0 (theo legal_ontology.docx)

5 lớp:
  L1 Structural   — cấu trúc văn bản          → 100% NODE
  L2 Normative    — chủ thể / hành vi / quyền → SPLIT (node + edge.modality)
  L3 Logic        — điều kiện / ngoại lệ      → 0% NODE (chỉ edge attr)
  L4 Governance   — license / compliance      → SPLIT (node + edge type)
  L5 System/Data  — hệ thống / dữ liệu        → 100% NODE
  + Domain extensions: Cyber / Telecom / IT   → 100% NODE
"""
from __future__ import annotations

# ── L1 Structural ─────────────────────────────────────────────────────
STRUCTURAL_NODES = {
    "LAW", "PART", "CHAPTER", "SECTION",
    "ARTICLE", "CLAUSE", "POINT", "APPENDIX",
}

# ── L2 Normative — SPLIT ──────────────────────────────────────────────
# Tạo node:
NORMATIVE_NODES = {
    "LEGAL_ACTOR", "LEGAL_OBJECT", "LEGAL_ACTION",
    "RIGHT", "VIOLATION", "SANCTION", "LEGAL_CONCEPT",
}
# Không tạo node — gắn vào edge.modality:
EDGE_MODALITY = {"OBLIGATION", "PROHIBITION", "PERMISSION"}

# ── L3 Logic — KHÔNG NODE ─────────────────────────────────────────────
# Toàn bộ là edge property. Map: NER label → key trên edge.
LOGIC_ROLE_OF = {
    "CONDITION":      "condition",
    "EXCEPTION":      "exception",
    "SCOPE":          "scope",
    "TIME":           "time",
    "STATUS":         "status",
    "CLASSIFICATION": "classification",
    "LEVEL":          "level",
}
EDGE_LOGIC = set(LOGIC_ROLE_OF.keys())

# ── L4 Governance — SPLIT ─────────────────────────────────────────────
GOVERNANCE_NODES = {"LICENSE", "CERTIFICATE"}
# Không tạo node — dùng làm edge type/role:
EDGE_GOVERNANCE = {
    "AUTHORIZATION", "COMPLIANCE", "AUDIT",
    "INSPECTION", "ENFORCEMENT",
}

# ── L5 System/Data ────────────────────────────────────────────────────
SYSTEM_NODES = {
    "SYSTEM", "DATA", "DATA_TYPE", "DATABASE",
    "PLATFORM", "NETWORK", "INFRASTRUCTURE",
}

# ── Domain extensions ─────────────────────────────────────────────────
CYBER_NODES = {
    "CYBER_ACTOR", "THREAT", "ATTACK", "VULNERABILITY",
    "SECURITY_MEASURE", "SECURITY_POLICY", "INCIDENT", "RISK", "IMPACT",
}
TELECOM_NODES = {
    "TELECOM_OPERATOR", "SERVICE", "SUBSCRIBER", "NETWORK_RESOURCE",
    "BANDWIDTH", "INTERCONNECTION", "TARIFF",
}
IT_NODES = {
    "IT_ACTOR", "SOFTWARE", "APPLICATION", "DIGITAL_PLATFORM",
    "IT_SERVICE", "STANDARD", "TECHNICAL_REGULATION",
    "DEVELOPMENT", "DEPLOYMENT", "OPERATION",
}

ALL_NODE_TYPES = (
    STRUCTURAL_NODES | NORMATIVE_NODES | GOVERNANCE_NODES | SYSTEM_NODES
    | CYBER_NODES | TELECOM_NODES | IT_NODES
)
ALL_EDGE_ATTR_TYPES = EDGE_MODALITY | EDGE_LOGIC | EDGE_GOVERNANCE

# ── Layer lookup ──────────────────────────────────────────────────────
LAYER_OF: dict[str, str] = {}
for _set, _layer in [
    (STRUCTURAL_NODES, "structural"),
    (NORMATIVE_NODES,  "normative"),
    (GOVERNANCE_NODES, "governance"),
    (SYSTEM_NODES,     "system"),
    (CYBER_NODES,      "cyber"),
    (TELECOM_NODES,    "telecom"),
    (IT_NODES,         "it"),
]:
    for _t in _set:
        LAYER_OF[_t] = _layer


# ── Catalog quan hệ (cho LLM prompt) ──────────────────────────────────
RELATION_CATALOG: dict[str, list[str]] = {
    "structural":   ["HAS_PART", "HAS_CHAPTER", "HAS_ARTICLE", "HAS_CLAUSE",
                     "HAS_POINT", "PART_OF"],
    "semantic":     ["DEFINES", "GOVERNS", "APPLIES_TO", "REQUIRES",
                     "PROHIBITS", "GRANTS", "ALLOWS",
                     "CREATES_RIGHT", "IMPOSES_OBLIGATION"],
    "violation":    ["VIOLATES", "PENALIZED_BY", "LEADS_TO_SANCTION",
                     "ENFORCED_BY"],
    "governance":   ["REQUIRES_LICENSE", "ISSUED_BY", "REVOKED_BY",
                     "AUTHORIZES", "SUPERVISED_BY", "COMPLIES_WITH",
                     "AUDITED_BY", "INSPECTED_BY"],
    "data":         ["USES", "PROCESSES", "STORES", "SHARES", "COLLECTS",
                     "DEPLOYS", "OPERATES", "MANAGES"],
    "cyber":        ["ATTACKS", "TARGETS", "EXPLOITS", "DETECTS",
                     "PREVENTS", "MITIGATES", "RESPONDS_TO",
                     "CAUSES", "RESULTS_IN"],
    "telecom":      ["PROVIDES_SERVICE", "USES_RESOURCE", "ALLOCATED_BY",
                     "INTERCONNECTS", "CHARGES_FEE", "SERVES"],
    "it":           ["DEVELOPS", "DEPLOYS", "OPERATES",
                     "COMPLIES_WITH_STANDARD", "INTEGRATES_WITH"],
    "cross_law":    ["REFERS_TO", "AMENDS", "SUPERSEDES", "CONFLICTS_WITH"],
}
ALL_RELATION_TYPES = {r for rs in RELATION_CATALOG.values() for r in rs}


# ── Helpers ───────────────────────────────────────────────────────────
def is_node(etype: str) -> bool:
    return etype in ALL_NODE_TYPES


def is_edge_attr(etype: str) -> bool:
    return etype in ALL_EDGE_ATTR_TYPES


def get_layer(etype: str) -> str:
    return LAYER_OF.get(etype, "unknown")


def edge_attr_role(etype: str) -> tuple[str, str] | None:
    """
    Cho NER label, trả (role, key) để gắn lên edge:
      modality.<key>  → ('modality', 'OBLIGATION'|'PROHIBITION'|'PERMISSION')
      logic.<key>     → ('logic',    'condition'|'exception'|...)
      governance.<key>→ ('governance','AUTHORIZATION'|...)
    """
    if etype in EDGE_MODALITY:
        return ("modality", etype)
    if etype in LOGIC_ROLE_OF:
        return ("logic", LOGIC_ROLE_OF[etype])
    if etype in EDGE_GOVERNANCE:
        return ("governance", etype)
    return None


# ── Cypher schema ─────────────────────────────────────────────────────
# Mỗi node đều có .id (UUID), .label (text hiển thị). Constraints theo label.
CONSTRAINTS: list[str] = [
    f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{lbl}) REQUIRE n.id IS UNIQUE"
    for lbl in sorted(ALL_NODE_TYPES)
]

FULLTEXT_INDEXES: list[str] = [
    """CREATE FULLTEXT INDEX article_fts IF NOT EXISTS
       FOR (a:ARTICLE) ON EACH [a.label, a.content]""",
    """CREATE FULLTEXT INDEX clause_fts IF NOT EXISTS
       FOR (k:CLAUSE)  ON EACH [k.content]""",
    """CREATE FULLTEXT INDEX entity_fts IF NOT EXISTS
       FOR (n:LEGAL_ACTOR|LEGAL_CONCEPT|LEGAL_ACTION|VIOLATION|SANCTION
              |LICENSE|CERTIFICATE
              |SYSTEM|DATA|DATA_TYPE|DATABASE|PLATFORM|NETWORK|INFRASTRUCTURE)
       ON EACH [n.label]""",
]
