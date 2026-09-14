from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.ai import assistant
from app.ai.llm_client import is_configured
from app.database import get_db
from app.deps import get_current_user
from app.models import ChatMessage, ChatSession, User
from app.schemas import ChatRequest, ChatResponse

router = APIRouter(prefix="/ai", tags=["ai"])


@router.get("/status")
def ai_status():
    return {"ai_enabled": is_configured()}


@router.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    session = None
    if payload.session_id:
        session = db.query(ChatSession).filter(ChatSession.id == payload.session_id, ChatSession.user_id == current_user.id).first()
    if not session:
        session = ChatSession(user_id=current_user.id, title=payload.message[:50])
        db.add(session)
        db.flush()

    db.add(ChatMessage(session_id=session.id, role="user", content=payload.message))

    # The assistant only ever sees THIS user's id -> it can only build context
    # from this user's own data (spec section 17: never expose another user's data).
    reply_text, used_ai = assistant.answer(db, current_user.id, payload.message)

    db.add(ChatMessage(session_id=session.id, role="assistant", content=reply_text))
    db.commit()

    return ChatResponse(session_id=session.id, reply=reply_text, used_ai=used_ai)


@router.get("/chat/{session_id}/history")
def chat_history(session_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == current_user.id).first()
    if not session:
        return []
    return [{"role": m.role, "content": m.content, "created_at": m.created_at} for m in session.messages]
