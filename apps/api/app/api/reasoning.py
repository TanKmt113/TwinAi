from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import AgentRun, InspectionTask
from app.schemas import AgentRunRead, InspectionTaskRead, ReasoningRunResponse
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


