import pytest
from httpx import AsyncClient, ASGITransport
from fastapi import status
from unittest.mock import AsyncMock

from app import models
from app.main import app


@pytest.mark.asyncio
async def test_health_check(test_settings):
    base_url = test_settings.base_url
    async with AsyncClient(base_url=base_url, transport=ASGITransport(app=app)) as client:
        response = await client.get("/health")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"status": "db healthy"}

# @pytest.mark.asyncio
# async def test_health_check_db_failure(override_settings, override_db):
#     pass

@pytest.mark.asyncio
async def test_create_short_url(test_settings, db_session, mocked_redis: AsyncMock):
    base_url = test_settings.base_url
    async with AsyncClient(base_url=base_url, transport=ASGITransport(app=app)) as client:
        # Create a test payload
        payload = {"target_url": "https://example.com"}
        # Post it to the server and wait for a response
        response = await client.post("/url", json=payload)

        # Check if it went through
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # Check if it has a shortened url "url"
        assert "url" in data
        assert data["target_url"] == "https://example.com"
        url_key = data["url"]

        # DB check
        db_row: models.URL = db_session.query(models.URL).filter(models.URL.key == url_key, models.URL.is_active).first()
        assert db_row.target_url == payload["target_url"]
        
        # Cache check
        mocked_redis.set.assert_awaited_with(url_key, payload["target_url"], ex=3600*24)
        cached = await mocked_redis.get(url_key)
        assert cached == payload["target_url"]

@pytest.mark.asyncio
async def test_forward_to_target_url(test_settings, db_session, mocked_redis):
    base_url = test_settings.base_url
    async with AsyncClient(base_url=base_url, transport=ASGITransport(app=app)) as client:
        payload = {"target_url": "https://example.com"}
        response = await client.post("/url", json=payload)
        url_key = response.json()["url"]

        response = await client.get(f"/{url_key}", follow_redirects=False)
        assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
        assert response.headers["location"] == "https://example.com"