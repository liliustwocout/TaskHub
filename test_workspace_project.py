import pytest
import uuid
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_workspace_and_project_flow():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        uid1 = str(uuid.uuid4())[:8]
        uid2 = str(uuid.uuid4())[:8]
        
        # Register User 1 (Owner)
        reg1 = await ac.post("/api/v1/auth/register", json={
            "email": f"owner_{uid1}@example.com",
            "full_name": "Workspace Owner",
            "password": "Password123!"
        })
        assert reg1.status_code == 201, reg1.text
        
        login1 = await ac.post("/api/v1/auth/login", json={
            "email": f"owner_{uid1}@example.com",
            "password": "Password123!"
        })
        token1 = login1.json()["access_token"]
        headers1 = {"Authorization": f"Bearer {token1}"}

        # Register User 2 (Member)
        reg2 = await ac.post("/api/v1/auth/register", json={
            "email": f"member_{uid2}@example.com",
            "full_name": "Workspace Member",
            "password": "Password123!"
        })
        assert reg2.status_code == 201, reg2.text
        member2_id = reg2.json()["id"]

        login2 = await ac.post("/api/v1/auth/login", json={
            "email": f"member_{uid2}@example.com",
            "password": "Password123!"
        })
        token2 = login2.json()["access_token"]
        headers2 = {"Authorization": f"Bearer {token2}"}

        # 1. Create Workspace
        ws_create = await ac.post("/api/v1/workspaces", json={"name": "Engineering Workspace"}, headers=headers1)
        assert ws_create.status_code == 201, ws_create.text
        ws_data = ws_create.json()
        ws_id = ws_data["id"]
        assert ws_data["name"] == "Engineering Workspace"
        assert ws_data["my_role"] == "OWNER"

        # 2. Add Member with EDITOR role
        add_mem = await ac.post(f"/api/v1/workspaces/{ws_id}/members", json={
            "user_id": member2_id,
            "role": "EDITOR"
        }, headers=headers1)
        assert add_mem.status_code == 201, add_mem.text
        assert add_mem.json()["role"] == "EDITOR"

        # 3. List Members
        members_list = await ac.get(f"/api/v1/workspaces/{ws_id}/members", headers=headers1)
        assert members_list.status_code == 200
        assert len(members_list.json()) == 2

        # 4. User 2 lists workspaces
        u2_workspaces = await ac.get("/api/v1/workspaces", headers=headers2)
        assert u2_workspaces.status_code == 200
        assert len(u2_workspaces.json()) == 1
        assert u2_workspaces.json()[0]["my_role"] == "EDITOR"

        # 5. User 2 creates a Project in Workspace
        proj_create = await ac.post(f"/api/v1/workspaces/{ws_id}/projects", json={
            "name": "TaskHub Backend",
            "description": "FastAPI REST Service"
        }, headers=headers2)
        assert proj_create.status_code == 201, proj_create.text
        proj_data = proj_create.json()
        proj_id = proj_data["id"]
        assert proj_data["name"] == "TaskHub Backend"
        assert proj_data["status"] == "ACTIVE"

        # 6. List Projects in Workspace
        projects_list = await ac.get(f"/api/v1/workspaces/{ws_id}/projects", headers=headers1)
        assert projects_list.status_code == 200
        assert len(projects_list.json()) == 1

        # 7. Update Project status to ARCHIVED
        proj_update = await ac.patch(f"/api/v1/projects/{proj_id}", json={
            "status": "ARCHIVED"
        }, headers=headers2)
        assert proj_update.status_code == 200
        assert proj_update.json()["status"] == "ARCHIVED"

        # 8. User 2 tries to delete project (should be 403, only OWNER can delete project)
        proj_del_forbidden = await ac.delete(f"/api/v1/projects/{proj_id}", headers=headers2)
        assert proj_del_forbidden.status_code == 403

        # 9. User 1 deletes project
        proj_del = await ac.delete(f"/api/v1/projects/{proj_id}", headers=headers1)
        assert proj_del.status_code == 204

        # 10. Delete Workspace
        ws_del = await ac.delete(f"/api/v1/workspaces/{ws_id}", headers=headers1)
        assert ws_del.status_code == 204
