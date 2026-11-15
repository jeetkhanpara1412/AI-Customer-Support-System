import re
from datetime import datetime
from typing import Literal

from pydantic import (
    AliasChoices,
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
)


class RegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)

    @field_validator("password")
    @classmethod
    def password_policy(cls, value: str) -> str:
        if (
            not re.search(r"[a-z]", value)
            or not re.search(r"[A-Z]", value)
            or not re.search(r"\d", value)
        ):
            raise ValueError(
                "Password must include uppercase, lowercase, and numeric characters"
            )
        return value

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Name cannot be blank")
        return value


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: EmailStr
    name: str = Field(validation_alias=AliasChoices("name", "full_name"))
    role: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
    conversation_id: int | None = None

    @field_validator("message")
    @classmethod
    def clean_message(cls, value: str) -> str:
        value = "".join(
            char for char in value if char in "\n\t" or ord(char) >= 32
        ).strip()
        if not value:
            raise ValueError("Message cannot be blank")
        return value


class ChatResponse(BaseModel):
    conversation_id: int
    message_id: int
    reply: str
    category: str
    confidence: float
    similarity: float
    mode: Literal[
        "matched",
        "default",
        "fallback",
        "clarify",
        "greeting",
        "thanks",
        "out_of_scope",
    ]
    escalated: bool
    ticket_id: int | None = None
    options: list[str] = Field(default_factory=list)


class MessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    role: Literal["user", "assistant", "agent"]
    text: str
    category: str | None
    confidence: float | None
    escalated: bool = False
    created_at: datetime


class ConversationRead(BaseModel):
    id: int
    title: str
    updated_at: datetime
    messages: list[MessageRead]


class ConversationSummary(BaseModel):
    id: int
    title: str
    updated_at: datetime


class TicketRead(BaseModel):
    id: int
    subject: str
    conversation_id: int
    category: str
    priority: Literal["low", "medium", "high"]
    status: Literal["open", "in_progress", "resolved"]
    replies: list["TicketReplyRead"] = Field(default_factory=list)
    created_at: datetime


class TicketReplyRead(BaseModel):
    id: int
    text: str
    created_at: datetime


class TicketStatusUpdate(BaseModel):
    status: Literal["open", "in_progress", "resolved"]


class TicketReply(BaseModel):
    text: str = Field(min_length=1, max_length=1000)

    @field_validator("text")
    @classmethod
    def clean_reply(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Reply cannot be blank")
        return value


class KnowledgeEntryCreate(BaseModel):
    message: str = Field(min_length=3, max_length=1000)
    category: str = Field(min_length=1, max_length=64)
    response: str = Field(min_length=3, max_length=2000)


TicketRead.model_rebuild()
