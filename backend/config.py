import os
import base64
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

BASE_DIR = Path(__file__).parent

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.2")

PROMPT_PATH = BASE_DIR / "prompt.txt"
SYSTEM_INSTRUCTIONS = PROMPT_PATH.read_text(encoding="utf-8")

MAX_IMAGE_BYTES = 7 * 1024 * 1024 #7MB por imagen
ALLOWED_MIME = {"image/png", "image/jpeg", "image/jpg", "image/webp"}

client = OpenAI(api_key=OPENAI_API_KEY)

def to_data_url(content_type: str, data: bytes) -> str:
    b64 = base64.b64encode(data).decode("utf-8")
    return f"data:{content_type};base64,{b64}"

