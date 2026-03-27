from app import schemas
from app.core import keygen
from app.database import crud


def _create_url(db_session, monkeypatch, key="ABCDE", secret_suffix="ZZZZZZZZ"):
    monkeypatch.setattr(keygen, "create_unique_key", lambda db: key)
    monkeypatch.setattr(keygen, "create_key", lambda length=8: secret_suffix[:length])
    return crud.create_db_url(
        db_session, schemas.URLBase(target_url="https://example.com")
    )


def test_create_db_url_persists_expected_fields(db_session, monkeypatch):
    db_url = _create_url(db_session, monkeypatch, key="ABCDE", secret_suffix="SECRETS1")

    assert db_url.key == "ABCDE"
    assert db_url.secret_key == "ABCDE_SECRETS1"
    assert db_url.is_active is True
    assert db_url.clicks == 0


def test_get_db_url_by_key_and_secret(db_session, monkeypatch):
    db_url = _create_url(db_session, monkeypatch, key="LOOK1", secret_suffix="LOOKUP12")

    fetched_by_key = crud.get_db_url_by_key(db_session, "LOOK1")
    fetched_by_secret = crud.get_db_url_by_secret_key(db_session, db_url.secret_key)

    assert fetched_by_key.id == db_url.id
    assert fetched_by_secret.id == db_url.id


def test_add_click_and_add_click_by_key(db_session, monkeypatch):
    db_url = _create_url(db_session, monkeypatch, key="CLICK", secret_suffix="CLICK123")

    updated = crud.add_click(db_session, db_url)
    assert updated.clicks == 1

    updated_again = crud.add_click_by_key(db_session, "CLICK")
    assert updated_again.clicks == 2


def test_deactivate_db_url_by_secret_key(db_session, monkeypatch):
    db_url = _create_url(db_session, monkeypatch, key="DELTA", secret_suffix="DELETE11")

    deactivated = crud.deactivate_db_url_by_secret_key(db_session, db_url.secret_key)

    assert deactivated.is_active is False
    assert crud.get_db_url_by_key(db_session, db_url.key) is None
    assert crud.get_db_url_by_secret_key(db_session, db_url.secret_key) is None