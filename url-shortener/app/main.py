from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from app.database import urls_collection, counter_collection
from app.base62 import encode
import time

app = FastAPI()


@app.post("/shorten")
async def shorten(long_url: str):

    doc = await counter_collection.find_one_and_update(
        {"_id": "counter"},
        {"$inc": {"value": 1}},
        upsert=True,
        return_document=True
    )

    counter_value = doc["value"]

    short_code = encode(counter_value)

    await urls_collection.insert_one({
        "_id": short_code,
        "long_url": long_url,
        "created_at": time.time()
    })

    return {"short_url": f"http://localhost:8000/{short_code}"}


@app.get("/{code}")
async def redirect(code: str):

    doc = await urls_collection.find_one({"_id": code})

    if not doc:
        raise HTTPException(status_code=404, detail="URL not found")

    return RedirectResponse(doc["long_url"])