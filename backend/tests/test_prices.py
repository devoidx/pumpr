import pytest

pytestmark = pytest.mark.asyncio


async def test_health(client):
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


async def test_cheapest_requires_fuel(client):
    r = await client.get("/api/v1/prices/cheapest")
    assert r.status_code == 422


@pytest.mark.live
async def test_cheapest_returns_list(client):
    r = await client.get("/api/v1/prices/cheapest?fuel=E10&lat=52.3&lng=-0.07&radius_km=10&limit=5")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


@pytest.mark.live
async def test_cheapest_price_fields(client):
    r = await client.get("/api/v1/prices/cheapest?fuel=E10&lat=52.3&lng=-0.07&radius_km=10&limit=5")
    assert r.status_code == 200
    data = r.json()
    if not data:
        pytest.skip("No data available")
    station = data[0]
    assert "station_id" in station
    assert "price_pence" in station
    assert "price_flagged" in station
    assert "is_county_cheapest" in station
    assert "price_change_pence" in station
    assert station["price_pence"] >= 100


@pytest.mark.live
async def test_cheapest_brand_filter(client):
    r = await client.get("/api/v1/prices/cheapest?fuel=E10&lat=52.3&lng=-0.07&radius_km=20&limit=10&brand=TESCO")
    assert r.status_code == 200
    for station in r.json():
        assert station["brand"] == "TESCO"


@pytest.mark.live
async def test_stats_returns_fuel_types(client):
    r = await client.get("/api/v1/prices/stats")
    assert r.status_code == 200
    data = r.json()
    if not data:
        pytest.skip("No data available")
    fuel_types = [s["fuel_type"] for s in data]
    assert "E10" in fuel_types
    assert "B7" in fuel_types


@pytest.mark.live
async def test_flagged_prices_excluded_from_stats(client):
    r = await client.get("/api/v1/prices/stats")
    assert r.status_code == 200
    for stat in r.json():
        assert stat["min_price_pence"] >= 100
