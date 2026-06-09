from pydantic import BaseModel
from typing import Optional

class Center(BaseModel):
    center_id: int
    region1: str = ""
    region2: str = ""
    center_name: str = ""
    address: str = ""
    homepage_url: str = ""
    operator_name: str = ""

class RecruitPost(BaseModel):
    region: str
    center_name: str
    operator_name: str = ""
    title: str
    url: str
    source: str = "homepage"
    status: str = "NEW"
    matched_keyword: Optional[str] = None
