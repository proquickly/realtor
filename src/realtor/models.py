from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, List

from pydantic import BaseModel, Field


class Address(BaseModel):
    street: Optional[str] = None
    unit: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: str = "US"


class SellerDescriptionRaw(BaseModel):
    text: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PropertyData(BaseModel):
    # Link to raw free-form doc
    description_raw_id: str

    # Contact
    seller_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None

    # Address
    address: Address = Field(default_factory=Address)

    # Property attributes
    price: Optional[float] = None
    bedrooms: Optional[float] = None
    bathrooms: Optional[float] = None
    square_feet: Optional[float] = None
    lot_size: Optional[str] = None  # preserve units (e.g., "0.25 acre", "10890 sqft")
    year_built: Optional[int] = None
    property_type: Optional[str] = None

    amenities: List[str] = Field(default_factory=list)
    parking: Optional[str] = None
    hoa_fees: Optional[float] = None

    notes: Optional[str] = None

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

