import asyncio
import string
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException, Request

from app import models
from app.core import keygen, logging
from app.database import caching


def test_create_key_length_and_charset():
    key = keygen.create_key(7)
    assert len(key) == 7
    allowed = set(string.ascii_letters + string.digits)
    assert all(char in allowed for char in key)


def test_create_unique_key_avoids_existing(db_session, monkeypatch):
    existing = models.URL(
        target_url="https://exists.com", key="EXIST77", secret_key="EXIST_SECRET"
    )
    db_session.add(existing)
    db_session.commit()

    keys = iter(["EXIST77", "UNIQ2RR"])
    monkeypatch.setattr(keygen, "create_key", lambda length=7: next(keys))

    unique_key = keygen.create_unique_key(db_session)
    assert unique_key == "UNIQ2RR"


def test_get_admin_info_returns_bearer_format(test_settings):
    """
    Test that get_admin_info() now returns admin_url in Bearer token format.
    Security improvement: secrets are now in Authorization header, not URL path.
    """
    from app.core import url_utils
    
    db_url = models.URL(
        target_url="https://example.com",
        key="ABCDE",
        secret_key="ABCDE_SECRET",
    )
    config_base_url = test_settings.base_url

    admin_info = url_utils.get_admin_info(db_url, test_settings)

    # Public shortened URL should include key
    assert admin_info.url.startswith(config_base_url)
    assert admin_info.url.endswith("ABCDE")
    
    # Admin URL should now show Bearer format instruction (not the old URL format)
    assert admin_info.admin_url.startswith("Use Authorization header: Bearer ")
    assert "ABCDE_SECRET" in admin_info.admin_url


def test_logging_helpers_raise():
    with pytest.raises(HTTPException) as bad_request:
        logging.raise_bad_request("invalid")
    assert bad_request.value.status_code == 400
    assert "invalid" in bad_request.value.detail

    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/missing",
            "scheme": "http",
            "server": ("testserver", 80),
            "client": ("testclient", 1234),
            "headers": [],
        }
    )
    with pytest.raises(HTTPException) as not_found:
        logging.raise_not_found(request)
    assert not_found.value.status_code == 404
    assert "/missing" in not_found.value.detail


@pytest.mark.asyncio
async def test_safe_redis_set_handles_timeout():
    client = AsyncMock()
    client.set = AsyncMock(side_effect=asyncio.TimeoutError())

    await caching.safe_redis_set(client, "key", "value", ex=10)

    client.set.assert_awaited()
