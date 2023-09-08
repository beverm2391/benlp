from typing import List, Optional
from pydantic import BaseModel

class FunctionCall(BaseModel):
    name: str
    args: dict

class Message(BaseModel):
    role: str
    content: Optional[str]
    name: Optional[str]
    function_call: Optional[FunctionCall]

class ChatRequest(BaseModel):
    messages: List[Message]
    max_tokens: Optional[int] = 2048
    temperature: Optional[float] = 0
    model: Optional[str] = "gpt-3.5-turbo-16k"