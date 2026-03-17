import math
from typing import Dict, List, Optional

from config.db_config import db, to_pgvector
from backend.text_utils import normalize_vi


class SemanticMatcher:
    def __init__(self):
        self.items: List[Dict] = []
        self.item_count: int = 0

    def load_from_db(self):
        conn = db.connect()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) AS cnt FROM prompts")
                row = cur.fetchone() or {}
                self.item_count = int(row.get("cnt") or 0)
                self.items = [{"loaded": True}] if self.item_count > 0 else []
        finally:
            conn.close()

    def keyword_fallback(self, user_norm: str) -> Optional[Dict]:
        if not user_norm:
            return None
        conn = db.connect()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT i.intent_name,
                           p.prompt_id,
                           p.prompt_text,
                           p.prompt_norm,
                           a.answer_text,
                           1.0::float AS confidence,
                           'EXACT'::text AS retrieval_mode
                    FROM prompts p
                    JOIN intents i ON i.intent_id = p.intent_id
                    JOIN answers a ON a.intent_id = p.intent_id
                    WHERE p.prompt_norm = %s
                    ORDER BY a.answer_id ASC
                    LIMIT 1
                    """,
                    (user_norm,),
                )
                return cur.fetchone()
        finally:
            conn.close()

    def _fts_search(self, conn, user_norm: str, top_k: int) -> List[Dict]:
        if not user_norm:
            return []
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT i.intent_name,
                       p.prompt_id,
                       p.prompt_text,
                       p.prompt_norm,
                       a.answer_text,
                       LEAST(1.0, ts_rank_cd(p.tsv, plainto_tsquery('simple', %s))::float) AS confidence,
                       'FTS'::text AS retrieval_mode
                FROM prompts p
                JOIN intents i ON i.intent_id = p.intent_id
                JOIN answers a ON a.intent_id = p.intent_id
                WHERE p.tsv @@ plainto_tsquery('simple', %s)
                ORDER BY ts_rank_cd(p.tsv, plainto_tsquery('simple', %s)) DESC,
                         p.prompt_id ASC
                LIMIT %s
                """,
                (user_norm, user_norm, user_norm, top_k),
            )
            return cur.fetchall() or []

    def _vector_search(self, conn, user_embedding: Optional[List[float]], top_k: int) -> List[Dict]:
        if not user_embedding:
            return []
        vector_literal = to_pgvector(user_embedding)
        if not vector_literal:
            return []
        with conn.cursor() as cur:
            cur.execute("SET ivfflat.probes = %s", (max(1, min(10, top_k * 2)),))
            cur.execute(
                """
                SELECT i.intent_name,
                       p.prompt_id,
                       p.prompt_text,
                       p.prompt_norm,
                       a.answer_text,
                       GREATEST(0.0, 1 - (p.embedding <=> %s::vector))::float AS confidence,
                       'VECTOR'::text AS retrieval_mode
                FROM prompts p
                JOIN intents i ON i.intent_id = p.intent_id
                JOIN answers a ON a.intent_id = p.intent_id
                WHERE p.embedding IS NOT NULL
                ORDER BY p.embedding <=> %s::vector
                LIMIT %s
                """,
                (vector_literal, vector_literal, top_k),
            )
            return cur.fetchall() or []

    def search(self, user_text: str, user_embedding: Optional[List[float]] = None, top_k: int = 3) -> List[Dict]:
        user_norm = normalize_vi(user_text)
        if not user_norm and not user_embedding:
            return []

        exact_hit = self.keyword_fallback(user_norm)
        conn = db.connect()
        try:
            fts_hits = self._fts_search(conn, user_norm, top_k=top_k)
            vector_hits = self._vector_search(conn, user_embedding, top_k=top_k)
        finally:
            conn.close()

        merged: Dict[str, Dict] = {}

        def _merge(item: Dict, bonus: float = 0.0):
            if not item:
                return
            key = f"{item.get('intent_name')}::{item.get('answer_text')}"
            score = float(item.get("confidence") or 0.0) + bonus
            if key not in merged:
                merged[key] = {**item, "confidence": min(1.0, score)}
                return
            prev = merged[key]
            prev_score = float(prev.get("confidence") or 0.0)
            retrieval_modes = {prev.get("retrieval_mode", "")} | {item.get("retrieval_mode", "")}
            merged[key] = {
                **prev,
                **item,
                "confidence": min(1.0, max(prev_score, score) + (0.05 if len(retrieval_modes) > 1 else 0.0)),
                "retrieval_mode": "+".join(sorted([m for m in retrieval_modes if m])),
            }

        _merge(exact_hit, bonus=0.10)
        for row in fts_hits:
            _merge(row)
        for row in vector_hits:
            _merge(row)

        ordered = sorted(merged.values(), key=lambda x: (x.get("confidence", 0.0), x.get("prompt_id", 0)), reverse=True)
        return ordered[:top_k]

    def match(self, user_embedding: List[float], user_text: str, threshold: float = 0.78) -> Optional[Dict]:
        results = self.search(user_text=user_text, user_embedding=user_embedding, top_k=1)
        if results and float(results[0].get("confidence", 0.0)) >= threshold:
            return results[0]
        return None
