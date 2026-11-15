"""Direct Postgres helpers for white-box verification/setup/cleanup.

Schema: "User" (quoted identifier — `user` is reserved).
"""

import hashlib


def sha256_hex(plain: str) -> str:
    """Mirror util.HashSHA256 — 64-char lowercase hex digest."""
    return hashlib.sha256(plain.encode()).hexdigest()


def get_user_by_uid(conn, uid: str):
    """Return user row as dict, or None."""
    with conn.cursor() as cur:
        cur.execute(
            'SELECT uid, first_name, last_name, username, email, role_id, password '
            'FROM "User".users WHERE uid = %s',
            (uid,),
        )
        row = cur.fetchone()
    if row is None:
        return None
    return {
        "uid": row[0],
        "first_name": row[1],
        "last_name": row[2],
        "username": row[3],
        "email": row[4],
        "role_id": row[5],
        "password": row[6],
    }


def delete_user(conn, uid: str):
    with conn.cursor() as cur:
        cur.execute('DELETE FROM "User".users WHERE uid = %s', (uid,))


def get_role_by_id(conn, role_id: int):
    """Return (id, name) tuple, or None."""
    with conn.cursor() as cur:
        cur.execute(
            'SELECT id, name FROM "User".roles WHERE id = %s', (role_id,)
        )
        return cur.fetchone()


def insert_role(conn, role_id: int, name: str):
    """Insert a role with an explicit id (roles.id is not auto-generated)."""
    with conn.cursor() as cur:
        cur.execute(
            'INSERT INTO "User".roles (id, name) VALUES (%s, %s)', (role_id, name)
        )


def update_user_role(conn, uid: str, role_id: int):
    """Force-assign a role (used to release a role before cleanup)."""
    with conn.cursor() as cur:
        cur.execute(
            'UPDATE "User".users SET role_id = %s WHERE uid = %s',
            (role_id, uid),
        )


def delete_role(conn, role_id: int):
    with conn.cursor() as cur:
        cur.execute('DELETE FROM "User".roles WHERE id = %s', (role_id,))
