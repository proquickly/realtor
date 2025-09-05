# Realtor Property Intake App

A Flet web application to capture a seller's free-form property description and store it in MongoDB (Dockerized). The app also parses structured property data using NLP (spaCy), usaddress, and phonenumbers and stores it in a separate collection, linked to the raw description.

- Database: `realtor`
- Collections: `seller_description` (raw free-form) and `property_data` (structured)
- MongoDB runs in Docker with data persisted to `./data`

## Prerequisites

- Docker and Docker Compose
- Python 3.11+
- uv (https://docs.astral.sh/uv/)

## Setup

1) Start MongoDB (no auth) with Docker Compose:

```
docker compose up -d
```

MongoDB will listen on `localhost:27017` and persist data in `./data`.

2) Configure environment (optional; defaults are fine):

Copy `.env.example` to `.env` if you need to customize.

```
cp .env.example .env
```

3) Install dependencies with uv:

```
uv sync
```

Note: The first run will download the spaCy model `en_core_web_sm` automatically.

## Run the app

```
uv run realator
```

This launches the Flet web UI in your browser. Enter the free-form description, click "Parse details" to pre-fill the form, review/edit, then "Save both" to insert documents into MongoDB.

## Testing

```
uv run pytest -q
```

## Data model (structured document)

- seller_name, email, phone
- address: street, unit, city, state, postal_code, country
- price, bedrooms, bathrooms, square_feet, lot_size, year_built, property_type
- amenities (list), parking, hoa_fees, description_raw_id (link to raw), notes
- created_at, updated_at

## Notes

- The parser uses heuristics; review parsed values before saving.
- Timestamps are stored in UTC.
- The app always creates a new raw and structured record on save.
