from __future__ import annotations

from typing import Any

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.config import get_settings

_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None
_connected = False


async def connect_db() -> None:
    global _client, _db, _connected
    settings = get_settings()
    _client = AsyncIOMotorClient(
        settings.mongodb_uri,
        serverSelectionTimeoutMS=3000,
        connectTimeoutMS=3000,
    )
    _db = _client[settings.mongodb_db]
    try:
        await _client.admin.command("ping")
        await _db.analyses.create_index("cache_key", unique=True)
        await _db.analyses.create_index("created_at", expireAfterSeconds=settings.cache_ttl_seconds)
        _connected = True
    except Exception:
        _connected = False
        if _client is not None:
            _client.close()
        _client = None
        _db = None
        raise


async def close_db() -> None:
    global _client, _db, _connected
    if _client is not None:
        _client.close()
    _client = None
    _db = None
    _connected = False


def is_db_connected() -> bool:
    return _connected and _db is not None


def get_db() -> AsyncIOMotorDatabase:
    if _db is None:
        raise RuntimeError("Database is not connected")
    return _db


async def get_cached_analysis(cache_key: str) -> dict[str, Any] | None:
    if not is_db_connected():
        return None
    doc = await get_db().analyses.find_one({"cache_key": cache_key})
    if not doc:
        return None
    result = doc.get("result")
    return result if isinstance(result, dict) else None


async def store_analysis(cache_key: str, result: dict[str, Any]) -> None:
    if not is_db_connected():
        raise RuntimeError("Database is not connected")
    from datetime import datetime, timezone

    await get_db().analyses.update_one(
        {"cache_key": cache_key},
        {
            "$set": {
                "cache_key": cache_key,
                "result": result,
                "created_at": datetime.now(timezone.utc),
            }
        },
        upsert=True,
    )
