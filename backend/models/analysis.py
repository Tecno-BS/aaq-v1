from datetime import datetime, timezone
from typing import Optional, Dict, List
from beanie import Document
from pydantic import Field

class Analysis(Document):
    project_id : str
    answers : Dict[str, str]
    has_previous_study : Optional[str] = None
    slide_paths: List[str] = []
    context_image_paths: List[str] = []
    pdf_path: Optional[str] = None
    output_text: str = ""
    created_at : datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "analyses"