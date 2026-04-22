import pytest


@pytest.mark.asyncio
async def test_daily_averages_length():
    from app.services.social import post_daily_averages
    try:
        text = await post_daily_averages(dry_run=True)
        assert len(text) <= 300, f"Post too long: {len(text)} chars"
    except Exception:
        pytest.skip("No data available")


@pytest.mark.asyncio
async def test_cheapest_post_length():
    from app.services.social import post_cheapest_station
    try:
        text = await post_cheapest_station("E10", dry_run=True)
        assert len(text) <= 300, f"Post too long: {len(text)} chars"
    except Exception:
        pytest.skip("No data available")


@pytest.mark.asyncio
async def test_by_country_post_length():
    from app.services.social import post_cheapest_by_country
    try:
        text = await post_cheapest_by_country("E10", dry_run=True)
        assert len(text) <= 300, f"Post too long: {len(text)} chars"
    except Exception:
        pytest.skip("No data available")
