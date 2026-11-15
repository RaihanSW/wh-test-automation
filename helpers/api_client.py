"""Thin wrapper around Playwright's APIRequestContext for the User service.

Response envelope (all endpoints):
    {"status": "Created", "data": {"is_success": true, ...}, "accessTime": "..."}
"""


class UserServiceClient:
    def __init__(self, request_context):
        self._ctx = request_context

    # ---- /account (table "User".users) ----

    def register_user(self, payload: dict):
        resp = self._ctx.post("/account/register", data=payload)
        return resp.status, resp.json()

    def login(self, username: str, password: str):
        resp = self._ctx.post(
            "/account/login", data={"username": username, "password": password}
        )
        return resp.status, resp.json()

    def get_user(self, uid: str):
        resp = self._ctx.get(f"/account/{uid}")
        return resp.status, resp.json()

    def update_user(self, uid: str, payload: dict):
        resp = self._ctx.put(f"/account/{uid}", data=payload)
        return resp.status, resp.json()

    def delete_user(self, uid: str):
        resp = self._ctx.delete(f"/account/{uid}")
        return resp.status, resp.json()

    # ---- /role (table "User".roles) ----

    def create_role(self, name: str):
        resp = self._ctx.post("/role", data={"name": name})
        return resp.status, resp.json()

    def get_all_roles(self):
        resp = self._ctx.get("/role")
        return resp.status, resp.json()

    def get_role(self, role_id: int):
        resp = self._ctx.get(f"/role/{role_id}")
        return resp.status, resp.json()

    def update_role(self, role_id: int, name: str):
        resp = self._ctx.put(f"/role/{role_id}", data={"name": name})
        return resp.status, resp.json()

    def delete_role(self, role_id: int):
        resp = self._ctx.delete(f"/role/{role_id}")
        return resp.status, resp.json()
