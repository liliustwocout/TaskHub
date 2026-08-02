import pytest
import uuid
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_task_and_label_flow():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        uid1 = str(uuid.uuid4())[:8]
        uid2 = str(uuid.uuid4())[:8]
        uid3 = str(uuid.uuid4())[:8]

        # 1. Register Owner (User 1)
        reg1 = await ac.post("/api/v1/auth/register", json={
            "email": f"owner_{uid1}@example.com",
            "full_name": "Task Owner",
            "password": "Password123!"
        })
        assert reg1.status_code == 201, reg1.text
        owner_id = reg1.json()["id"]

        login1 = await ac.post("/api/v1/auth/login", json={
            "email": f"owner_{uid1}@example.com",
            "password": "Password123!"
        })
        headers_owner = {"Authorization": f"Bearer {login1.json()['access_token']}"}

        # 2. Register Editor (User 2)
        reg2 = await ac.post("/api/v1/auth/register", json={
            "email": f"editor_{uid2}@example.com",
            "full_name": "Task Editor",
            "password": "Password123!"
        })
        assert reg2.status_code == 201, reg2.text
        editor_id = reg2.json()["id"]

        login2 = await ac.post("/api/v1/auth/login", json={
            "email": f"editor_{uid2}@example.com",
            "password": "Password123!"
        })
        headers_editor = {"Authorization": f"Bearer {login2.json()['access_token']}"}

        # 3. Register Viewer (User 3)
        reg3 = await ac.post("/api/v1/auth/register", json={
            "email": f"viewer_{uid3}@example.com",
            "full_name": "Task Viewer",
            "password": "Password123!"
        })
        assert reg3.status_code == 201, reg3.text
        viewer_id = reg3.json()["id"]

        login3 = await ac.post("/api/v1/auth/login", json={
            "email": f"viewer_{uid3}@example.com",
            "password": "Password123!"
        })
        headers_viewer = {"Authorization": f"Bearer {login3.json()['access_token']}"}

        # 4. Setup Workspace & Project
        ws_res = await ac.post("/api/v1/workspaces", json={"name": "Task Team Workspace"}, headers=headers_owner)
        ws_id = ws_res.json()["id"]

        # Add Editor and Viewer to Workspace
        await ac.post(f"/api/v1/workspaces/{ws_id}/members", json={"user_id": editor_id, "role": "EDITOR"}, headers=headers_owner)
        await ac.post(f"/api/v1/workspaces/{ws_id}/members", json={"user_id": viewer_id, "role": "VIEWER"}, headers=headers_owner)

        proj_res = await ac.post(f"/api/v1/workspaces/{ws_id}/projects", json={"name": "TaskHub Sprint 1"}, headers=headers_owner)
        proj_id = proj_res.json()["id"]

        # --- FEATURE 6: LABEL MANAGEMENT ---
        # 5. Create Labels (Owner/Editor)
        lbl1_res = await ac.post(f"/api/v1/projects/{proj_id}/labels", json={"name": "Backend", "color": "#FF0000"}, headers=headers_owner)
        assert lbl1_res.status_code == 201, lbl1_res.text
        lbl1_id = lbl1_res.json()["id"]
        assert lbl1_res.json()["name"] == "Backend"

        lbl2_res = await ac.post(f"/api/v1/projects/{proj_id}/labels", json={"name": "UrgentBug", "color": "#00FF00"}, headers=headers_editor)
        assert lbl2_res.status_code == 201, lbl2_res.text
        lbl2_id = lbl2_res.json()["id"]

        # Viewer trying to create label (Should be 403)
        lbl_fail = await ac.post(f"/api/v1/projects/{proj_id}/labels", json={"name": "FailLabel"}, headers=headers_viewer)
        assert lbl_fail.status_code == 403

        # List Labels
        lbl_list = await ac.get(f"/api/v1/projects/{proj_id}/labels", headers=headers_viewer)
        assert lbl_list.status_code == 200
        assert len(lbl_list.json()) == 2

        # Update Label
        lbl_up = await ac.patch(f"/api/v1/labels/{lbl1_id}", json={"name": "Core Backend"}, headers=headers_editor)
        assert lbl_up.status_code == 200
        assert lbl_up.json()["name"] == "Core Backend"

        # --- FEATURE 5: TASK MANAGEMENT ---
        # 6. Create Task with invalid assignee (not in workspace -> 400)
        invalid_assignee_res = await ac.post(f"/api/v1/projects/{proj_id}/tasks", json={
            "title": "Invalid Task",
            "assignee_id": 99999
        }, headers=headers_owner)
        assert invalid_assignee_res.status_code == 400

        # 7. Create Task successfully (Editor creates task assigned to Editor)
        t1_res = await ac.post(f"/api/v1/projects/{proj_id}/tasks", json={
            "title": "Implement Auth System",
            "description": "JWT authentication module",
            "assignee_id": editor_id,
            "status": "TODO",
            "priority": "HIGH"
        }, headers=headers_editor)
        assert t1_res.status_code == 201, t1_res.text
        t1_data = t1_res.json()
        t1_id = t1_data["id"]
        assert t1_data["title"] == "Implement Auth System"
        assert t1_data["priority"] == "HIGH"

        # 8. Create second task
        t2_res = await ac.post(f"/api/v1/projects/{proj_id}/tasks", json={
            "title": "Fix Database Indexing",
            "status": "IN_PROGRESS",
            "priority": "URGENT",
            "assignee_id": owner_id
        }, headers=headers_owner)
        assert t2_res.status_code == 201
        t2_id = t2_res.json()["id"]

        # Viewer tries to create task (Should be 403)
        t_fail = await ac.post(f"/api/v1/projects/{proj_id}/tasks", json={"title": "Unauthorized Task"}, headers=headers_viewer)
        assert t_fail.status_code == 403

        # 9. Attach Label to Task
        add_lbl_res = await ac.post(f"/api/v1/tasks/{t1_id}/labels/{lbl1_id}", headers=headers_editor)
        assert add_lbl_res.status_code == 200, add_lbl_res.text
        assert len(add_lbl_res.json()["labels"]) == 1
        assert add_lbl_res.json()["labels"][0]["id"] == lbl1_id

        # 10. Update Task status, priority, description
        t1_patch = await ac.patch(f"/api/v1/tasks/{t1_id}", json={
            "status": "IN_PROGRESS",
            "priority": "URGENT",
            "description": "Updated JWT description"
        }, headers=headers_editor)
        assert t1_patch.status_code == 200
        assert t1_patch.json()["status"] == "IN_PROGRESS"
        assert t1_patch.json()["priority"] == "URGENT"

        # 11. Get Task details
        t1_get = await ac.get(f"/api/v1/tasks/{t1_id}", headers=headers_viewer)
        assert t1_get.status_code == 200
        assert t1_get.json()["title"] == "Implement Auth System"
        assert len(t1_get.json()["labels"]) == 1

        # 12. Filter tasks by status and priority
        filter_status = await ac.get(f"/api/v1/projects/{proj_id}/tasks?status=IN_PROGRESS", headers=headers_viewer)
        assert filter_status.status_code == 200
        assert len(filter_status.json()) == 2

        filter_priority = await ac.get(f"/api/v1/projects/{proj_id}/tasks?priority=URGENT", headers=headers_viewer)
        assert filter_priority.status_code == 200
        assert len(filter_priority.json()) == 2

        filter_assignee = await ac.get(f"/api/v1/projects/{proj_id}/tasks?assignee_id={editor_id}", headers=headers_viewer)
        assert filter_assignee.status_code == 200
        assert len(filter_assignee.json()) == 1

        # 13. Remove Label from Task
        del_lbl_res = await ac.delete(f"/api/v1/tasks/{t1_id}/labels/{lbl1_id}", headers=headers_editor)
        assert del_lbl_res.status_code == 204

        t1_after_del_lbl = await ac.get(f"/api/v1/tasks/{t1_id}", headers=headers_viewer)
        assert len(t1_after_del_lbl.json()["labels"]) == 0

        # 14. Delete Label
        del_label = await ac.delete(f"/api/v1/labels/{lbl2_id}", headers=headers_editor)
        assert del_label.status_code == 204

        # 15. Delete Task
        del_task = await ac.delete(f"/api/v1/tasks/{t1_id}", headers=headers_editor)
        assert del_task.status_code == 204

        # Verify task is deleted
        task_404 = await ac.get(f"/api/v1/tasks/{t1_id}", headers=headers_viewer)
        assert task_404.status_code == 404
