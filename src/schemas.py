from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class NodeCreate(BaseModel):
    name: str
    host: str
    port: int = Field(..., ge=1, le=65535)

class NodeUpdate(BaseModel):
    host: Optional[str] = None
    port: Optional[int] = Field(None, ge=1, le=65535)

class NodeResponse(BaseModel):
    id: int
    name: str
    host: str
    port: int
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Pydantic v2

class NodeList(BaseModel):
    __root__: list[NodeResponse]
