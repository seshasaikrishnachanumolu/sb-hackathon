# schemas.py
from pydantic import BaseModel
from typing import Optional, Dict, Any

class UploadResponse(BaseModel):
    ratios: Dict[str, Optional[float]]
    explanations: Dict[str, Any]

class ChatRequest(BaseModel):
    message: str
    context: Optional[str] = None
