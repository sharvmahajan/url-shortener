from pydantic import BaseModel
from typing import Optional

class ShortenRequest(BaseModel):
    url: str
    ttl_value: Optional[int] = None
    ttl_unit: Optional[str] = None


class TTLUpdateRequest(BaseModel):
    ttl_value: int
    ttl_unit: str