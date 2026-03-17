import os
from config.db_config import db, to_pgvector
from backend.embedding_service import EmbeddingService
from backend.text_utils import normalize_vi

EMBED_DIM = int(os.getenv("EMBED_DIM", "768"))
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")
BATCH_LIMIT = int(os.getenv("EMBED_BATCH_LIMIT", "0"))


def main():
    es = EmbeddingService()
    conn = db.connect()
    try:
        with conn.cursor() as cur:
            sql = "SELECT prompt_id, prompt_text FROM prompts ORDER BY prompt_id"
            if BATCH_LIMIT > 0:
                sql += " LIMIT %s"
                cur.execute(sql, (BATCH_LIMIT,))
            else:
                cur.execute(sql)
            rows = cur.fetchall()

        for row in rows:
            pid = row["prompt_id"]
            text = row["prompt_text"] or ""
            norm = normalize_vi(text)
            emb = es.embed(text, task="document")
            if not emb:
                print(f"[WARN] prompt_id={pid} không tạo được embedding")
                continue
            if len(emb) != EMBED_DIM:
                raise ValueError(
                    f"Embedding dimension không khớp: prompt_id={pid}, got={len(emb)}, expected={EMBED_DIM}. "
                    f"Hãy chỉnh EMBED_DIM hoặc schema_pg.sql cho đúng model {EMBED_MODEL}."
                )
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE prompts
                    SET prompt_norm = %s,
                        embedding_model = %s,
                        embedding = %s::vector,
                        updated_at = NOW()
                    WHERE prompt_id = %s
                    """,
                    (norm, EMBED_MODEL, to_pgvector(emb), pid),
                )
            print(f"[OK] Updated prompt_id={pid} dim={len(emb)}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
