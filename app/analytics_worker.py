import asyncio
from datetime import datetime, timezone
from app.database import urls_collection
from app.cache import redis_client

STREAM_NAME = "analytics_stream"

async def worker():

    last_id = "0"

    while True:

        events = redis_client.xread(
            {STREAM_NAME: last_id},
            block=5000,
            count=10
        )

        if not events:
            continue

        for stream, messages in events:
            for message_id, data in messages:

                code = data.get(b"code") or data.get("code")

                if isinstance(code, bytes):
                    code = code.decode()

                await urls_collection.update_one(
                    {"_id": code},
                    {"$inc": {"clicks": 1}}
                )
                redis_client.xdel("analytics_stream", message_id)
                last_id = message_id
if __name__ == "__main__":
    asyncio.run(worker())