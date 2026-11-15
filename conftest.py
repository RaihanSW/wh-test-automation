import uuid

import psycopg2
import pytest
from playwright.sync_api import sync_playwright

import config
from helpers import UserServiceClient, db


@pytest.fixture(scope="session")
def api_ctx():
    """Playwright APIRequestContext pointed at the User service."""
    with sync_playwright() as p:
        ctx = p.request.new_context(base_url=config.BASE_URL)
        yield ctx
        ctx.dispose()


@pytest.fixture(scope="session")
def api(api_ctx):
    return UserServiceClient(api_ctx)


@pytest.fixture(scope="session")
def db_conn():
    """Autocommit Postgres connection for white-box verification."""
    conn = psycopg2.connect(**config.DB_CONFIG)
    conn.autocommit = True
    yield conn
    conn.close()


def unique_user_payload(**overrides):
    """RegisterRequest-compatible payload with unique username/email."""
    suffix = uuid.uuid4().hex[:8]
    payload = {
        "first_name": "Test",
        "last_name": "Automation",
        "username": f"test_{suffix}",
        "email": f"test_{suffix}@example.com",
        "role_id": 3,  # Staff (seeded)
        "password": "password123",
    }
    payload.update(overrides)
    return payload


@pytest.fixture
def user_factory(api, db_conn):
    """Create a user via the API; tear down via API + DB fallback."""
    created = []

    def _create(**overrides):
        payload = unique_user_payload(**overrides)
        status, body = api.register_user(payload)
        assert status == 201, f"setup register failed: {status} {body}"
        uid = body["data"]["uid"]
        created.append(uid)
        return uid, payload

    yield _create

    for uid in created:
        api.delete_user(uid)
        db.delete_user(db_conn, uid)  # no-op if API delete already removed it


def new_role_id(db_conn):
    """Pick an unused role id in the test range (9000+) to avoid seeded 1-3."""
    with db_conn.cursor() as cur:
        cur.execute(
            'SELECT COALESCE(MAX(id), 8999) + 1 FROM "User".roles WHERE id >= 9000'
        )
        return cur.fetchone()[0]


@pytest.fixture
def role_factory(db_conn):
    """Create a role via direct DB insert (POST /role is currently broken —
    roles.id is INT PRIMARY KEY without identity, so InsertRole fails).
    Teardown deletes the role unless still referenced by a user."""
    created = []

    def _create(name=None):
        role_id = new_role_id(db_conn)
        db.insert_role(db_conn, role_id, name or f"TestRole_{role_id}")
        created.append(role_id)
        return role_id

    yield _create

    for role_id in created:
        with db_conn.cursor() as cur:
            # release any users still referencing this role before cleanup
            cur.execute(
                'UPDATE "User".users SET role_id = 3 WHERE role_id = %s',
                (role_id,),
            )
        db.delete_role(db_conn, role_id)
