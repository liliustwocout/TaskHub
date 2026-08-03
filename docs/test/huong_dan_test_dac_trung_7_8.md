# Hướng dẫn Test Đặc trưng 7 & 8 (Comment & Filtering/Pagination)

> Server đang chạy tại **http://localhost:8000**

## Mở Swagger UI

Truy cập: **http://localhost:8000/docs**

---

## Điều kiện tiền đề

- Đã tạo Workspace và Project (`project_id = 1` hoặc `2`).
- Đã tạo ít nhất 1-3 Task với trạng thái và ưu tiên khác nhau trong project (vd: Task 1: status `TODO`, priority `HIGH`; Task 2: status `IN_PROGRESS`, priority `LOW`).
- Token của user là thành viên Workspace (Owner/Editor/Viewer).

---

## Feature 7 — Comment (Bình luận trên Task)

### Test 7.1: Thêm Comment vào Task - Thành công

**POST `/api/v1/tasks/{task_id}/comments`** → `task_id = 1`:

```json
{
  "content": "Tôi đang tiến hành làm module này, dự kiến xong vào cuối ngày."
}
```

→ Kỳ vọng: `201 Created`
```json
{
  "id": 1,
  "task_id": 1,
  "author_id": 2,
  "content": "Tôi đang tiến hành làm module này, dự kiến xong vào cuối ngày.",
  "created_at": "...",
  "author": {
    "id": 2,
    "email": "member@test.com",
    "full_name": "Member User"
  }
}
```

---

### Test 7.2: Xem danh sách Comment của Task - Thành công

**GET `/api/v1/tasks/{task_id}/comments`** → `task_id = 1`

→ Kỳ vọng: `200 OK`, mảng chứa danh sách comment của task theo thứ tự thời gian.

---

### Test 7.3: Xóa Comment của chính mình (Tác giả / Owner) - Thành công

**DELETE `/api/v1/comments/{comment_id}`** → `comment_id = 1`

→ Kỳ vọng: `204 No Content`.

---

### Test 7.4: User khác không được xóa Comment của người khác - Thất bại

1. User A (id = 2) tạo comment `comment_id = 2`.
2. Đăng nhập User B (không phải tác giả comment và không phải Workspace Owner).
3. Gọi **DELETE `/api/v1/comments/2`**.

→ Kỳ vọng: `403 Forbidden` — *"Only author or workspace owner can delete this comment"*.

---

## Feature 8 — Filtering & Pagination (Lọc & Phân trang Task)

### Test 8.1: Lọc Task theo Status - Thành công

**GET `/api/v1/projects/{project_id}/tasks?status=TODO`** → `project_id = 1`

→ Kỳ vọng: `200 OK`, chỉ các task có `status = "TODO"` được trả về.

---

### Test 8.2: Lọc Task theo Priority - Thành công

**GET `/api/v1/projects/{project_id}/tasks?priority=HIGH`** → `project_id = 1`

→ Kỳ vọng: `200 OK`, chỉ các task có `priority = "HIGH"` được trả về.

---

### Test 8.3: Lọc Task theo Assignee - Thành công

**GET `/api/v1/projects/{project_id}/tasks?assignee_id=2`** → `project_id = 1`

→ Kỳ vọng: `200 OK`, chỉ các task được giao cho user có `id = 2`.

---

### Test 8.4: Kết hợp nhiều bộ lọc (Status + Priority + Assignee) - Thành công

**GET `/api/v1/projects/{project_id}/tasks?status=IN_PROGRESS&priority=URGENT&assignee_id=2`**

→ Kỳ vọng: `200 OK`, trả về các task thỏa mãn **đồng thời** cả 3 điều kiện.

---

### Test 8.5: Phân trang Task (Page & Limit) - Thành công

**GET `/api/v1/projects/{project_id}/tasks?page=1&limit=2`** → `project_id = 1`

→ Kỳ vọng: `200 OK`, cấu trúc response có phân trang:

```json
{
  "items": [
    ...
  ],
  "total": 5,
  "page": 1,
  "limit": 2,
  "total_pages": 3
}
```

Kiểm tra trang tiếp theo bằng cách đổi query: `page=2&limit=2`.
