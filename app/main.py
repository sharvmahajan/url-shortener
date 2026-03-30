from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse, Response
from app.database import urls_collection, counter_collection
from app.base62 import encode
from app.cache import redis_client
from app.qr import generate_qr_png
from app.schemas import ShortenRequest
from datetime import datetime, timezone
from app.utils import compute_expiry, ensure_utc, hash_url
from pymongo.errors import DuplicateKeyError
import json

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

    expire_at = compute_expiry(req.ttl_value, req.ttl_unit)

    url_doc = {
        "_id": short_code,
        "long_url": long_url,
        "created_at": datetime.now(timezone.utc)
    }

    if expire_at:
        url_doc["expire_at"] = expire_at

    try:
        await urls_collection.insert_one(url_doc)

    except DuplicateKeyError:
        # another request inserted the same long_url
        existing = await urls_collection.find_one({"long_url": long_url})
        short_code = existing["_id"]
        expire_at = existing.get("expire_at")

    # compute remaining TTL once
    if expire_at:
        expire_at = ensure_utc(expire_at)

        remaining = int((expire_at - datetime.now(timezone.utc)).total_seconds())

        if remaining <= 0:
            raise HTTPException(status_code=410, detail="URL expired")

        # cache warming
        ttl = min(3600, remaining)
    else:
        ttl = 3600

    payload = json.dumps({
        "long_url": long_url,
        "expire_at": expire_at.isoformat() if expire_at else None
    })

    redis_client.setex(f"url:{short_code}", ttl, payload)
    redis_client.setex(f"long:{url_hash}", ttl, short_code)

    return {
        "short_code": short_code,
        "short_url": f"http://localhost:8000/{short_code}",
        "qr_url": f"http://localhost:8000/qr/{short_code}"
    }

@app.get("/qr/{code}")
async def get_qr(code: str):

    cached = redis_client.get(f"url:{code}")

    if cached:
        data = json.loads(cached)

        expire_at = data.get("expire_at")

        if expire_at:
            expire_at = ensure_utc(datetime.fromisoformat(expire_at))

            if expire_at < datetime.now(timezone.utc):
                raise HTTPException(status_code=410, detail="URL expired")

        long_url = data["long_url"]

    else:
        doc = await urls_collection.find_one({"_id": code})

        if not doc:
            raise HTTPException(status_code=404, detail="URL not found")

        expire_at = ensure_utc(doc.get("expire_at"))

        if expire_at and expire_at < datetime.now(timezone.utc):
            raise HTTPException(status_code=410, detail="URL expired")

        long_url = doc["long_url"]

        # compute Redis TTL
        if expire_at:
            remaining = int((expire_at - datetime.now(timezone.utc)).total_seconds())

            if remaining <= 0:
                raise HTTPException(status_code=410, detail="URL expired")

            ttl = min(3600, remaining)
        else:
            ttl = 3600

        payload = json.dumps({
            "long_url": long_url,
            "expire_at": expire_at.isoformat() if expire_at else None
        })

        redis_client.setex(f"url:{code}", ttl, payload)

    short_url = f"http://localhost:8000/{code}"

    png = generate_qr_png(short_url)

    return Response(content=png, media_type="image/png")

@app.get("/{code}")
async def redirect(code: str):

    cached = redis_client.get(f"url:{code}")

    if cached:
        data = json.loads(cached)

        expire_at = data.get("expire_at")

        if expire_at:
            expire_at = ensure_utc(datetime.fromisoformat(expire_at))

            if expire_at < datetime.now(timezone.utc):
                raise HTTPException(status_code=410, detail="URL expired")

        print("Cache Hit :)")
        return RedirectResponse(data["long_url"])
    print("Cache Miss :(")

    doc = await urls_collection.find_one({"_id": code})

    if not doc:
        raise HTTPException(status_code=404, detail="URL not found")

    expire_at = ensure_utc(doc.get("expire_at"))

    if expire_at and expire_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=410, detail="URL expired")
    if expire_at:
        remaining = int((expire_at - datetime.now(timezone.utc)).total_seconds())

        if remaining <= 0:
            raise HTTPException(status_code=410, detail="URL expired")

        ttl = min(3600, remaining)
    else:
        ttl = 3600

    payload = json.dumps({
        "long_url": doc["long_url"],
        "expire_at": expire_at.isoformat() if expire_at else None
    })

    redis_client.setex(f"url:{code}", ttl, payload)

    return RedirectResponse(doc["long_url"])