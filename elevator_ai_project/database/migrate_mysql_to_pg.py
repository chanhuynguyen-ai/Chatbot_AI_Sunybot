import json
import os
from typing import Any, Iterable, Optional

import pymysql
import psycopg
from psycopg.rows import dict_row

from database.remove_vietnamese_accent import remove_vietnamese_accent

MYSQL_CFG = {
    "host": os.getenv("MYSQL_HOST", os.getenv("DB_HOST", "localhost")),
    "user": os.getenv("MYSQL_USER", os.getenv("DB_USER", "elevator_ai")),
    "password": os.getenv("MYSQL_PASSWORD", os.getenv("DB_PASSWORD", "elevator123")),
    "database": os.getenv("MYSQL_DATABASE", os.getenv("DB_NAME", "elevator_ai")),
    "port": int(os.getenv("MYSQL_PORT", os.getenv("DB_PORT", "3306"))),
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor,
}

PG_DSN = (
    f"host={os.getenv('PGHOST', 'localhost')} "
    f"port={os.getenv('PGPORT', '5432')} "
    f"dbname={os.getenv('PGDATABASE', 'elevator_ai_pg')} "
    f"user={os.getenv('PGUSER', 'elevator_ai')} "
    f"password={os.getenv('PGPASSWORD', 'elevator123')}"
)


def to_pgvector(values: Optional[Iterable[Any]]) -> Optional[str]:
    if values is None:
        return None
    casted = []
    for item in values:
        try:
            casted.append(str(float(item)))
        except Exception:
            return None
    if not casted:
        return None
    return "[" + ",".join(casted) + "]"


def normalize_vi(text: Optional[str]) -> str:
    if not text:
        return ""
    return remove_vietnamese_accent(text).strip().lower()


def fetch_all(mysql_conn, sql: str):
    with mysql_conn.cursor() as cur:
        cur.execute(sql)
        return cur.fetchall() or []


def main():
    mysql_conn = pymysql.connect(**MYSQL_CFG)
    pg_conn = psycopg.connect(PG_DSN, autocommit=True, row_factory=dict_row)
    try:
        intents = fetch_all(mysql_conn, "SELECT * FROM intents ORDER BY intent_id")
        prompts = fetch_all(mysql_conn, "SELECT * FROM prompts ORDER BY prompt_id")
        answers = fetch_all(mysql_conn, "SELECT * FROM answers ORDER BY answer_id")
        employees = fetch_all(mysql_conn, "SELECT * FROM employees ORDER BY id")
        chat_logs = fetch_all(mysql_conn, "SELECT * FROM chat_logs ORDER BY log_id")

        with pg_conn.cursor() as cur:
            cur.execute("TRUNCATE TABLE chat_logs RESTART IDENTITY CASCADE")
            cur.execute("TRUNCATE TABLE answers RESTART IDENTITY CASCADE")
            cur.execute("TRUNCATE TABLE prompts RESTART IDENTITY CASCADE")
            cur.execute("TRUNCATE TABLE intents RESTART IDENTITY CASCADE")
            cur.execute("TRUNCATE TABLE employees RESTART IDENTITY CASCADE")

            for row in intents:
                cur.execute(
                    """
                    INSERT INTO intents(intent_id, intent_name, domain, description, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, NOW(), NOW())
                    """,
                    (row["intent_id"], row["intent_name"], row.get("domain"), row.get("description")),
                )

            for row in prompts:
                raw_emb = row.get("embedding")
                vec = None
                if raw_emb:
                    try:
                        vec = to_pgvector(json.loads(raw_emb))
                    except Exception:
                        vec = None
                prompt_text = row["prompt_text"]
                cur.execute(
                    """
                    INSERT INTO prompts(
                        prompt_id, intent_id, prompt_text, prompt_norm, embedding, embedding_model, meta, created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, %s::vector, %s, %s::jsonb, NOW(), NOW())
                    """,
                    (
                        row["prompt_id"],
                        row["intent_id"],
                        prompt_text,
                        normalize_vi(prompt_text),
                        vec,
                        row.get("embedding_model") or "nomic-embed-text",
                        json.dumps({"migrated_from": "mysql"}, ensure_ascii=False),
                    ),
                )

            for row in answers:
                cur.execute(
                    """
                    INSERT INTO answers(answer_id, intent_id, answer_text, created_at, updated_at)
                    VALUES (%s, %s, %s, NOW(), NOW())
                    """,
                    (row["answer_id"], row["intent_id"], row["answer_text"]),
                )

            for row in employees:
                cur.execute(
                    """
                    INSERT INTO employees(
                        id, employee_code, full_name, full_name_norm, birth_year, position,
                        department, hometown, phone, email, photo_path, created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                    """,
                    (
                        row["id"],
                        row["employee_code"],
                        row["full_name"],
                        normalize_vi(row["full_name"]),
                        row.get("birth_year"),
                        row.get("position"),
                        row.get("department"),
                        row.get("hometown"),
                        row.get("phone"),
                        row.get("email"),
                        row.get("photo_path"),
                    ),
                )

            for row in chat_logs:
                trace_json = row.get("tool_trace_json")
                if not trace_json:
                    trace_json = "[]"
                cur.execute(
                    """
                    INSERT INTO chat_logs(
                        log_id, session_id, question, intent_name, confidence, source,
                        answer_preview, tool_trace_json, tool_count, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s, COALESCE(%s, NOW()))
                    """,
                    (
                        row["log_id"],
                        row.get("session_id"),
                        row["question"],
                        row.get("intent_name"),
                        float(row.get("confidence") or 0),
                        row.get("source") or "UNKNOWN",
                        row.get("answer_preview"),
                        trace_json,
                        int(row.get("tool_count") or 0),
                        row.get("created_at"),
                    ),
                )

            cur.execute(
                "SELECT setval(pg_get_serial_sequence('intents', 'intent_id'), COALESCE(MAX(intent_id), 1), true) FROM intents"
            )
            cur.execute(
                "SELECT setval(pg_get_serial_sequence('prompts', 'prompt_id'), COALESCE(MAX(prompt_id), 1), true) FROM prompts"
            )
            cur.execute(
                "SELECT setval(pg_get_serial_sequence('answers', 'answer_id'), COALESCE(MAX(answer_id), 1), true) FROM answers"
            )
            cur.execute(
                "SELECT setval(pg_get_serial_sequence('employees', 'id'), COALESCE(MAX(id), 1), true) FROM employees"
            )
            cur.execute(
                "SELECT setval(pg_get_serial_sequence('chat_logs', 'log_id'), COALESCE(MAX(log_id), 1), true) FROM chat_logs"
            )

        print("[OK] Đã migrate MySQL -> PostgreSQL thành công")
    finally:
        mysql_conn.close()
        pg_conn.close()


if __name__ == "__main__":
    main()
