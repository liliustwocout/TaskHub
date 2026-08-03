import pytest
import uuid
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_comment_and_pagination_flow():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        uid1 = str(uuid.uuid4())[:8]
        uid2 = str(uuid.uuid4())[:8]

        # 1. Register Owner
        reg1 = await ac.post("/api/v1/auth/register", json={
            "email": f"owner_{uid1}@example.com",
            "full_name": "Workspace Owner",
            "password": "Password123!"
        })
        assert reg1.status_code == 201
        owner_id = reg1.json()["id"]

        login1 = await ac.post("/api/v1/auth/login", json={
            "email": f"owner_{uid1}@example.com",
            "password": "Password123!"
        })
        headers_owner = {"Authorization": f"Bearer {login1.json()['access_token']}"}

        # 2. Register Member/Editor
        reg2 = await ac.post("/api/v1/auth/register", json={
            "email": f"member_{uid2}@example.com",
            "full_name": "Workspace Member",
            "password": "Password123!"
        })
        assert reg2.status_code == 201
        member_id = reg2.json()["id"]

        login2 = await ac.post("/api/v1/auth/login", json={
            "email": f"member_{uid2}@example.com",
            "password": "Password123!"
        })
        headers_member = {"Authorization": f"Bearer {login2.json()['access_token']}"}

        # 3. Setup Workspace & Project
        ws_res = await ac.post("/api/v1/workspaces", json={"name": "Comment WS"}, headers=headers_owner)
        ws_id = ws_res.json()["id"]

        await ac.post(f"/api/v1/workspaces/{ws_id}/members", json={"user_id": member_id, "role": "EDITOR"}, headers=headers_owner)

        proj_res = await ac.post(f"/api/v1/workspaces/{ws_id}/projects", json={"name": "Comment Project"}, headers=headers_owner)
        proj_id = proj_res.json()["id"]

        # 4. Create Tasks for testing filtering & pagination
        for i in range(1, 6):
            await ac.post(f"/api/v1/projects/{proj_id}/tasks", json={
                "title": f"Task {i}",
                "status": "TODO" if i <= 3 else "IN_PROGRESS",
                "priority": "HIGH" if i % 2 == 1 else "LOW",
                "assignee_id": member_id if i <= 2 else owner_id
            }, headers=headers_owner)

        # --- TEST FEATURE 8: FILTERING & PAGINATION ---
        # Pagination test (page 1, limit 2)
        page1_res = await ac.get(f"/api/v1/projects/{proj_id}/tasks?page=1&limit=2", headers=headers_member)
        assert page1_res.status_code == 200
        p1_data = page1_res.json()
        assert len(p1_data["items"]) == 2
        assert p1_data["total"] == 5
        assert p1_data["page"] == 1
        assert p1_data["limit"] == 2
        assert p1_data["total_pages"] == 3

        # Filtering test (status=TODO)
        filter_status = await ac.get(f"/api/v1/projects/{proj_id}/tasks?status=TODO", headers=headers_member)
        assert filter_status.status_code == 200
        fs_data = filter_status.json()
        assert fs_data["total"] == 3
        assert len(fs_data["items"]) == 3

        # Combined filtering & pagination
        combined = await ac.get(f"/api/v1/projects/{proj_id}/tasks?status=TODO&priority=HIGH&page=1&limit=10", headers=headers_member)
        assert combined.status_code == 200
        comb_data = combined.json()
        assert comb_data["total"] == 2

        # --- TEST FEATURE 7: COMMENT ---
        first_task_id = p1_data["items"][0]["id"]

        # Add comment (Member)
        c1_res = await ac.post(f"/api/v1/tasks/{first_task_id}/comments", json={
            "content": "This is a test comment by member."
        }, headers=headers_member)
        assert c1_res.status_code == 201, c1_res.text
        c1_data = c1_res.json()
        c1_id = c1_data["id"]
        assert c1_data["content"] == "This is a test comment by member."
        assert c1_data["author"]["id"] == member_id

        # List comments
        list_c = await ac.get(f"/api/v1/tasks/{first_task_id}/comments", headers=headers_owner)
        assert list_c.status_code == 200
        assert len(list_c.json()) == 1

        # Delete comment by author (Member)
        del_c = await ac.delete(f"/api/v1/comments/{c1_id}", headers=headers_member)
        assert del_c.status_code == 204

        # Verify comment deleted
        list_c_after = await ac.get(f"/api/v1/tasks/{first_task_id}/comments", headers=headers_owner)
        assert len(list_c_after.json()) == 0
