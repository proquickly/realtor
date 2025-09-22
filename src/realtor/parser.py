from __future__ import annotations

import re
from typing import Dict, Any, List, Optional

import phonenumbers
import spacy
import usaddress
from spacy.cli import download as spacy_download

# Heuristic keyword lists
AMENITY_KEYWORDS = [
    "pool", "garage", "fireplace", "hardwood", "garden", "deck", "patio",
    "balcony", "elevator", "gym", "fitness", "doorman", "basement", "fenced",
    "central air", "ac", "air conditioning", "walk-in closet", "granite", "stainless",
]
PROPERTY_TYPES = [
    "single family", "condo", "townhouse", "apartment", "duplex", "triplex", "land",
    "multi-family", "manufactured", "mobile", "co-op",
]

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
CURRENCY_RE = re.compile(r"\$\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{1,2})?|[0-9]+(?:\.[0-9]{1,2})?)")
BED_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(?:bed|beds|bedroom|bedrooms)\b", re.I)
BATH_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(?:bath|baths|bathroom|bathrooms)\b", re.I)
SQFT_RE = re.compile(r"(\d{3,6})\s*(?:sq\s?ft|sqft|square\s?feet)\b", re.I)
YEAR_BUILT_RE = re.compile(r"built\s*(?:in\s*)?(\d{4})", re.I)
HOA_RE = re.compile(r"HOA\s*(?:fees?)?\s*[:\-]?\s*\$\s*([0-9]{1,4}(?:\.[0-9]{1,2})?)", re.I)
ACRES_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(?:acre|acres)\b", re.I)
LOT_SQFT_RE = re.compile(r"(\d{3,7})\s*(?:sq\s?ft|sqft|square\s?feet)\b", re.I)


def ensure_spacy_model(model: str = "en_core_web_sm") -> spacy.Language:
    try:
        return spacy.load(model)
    except OSError:
        # download on first run
        spacy_download(model)
        return spacy.load(model)


def extract_email(text: str) -> Optional[str]:
    m = EMAIL_RE.search(text)
    return m.group(0) if m else None


def extract_phone(text: str, default_region: str = "US") -> Optional[str]:
    for m in phonenumbers.PhoneNumberMatcher(text, default_region):
        num = phonenumbers.format_number(m.number, phonenumbers.PhoneNumberFormat.E164)
        return num
    return None


def extract_price(text: str, doc: spacy.tokens.Doc) -> Optional[float]:
    # Prefer spaCy MONEY entities; fallback to regex
    for ent in doc.ents:
        if ent.label_ == "MONEY":
            # Strip $ and commas
            cleaned = re.sub(r"[^0-9.]+", "", ent.text)
            try:
                return float(cleaned)
            except ValueError:
                pass
    m = CURRENCY_RE.search(text)
    if m:
        try:
            return float(m.group(1).replace(",", ""))
        except ValueError:
            return None
    return None


def extract_bed_bath_sqft(text: str) -> Dict[str, Optional[float]]:
    beds = baths = sqft = None
    mb = BED_RE.search(text)
    if mb:
        try:
            beds = float(mb.group(1))
        except ValueError:
            pass
    mba = BATH_RE.search(text)
    if mba:
        try:
            baths = float(mba.group(1))
        except ValueError:
            pass
    ms = SQFT_RE.search(text)
    if ms:
        try:
            sqft = float(ms.group(1).replace(",", ""))
        except ValueError:
            pass
    return {"bedrooms": beds, "bathrooms": baths, "square_feet": sqft}


def extract_property_type(text: str) -> Optional[str]:
    lower = text.lower()
    for t in PROPERTY_TYPES:
        if t in lower:
            return t
    return None


def extract_year_built(text: str) -> Optional[int]:
    m = YEAR_BUILT_RE.search(text)
    if m:
        try:
            y = int(m.group(1))
            if 1800 <= y <= 2100:
                return y
        except ValueError:
            pass
    return None


def extract_lot_size(text: str) -> Optional[str]:
    m = ACRES_RE.search(text)
    if m:
        return f"{m.group(1)} acre"
    m = LOT_SQFT_RE.search(text)
    if m:
        return f"{m.group(1)} sqft"
    return None


def extract_hoa(text: str, doc: spacy.tokens.Doc) -> Optional[float]:
    m = HOA_RE.search(text)
    if m:
        try:
            return float(m.group(1))
        except ValueError:
            pass
    return None


def extract_amenities(text: str) -> List[str]:
    lower = text.lower()
    found = []
    for kw in AMENITY_KEYWORDS:
        if kw in lower:
            found.append(kw)
    # de-duplicate & sort for consistency
    return sorted(list(dict.fromkeys(found)))


def extract_address(text: str) -> Dict[str, Optional[str]]:
    # usaddress.tag returns (dict, label)
    try:
        tagged, _ = usaddress.tag(text)
    except usaddress.RepeatedLabelError:
        return {"street": None,"city": None, "state": None, "postal_code": None}

    street_parts = [
        tagged.get("AddressNumber"),
        tagged.get("StreetNamePreType"),
        tagged.get("StreetNamePreDirectional"),
        tagged.get("StreetName"),
        tagged.get("StreetNamePostType"),
        tagged.get("StreetNamePostDirectional"),
    ]
    street = " ".join([p for p in street_parts if p]) or None

    #unit_parts = [tagged.get("OccupancyType"), tagged.get("OccupancyIdentifier")]
    #unit = " ".join([p for p in unit_parts if p]) or None

    return {
        "street": street,
        "city": tagged.get("PlaceName"),
        "state": tagged.get("StateName"),
        "postal_code": tagged.get("ZipCode"),
    }


def extract_contact_name(doc: spacy.tokens.Doc) -> Optional[str]:
    # First PERSON entity is likely the contact name
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            return ent.text
    return None


def parse_free_text_to_structured(text: str) -> Dict[str, Any]:
    nlp = ensure_spacy_model()
    doc = nlp(text)

    data: Dict[str, Any] = {
        "contact_name": extract_contact_name(doc),
        "email": extract_email(text),
        "phone": extract_phone(text),
        "address": extract_address(text) | {"country": "US"},
        "price": extract_price(text, doc),
        **extract_bed_bath_sqft(text),
        "lot_size": extract_lot_size(text),
        "year_built": extract_year_built(text),
        "property_type": extract_property_type(text),
        "amenities": extract_amenities(text),
        "parking": ("garage" if "garage" in text.lower() else ("carport" if "carport" in text.lower() else None)),
        "hoa_fees": extract_hoa(text, doc),
    }

    # Notes can accumulate ambiguous or leftover hints (simple heuristic for now)
    notes: List[str] = []
    if not data.get("contact_name"):
        notes.append("Contact name not confidently detected.")
    if not any(data["address"].get(k) for k in ("street", "city", "state", "postal_code")):
        notes.append("Address not confidently detected.")
    if notes:
        data["notes"] = " ".join(notes)

    return data

