"""
PostgreSQL-only: add missing columns / relax legacy NOT NULL so the DB matches SQLAlchemy models.

If DATABASE_URL is not PostgreSQL, migrations are skipped (set DATABASE_URL to postgres://...).
"""
from __future__ import annotations

import logging
from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)


def _has_col(engine: Engine, table: str, col: str) -> bool:
    insp = inspect(engine)
    if table not in insp.get_table_names():
        return True
    return col in {c["name"] for c in insp.get_columns(table)}


def _exec(engine: Engine, sql: str) -> None:
    with engine.begin() as conn:
        conn.execute(text(sql))


def _safe_add(engine: Engine, table: str, col: str, sql: str) -> None:
    if _has_col(engine, table, col):
        return
    try:
        _exec(engine, sql)
        logger.info("Added column %s.%s", table, col)
    except Exception as e:
        logger.warning("Could not add %s.%s: %s", table, col, e)
        raise


def _pg_exec_ignore(engine: Engine, sql: str) -> None:
    try:
        _exec(engine, sql)
    except Exception as e:
        logger.debug("ensure_schema (ignored): %s", e)


def ensure_schema(engine: Engine) -> None:
    if engine.dialect.name != "postgresql":
        logger.warning(
            "ensure_schema skipped: PostgreSQL only (current dialect=%s). "
            "Set DATABASE_URL to a postgres:// connection.",
            engine.dialect.name,
        )
        return

    # users
    _safe_add(
        engine,
        "users",
        "full_name",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS full_name VARCHAR NOT NULL DEFAULT 'User'",
    )
    _safe_add(
        engine,
        "users",
        "hashed_password",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS hashed_password VARCHAR",
    )

    _safe_add(
        engine,
        "users",
        "is_guest",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_guest BOOLEAN DEFAULT FALSE",
    )
    _safe_add(engine, "users", "ai_model", "ALTER TABLE users ADD COLUMN IF NOT EXISTS ai_model VARCHAR")
    _safe_add(engine, "users", "ai_language", "ALTER TABLE users ADD COLUMN IF NOT EXISTS ai_language VARCHAR")
    _safe_add(engine, "users", "ai_voice", "ALTER TABLE users ADD COLUMN IF NOT EXISTS ai_voice VARCHAR")
    _safe_add(
        engine,
        "users",
        "ai_name",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS ai_name VARCHAR DEFAULT 'Nova'",
    )
    _safe_add(
        engine,
        "users",
        "created_at",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW()",
    )

    # chat_sessions
    _safe_add(
        engine,
        "chat_sessions",
        "session_name",
        "ALTER TABLE chat_sessions ADD COLUMN IF NOT EXISTS session_name VARCHAR DEFAULT 'New Chat'",
    )
    _safe_add(
        engine,
        "chat_sessions",
        "created_at",
        "ALTER TABLE chat_sessions ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW()",
    )
    _safe_add(
        engine,
        "chat_sessions",
        "title",
        "ALTER TABLE chat_sessions ADD COLUMN IF NOT EXISTS title VARCHAR",
    )

    # interview_sessions
    _safe_add(engine, "interview_sessions", "role", "ALTER TABLE interview_sessions ADD COLUMN IF NOT EXISTS role VARCHAR")
    _safe_add(
        engine,
        "interview_sessions",
        "interview_type",
        "ALTER TABLE interview_sessions ADD COLUMN IF NOT EXISTS interview_type VARCHAR",
    )
    _safe_add(
        engine,
        "interview_sessions",
        "difficulty",
        "ALTER TABLE interview_sessions ADD COLUMN IF NOT EXISTS difficulty VARCHAR",
    )
    _safe_add(
        engine,
        "interview_sessions",
        "session_date",
        "ALTER TABLE interview_sessions ADD COLUMN IF NOT EXISTS session_date TIMESTAMP DEFAULT NOW()",
    )
    _safe_add(
        engine,
        "interview_sessions",
        "overall_feedback",
        "ALTER TABLE interview_sessions ADD COLUMN IF NOT EXISTS overall_feedback TEXT",
    )
    _safe_add(
        engine,
        "interview_sessions",
        "score",
        "ALTER TABLE interview_sessions ADD COLUMN IF NOT EXISTS score INTEGER",
    )

    # interview_questions
    _safe_add(engine, "interview_questions", "category", "ALTER TABLE interview_questions ADD COLUMN IF NOT EXISTS category VARCHAR")
    _safe_add(engine, "interview_questions", "difficulty", "ALTER TABLE interview_questions ADD COLUMN IF NOT EXISTS difficulty VARCHAR")
    _safe_add(engine, "interview_questions", "expected_answer", "ALTER TABLE interview_questions ADD COLUMN IF NOT EXISTS expected_answer TEXT")
    _safe_add(engine, "interview_questions", "user_answer", "ALTER TABLE interview_questions ADD COLUMN IF NOT EXISTS user_answer TEXT")
    _safe_add(engine, "interview_questions", "feedback", "ALTER TABLE interview_questions ADD COLUMN IF NOT EXISTS feedback TEXT")
    _safe_add(engine, "interview_questions", "score", "ALTER TABLE interview_questions ADD COLUMN IF NOT EXISTS score INTEGER")
    _safe_add(engine, "interview_questions", "question_order", "ALTER TABLE interview_questions ADD COLUMN IF NOT EXISTS question_order INTEGER NOT NULL DEFAULT 1")
    _safe_add(
        engine,
        "interview_questions",
        "expected_answer_points",
        "ALTER TABLE interview_questions ADD COLUMN IF NOT EXISTS expected_answer_points JSONB",
    )
    # Ensure interview_answers table exists
    _pg_exec_ignore(engine, """
        CREATE TABLE IF NOT EXISTS interview_answers (
            id SERIAL PRIMARY KEY,
            question_id INTEGER NOT NULL REFERENCES interview_questions(id),
            answer_text TEXT NOT NULL
        )
    """)
    _safe_add(engine, "interview_answers", "is_correct", "ALTER TABLE interview_answers ADD COLUMN IF NOT EXISTS is_correct BOOLEAN DEFAULT FALSE")

    _ensure_chat_messages(engine)

    _ensure_chat_sessions_title(engine)
    _ensure_resumes_columns(engine)
    _ensure_job_applications_columns(engine)
    _ensure_interview_sessions_job_application(engine)
    _ensure_interview_sessions_dates(engine)

