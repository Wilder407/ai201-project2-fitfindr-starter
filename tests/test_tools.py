# tests/test_tools.py
from tools import search_listings, suggest_outfit, create_fit_card

def test_search_returns_results():
    results = search_listings("Vintage Graphic Hoodie", size=None, max_price=50)
    assert isinstance(results, list)
    assert len(results) > 0

def test_search_empty_results():
    results = search_listings("designer ballgown", size="XXS", max_price=5)
    assert results == []   # empty list, no exception

def test_search_price_filter():
    results = search_listings("jacket", size=None, max_price=10)
    assert all(item["price"] <= 10 for item in results)

def test_search_size_filter():
    results = search_listings("jacket", size="M", max_price=None)
    assert all("m" in item["size"].lower() for item in results)

def test_suggest_outfit_returns_string():
    new_item = {
        "title": "Vintage Band Tee — Faded Grey",
        "category": "tops",
        "style_tags": ["vintage", "band", "graphic"],
        "colors": ["grey"],
        "brand": "Unknown",
        "condition": "good"
    }
    wardrobe = {
        "items": [
            {
                "id": "w_001",
                "name": "Baggy straight-leg jeans, dark wash",
                "category": "bottoms",
                "colors": ["dark blue", "indigo"],
                "style_tags": ["denim", "streetwear", "baggy"]
            }
        ]
    }
    result = suggest_outfit(new_item, wardrobe)
    assert isinstance(result, str)
    assert len(result) > 0

def test_suggest_outfit_empty_wardrobe():
    new_item = {
        "title": "Vintage Band Tee — Faded Grey",
        "category": "tops",
        "style_tags": ["vintage"],
        "colors": ["grey"],
        "brand": "Unknown",
        "condition": "good"
    }
    wardrobe = {"items": []}

def test_create_fit_card_returns_string():
    new_item = {
        "title": "Vintage Band Tee — Faded Grey",
        "price": 18.00,
        "platform": "depop"
    }
    outfit = "Pair with baggy jeans and chunky sneakers for a laid-back streetwear look."
    result = create_fit_card(outfit, new_item)
    assert isinstance(result, str)
    assert len(result) > 0

def test_create_fit_card_empty_outfit():
    new_item = {
        "title": "Vintage Band Tee — Faded Grey",
        "price": 18.00,
        "platform": "depop"
    }
    result = create_fit_card("", new_item)
    assert isinstance(result, str)
    assert "missing or empty" in result

def test_create_fit_card_variation():
    new_item = {
        "title": "Vintage Band Tee — Faded Grey",
        "price": 18.00,
        "platform": "depop"
    }
    outfit = "Pair with baggy jeans and chunky sneakers for a laid-back streetwear look."
    result1 = create_fit_card(outfit, new_item)
    result2 = create_fit_card(outfit, new_item)
    assert result1 != result2