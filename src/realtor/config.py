from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

# Load .env if present
load_dotenv()


@dataclass(frozen=True)
class Settings:
    mongo_uri: str = os.getenv("MONGO_URI", "mongodb://localhost:27017/realtor")
    db_name: str = os.getenv("MONGO_DB", "realtor")
    collection_raw: str = os.getenv("MONGO_COLLECTION_RAW", "seller_description")
    collection_structured: str = os.getenv("MONGO_COLLECTION_STRUCTURED", "property_data")


settings = Settings()

