from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas import ChatQuery, ChatResponse
from app.services.chat import ChatService

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/query", response_model=ChatResponse)
def query_chat(payload: ChatQuery, db: Session = Depends(get_db)) -> ChatResponse:
    return ChatService(db).answer(payload.question)

