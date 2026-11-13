from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class ChatRequest(BaseModel):
    message: str = Field(..., description="User query or risk research prompt")
    conversation_history: Optional[List[ChatMessage]] = Field(default_factory=list)
    language: Literal["en", "hi", "gu", "mr"] = Field(default="en", description="Target vernacular language")
    include_market_context: bool = Field(default=True, description="Inject live index & option chain metrics")


class ChatResponse(BaseModel):
    reply: str
    disclaimer: str
    language: str
    is_refused: bool = False
    latency_ms: float
    model: str

