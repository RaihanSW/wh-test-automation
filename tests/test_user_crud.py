"""User CRUD + role reassignment — table "User".users.

Covers: create user (register), update user, delete user, change user role.
Each test asserts the HTTP response AND the resulting DB state.
"""

from conftest import unique_user_payload
from helpers import db


def test_create_user(api, db_conn):
    # build payload manually (no factory) so we control the cleanup order
    payload = unique_user_payload()
    status, body = api.register_user(payload)

    try:
        assert status == 201, body
        data = body["data"]
        assert data["is_success"] is True
        assert data["uid"]

        row = db.get_user_by_uid(db_conn, data["uid"])
        assert row is not None, "user not found in DB after register"
        assert row["username"] == payload["username"]
        assert row["email"] == payload["email"]
        assert row["role_id"] == 3
        # white-box: password must be stored as SHA256 hex, never plaintext
        assert row["password"] == db.sha256_hex(payload["password"])
    finally:
        if status == 201:
            db.delete_user(db_conn, body["data"]["uid"])


def test_update_user(api, db_conn, user_factory):
    uid, payload = user_factory()
    original = db.get_user_by_uid(db_conn, uid)

    updated = {
        "first_name": "Updated",
        "last_name": "Name",
        "username": payload["username"],  # unchanged
        "email": payload["email"],  # unchanged
        "role_id": payload["role_id"],
        "password": "",  # empty -> old hash must be kept
    }
    status, body = api.update_user(uid, updated)

    assert status == 200, body
    assert body["data"]["is_success"] is True

    row = db.get_user_by_uid(db_conn, uid)
    assert row["first_name"] == "Updated"
    assert row["last_name"] == "Name"
    assert row["password"] == original["password"], "password must not change"


def test_delete_user(api, db_conn, user_factory):
    uid, _ = user_factory()

    status, body = api.delete_user(uid)
    assert status == 200, body
    assert body["data"]["is_success"] is True

    assert db.get_user_by_uid(db_conn, uid) is None, "user still in DB"

    status, _ = api.get_user(uid)
    assert status == 404


def test_change_user_role(api, db_conn, user_factory):
    """Reassign a user's role via PUT /account/{uid} (role_id is required)."""
    uid, payload = user_factory(role_id=3)
    assert db.get_user_by_uid(db_conn, uid)["role_id"] == 3

    updated = dict(payload)
    updated["role_id"] = 2  # Staff -> Admin (seeded role)
    updated["password"] = ""
    status, body = api.update_user(uid, updated)

    assert status == 200, body
    assert body["data"]["is_success"] is True
    assert db.get_user_by_uid(db_conn, uid)["role_id"] == 2
