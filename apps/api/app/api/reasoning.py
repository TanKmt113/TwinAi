from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import AgentRun, InspectionTask, PurchaseRequest
from app.schemas import AgentRunRead, InspectionTaskRead, PurchaseRequestRead, ReasoningRunResponse
from app.services.reasoning import ReasoningEngine

router = APIRouter(prefix="/api", tags=["reasoning"])


@router.post("/reasoning/run", response_model=ReasoningRunResponse)
def run_reasoning(db: Session = Depends(get_db)) -> ReasoningRunResponse:
    return ReasoningEngine(db).run()


@router.get("/agent-runs", response_model=list[AgentRunRead])
def list_agent_runs(db: Session = Depends(get_db)) -> list[AgentRun]:
    return list(db.scalars(select(AgentRun).order_by(AgentRun.started_at.desc())))


@router.get("/agent-runs/{run_id}", response_model=AgentRunRead)
def get_agent_run(run_id: str, db: Session = Depends(get_db)) -> AgentRun:
    run = db.get(AgentRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Agent run not found")
    return run


@router.get("/inspection-tasks", response_model=list[InspectionTaskRead])
def list_tasks(db: Session = Depends(get_db)) -> list[InspectionTask]:
    return list(db.scalars(select(InspectionTask).order_by(InspectionTask.created_at.desc())))


@router.get("/purchase-requests", response_model=list[PurchaseRequestRead])
def list_purchase_requests(db: Session = Depends(get_db)) -> list[PurchaseRequest]:
    return list(db.scalars(select(PurchaseRequest).order_by(PurchaseRequest.created_at.desc())))
