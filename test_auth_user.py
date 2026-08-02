import pytest
import uuid
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_auth_and_user_flow():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        email = f"user_{uuid.uuid4().hex[:8]}@example.com"
        
        # 1. Register User
        reg_resp = await ac.post("/api/v1/auth/register", json={
            "email": email,
            "full_name": "Test User",
            "password": "Password123!"
        })
        assert reg_resp.status_code == 201, reg_resp.text
        user_data = reg_resp.json()
        assert user_data["email"] == email
        assert user_data["full_name"] == "Test User"

        # 2. Login User
        login_resp = await ac.post("/api/v1/auth/login", json={
            "email": email,
            "password": "Password123!"
        })
        assert login_resp.status_code == 200, login_resp.text
        tokens = login_resp.json()
        access_token = tokens["access_token"]
        refresh_token = tokens["refresh_token"]

        headers = {"Authorization": f"Bearer {access_token}"}

        # 3. Get Profile
        me_resp = await ac.get("/api/v1/users/me", headers=headers)
        assert me_resp.status_code == 200
        assert me_resp.json()["email"] == email

        # 4. Update Profile
        update_resp = await ac.patch("/api/v1/users/me", json={"full_name": "Updated User"}, headers=headers)
        assert update_resp.status_code == 200
        assert update_resp.json()["full_name"] == "Updated User"

        # 5. Change Password
        pass_resp = await ac.post("/api/v1/users/me/change-password", json={
            "old_password": "Password123!",
            "new_password": "NewPassword123!"
        }, headers=headers)
        assert pass_resp.status_code == 200

        # 6. Refresh Token
        ref_resp = await ac.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
        assert ref_resp.status_code == 200
        new_tokens = ref_resp.json()
        assert "access_token" in new_tokens

        # 7. Logout
        logout_resp = await ac.post("/api/v1/auth/logout", json={"refresh_token": new_tokens["refresh_token"]})
        assert logout_resp.status_code == 200
