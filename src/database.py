import asyncio

from motor.motor_asyncio import AsyncIOMotorClient

from settings import settings
from models import Poll

DB_NAME = settings.DB_NAME
MONGO_URL = f"mongodb://{settings.MONGO_HOST}:{settings.MONGO_PORT}" # {settings.MONGO_USER}:{settings.MONGO_PASSWORD}@
client = AsyncIOMotorClient(MONGO_URL)
client.get_io_loop = asyncio.get_running_loop

db = client[DB_NAME]


polls_db = db["polls"]


async def add_new_poll(where: str, poll: Poll):
    await polls_db.update_one(
        {"where": where},
        {"$addToSet": {"polls": poll.model_dump()}},
        upsert=True,
    )


async def reset_and_add_new_poll(where: str, poll: Poll):
    await polls_db.update_one(
        {"where": where},
        {"$set": {"polls": [poll.model_dump()]}},
        upsert=True,
    )


async def get_poll_by_location(where: str):
    return await polls_db.find_one({"where": where})


async def has_at_least_one_poll(where: str):
    poll = await get_poll_by_location(where)
    return poll is not None and poll.get("polls")
