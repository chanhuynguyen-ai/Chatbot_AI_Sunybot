import os
from typing import Iterable, Optional

try:
    import psycopg
    from psycopg.rows import dict_row
except Exception as exc:  # pragma: no cover
    raise RuntimeError(
        "Thiếu psycopg. Hãy cài: pip install 'psycopg[binary]'"
    ) from exc


class DB:
    def __init__(self):
        self.host = os.getenv("PGHOST", os.getenv("DB_HOST", "localhost"))
        self.user = os.getenv("PGUSER", os.getenv("DB_USER", "elevator_ai"))
        self.password = os.getenv("PGPASSWORD", os.getenv("DB_PASSWORD", "elevator123"))
        self.database = os.getenv("PGDATABASE", os.getenv("DB_NAME", "elevator_ai_pg"))
        self.port = int(os.getenv("PGPORT", os.getenv("DB_PORT", "5432")))
        self.application_name = os.getenv("PGAPPNAME", "sunybot")
        self.sslmode = os.getenv("PGSSLMODE", "prefer")

    def dsn(self) -> str:
        return (
            f"host={self.host} port={self.port} dbname={self.database} "
            f"user={self.user} password={self.password} "
            f"application_name={self.application_name} sslmode={self.sslmode}"
        )

    def connect(self):
        return psycopg.connect(
            self.dsn(),
            autocommit=True,
            row_factory=dict_row,
        )

    def test_connection(self) -> bool:
        try:
            conn = self.connect()
            try:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1 AS ok")
                    row = cur.fetchone()
                    return bool(row and row.get("ok") == 1)
            finally:
                conn.close()
        except Exception:
            return False


def to_pgvector(values: Optional[Iterable[float]]) -> Optional[str]:
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


# Dùng chung toàn project
# Lưu ý: runtime chatbot bây giờ đọc từ PostgreSQL, không còn từ MySQL.
db = DB()
