import os 
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from models.project import Project
from models.analysis import Analysis

async def init_db():
    client = AsyncIOMotorClient(os.getenv("MONGODB_URI"))
    await init_beanie(
        database=client.get_default_database(),
        document_models=[Project, Analysis],
    )