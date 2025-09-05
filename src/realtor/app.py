from __future__ import annotations

import flet as ft

from .db import save_raw_description, save_property_data, list_recent
from .models import PropertyData
from .parser import parse_free_text_to_structured


def _spacer(height: int = 10) -> ft.Control:
    return ft.Container(height=height)


def main(page: ft.Page) -> None:
    page.title = "Realtor Property Intake"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.scroll = ft.ScrollMode.AUTO

    # State
    parsed_data: dict | None = None

    # Controls
    description_input = ft.TextField(
        label="Free-form property description",
        multiline=True,
        min_lines=8,
        max_lines=16,
        expand=True,
        autofocus=True,
        hint_text="Describe the property and include seller name, address, phone, price, beds/baths, etc.",
    )

    # Parsed fields (editable)
    seller_name = ft.TextField(label="Seller name", width=400)
    email = ft.TextField(label="Email", width=400)
    phone = ft.TextField(label="Phone (E.164)", width=400)

    street = ft.TextField(label="Street", width=500)
    unit = ft.TextField(label="Unit", width=200)
    city = ft.TextField(label="City", width=250)
    state = ft.TextField(label="State", width=120)
    postal_code = ft.TextField(label="Postal code", width=160)
    country = ft.TextField(label="Country", width=160, value="US")

    price = ft.TextField(label="Price ($)", width=220)
    bedrooms = ft.TextField(label="Bedrooms", width=160)
    bathrooms = ft.TextField(label="Bathrooms", width=160)
    square_feet = ft.TextField(label="Square feet", width=200)
    lot_size = ft.TextField(label="Lot size (preserve units)", width=250)
    year_built = ft.TextField(label="Year built", width=160)
    property_type = ft.TextField(label="Property type", width=240)

    amenities = ft.TextField(label="Amenities (comma-separated)", width=600)
    parking = ft.TextField(label="Parking", width=240)
    hoa_fees = ft.TextField(label="HOA fees ($/mo)", width=200)

    notes = ft.TextField(label="Notes", width=700, multiline=True, min_lines=2, max_lines=4)

    # History
    history_list = ft.ListView(expand=True, spacing=6, padding=0)

    def refresh_history() -> None:
        history_list.controls.clear()
        try:
            recent = list_recent(limit=10)
            for item in recent:
                addr = item.get("address") or {}
                addr_str = ", ".join(
                    [
                        x
                        for x in [addr.get("street"), addr.get("city"), addr.get("state"), addr.get("postal_code")]
                        if x
                    ]
                )
                history_list.controls.append(
                    ft.ListTile(
                        title=ft.Text(item.get("seller_name") or "(unknown seller)"),
                        subtitle=ft.Text(addr_str or "(no address)"),
                        trailing=ft.Text(str(item.get("created_at") or "")),
                    )
                )
        except Exception as e:
            history_list.controls.append(ft.Text(f"History unavailable: {e}", color=ft.Colors.RED))
        page.update()

    def populate_form(data: dict) -> None:
        seller_name.value = data.get("seller_name") or ""
        email.value = data.get("email") or ""
        phone.value = data.get("phone") or ""
        addr = data.get("address") or {}
        street.value = addr.get("street") or ""
        unit.value = addr.get("unit") or ""
        city.value = addr.get("city") or ""
        state.value = addr.get("state") or ""
        postal_code.value = addr.get("postal_code") or ""
        country.value = addr.get("country") or "US"
        price.value = str(data.get("price") or "")
        bedrooms.value = str(data.get("bedrooms") or "")
        bathrooms.value = str(data.get("bathrooms") or "")
        square_feet.value = str(data.get("square_feet") or "")
        lot_size.value = str(data.get("lot_size") or "")
        year_built.value = str(data.get("year_built") or "")
        property_type.value = data.get("property_type") or ""
        amenities.value = ", ".join(data.get("amenities") or [])
        parking.value = data.get("parking") or ""
        hoa_fees.value = str(data.get("hoa_fees") or "")
        notes.value = data.get("notes") or ""

    def handle_parse(e: ft.ControlEvent) -> None:
        text = (description_input.value or "").strip()
        if not text:
            page.snack_bar = ft.SnackBar(ft.Text("Please enter a description to parse."), open=True)
            page.update()
            return
        try:
            data = parse_free_text_to_structured(text)
            populate_form(data)
            page.snack_bar = ft.SnackBar(ft.Text("Parsed details. Please review and edit if needed."), open=True)
        except Exception as ex:
            page.snack_bar = ft.SnackBar(ft.Text(f"Parse failed: {ex}"), open=True)
        page.update()

    def handle_reset(e: ft.ControlEvent) -> None:
        description_input.value = ""
        populate_form({})
        page.update()

    def handle_save(e: ft.ControlEvent) -> None:
        text = (description_input.value or "").strip()
        if not text:
            page.snack_bar = ft.SnackBar(ft.Text("Please enter a description before saving."), open=True)
            page.update()
            return
        try:
            raw_id = save_raw_description(text)
            # Build structured dict from form
            structured = {
                "description_raw_id": raw_id,
                "seller_name": (seller_name.value or None),
                "email": (email.value or None),
                "phone": (phone.value or None),
                "address": {
                    "street": (street.value or None),
                    "unit": (unit.value or None),
                    "city": (city.value or None),
                    "state": (state.value or None),
                    "postal_code": (postal_code.value or None),
                    "country": (country.value or "US"),
                },
                "price": float(price.value.replace(",", "")) if price.value else None,
                "bedrooms": float(bedrooms.value) if bedrooms.value else None,
                "bathrooms": float(bathrooms.value) if bathrooms.value else None,
                "square_feet": float(square_feet.value.replace(",", "")) if square_feet.value else None,
                "lot_size": (lot_size.value or None),
                "year_built": int(year_built.value) if year_built.value else None,
                "property_type": (property_type.value or None),
                "amenities": [a.strip() for a in (amenities.value or "").split(",") if a.strip()],
                "parking": (parking.value or None),
                "hoa_fees": float(hoa_fees.value) if hoa_fees.value else None,
                "notes": (notes.value or None),
            }
            # Validate with Pydantic
            _ = PropertyData(**structured)
            save_property_data(structured)
            page.snack_bar = ft.SnackBar(ft.Text("Saved raw and structured documents."), open=True)
            refresh_history()
        except Exception as ex:
            page.snack_bar = ft.SnackBar(ft.Text(f"Save failed: {ex}"), open=True)
        page.update()

    parse_btn = ft.ElevatedButton("Parse details", icon=ft.Icons.PLAY_ARROW, on_click=handle_parse)
    reset_btn = ft.OutlinedButton("Reset", icon=ft.Icons.CLEAR, on_click=handle_reset)
    save_btn = ft.FilledButton("Save both", icon=ft.Icons.SAVE, on_click=handle_save)

    form_grid = ft.ResponsiveRow([
        ft.Column([seller_name, email, phone], col={"xs": 12, "sm": 6}),
        ft.Column([
            ft.Row([street, unit]),
            ft.Row([city, state, postal_code, country]),
        ], col={"xs": 12, "sm": 6}),
        ft.Column([
            ft.Row([price, bedrooms, bathrooms, square_feet]),
            ft.Row([lot_size, year_built, property_type]),
        ], col=12),
        ft.Column([amenities, parking, hoa_fees, notes], col=12),
    ], spacing=12)

    layout = ft.Tabs(
        selected_index=0,
        tabs=[
            ft.Tab(
                text="Input",
                content=ft.Container(
                    content=ft.Column([
                        description_input,
                        ft.Row([parse_btn, reset_btn, save_btn], alignment=ft.MainAxisAlignment.START),
                        _spacer(),
                        ft.Text("Parsed details (review & edit):", weight=ft.FontWeight.BOLD),
                        form_grid,
                    ], tight=False, spacing=12),
                    padding=20,
                    expand=True,
                ),
            ),
            ft.Tab(
                text="History",
                content=ft.Container(content=history_list, padding=20),
            ),
        ],
        expand=1,
    )

    page.add(layout)
    refresh_history()

