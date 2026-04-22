import pytest
from app.services.ingestion import _normalise_brand


def test_brand_normalisation():
    assert _normalise_brand("texaco") == "TEXACO"
    assert _normalise_brand("Texaco") == "TEXACO"
    assert _normalise_brand("TEXACO") == "TEXACO"
    assert _normalise_brand("asda express") == "ASDA"
    assert _normalise_brand("gulf") == "GULF"
    assert _normalise_brand("Gulf") == "GULF"
    assert _normalise_brand(None) is None


def test_price_hard_floor():
    from app.services.ingestion import FUEL_HARD_LIMITS
    for fuel, (low, high) in FUEL_HARD_LIMITS.items():
        assert low >= 100, f"{fuel} hard floor too low"


