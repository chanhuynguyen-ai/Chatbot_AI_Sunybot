# backend/build_embeddings.py
import json
from config.db_config import db
from backend.embedding_service import EmbeddingService
from backend.text_utils import normalize_vi

def main():
    es = EmbeddingService()
    conn = db.connect()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT prompt_id, prompt_text FROM prompts")
            rows = cur.fetchall()

        for r in rows:
            pid = r["prompt_id"]
            text = r["prompt_text"] or ""
            norm = normalize_vi(text)
            emb = es.embed(text)
            emb_json = json.dumps(emb, ensure_ascii=False)

            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE prompts
                    SET embedding=%s, normalized_text=%s, embedding_model=%s
                    WHERE prompt_id=%s
                """, (emb_json, norm, "nomic-embed-text", pid))

            print(f"Updated prompt_id={pid} len(emb)={len(emb)}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()