def _ensure_interview_sessions_dates(engine: Engine) -> None:
    """Ensure session_date is populated from created_at if it exists."""
    insp = inspect(engine)
    if "interview_sessions" not in insp.get_table_names():
        return
    cols = {c["name"] for c in insp.get_columns("interview_sessions")}
    if "created_at" in cols and "session_date" in cols:
        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    UPDATE interview_sessions
                    SET session_date = created_at
                    WHERE session_date IS NULL AND created_at IS NOT NULL
                    """
                )
            )



def _ensure_chat_sessions_title(engine: Engine) -> None:
    insp = inspect(engine)
    if "chat_sessions" not in insp.get_table_names():
        return
    cols = {c["name"] for c in insp.get_columns("chat_sessions")}
    with engine.begin() as conn:
        if "title" in cols and "session_name" in cols:
            conn.execute(
                text(
                    """
                    UPDATE chat_sessions
                    SET title = COALESCE(session_name, 'New Chat')
                    WHERE title IS NULL OR TRIM(COALESCE(title, '')) = ''
                    """
                )
            )
        elif "title" in cols:
            conn.execute(
                text(
                    "UPDATE chat_sessions SET title = 'New Chat' WHERE title IS NULL OR TRIM(COALESCE(title, '')) = ''"
                )
            )
    _pg_exec_ignore(engine, "ALTER TABLE chat_sessions ALTER COLUMN title DROP NOT NULL")


def _ensure_resumes_columns(engine: Engine) -> None:
    _safe_add(
        engine,
        "resumes",
        "title",
        "ALTER TABLE resumes ADD COLUMN IF NOT EXISTS title VARCHAR NOT NULL DEFAULT 'My Resume'",
    )
    _safe_add(
        engine,
        "resumes",
        "updated_at",
        "ALTER TABLE resumes ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW()",
    )
    _safe_add(
        engine,
        "resumes",
        "content",
        "ALTER TABLE resumes ADD COLUMN IF NOT EXISTS content TEXT NOT NULL DEFAULT ''",
    )
    _safe_add(
        engine,
        "resumes",
        "created_at",
        "ALTER TABLE resumes ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW()",
    )


def _ensure_job_applications_columns(engine: Engine) -> None:
    insp = inspect(engine)
    if "job_applications" not in insp.get_table_names():
        return
    cols = {c["name"] for c in insp.get_columns("job_applications")}
    _safe_add(engine, "job_applications", "company_name", "ALTER TABLE job_applications ADD COLUMN IF NOT EXISTS company_name VARCHAR")
    _safe_add(engine, "job_applications", "job_title", "ALTER TABLE job_applications ADD COLUMN IF NOT EXISTS job_title VARCHAR")
    _safe_add(
        engine,
        "job_applications",
        "application_date",
        "ALTER TABLE job_applications ADD COLUMN IF NOT EXISTS application_date TIMESTAMP DEFAULT NOW()",
    )
    _safe_add(
        engine,
        "job_applications",
        "status",
        "ALTER TABLE job_applications ADD COLUMN IF NOT EXISTS status VARCHAR DEFAULT 'Applied'",
    )
    _safe_add(engine, "job_applications", "notes", "ALTER TABLE job_applications ADD COLUMN IF NOT EXISTS notes TEXT")
    _safe_add(
        engine,
        "job_applications",
        "linkedin_job_url",
        "ALTER TABLE job_applications ADD COLUMN IF NOT EXISTS linkedin_job_url VARCHAR",
    )
    with engine.begin() as conn:
        if "company" in cols and "company_name" in cols:
            conn.execute(
                text(
                    """
                    UPDATE job_applications
                    SET company_name = CAST(company AS TEXT)
                    WHERE company_name IS NULL AND company IS NOT NULL
                    """
                )
            )
        if "role" in cols and "job_title" in cols:
            conn.execute(
                text(
                    """
                    UPDATE job_applications
                    SET job_title = CAST(role AS TEXT)
                    WHERE job_title IS NULL AND role IS NOT NULL
                    """
                )
            )
        if "position" in cols and "job_title" in cols:
            conn.execute(
                text(
                    """
                    UPDATE job_applications
                    SET job_title = CAST("position" AS TEXT)
                    WHERE job_title IS NULL AND "position" IS NOT NULL
                    """
                )
            )
        conn.execute(
            text(
                """
                UPDATE job_applications
                SET company_name = COALESCE(company_name, 'Unknown')
                WHERE company_name IS NULL OR TRIM(COALESCE(company_name, '')) = ''
                """
            )
        )
        conn.execute(
            text(
                """
                UPDATE job_applications
                SET job_title = COALESCE(job_title, 'Role')
                WHERE job_title IS NULL OR TRIM(COALESCE(job_title, '')) = ''
                """
            )
        )


def _ensure_interview_sessions_job_application(engine: Engine) -> None:
    _safe_add(
        engine,
        "interview_sessions",
        "job_application_id",
        "ALTER TABLE interview_sessions ADD COLUMN IF NOT EXISTS job_application_id INTEGER",
    )


def _ensure_chat_messages(engine: Engine) -> None:
    """Align chat_messages with ChatMessage model; backfill legacy sender/message columns."""
    insp = inspect(engine)
    if "chat_messages" not in insp.get_table_names():
        return
    cols = {c["name"] for c in insp.get_columns("chat_messages")}

    with engine.begin() as conn:
        if "role" not in cols:
            conn.execute(
                text(
                    "ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS role VARCHAR NOT NULL DEFAULT 'user'"
                )
            )
            logger.info("Added column chat_messages.role")

        if "sender" in cols:
            conn.execute(
                text(
                    """
                    UPDATE chat_messages
                    SET role = CASE
                        WHEN lower(CAST(sender AS TEXT)) IN ('assistant', 'ai', 'system') THEN 'assistant'
                        ELSE 'user'
                    END
                    """
                )
            )

        if "content" not in cols:
            conn.execute(
                text(
                    "ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS content TEXT NOT NULL DEFAULT ''"
                )
            )
            logger.info("Added column chat_messages.content")

        if "message" in cols:
            conn.execute(
                text(
                    """
                    UPDATE chat_messages
                    SET content = message
                    WHERE message IS NOT NULL
                      AND (content IS NULL OR TRIM(COALESCE(content, '')) = '')
                    """
                )
            )

        if "timestamp" not in cols:
            conn.execute(
                text(
                    "ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS timestamp TIMESTAMP DEFAULT NOW()"
                )
            )
            logger.info("Added column chat_messages.timestamp")

        conn.execute(
            text(
                "UPDATE chat_messages SET content = '.' WHERE content IS NULL OR TRIM(content) = ''"
            )
        )

        if "sender" in cols and "role" in cols:
            conn.execute(
                text(
                    """
                    UPDATE chat_messages
                    SET sender = role
                    WHERE sender IS NULL AND role IS NOT NULL
                    """
                )
            )
        if "message" in cols and "content" in cols:
            conn.execute(
                text(
                    """
                    UPDATE chat_messages
                    SET message = content
                    WHERE message IS NULL AND content IS NOT NULL
                    """
                )
            )

    _pg_exec_ignore(engine, "ALTER TABLE chat_messages ALTER COLUMN sender DROP NOT NULL")
    _pg_exec_ignore(engine, "ALTER TABLE chat_messages ALTER COLUMN message DROP NOT NULL")
