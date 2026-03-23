from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse, Response
from app.database import urls_collection, counter_collection
from app.base62 import encode
from app.cache import redis_client
from app.qr import generate_qr_png
from app.schemas import ShortenRequest
from app.utils import hash_url
import time

app = FastAPI()



@app.post("/shorten")
async def shorten(req: ShortenRequest):

    long_url = req.url

    url_hash = hash_url(long_url)

    cached_code = redis_client.get(f"long:{url_hash}")

    if cached_code:
        return {
            "short_code": cached_code,
            "short_url": f"http://localhost:8000/{cached_code}",
            "qr_url": f"http://localhost:8000/qr/{cached_code}"
        }

    doc = await counter_collection.find_one_and_update(
        {"_id": "counter"},
        {"$inc": {"value": 1}},
        upsert=True,
        return_document=True
    )

    short_code = encode(doc["value"])

    await urls_collection.insert_one({
        "_id": short_code,
        "long_url": long_url,
        "created_at": time.time()
    })

    redis_client.setex(f"url:{short_code}", 3600, long_url)
    redis_client.setex(f"long:{url_hash}", 3600, short_code)

    return {
        "short_code": short_code,
        "short_url": f"http://localhost:8000/{short_code}",
        "qr_url": f"http://localhost:8000/qr/{short_code}"
    }

@app.get("/qr/{code}")
async def get_qr(code: str):

    cached = redis_client.get(f"url:{code}")

    if cached:
        long_url = cached
    else:
        doc = await urls_collection.find_one({"_id": code})

        if not doc:
            raise HTTPException(status_code=404, detail="URL not found")

        long_url = doc["long_url"]

        redis_client.setex(f"url:{code}", 3600, long_url)

    short_url = f"http://localhost:8000/{code}"

    png = generate_qr_png(short_url)

    return Response(content=png, media_type="image/png")

@app.get("/{code}")
async def redirect(code: str):

    cached = redis_client.get(f"url:{code}")

    if cached:
        print("Cache Hit :)")
        return RedirectResponse(cached)
    print("Cache Miss :(")
    doc = await urls_collection.find_one({"_id": code})

    if not doc:
        raise HTTPException(status_code=404, detail="URL not found")

    redis_client.setex(f"url:{code}", 3600, doc["long_url"])

    return RedirectResponse(doc["long_url"])