"""
Đánh giá chất lượng Graph trong Neo4j cho 3 luật, in bảng so sánh.
Chạy: python quality_check.py
"""
import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from docx import Document
from neo4j import GraphDatabase

CASES = [
    ('LuatAnNinhMang2025', 'law_dataset/Luật-116-2025-QH15.docx'),
    ('LuatVienThong2023',  'law_dataset/Luật-24-2023-QH15.docx'),
    ('LuatCNTT2025',       'law_dataset/Văn-bản-hợp-nhất-65-VBHN-VPQH.docx'),
]

art_re    = re.compile(r'^\s*Điều\s+(\d+[a-z]?)\.', re.I)
chap_re   = re.compile(r'^\s*Chương\s+([IVXLCDM]+)\b', re.I)
clause_re = re.compile(r'^\s*(\d+)\.\s')


def parse_docx(path):
    doc = Document(path)
    chapters, articles, clauses_by_art = [], [], {}
    cur = None
    for p in doc.paragraphs:
        t = p.text.strip()
        if not t: continue
        if chap_re.match(t): chapters.append(t); continue
        if (m := art_re.match(t)):
            cur = m.group(1); articles.append(cur); clauses_by_art.setdefault(cur,0); continue
        if cur and clause_re.match(t):
            clauses_by_art[cur] = clauses_by_art.get(cur,0)+1
    return len(chapters), articles, clauses_by_art


def neo_stats(s, lid):
    rows = list(s.run("""
        MATCH (l:LAW {id:$lid})-[:HAS_ARTICLE]->(a)
        OPTIONAL MATCH (a)-[:HAS_CLAUSE]->(k)
        OPTIONAL MATCH (a)-[:MENTIONS]->(e)
        RETURN a.so AS so, a.label AS label, a.content AS content,
               count(DISTINCT k) AS ncl, count(DISTINCT e) AS nent
    """, lid=lid))
    chap_n = s.run("MATCH (:LAW {id:$lid})-[:HAS_CHAPTER]->(c) RETURN count(c) AS n",
                   lid=lid).single()['n']
    edges_n = s.run("""
        MATCH ()-[r]->() WHERE r.article_id STARTS WITH $pre RETURN count(r) AS n
    """, pre=lid+'_dieu_').single()['n']
    refs = s.run("""
        MATCH (a:ARTICLE)-[r:REFERS_TO]->(b:ARTICLE) WHERE a.id STARTS WITH $pre
        RETURN count(r) AS n,
               sum(CASE WHEN b.id STARTS WITH $pre THEN 1 ELSE 0 END) AS internal,
               sum(CASE WHEN NOT b.id STARTS WITH $pre THEN 1 ELSE 0 END) AS external
    """, pre=lid+'_dieu_').single()
    return {'rows': rows, 'chapters': chap_n, 'edges': edges_n,
            'refs_total': refs['n'], 'refs_internal': refs['internal'],
            'refs_external': refs['external']}


