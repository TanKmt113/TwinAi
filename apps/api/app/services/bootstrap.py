import logging

from app.core.config import get_settings
from app.core.database import Base, SessionLocal, engine
from app.models import domain  # noqa: F401
from app.services.neo4j_sync import Neo4jSyncService
from app.services.rag import RagService
from app.services.schema_patches import apply_postgres_schema_patches
from app.services.seed import backfill_null_org_user_passwords, seed_phase_two_data

logger = logging.getLogger(__name__)


def bootstrap_application() -> None:
    settings = get_settings()
    Base.metadata.create_all(bind=engine)
    apply_postgres_schema_patches(engine)

    with SessionLocal() as db:
        filled = backfill_null_org_user_passwords(db)
        if filled:
            db.commit()
            logger.info("bootstrap: đã gán mật khẩu demo (bcrypt) cho %s org user thiếu password_hash", filled)

    if settings.auto_seed:
        with SessionLocal() as db:
            seed_phase_two_data(db)
            for manual in RagService(db).list_manuals():
                try:
                    RagService(db).parse_manual(manual)
                except Exception as exc:
                    # Bucket/object MinIO trống sau `docker compose down -v` hoặc chưa upload PDF — không chặn khởi động API.
                    logger.warning(
                        "bootstrap: bỏ qua parse manual %s (%s)",
                        manual.code,
                        exc,
                    )
            Neo4jSyncService().sync_seed_graph(db)
