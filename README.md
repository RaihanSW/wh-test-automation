# automation — User Service API Tests

White-box API tests untuk **User service** (`User/`, port 4000) memakai
**pytest + Playwright `APIRequestContext`** (HTTP-only, tanpa browser) +
**psycopg2** untuk verifikasi langsung ke Postgres `warehouse_db`.

## Skenario yang Dicakup

| # | Test | Endpoint | Assert |
|---|---|---|---|
| 1 | `test_create_user` | `POST /account/register` | 201 + `uid`; DB: password = SHA256 hex |
| 2 | `test_update_user` | `PUT /account/{uid}` | 200; DB: field berubah, password lama tetap |
| 3 | `test_delete_user` | `DELETE /account/{uid}` | 200; GET → 404; DB: row hilang |
| 4 | `test_create_role` | `POST /role` | expect 201 — **FAIL by design** (lihat Known Bug) |
| 5 | `test_update_role` | `PUT /role/{id}` | 200; DB: name berubah |
| 6 | `test_delete_role` | `DELETE /role/{id}` | 200; DB: row hilang |
| 7 | `test_change_user_role` | `PUT /account/{uid}` role_id 3→2 | 200; DB: role_id berubah |
| 8 | `test_delete_assigned_role_fails` | `DELETE /role/{id}` | 500 (FK violation), role tetap ada di DB |

### Known Bug

`POST /role` broken: migrasi `0001` membuat `roles.id INT PRIMARY KEY` tanpa
`GENERATED AS IDENTITY`/serial, sedangkan `InsertRole` hanya
`INSERT (name) RETURNING id` → Postgres `23502` → HTTP 500.
`test_create_role` assert ekspektasi benar (201) sehingga **selalu FAIL**
sampai bug diperbaiki. Karena itu, test 5/6/8 menyiapkan role lewat
`role_factory` (direct DB insert, id range 9000+).

## Setup

```bash
# 1. jalankan service (dari repo User)
cd ..\User
go run main.go -env local migrate up
go run main.go -env local seed
go run main.go -env local          # serve di :4000

# 2. setup test env (dari folder ini)
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt    # tanpa 'playwright install' (API-only)
copy .env.example .env             # isi DB_PASSWORD dsb.
```

## Menjalankan

```bash
pytest                             # semua test (ekspektasi: 7 pass, 1 fail)
pytest tests/test_user_crud.py     # user saja
pytest tests/test_role_crud.py     # role saja
pytest -k change_user_role         # satu test
```

Pre-check service hidup: `curl http://localhost:4000/ping`

## Struktur

```
automation/
├── config.py            # BASE_URL + DB_CONFIG dari env/.env
├── conftest.py          # fixtures: api_ctx, api, db_conn, user_factory, role_factory
├── helpers/
│   ├── api_client.py    # UserServiceClient — wrapper endpoint /account & /role
│   └── db.py            # query "User".users / "User".roles + sha256_hex
└── tests/
    ├── test_user_crud.py
    └── test_role_crud.py
```

Test bersifat idempotent: username/email unik per run (uuid), semua data
uji dibersihkan di teardown fixture (API + fallback DB).
