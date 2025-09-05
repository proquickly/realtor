from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.errors import ServerSelectionTimeoutError

from .config import settings

_CLIENT: MongoClient | None = None


def _get_client() -> MongoClient:
    global _CLIENT
    if _CLIENT is not None:
        return _CLIENT

    _CLIENT = MongoClient(settings.mongo_uri, serverSelectionTimeoutMS=3000)
    # Touch server to fail fast if unavailable
    try:
        _CLIENT.admin.command("ping")
    except ServerSelectionTimeoutError as e:
        raise RuntimeError(
            f"Unable to connect to MongoDB at {settings.mongo_uri}. Is Docker running and the container up?"
        ) from e
    return _CLIENT


def _get_collection(name: str) -> Collection:
    client = _get_client()
    db = client[settings.db_name]
    return db[name]


def collections() -> Tuple[Collection, Collection]:
    raw = _get_collection(settings.collection_raw)
    structured = _get_collection(settings.collection_structured)
    return raw, structured


def save_raw_description(text: str) -> str:
    raw_col, _ = collections()
    doc = {
        "text": text,
        "created_at": datetime.now(timezone.utc),
    }
    res = raw_col.insert_one(doc)
    return str(res.inserted_id)


def save_property_data(data: Dict[str, Any]) -> str:
    _, structured_col = collections()
    # Ensure timestamp fields
    now = datetime.now(timezone.utc)
    data = {
        **data,
        "created_at": data.get("created_at", now),
        "updated_at": now,
    }
    res = structured_col.insert_one(data)
    return str(res.inserted_id)


def list_recent(limit: int = 10) -> List[Dict[str, Any]]:
    raw_col, structured_col = collections()
    cursor = structured_col.find({}, {"_id": 1, "description_raw_id": 1, "seller_name": 1, "address": 1, "created_at": 1}).sort("created_at", -1).limit(limit)
    return [
        {
            "id": str(doc.get("_id")),
            "description_raw_id": doc.get("description_raw_id"),
            "seller_name": doc.get("seller_name"),
            "address": doc.get("address"),
            "created_at": doc.get("created_at"),
        }
        for doc in cursor
    ]

