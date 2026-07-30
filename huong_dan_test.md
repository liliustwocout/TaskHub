# 🧪 Hướng dẫn Test Feature 3 (Workspace) & Feature 4 (Project)

> Server đang chạy tại **http://localhost:8000**

## Mở Swagger UI

Truy cập: **http://localhost:8000/docs**

---

## Bước 0 — Tạo 2 tài khoản test

Cần 2 user để test phân quyền: **Owner** và **Member**.

### 0.1 Đăng ký Owner

Mở **POST `/api/v1/auth/register`** → **Try it out** → nhập:

```json
{
  "email": "owner@test.com",
  "full_name": "Owner User",
  "password": "Password123!"
}
```

→ **Execute** → Kỳ vọng: `201 Created`, ghi nhớ `"id"` trả về (ví dụ `id = 1`).

### 0.2 Đăng ký Member

Gọi lại **POST `/api/v1/auth/register`** với:

```json
{
  "email": "member@test.com",
  "full_name": "Member User",
  "password": "Password123!"
}
```

→ Ghi nhớ `"id"` (ví dụ `id = 2`). **Giá trị id này sẽ dùng ở bước invite member.**

### 0.3 Đăng nhập Owner

Gọi **POST `/api/v1/auth/login`** với:

```json
{
  "email": "owner@test.com",
  "password": "Password123!"
}
```

→ Copy giá trị `"access_token"` từ response.

### 0.4 Gắn token vào Swagger

1. Kéo lên đầu trang Swagger, bấm nút **🔓 Authorize** (góc phải trên).
2. Nhập vào ô **Value**: `Bearer <access_token_vừa_copy>`  
   *(Ví dụ: `Bearer eyJhbGciOiJIUzI1NiIs...`)*
3. Bấm **Authorize** → **Close**.

> [!IMPORTANT]
> Từ giờ mọi request đều gửi kèm token của Owner. Khi cần chuyển sang Member, bạn logout rồi login lại bằng tài khoản member.

---

## Feature 3 — Workspace

### Test 3.1: Tạo Workspace ✅

**POST `/api/v1/workspaces`** → Try it out:

```json
{
  "name": "Engineering Team"
}
```

→ Kỳ vọng: `201 Created`

```json
{
  "id": 1,
  "name": "Engineering Team",
  "owner_id": 1,
  "created_at": "...",
  "my_role": "OWNER"
}
```

→ Ghi nhớ `workspace id = 1`.

---

### Test 3.2: Xem danh sách Workspace ✅

**GET `/api/v1/workspaces`** → Execute

→ Kỳ vọng: `200 OK`, mảng chứa 1 workspace, `my_role = "OWNER"`.

---

### Test 3.3: Xem chi tiết Workspace ✅

**GET `/api/v1/workspaces/{workspace_id}`** → nhập `workspace_id = 1`

→ Kỳ vọng: `200 OK` với thông tin workspace.

---

### Test 3.4: Cập nhật Workspace (OWNER only) ✅

**PATCH `/api/v1/workspaces/{workspace_id}`** → `workspace_id = 1`:

```json
{
  "name": "Engineering Team v2"
}
```

→ Kỳ vọng: `200 OK`, `name` đã đổi thành `"Engineering Team v2"`.

---

### Test 3.5: Invite Member vào Workspace ✅

**POST `/api/v1/workspaces/{workspace_id}/members`** → `workspace_id = 1`:

```json
{
  "user_id": 2,
  "role": "EDITOR"
}
```

→ Kỳ vọng: `201 Created`

```json
{
  "id": 2,
  "workspace_id": 1,
  "user_id": 2,
  "role": "EDITOR",
  "created_at": "...",
  "user": {
    "id": 2,
    "email": "member@test.com",
    "full_name": "Member User",
    ...
  }
}
```

---

### Test 3.6: Xem danh sách Members ✅

**GET `/api/v1/workspaces/{workspace_id}/members`** → `workspace_id = 1`

→ Kỳ vọng: `200 OK`, mảng 2 members (OWNER + EDITOR).

---

### Test 3.7: Test phân quyền — Member không được invite ❌

1. Bấm **🔓 Authorize** → **Logout**.
2. Login lại bằng tài khoản **member@test.com**.
3. Copy token mới → Authorize lại.
4. Thử **POST `/api/v1/workspaces/1/members`** với bất kỳ body nào.

→ Kỳ vọng: `403 Forbidden` — *"Only workspace owner can invite members"*.

---

### Test 3.8: Test phân quyền — Member không được xóa workspace ❌

Vẫn dùng token của Member:

**DELETE `/api/v1/workspaces/{workspace_id}`** → `workspace_id = 1`

→ Kỳ vọng: `403 Forbidden` — *"Only workspace owner can delete workspace"*.

---

### Test 3.9: Xóa Member khỏi Workspace ✅

Chuyển lại token **Owner** (login lại owner@test.com).

