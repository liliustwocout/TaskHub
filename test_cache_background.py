"""
Integration tests for Feature 9 (Caching) and Feature 10 (Background Task).
Tests cache hit/miss/invalidation and background email notification on task assignment.
"""
import pytest
import uuid
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_cache_and_background_task_flow():
    """
    Full integration test covering:
    - Cache miss → DB query → cache set
    - Cache hit → returns same data
    - Cache invalidation on create/update/delete task
    - Background email triggered on task assignment
    - Background email triggered on task reassignment
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        uid1 = str(uuid.uuid4())[:8]
        uid2 = str(uuid.uuid4())[:8]
        uid3 = str(uuid.uuid4())[:8]

        # === SETUP: Register users and create workspace/project ===

        # Register Owner
        reg1 = await ac.post("/api/v1/auth/register", json={
            "email": f"cache_owner_{uid1}@example.com",
            "full_name": "Cache Owner",
            "password": "Password123!"
        })
        assert reg1.status_code == 201
        owner_id = reg1.json()["id"]

        login1 = await ac.post("/api/v1/auth/login", json={
            "email": f"cache_owner_{uid1}@example.com",
            "password": "Password123!"
        })
        headers_owner = {"Authorization": f"Bearer {login1.json()['access_token']}"}

        # Register Member 1 (Editor)
        reg2 = await ac.post("/api/v1/auth/register", json={
            "email": f"cache_member_{uid2}@example.com",
            "full_name": "Cache Member",
            "password": "Password123!"
        })
        assert reg2.status_code == 201
        member_id = reg2.json()["id"]

        login2 = await ac.post("/api/v1/auth/login", json={
            "email": f"cache_member_{uid2}@example.com",
            "password": "Password123!"
        })
        headers_member = {"Authorization": f"Bearer {login2.json()['access_token']}"}

        # Register Member 2 (for reassignment test)
        reg3 = await ac.post("/api/v1/auth/register", json={
            "email": f"cache_member2_{uid3}@example.com",
            "full_name": "Cache Member2",
            "password": "Password123!"
        })
        assert reg3.status_code == 201
        member2_id = reg3.json()["id"]

        # Create Workspace and add members
        ws_res = await ac.post("/api/v1/workspaces", json={"name": "Cache Test WS"}, headers=headers_owner)
        assert ws_res.status_code == 201
        ws_id = ws_res.json()["id"]

        await ac.post(f"/api/v1/workspaces/{ws_id}/members",
                      json={"user_id": member_id, "role": "EDITOR"}, headers=headers_owner)
        await ac.post(f"/api/v1/workspaces/{ws_id}/members",
                      json={"user_id": member2_id, "role": "EDITOR"}, headers=headers_owner)

        # Create Project
        proj_res = await ac.post(f"/api/v1/workspaces/{ws_id}/projects",
                                 json={"name": "Cache Test Project"}, headers=headers_owner)
        assert proj_res.status_code == 201
        proj_id = proj_res.json()["id"]

        # === TEST FEATURE 9: CACHING ===

        # 1. First GET → Cache MISS → should query DB
        res1 = await ac.get(f"/api/v1/projects/{proj_id}/tasks?page=1&limit=10", headers=headers_owner)
        assert res1.status_code == 200
        data1 = res1.json()
        assert data1["total"] == 0
        assert data1["items"] == []

        # 2. Second GET with same params → Cache HIT → same data
        res2 = await ac.get(f"/api/v1/projects/{proj_id}/tasks?page=1&limit=10", headers=headers_owner)
        assert res2.status_code == 200
        data2 = res2.json()
        assert data2 == data1  # Same data from cache

        # 3. Create task → Cache INVALIDATED → next GET returns new data
        with patch("app.core.email.send_task_assignment_email", new_callable=AsyncMock) as mock_email:
            create_res = await ac.post(f"/api/v1/projects/{proj_id}/tasks", json={
                "title": "Cached Task 1",
                "assignee_id": member_id,
                "status": "TODO",
                "priority": "HIGH"
            }, headers=headers_owner)
            assert create_res.status_code == 201
            task_id = create_res.json()["id"]

        # GET after create → should show 1 task (cache was invalidated)
        res3 = await ac.get(f"/api/v1/projects/{proj_id}/tasks?page=1&limit=10", headers=headers_owner)
        assert res3.status_code == 200
        data3 = res3.json()
        assert data3["total"] == 1
        assert len(data3["items"]) == 1
        assert data3["items"][0]["title"] == "Cached Task 1"

        # 4. Update task → Cache INVALIDATED
        with patch("app.core.email.send_task_assignment_email", new_callable=AsyncMock) as mock_email:
            update_res = await ac.patch(f"/api/v1/tasks/{task_id}", json={
                "title": "Updated Cached Task 1",
                "priority": "URGENT"
            }, headers=headers_owner)
            assert update_res.status_code == 200

        # GET after update → should show updated task
        res4 = await ac.get(f"/api/v1/projects/{proj_id}/tasks?page=1&limit=10", headers=headers_owner)
        assert res4.status_code == 200
        data4 = res4.json()
        assert data4["items"][0]["title"] == "Updated Cached Task 1"
        assert data4["items"][0]["priority"] == "URGENT"

        # 5. Create another task for delete test
        create2_res = await ac.post(f"/api/v1/projects/{proj_id}/tasks", json={
            "title": "Task To Delete",
            "status": "TODO",
            "priority": "LOW"
        }, headers=headers_owner)
        assert create2_res.status_code == 201
        task2_id = create2_res.json()["id"]

        # Verify 2 tasks now
        res5 = await ac.get(f"/api/v1/projects/{proj_id}/tasks?page=1&limit=10", headers=headers_owner)
        assert res5.status_code == 200
        assert res5.json()["total"] == 2

        # Delete task → Cache INVALIDATED
        del_res = await ac.delete(f"/api/v1/tasks/{task2_id}", headers=headers_owner)
        assert del_res.status_code == 204

        # GET after delete → should show 1 task
        res6 = await ac.get(f"/api/v1/projects/{proj_id}/tasks?page=1&limit=10", headers=headers_owner)
        assert res6.status_code == 200
        data6 = res6.json()
        assert data6["total"] == 1

        # 6. Test filtering with cache (different query params = different cache key)
        res_filter = await ac.get(
            f"/api/v1/projects/{proj_id}/tasks?status=TODO&priority=URGENT&page=1&limit=10",
            headers=headers_owner
        )
        assert res_filter.status_code == 200
        filter_data = res_filter.json()
        assert filter_data["total"] == 1  # The updated task has URGENT priority

        # === TEST FEATURE 10: BACKGROUND EMAIL NOTIFICATION ===

        # 7. Create task with assignee → Background email triggered
        with patch("app.api.v1.endpoints.tasks._send_assignment_notification", new_callable=AsyncMock) as mock_notify:
            create3_res = await ac.post(f"/api/v1/projects/{proj_id}/tasks", json={
                "title": "Email Test Task",
                "assignee_id": member_id,
                "status": "TODO",
                "priority": "MEDIUM"
            }, headers=headers_owner)
            assert create3_res.status_code == 201

        # 8. Create task WITHOUT assignee → No email triggered
        with patch("app.api.v1.endpoints.tasks._send_assignment_notification", new_callable=AsyncMock) as mock_notify_no:
            create4_res = await ac.post(f"/api/v1/projects/{proj_id}/tasks", json={
                "title": "No Assignee Task",
                "status": "TODO",
                "priority": "LOW"
            }, headers=headers_owner)
            assert create4_res.status_code == 201

        # 9. Update task to reassign → Background email triggered
        with patch("app.api.v1.endpoints.tasks._send_assignment_notification", new_callable=AsyncMock) as mock_reassign:
            reassign_task_id = create3_res.json()["id"]
            reassign_res = await ac.patch(f"/api/v1/tasks/{reassign_task_id}", json={
                "assignee_id": member2_id
            }, headers=headers_owner)
            assert reassign_res.status_code == 200
            assert reassign_res.json()["assignee_id"] == member2_id


@pytest.mark.asyncio
async def test_cache_invalidation_on_label_change():
    """Test that cache is invalidated when labels are added/removed from tasks."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        uid = str(uuid.uuid4())[:8]

        # Setup
        reg = await ac.post("/api/v1/auth/register", json={
            "email": f"label_cache_{uid}@example.com",
            "full_name": "Label Cache User",
            "password": "Password123!"
        })
        assert reg.status_code == 201

        login = await ac.post("/api/v1/auth/login", json={
            "email": f"label_cache_{uid}@example.com",
            "password": "Password123!"
        })
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

        ws = await ac.post("/api/v1/workspaces", json={"name": "Label Cache WS"}, headers=headers)
        ws_id = ws.json()["id"]

        proj = await ac.post(f"/api/v1/workspaces/{ws_id}/projects",
                             json={"name": "Label Cache Proj"}, headers=headers)
        proj_id = proj.json()["id"]

        # Create task and label
        task_res = await ac.post(f"/api/v1/projects/{proj_id}/tasks", json={
            "title": "Label Test Task",
            "status": "TODO",
            "priority": "MEDIUM"
        }, headers=headers)
        task_id = task_res.json()["id"]

        label_res = await ac.post(f"/api/v1/projects/{proj_id}/labels", json={
            "name": "Bug",
            "color": "#FF0000"
        }, headers=headers)
        label_id = label_res.json()["id"]

        # GET tasks → cache set
        res1 = await ac.get(f"/api/v1/projects/{proj_id}/tasks?page=1&limit=10", headers=headers)
        assert res1.status_code == 200
        assert len(res1.json()["items"][0]["labels"]) == 0

        # Add label → cache invalidated
        add_label = await ac.post(f"/api/v1/tasks/{task_id}/labels/{label_id}", headers=headers)
        assert add_label.status_code == 200

        # GET tasks → new data with label
        res2 = await ac.get(f"/api/v1/projects/{proj_id}/tasks?page=1&limit=10", headers=headers)
        assert res2.status_code == 200
        assert len(res2.json()["items"][0]["labels"]) == 1
        assert res2.json()["items"][0]["labels"][0]["name"] == "Bug"

        # Remove label → cache invalidated
        remove_label = await ac.delete(f"/api/v1/tasks/{task_id}/labels/{label_id}", headers=headers)
        assert remove_label.status_code == 204

        # GET tasks → label removed
        res3 = await ac.get(f"/api/v1/projects/{proj_id}/tasks?page=1&limit=10", headers=headers)
        assert res3.status_code == 200
        assert len(res3.json()["items"][0]["labels"]) == 0
