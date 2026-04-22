from app.core.config import get_settings
from app.core.database import Base, SessionLocal, engine
from app.models import domain  # noqa: F401
from app.services.neo4j_sync import Neo4jSyncService
from app.services.seed import seed_phase_two_data


def bootstrap_application() -> None:
    settings = get_settings()
    Base.metadata.create_all(bind=engine)

    if settings.auto_seed:
        with SessionLocal() as db:
            seed_phase_two_data(db)
            Neo4jSyncService().sync_seed_graph(db)
