import pytest
from fastapi import status
from unittest.mock import AsyncMock
from datetime import datetime, timedelta, timezone

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
async def test_create_url_with_time_to_expiry(api_client, db_session):
    payload = {
        "target_url": "https://example.com",
        "time_to_expiry": "2h",
    }
    response = await api_client.post("/url", json=payload)
    assert response.status_code == status.HTTP_200_OK
    url_key = response.json()["url"]
    expires_at = response.json()["expires_at"]

    db_row: models.URL = (
        db_session.query(models.URL)
        .filter(models.URL.key == url_key, models.URL.is_active)
        .first()
    )
    assert db_row is not None
    now_utc = datetime.now(timezone.utc)
    expires_at_utc = (
        db_row.expires_at.replace(tzinfo=timezone.utc)
        if db_row.expires_at.tzinfo is None
        else db_row.expires_at.astimezone(timezone.utc)
    )
    delta = expires_at_utc - now_utc
    assert timedelta(minutes=119) <= delta <= timedelta(minutes=121)
    assert expires_at == expires_at_utc.astimezone().isoformat()

@pytest.mark.asyncio
async def test_create_url_rejects_past_expiry(api_client):
    payload = {
        "target_url": "https://example.com",
        "time_to_expiry": "0h",
    }

    response = await api_client.post("/url", json=payload)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "time_to_expiry must be a future duration" in response.json()["detail"]

@pytest.mark.asyncio
async def test_create_url_rejects_too_long_expiry(api_client):
    payload = {
        "target_url": "https://example.com",
        "time_to_expiry": "400d",
    }

    response = await api_client.post("/url", json=payload)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "time_to_expiry cannot exceed 1 year (365 days)" in response.json()["detail"]

@pytest.mark.asyncio
async def test_get_admin_info_requires_bearer_token(api_client):
    """Test that /admin/info endpoint requires a valid Authorization header."""
    # Missing header should return 401
    response = await api_client.get("/admin/info")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Missing Authorization header" in response.json()["detail"]

    # Invalid header format should return 401
    response = await api_client.get("/admin/info", headers={"Authorization": "Basic token"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Invalid Authorization header format" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_admin_info_endpoint_returns_bearer_format(
    api_client, test_settings, extract_bearer_token, bearer_token_header
):
    """
    Test that /admin/info endpoint:
    1. Returns admin_url in Bearer token format (not URL path)
    2. Accepts Authorization header for authentication
    3. Does NOT accept URL-path secrets anymore
    """
    base_url = test_settings.base_url
    payload = {"target_url": "https://example.com"}
    
    # Create shortened URL
    create_response = await api_client.post("/url", json=payload)
    assert create_response.status_code == status.HTTP_200_OK
    
    create_data = create_response.json()
    url_key = create_data["url"]
    admin_url_response = create_data["admin_url"]
    
    # admin_url should now be in format: "Use Authorization header: Bearer <token>"
    assert admin_url_response.startswith("Use Authorization header: Bearer ")
    
    # Extract the actual bearer token
    secret_token = extract_bearer_token(admin_url_response)
    
    # Now call /admin/info with the Bearer token in Authorization header
    admin_response = await api_client.get(
        "/admin/info",
        headers=bearer_token_header(secret_token)
    )
    
    assert admin_response.status_code == status.HTTP_200_OK
    data = admin_response.json()
    assert data["target_url"] == payload["target_url"]
    assert data["url"].startswith(f"{base_url}/")
    assert data["url"].endswith(url_key)
    # admin_url in response is also in Bearer format
    assert data["admin_url"].startswith("Use Authorization header: Bearer ")


@pytest.mark.asyncio
async def test_get_admin_info_with_wrong_token(api_client, bearer_token_header):
    """Test that providing a wrong secret_key returns 404."""
    response = await api_client.get(
        "/admin/info",
        headers=bearer_token_header("wrong_token_that_has_never_been_created")
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_delete_url_requires_bearer_token(api_client):
    """Test that /admin/delete endpoint requires a valid Authorization header."""
    # Missing header should return 401
    response = await api_client.delete("/admin/delete")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_delete_url_deactivates_and_blocks_redirect(
    db_session, api_client, extract_bearer_token, bearer_token_header
):
    """
    Test that DELETE /admin/delete (with Bearer token):
    1. Deactivates the URL in the database
    2. Blocks subsequent redirects (404)
    """
    payload = {"target_url": "https://delete-me.com"}
    create_response = await api_client.post("/url", json=payload)
    assert create_response.status_code == status.HTTP_200_OK
    
    create_data = create_response.json()
    url_key = create_data["url"]
    admin_url_response = create_data["admin_url"]
    
    # Extract bearer token from response
    secret_token = extract_bearer_token(admin_url_response)
    
    # Delete via Authorization header
    delete_response = await api_client.delete(
        "/admin/delete",
        headers=bearer_token_header(secret_token)
    )
    
    assert delete_response.status_code == status.HTTP_200_OK
    
    # Verify DB shows URL as inactive
    db_row: models.URL = (
        db_session.query(models.URL).filter(models.URL.secret_key == secret_token).first()
    )
    assert db_row.is_active is False
    
    # Verify redirect is now blocked
    blocked_response = await api_client.get(f"/{url_key}", follow_redirects=False)
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

@pytest.mark.asyncio
async def test_same_url_diff_keys(api_client, db_session):
    payload = {"target_url": "https://same-url.com"}

    response1 = await api_client.post("/url", json=payload)
    response2 = await api_client.post("/url", json=payload)

    assert response1.status_code == status.HTTP_200_OK
    assert response2.status_code == status.HTTP_200_OK

    db_row1: models.URL = (
        db_session.query(models.URL)
        .filter(models.URL.key == response1.json()["url"])
        .first()
    )

    db_row2: models.URL = (
        db_session.query(models.URL)
        .filter(models.URL.key == response2.json()["url"])
        .first()
    )

    assert db_row1.target_url == db_row2.target_url
    assert db_row1.key != db_row2.key

@pytest.mark.asyncio
async def test_click_atomicity(api_client, db_session):
    payload = {"target_url": "https://example.com"}

    response = await api_client.post("/url", json=payload)
    assert response.status_code == status.HTTP_200_OK

    url_key = response.json()["url"]

    n_requests = 3

    for _ in range(n_requests):
        get_request = await api_client.get(f"/{url_key}", follow_redirects=False)

    db_row: models.URL = (
        db_session.query(models.URL)
        .filter(models.URL.key == url_key)
        .first()
    )

    assert db_row.clicks == n_requests
     