def score(law_name, n, docx_chapters, docx_articles, docx_clauses):
    rows = n['rows']
    art_neo = {r['so'] for r in rows}
    art_docx = set(docx_articles)

    # 1. Cấu trúc /10
    chap_score = 10 if n['chapters'] == docx_chapters else 6
    # Lọc bỏ article duplicate trong docx parser (do appendix amend)
    real_art_docx = art_docx
    art_score = 10 * len(art_neo & real_art_docx) / max(len(real_art_docx), 1)

    # 2. Khoản /10
    neo_cl = {r['so']: r['ncl'] for r in rows}
    cl_match = sum(1 for so in art_neo if neo_cl.get(so,0) == docx_clauses.get(so,0))
    cl_score = 10 * cl_match / max(len(art_neo), 1)

    # 3. Entities /10
    ents = [r['nent'] for r in rows] or [0]
    avg_ent = sum(ents)/len(ents)
    zero_ent = sum(1 for e in ents if e==0)
    pct_nonzero = (len(ents)-zero_ent) / max(len(ents),1)
    # 0 → 0đ, 5 → 5đ, 10+ → 8đ, 15+ → 10đ; phạt theo %điều có entity
    if   avg_ent >= 14: ent_base = 10
    elif avg_ent >= 10: ent_base = 9
    elif avg_ent >= 7:  ent_base = 7.5
    elif avg_ent >= 5:  ent_base = 6
    else:               ent_base = max(3, avg_ent)
    ent_score = ent_base * (0.7 + 0.3*pct_nonzero)

    # 4. Edges /10 — edges/Điều
    edge_per_art = n['edges'] / max(len(art_neo), 1)
    if   edge_per_art >= 5:   eg_score = 9.5
    elif edge_per_art >= 3.5: eg_score = 9
    elif edge_per_art >= 2.5: eg_score = 7.5
    elif edge_per_art >= 1.5: eg_score = 6
    else:                     eg_score = max(3, edge_per_art*4)

    # 5. REFERS_TO /10
    refs_total = n['refs_total']
    cross = n['refs_external']
    if refs_total >= 25 and cross >= 10: rf_score = 10
    elif refs_total >= 15 and cross >= 5: rf_score = 8.5
    elif refs_total >= 10:                rf_score = 7
    elif refs_total >= 5:                 rf_score = 5
    else:                                  rf_score = 3

    # 6. Toàn vẹn nội dung /10 — title không bị truncate (kết thúc bằng dấu
    # phẩy/chấm phẩy = mid-clause, hoặc đúng cap 250 = bị cắt cứng)
    truncated_titles = sum(1 for r in rows
                           if r['label']
                           and (r['label'].rstrip().endswith((',',';'))
                                or len(r['label']) == 250)
                           and 'bãi bỏ' not in r['label'].lower())
    short_content = sum(1 for r in rows
                        if r['content'] is None or len(r['content']) < 50)
    cont_score = 10 - 1.0*truncated_titles - 1*short_content
    cont_score = max(0, cont_score)

    # Trọng số
    weights = {'cấu trúc': (0.25, (chap_score+art_score)/2),
               'khoản':    (0.20, cl_score),
               'entities': (0.20, ent_score),
               'edges':    (0.15, eg_score),
               'REFERS_TO':(0.10, rf_score),
               'nội dung': (0.10, cont_score)}
    total = sum(w*s for w,s in weights.values())
    return weights, total, {'avg_ent':avg_ent, 'edge_per_art':edge_per_art,
                            'truncated_titles':truncated_titles,
                            'art_count':len(art_neo)}


def main():
    drv = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j","12345678"))
    laws = []
    with drv.session() as s:
        for lid, path in CASES:
            dc, da, dcl = parse_docx(path)
            n = neo_stats(s, lid)
            w, tot, dbg = score(lid, n, dc, da, dcl)
            laws.append((lid, w, tot, dbg, dc, da, dcl, n))
    drv.close()

    # In bảng
    print("\n" + "="*88)
    print(f"{'Tiêu chí':<14} {'Trọng':<6} " + " ".join(f"{l[0]:<20}" for l in laws))
    print("="*88)
    crits = list(laws[0][1].keys())
    for c in crits:
        line = f"{c:<14} {laws[0][1][c][0]*100:>4.0f}%  "
        for l in laws:
            line += f"{l[1][c][1]:>5.2f}/10           "
        print(line)
    print("-"*88)
    line = f"{'TỔNG':<14} {'100%':<6} "
    for l in laws:
        line += f"{l[2]:>5.2f}/10           "
    print(line)
    print("="*88)

    print("\nChi tiết:")
    for lid, w, tot, dbg, dc, da, dcl, n in laws:
        print(f"\n{lid} ({tot:.2f}/10)")
        print(f"  docx: {dc} chương, {len(set(da))} điều unique, {sum(dcl.values())} khoản")
        print(f"  neo4j: {n['chapters']} chương, {dbg['art_count']} điều, "
              f"{sum(r['ncl'] for r in n['rows'])} khoản, "
              f"{n['edges']} edges ({dbg['edge_per_art']:.2f}/điều), "
              f"REFERS_TO {n['refs_total']} ({n['refs_internal']}+{n['refs_external']})")
        print(f"  avg entities/điều: {dbg['avg_ent']:.2f}")
        print(f"  truncated titles (mid-clause hoặc hit cap): {dbg['truncated_titles']}")

    avg = sum(l[2] for l in laws)/len(laws)
    print(f"\n{'='*88}\n>>> TRUNG BÌNH 3 LUẬT: {avg:.2f}/10 <<<\n{'='*88}\n")


if __name__ == "__main__":
    main()
