from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

client = AsyncIOMotorClient(os.getenv("MONGO_URL"))

db = client.url_shortener

urls_collection = db.urls
counter_collection = db.counter