"""Pydantic schemas for the Legal-chatbots HTTP API."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class LawInfo(BaseModel):
    id: str
    label: str


class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1)
    law_id: Optional[str] = None
    thinking_mode: str = "auto"      # "auto" | "on" | "off"
    top_k: Optional[int] = None
    include_context: bool = False
    temperature: float = 0.2
    max_tokens: int = 8192


class RefinedInfo(BaseModel):
    original: str
    intent: Optional[str] = None
    objective: str = ""
    refined: str


class ChatResponse(BaseModel):
    answer: str
    refined: RefinedInfo
    intent: str
    thinking_used: bool
    vector_context: Optional[str] = None
    graph_context: Optional[str] = None
    graph_article_ids: Optional[list[str]] = None
    vector_results: Optional[list[dict]] = None


class GraphSubgraphRequest(BaseModel):
    article_ids: list[str] = Field(default_factory=list)
    limit: int = 160
