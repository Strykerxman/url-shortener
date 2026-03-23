"""Tests for new features: custom aliases, URL expiry, QR code endpoint."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from fastapi import status

from app import models, schemas
from app.database import crud


# -------------------------------------------------------
# Custom Alias tests
# -------------------------------------------------------


@pytest.mark.asyncio
async def test_create_url_with_custom_alias(api_client, db_session):
    """A custom alias is used as the short key when supplied."""
    payload = {"target_url": "https://example.com", "custom_alias": "mycoollink"}
    response = await api_client.post("/url", json=payload)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["url"] == "MYCOOLLINK"  # alias is uppercased


@pytest.mark.asyncio
async def test_custom_alias_conflict_returns_409(api_client, db_session):
    """A 409 is returned when the requested alias is already taken."""
    payload = {"target_url": "https://example.com", "custom_alias": "taken"}
    await api_client.post("/url", json=payload)

    response = await api_client.post("/url", json=payload)
    assert response.status_code == status.HTTP_409_CONFLICT
    assert "taken" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_custom_alias_invalid_format_returns_422(api_client):
    """An alias that is too short or contains special characters is rejected at schema level."""
    # Too short
    response = await api_client.post(
        "/url", json={"target_url": "https://example.com", "custom_alias": "ab"}
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Contains hyphen (non-alphanumeric)
    response = await api_client.post(
        "/url", json={"target_url": "https://example.com", "custom_alias": "my-link"}
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Too long (21 chars)
    response = await api_client.post(
        "/url",
        json={"target_url": "https://example.com", "custom_alias": "a" * 21},
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_custom_alias_redirect_works(api_client, db_session):
    """A URL created with a custom alias can be accessed via that alias."""
    payload = {"target_url": "https://example.com", "custom_alias": "myalias"}
    await api_client.post("/url", json=payload)

    response = await api_client.get("/MYALIAS", follow_redirects=False)
    assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
    assert response.headers["location"] == "https://example.com"


# -------------------------------------------------------
# URL Expiry tests
# -------------------------------------------------------


def test_create_db_url_with_expires_at(db_session):
    """An expires_at timestamp is persisted correctly."""
    future = datetime.now(timezone.utc) + timedelta(hours=1)
    url_data = schemas.URLBase(
        target_url="https://expiring.com", expires_at=future
    )
    db_url = crud.create_db_url(db_session, url_data)

    assert db_url.expires_at is not None
    fetched = crud.get_db_url_by_key(db_session, db_url.key)
    assert fetched is not None


def test_expired_url_is_not_returned(db_session):
    """An already-expired URL is invisible to get_db_url_by_key."""
    past = datetime.now(timezone.utc) - timedelta(seconds=1)
    url_data = schemas.URLBase(
        target_url="https://expired.com", expires_at=past
    )
    db_url = crud.create_db_url(db_session, url_data)

    fetched = crud.get_db_url_by_key(db_session, db_url.key)
    assert fetched is None


def test_add_click_by_key_ignores_expired(db_session):
    """Click increment is a no-op for expired URLs."""
    past = datetime.now(timezone.utc) - timedelta(seconds=1)
    url_data = schemas.URLBase(
        target_url="https://expired-click.com", expires_at=past
    )
    db_url = crud.create_db_url(db_session, url_data)

    result = crud.add_click_by_key(db_session, db_url.key)
    assert result is None


@pytest.mark.asyncio
async def test_expired_url_returns_404(api_client, db_session):
    """Accessing a redirect for an expired URL returns 404."""
    past = datetime.now(timezone.utc) - timedelta(seconds=1)
    payload = {
        "target_url": "https://gone.com",
        "expires_at": past.isoformat(),
    }
    create_resp = await api_client.post("/url", json=payload)
    url_key = create_resp.json()["url"]

    response = await api_client.get(f"/{url_key}", follow_redirects=False)
    assert response.status_code == status.HTTP_404_NOT_FOUND


# -------------------------------------------------------
# QR Code endpoint tests
# -------------------------------------------------------


@pytest.mark.asyncio
async def test_qr_code_returns_png(api_client, db_session):
    """GET /qr/{url_key} returns a valid PNG image for an active URL."""
    create_resp = await api_client.post(
        "/url", json={"target_url": "https://example.com"}
    )
    url_key = create_resp.json()["url"]

    qr_response = await api_client.get(f"/qr/{url_key}")
    assert qr_response.status_code == status.HTTP_200_OK
    assert qr_response.headers["content-type"] == "image/png"
    # PNG magic bytes: 0x89 0x50 0x4E 0x47
    assert qr_response.content[:4] == b"\x89PNG"


@pytest.mark.asyncio
async def test_qr_code_unknown_key_returns_404(api_client, db_session):
    """GET /qr/{url_key} with an unknown key returns 404."""
    response = await api_client.get("/qr/ZZZZZ")
    assert response.status_code == status.HTTP_404_NOT_FOUND