**DELETE `/api/v1/workspaces/{workspace_id}/members/{user_id}`** → `workspace_id = 1`, `user_id = 2`

→ Kỳ vọng: `204 No Content`.

Kiểm tra lại members → chỉ còn 1 member (Owner).

---

## Feature 4 — Project

> [!NOTE]
> Trước khi test, invite lại member@test.com vào workspace với role EDITOR (lặp lại bước 3.5).

### Test 4.1: Tạo Project trong Workspace (OWNER) ✅

**POST `/api/v1/workspaces/{workspace_id}/projects`** → `workspace_id = 1`:

```json
{
  "name": "TaskHub API",
  "description": "Backend REST API cho hệ thống quản lý công việc"
}
```

→ Kỳ vọng: `201 Created`

```json
{
  "id": 1,
  "workspace_id": 1,
  "name": "TaskHub API",
  "description": "Backend REST API cho hệ thống quản lý công việc",
  "status": "ACTIVE",
  "created_at": "..."
}
```

---

### Test 4.2: EDITOR cũng tạo được Project ✅

Chuyển sang token **Member** (EDITOR).

**POST `/api/v1/workspaces/1/projects`**:

```json
{
  "name": "TaskHub Frontend",
  "description": "React dashboard"
}
```

→ Kỳ vọng: `201 Created` — EDITOR có quyền tạo project.

---

### Test 4.3: Danh sách Projects trong Workspace ✅

**GET `/api/v1/workspaces/{workspace_id}/projects`** → `workspace_id = 1`

→ Kỳ vọng: `200 OK`, mảng 2 projects.

---

### Test 4.4: Chi tiết Project ✅

**GET `/api/v1/projects/{project_id}`** → `project_id = 1`

→ Kỳ vọng: `200 OK` với thông tin project.

---

### Test 4.5: Cập nhật Project (EDITOR) ✅

Vẫn dùng token Member (EDITOR):

**PATCH `/api/v1/projects/{project_id}`** → `project_id = 2`:

```json
{
  "name": "TaskHub Web App",
  "description": "Next.js dashboard"
}
```

→ Kỳ vọng: `200 OK`, name và description đã cập nhật.

---

### Test 4.6: Archive Project ✅

**PATCH `/api/v1/projects/{project_id}`** → `project_id = 2`:

```json
{
  "status": "ARCHIVED"
}
```

→ Kỳ vọng: `200 OK`, `status = "ARCHIVED"`.

---

### Test 4.7: EDITOR không được xóa Project ❌

Vẫn dùng token Member (EDITOR):

**DELETE `/api/v1/projects/{project_id}`** → `project_id = 1`

→ Kỳ vọng: `403 Forbidden` — *"Only workspace OWNER can delete projects"*.

---

### Test 4.8: OWNER xóa Project ✅

Chuyển sang token **Owner**:

**DELETE `/api/v1/projects/{project_id}`** → `project_id = 1`

→ Kỳ vọng: `204 No Content`.

---

### Test 4.9: VIEWER không tạo/sửa được Project ❌

1. Xóa member hiện tại: **DELETE `/api/v1/workspaces/1/members/2`**
2. Invite lại với role VIEWER:

```json
{
  "user_id": 2,
  "role": "VIEWER"
}
```

3. Chuyển sang token **Member** (giờ là VIEWER).
4. Thử **POST `/api/v1/workspaces/1/projects`**:

```json
{
  "name": "Should Fail"
}
```

→ Kỳ vọng: `403 Forbidden` — *"Only OWNER or EDITOR can create projects"*.

---

## Tóm tắt Ma trận Test

| # | Test Case                              | User  | Kỳ vọng          |
|---|----------------------------------------|-------|-------------------|
| 1 | Tạo workspace                          | Owner | `201 Created`     |
| 2 | Xem danh sách workspace                | Owner | `200 OK`          |
| 3 | Xem chi tiết workspace                 | Owner | `200 OK`          |
| 4 | Cập nhật workspace                     | Owner | `200 OK`          |
| 5 | Invite member (EDITOR)                 | Owner | `201 Created`     |
| 6 | Xem danh sách members                  | Owner | `200 OK` (2 items)|
| 7 | Member invite thêm người               | Member| `403 Forbidden`   |
| 8 | Member xóa workspace                   | Member| `403 Forbidden`   |
| 9 | Xóa member khỏi workspace             | Owner | `204 No Content`  |
| 10| Tạo project (Owner)                    | Owner | `201 Created`     |
| 11| Tạo project (Editor)                   | Member| `201 Created`     |
| 12| Danh sách projects                     | Any   | `200 OK`          |
| 13| Chi tiết project                       | Any   | `200 OK`          |
| 14| Update project (Editor)                | Member| `200 OK`          |
| 15| Archive project                        | Member| `200 OK`          |
| 16| Editor xóa project                     | Member| `403 Forbidden`   |
| 17| Owner xóa project                      | Owner | `204 No Content`  |
| 18| Viewer tạo project                     | Member| `403 Forbidden`   |
