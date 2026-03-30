from pydantic import BaseModel, Field, model_validator
from typing import Any, Optional
from datetime import datetime

class ChatSessionBase(BaseModel):
    session_name: Optional[str] = "New Chat"

class ChatSessionCreate(ChatSessionBase):
    user_id: int

    @model_validator(mode="before")
    @classmethod
    def title_alias(cls, data: Any) -> Any:
        if isinstance(data, dict) and data.get("title") and not data.get("session_name"):
            return {**data, "session_name": data["title"]}
        return data

class ChatSessionResponse(ChatSessionBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class ChatMessageCreate(BaseModel):
    session_id: int = Field(..., gt=0, description="Real chat_sessions.id from POST /chat/sessions (not 0)")
    content: Optional[str] = None
    role: str = "user"

    @model_validator(mode="before")
    @classmethod
    def map_legacy(cls, data: Any) -> Any:
        if isinstance(data, dict) and data.get("message") and not data.get("content"):
            data = {**data, "content": data["message"]}
        if isinstance(data, dict) and data.get("sender") and not data.get("role"):
            data = {**data, "role": "user" if data["sender"] == "user" else "assistant"}
        return data

class ChatMessageRow(BaseModel):
    id: int
    session_id: int
    role: str
    content: str
    timestamp: datetime

    class Config:
        from_attributes = True

class ChatMessageOut(BaseModel):
    id: int
    sender: str
    message: str

    @classmethod
    def from_row(cls, row: Any) -> "ChatMessageOut":
        r = getattr(row, "role", None) or ""
        sender = "user" if r == "user" else "ai"
        body = getattr(row, "content", None)
        if body is None:
            body = getattr(row, "message_body", None)
        return cls(id=row.id, sender=sender, message=body if body is not None else "")

class ChatTurnResponse(BaseModel):
    user_message: ChatMessageOut
    assistant_message: ChatMessageOut
