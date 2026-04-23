"""ALTER TABLE idempotent cho DB đã tồn tại — SQLAlchemy create_all không cập nhật cột mới."""

from __future__ import annotations

import logging

from sqlalchemy import text
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)


def apply_postgres_schema_patches(engine: Engine) -> None:
    if engine.dialect.name != "postgresql":
        return
    statements = [
        "ALTER TABLE purchase_requests ADD COLUMN IF NOT EXISTS first_approved_at TIMESTAMPTZ",
        "ALTER TABLE purchase_requests ADD COLUMN IF NOT EXISTS first_approved_by VARCHAR(120)",
        "ALTER TABLE org_users ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255)",
    ]
    with engine.begin() as conn:
        for sql in statements:
            conn.execute(text(sql))
    logger.info("schema_patches: đã áp dụng ALTER COLUMN (purchase_requests / org_users) nếu thiếu.")
