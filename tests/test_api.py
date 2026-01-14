import pytest
from fastapi import status
from unittest.mock import AsyncMock

from app import models


@pytest.mark.asyncio
async def test_health_check(api_client):
    response = await api_client.get("/health")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "db healthy"}


# @pytest.mark.asyncio
# async def test_health_check_db_failure(override_settings, override_db):
#     pass


@pytest.mark.asyncio
async def test_create_short_url(api_client, db_session, mocked_redis: AsyncMock):
    # Create a test payload
    payload = {"target_url": "https://example.com"}
    # Post it to the server and wait for a response
    response = await api_client.post("/url", json=payload)
    # Check if it went through
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    # Check if it has a shortened url "url"
    assert "url" in data
    assert data["target_url"] == "https://example.com"
    url_key = data["url"]

    # DB check
    db_row: models.URL = (
        db_session.query(models.URL)
        .filter(models.URL.key == url_key, models.URL.is_active)
        .first()
    )
    assert db_row.target_url == payload["target_url"]

    # Cache check
    mocked_redis.set.assert_awaited_with(url_key, payload["target_url"], ex=3600 * 24)
    cached = await mocked_redis.get(url_key)
    assert cached == payload["target_url"]


@pytest.mark.asyncio
async def test_forward_to_target_url(api_client):
    payload = {"target_url": "https://example.com"}
    response = await api_client.post("/url", json=payload)
    url_key = response.json()["url"]

    response = await api_client.get(f"/{url_key}", follow_redirects=False)
    assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
    assert response.headers["location"] == "https://example.com"


@pytest.mark.asyncio
async def test_create_url_invalid_format(api_client):
    response = await api_client.post("/url", json={"target_url": "invalid"})
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert (
        "Your provided URL is not valid. **Must include http:// or https://**"
        in response.json()["detail"]
    )


@pytest.mark.asyncio
async def test_get_admin_info_endpoint_includes_full_urls(api_client, test_settings):
    base_url = test_settings.base_url
    payload = {"target_url": "https://example.com"}
    create_response = await api_client.post("/url", json=payload)
    secret_key = create_response.json()["admin_url"]
    url_key = create_response.json()["url"]

    admin_response = await api_client.get(f"/admin/{secret_key}")

    assert admin_response.status_code == status.HTTP_200_OK
    data = admin_response.json()
    assert data["target_url"] == payload["target_url"]
    assert data["url"].startswith(f"{base_url}/")
    assert data["url"].endswith(url_key)
    assert data["admin_url"].startswith(f"{base_url}/admin/")
    assert data["admin_url"].endswith(secret_key)


@pytest.mark.asyncio
async def test_delete_url_deactivates_and_blocks_redirect(
    db_session, api_client
):
    payload = {"target_url": "https://delete-me.com"}
    create_response = await api_client.post("/url", json=payload)
    secret_key = create_response.json()["admin_url"]
    url_key = create_response.json()["url"]

    delete_response = await api_client.delete(f"/admin/{secret_key}")
    blocked_response = await api_client.get(f"/{url_key}", follow_redirects=False)

    assert delete_response.status_code == status.HTTP_200_OK
    db_row: models.URL = (
        db_session.query(models.URL).filter(models.URL.secret_key == secret_key).first()
    )
    assert db_row.is_active is False
    assert blocked_response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_forward_falls_back_when_redis_errors(
    mocked_redis, api_client
):
    old_get_side_effect = mocked_redis.get.side_effect
    mocked_redis.get.side_effect = Exception("redis down")

    payload = {"target_url": "https://fallback.com"}
    create_response = await api_client.post("/url", json=payload)
    url_key = create_response.json()["url"]

    redirect_response = await api_client.get(f"/{url_key}", follow_redirects=False)

    assert redirect_response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
    assert redirect_response.headers["location"] == payload["target_url"]
    mocked_redis.get.side_effect = old_get_side_effect
