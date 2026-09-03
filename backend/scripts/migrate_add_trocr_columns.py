"""
Additive schema migration for the TrOCR/MCQ integration.

Adds the new nullable columns introduced alongside local handwriting OCR
support, without touching existing data:
  - questions.question_type   (default 'short_answer' for existing rows)
  - questions.options
  - model_answers.correct_option
  - evaluations.status_detail
  - evaluations.has_uncertain_segments (default false for existing rows)

Safe to run multiple times — every ALTER is guarded by an existence check.
Works against both SQLite (dev) and PostgreSQL (prod).

Usage:
    python -m scripts.migrate_add_trocr_columns
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from sqlalchemy import inspect, text  # noqa: E402

from database.session import engine  # noqa: E402


COLUMNS = [
    # (table, column, ddl_type_sqlite, ddl_type_postgres, default_sql)
    ("questions", "question_type", "VARCHAR(20)", "VARCHAR(20)", "'short_answer'"),
    ("questions", "options", "JSON", "JSON", "NULL"),
    ("model_answers", "correct_option", "VARCHAR(8)", "VARCHAR(8)", "NULL"),
    ("evaluations", "status_detail", "VARCHAR(120)", "VARCHAR(120)", "NULL"),
    ("evaluations", "has_uncertain_segments", "BOOLEAN", "BOOLEAN", "0"),
]


def run():
    dialect = engine.dialect.name  # "sqlite" or "postgresql"
    inspector = inspect(engine)

    with engine.begin() as conn:
        for table, column, sqlite_type, pg_type, default in COLUMNS:
            existing_cols = {c["name"] for c in inspector.get_columns(table)}
            if column in existing_cols:
                print(f"skip  {table}.{column} (already exists)")
                continue

            col_type = sqlite_type if dialect == "sqlite" else pg_type
            default_clause = f" DEFAULT {default}" if default != "NULL" else ""
            ddl = f"ALTER TABLE {table} ADD COLUMN {column} {col_type}{default_clause}"
            conn.execute(text(ddl))
            print(f"added {table}.{column}")

    print("Migration complete.")


if __name__ == "__main__":
    run()
