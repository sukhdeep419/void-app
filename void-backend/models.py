from typing import List

from pydantic import BaseModel


class ImageAttachment(BaseModel):
    name: str
    mime_type: str
    data: str


class ChatMessage(BaseModel):
    role: str
    content: str
    images: List[ImageAttachment] = []


class CommandRequest(BaseModel):
    messages: List[ChatMessage]


class ConfirmActionRequest(BaseModel):
    token: str
