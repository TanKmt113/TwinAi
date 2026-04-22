from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas import AssetRead
from app.services.neo4j_sync import Neo4jSyncService
from app.services.repositories import AssetRepository

router = APIRouter(prefix="/api/assets", tags=["assets"])


@router.get("", response_model=list[AssetRead])
def list_assets(db: Session = Depends(get_db)) -> list:
    return AssetRepository(db).list_assets()


@router.get("/{asset_id}", response_model=AssetRead)
def get_asset(asset_id: str, db: Session = Depends(get_db)):
    asset = AssetRepository(db).get_by_id(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset


@router.get("/{asset_id}/ontology")
def get_asset_ontology(asset_id: str, db: Session = Depends(get_db)) -> dict:
    repo = AssetRepository(db)
    asset = repo.get_by_id(asset_id) or repo.get_by_code(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    context = Neo4jSyncService().get_asset_context(asset.code)
    if not context:
        context = {
            "asset": {"code": asset.code, "name": asset.name},
            "components": [
                {
                    "code": component.code,
                    "name": component.name,
                    "component_type": component.component_type,
                    "remaining_lifetime_months": component.remaining_lifetime_months,
                    "spare_part_code": component.spare_part_code,
                }
                for component in asset.components
            ],
            "source": "postgresql_fallback",
        }
    return context

