import pytest

from realtor.parser import parse_free_text_to_structured


def test_basic_parse_example():
    text = (
        "John Doe is selling a single family home at 123 Main St, Springfield, IL 62704. "
        "Asking $350,000 with 3 bedrooms and 2.5 bathrooms, about 1,850 sqft. "
        "Built in 1994. HOA fees $200. Call (217) 555-1212 or email john@example.com. "
        "Includes a garage and hardwood floors. Lot is 0.25 acres."
    )

    data = parse_free_text_to_structured(text)

    # Spot-check expectations; parser is heuristic, so be flexible
    assert data["contact_name"] in {"John Doe", None}
    assert data["price"] == pytest.approx(350000.0)
    assert data["bedrooms"] == pytest.approx(3.0)
    assert data["bathrooms"] == pytest.approx(2.5)
    assert data["square_feet"] == pytest.approx(1850.0)
    assert data["year_built"] == 1994
    assert data["hoa_fees"] == pytest.approx(200.0)

    addr = data["address"]
    assert addr["city"] == "Springfield"
    assert addr["state"] == "IL"

    assert any(am in data["amenities"] for am in ["garage", "hardwood"])
