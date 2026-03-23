from pydantic import BaseModel

class ShortenRequest(BaseModel):
    url: str