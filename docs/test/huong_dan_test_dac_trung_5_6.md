# Hướng dẫn Test Đặc trưng 5 & 6 (Task & Label)

> Server đang chạy tại **http://localhost:8000**

## Mở Swagger UI

Truy cập: **http://localhost:8000/docs**

---

## Điều kiện tiền đề

- Có Workspace (`id = 1`) và Project (`id = 2`).
- Có 3 user đại diện cho 3 role: **Owner**, **Editor**, và **Viewer** trong Workspace.

---

## Feature 6 — Label (Gán nhãn)

### Test 6.1: Tạo Label trong Project (OWNER / EDITOR) - Thành công

**POST `/api/v1/projects/{project_id}/labels`** → `project_id = 2`:

```json
{
  "name": "Backend",
  "color": "#FF0000"
}
```

→ Kỳ vọng: `201 Created`
```json
{
  "id": 1,
  "project_id": 2,
  "name": "Backend",
  "color": "#FF0000"
}
```

---

### Test 6.2: Xem danh sách Label trong Project - Thành công

**GET `/api/v1/projects/{project_id}/labels`** → `project_id = 2`

→ Kỳ vọng: `200 OK`, mảng chứa các label của project.

---

### Test 6.3: Cập nhật Label - Thành công

**PATCH `/api/v1/labels/{label_id}`** → `label_id = 1`:

```json
{
  "name": "Core Backend",
  "color": "#00FF00"
}
```

→ Kỳ vọng: `200 OK`, `name` đổi thành `"Core Backend"`.

---

## Feature 5 — Task (Công việc)

### Test 5.1: Tạo Task trong Project (EDITOR) - Thành công

Dùng token **Member** (role EDITOR):

**POST `/api/v1/projects/{project_id}/tasks`** → `project_id = 2`:

```json
{
  "title": "Xây dựng Module Auth",
  "description": "Cần hoàn thiện endpoint register, login, refresh token",
  "assignee_id": 2,
  "status": "TODO",
  "priority": "HIGH"
}
```

→ Kỳ vọng: `201 Created`
```json
{
  "id": 1,
  "project_id": 2,
  "assignee_id": 2,
  "title": "Xây dựng Module Auth",
  "description": "Cần hoàn thiện endpoint register, login, refresh token",
  "status": "TODO",
  "priority": "HIGH",
  "due_date": null,
  "created_by": 2,
  "created_at": "...",
  "labels": []
}
```

---

### Test 5.2: Gán Label cho Task - Thành công

**POST `/api/v1/tasks/{task_id}/labels/{label_id}`** → `task_id = 1`, `label_id = 1`

→ Kỳ vọng: `200 OK`, mảng `labels` trong task có chứa label `Core Backend`.

---

### Test 5.3: Cập nhật Task (Chuyển Status & Priority) - Thành công

**PATCH `/api/v1/tasks/{task_id}`** → `task_id = 1`:

```json
{
  "status": "IN_PROGRESS",
  "priority": "URGENT"
}
```

→ Kỳ vọng: `200 OK`, `status = "IN_PROGRESS"`, `priority = "URGENT"`.

---

### Test 5.4: VIEWER không tạo được Task / Label - Thất bại

Chuyển sang token **Viewer**:

**POST `/api/v1/projects/2/tasks`**:

```json
{
  "title": "Viewer task should fail"
}
```

→ Kỳ vọng: `403 Forbidden` — *"Only OWNER or EDITOR can create tasks in this project"*.

---

### Test 5.5: Bỏ Label khỏi Task - Thành công

Chuyển token **Editor**:

**DELETE `/api/v1/tasks/{task_id}/labels/{label_id}`** → `task_id = 1`, `label_id = 1`

→ Kỳ vọng: `204 No Content`.

---

### Test 5.6: Xóa Task - Thành công

**DELETE `/api/v1/tasks/{task_id}`** → `task_id = 1`

→ Kỳ vọng: `204 No Content`.

---

### Test 6.4: Xóa Label - Thành công

**DELETE `/api/v1/labels/{label_id}`** → `label_id = 1`

→ Kỳ vọng: `204 No Content`.
