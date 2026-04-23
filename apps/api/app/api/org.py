from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.models import OrgUnit, OrgUser
from app.schemas import OrgUnitRead, OrgUserRead

router = APIRouter(prefix="/api/org", tags=["organization"])


@router.get("/units", response_model=list[OrgUnitRead])
def list_org_units(db: Session = Depends(get_db)) -> list[OrgUnit]:
    return list(
        db.scalars(select(OrgUnit).order_by(OrgUnit.sort_order, OrgUnit.code)),
    )


@router.get("/users", response_model=list[OrgUserRead])
def list_org_users(db: Session = Depends(get_db)) -> list[OrgUserRead]:
    users = list(
        db.scalars(
            select(OrgUser)
            .options(joinedload(OrgUser.org_unit), joinedload(OrgUser.manager))
            .order_by(OrgUser.user_code),
        ),
    )
    return [_org_user_to_read(user) for user in users]


def _org_user_to_read(user: OrgUser) -> OrgUserRead:
    unit = user.org_unit
    mgr = user.manager
    return OrgUserRead(
        id=user.id,
        user_code=user.user_code,
        full_name=user.full_name,
        email=user.email,
        job_title=user.job_title,
        org_unit_id=user.org_unit_id,
        org_unit_code=unit.code if unit else None,
        org_unit_name=unit.name if unit else None,
        manager_user_id=user.manager_user_id,
        manager_user_code=mgr.user_code if mgr else None,
        role_tags=user.role_tags or [],
        is_active=user.is_active,
    )
