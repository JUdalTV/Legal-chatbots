"""Graph RAG — Legal Knowledge Graph (NER + LLM relation extraction → Neo4j).

Để tránh cascade import nặng (torch/transformers/underthesea), package này
KHÔNG re-export module ở đây. Hãy import trực tiếp module bạn cần:

    from graph_rag.neo4j_loader    import Neo4jKG
    from graph_rag.graph_retriever import GraphRetriever
    from graph_rag.ingestion       import ingest_docx       # nặng (torch)
    from graph_rag.ner_extractor   import get_ner_extractor # nặng (torch)
"""
