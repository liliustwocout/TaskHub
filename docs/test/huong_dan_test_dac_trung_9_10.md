# Hướng dẫn Test Đặc trưng 9 & 10 (Redis Caching & Background Task Email)

> Server đang chạy tại **http://localhost:8000**
> Swagger UI: **http://localhost:8000/docs**

---

## Giải thích về lỗi kết nối Docker Desktop (Nếu gặp phải)

Nếu bạn chạy lệnh `docker run` hoặc `docker exec` trong terminal và thấy thông báo:
> `failed to connect to the docker API at npipe:////./pipe/dockerDesktopLinuxEngine...` hoặc `request returned 500 Internal Server Error`

**Nguyên nhân:**Ứng dụng **Docker Desktop trên Windows chưa được khởi động** hoặc engine Linux của Docker đang trong quá trình khởi động lại.

**Cách khắc phục:**
1. Mở ứng dụng **Docker Desktop** từ menu Start của Windows.
2. Chờ biểu tượng con cá voi ở thanh Taskbar góc dưới bên phải chuyển sang màu **xanh lá sáng** (Docker Engine is running).
3. Nếu Docker Desktop bị kẹt hoặc báo lỗi 500, nhấp chuột phải vào biểu tượng Docker ở Taskbar -> chọn **Restart Docker Desktop**.

> 💡 **Lưu ý:** Ngay cả khi chưa khởi chạy Redis/Docker Desktop, các API của TaskHub vẫn hoạt động bình thường nhờ cơ chế **Graceful Degradation** (Fail-safe): Caching & Email gửi bị ngắt mượt mà và ghi log warning thay vì làm crash API response!

---

## Điều kiện tiền đề để test

1. Đã đăng nhập trên Swagger UI (`/docs`) bằng cách bấm nút **Authorize** và nhập Token.
2. Đã có **Workspace** và **Project** (`project_id = 1`).
3. Đã có tài khoản phụ (ví dụ: `member@test.com`, `user_id = 2`) nằm trong cùng Workspace để test giao task.

---

## Feature 9 — Redis Caching (GET /projects/{id}/tasks)

### Test 9.1: Kiểm tra Cache Hit & Miss khi lấy danh sách Task

1. Mở Swagger UI tại endpoint: **`GET /api/v1/projects/{project_id}/tasks`**.
2. Nhập `project_id = 1`, bấm **Execute**.
   - **Lần 1 (Cache MISS):** Hệ thống sẽ truy vấn trực tiếp từ cơ sở dữ liệu PostgreSQL, sau đó tự động lưu kết quả vào Redis với TTL 300 giây (5 phút).
   - Kiểm tra log terminal chạy uvicorn: Bạn sẽ thấy dòng log `Cache MISS for project 1` và tiếp theo là `Cache SET for project 1 (TTL=300s)`.
3. Bấm **Execute** lại một lần nữa với cùng tham số:
   - **Lần 2 (Cache HIT):** Dữ liệu được trả về tức thì từ Redis mà không cần query lại DB.
   - Log terminal hiển thị: `Cache HIT for project 1`.

---

### Test 9.2: Tự động Invalidate (xóa) Cache khi Tạo/Sửa/Xóa Task hoặc Label

1. Gọi **`POST /api/v1/projects/1/tasks`** để tạo task mới (hoặc `PATCH` / `DELETE` task cũ).
2. Log terminal sẽ thông báo: `Cache INVALIDATED ... keys for project 1`.
3. Gọi lại **`GET /api/v1/projects/1/tasks`**:
   - Hệ thống thông báo `Cache MISS for project 1`, sau đó query DB để lấy dữ liệu mới nhất (bao gồm task vừa tạo/sửa) và lưu lại vào Cache.

---

## Feature 10 — Background Task (Email Notification khi Assign Task)

### Cấu hình Gmail SMTP (Cần thiết nếu muốn nhận Email thật)

Cập nhật file `.env` ở thư mục gốc project:

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=email_cua_ban@gmail.com
SMTP_PASSWORD=mat_khau_ung_dung_16_ky_tu
SMTP_FROM=email_cua_ban@gmail.com
SMTP_TLS=true
```

*(Xem chi tiết cách tạo Mật khẩu ứng dụng Gmail 16 ký tự trong file `README.md`)*

---

### Test 10.1: Gửi Email Notification khi Gán Task Mới (Create Task)

1. Mở Swagger UI endpoint: **`POST /api/v1/projects/{project_id}/tasks`** (`project_id = 1`).
2. Nhập request body có gán `assignee_id`:

```json
{
  "title": "Nghiên cứu Redis Cache & Celery",
  "description": "Task được gán tự động để test tính năng gửi Email background",
  "assignee_id": 2,
  "status": "TODO",
  "priority": "HIGH"
}
```

3. Bấm **Execute**.
   - **Kỳ vọng Response:** Trả về HTTP `201 Created` ngay lập tức (không bị kẹt hay giật lag chờ gửi email).
   - **Background Process:** Tác vụ gửi email được đẩy vào chạy ngầm (`BackgroundTasks`).
   - **Kết quả:** Thành viên có `id = 2` sẽ nhận được 1 Email thông báo giao task từ TaskHub vào hộp thư (Inbox/Spam). Nếu chưa điền SMTP, terminal sẽ log `SMTP not configured. Skipping email...` mà API vẫn trả về `201 Created` thành công.

---

### Test 10.2: Gửi Email Notification khi Chuyển Assignee (Update Task)

1. Mở Swagger UI endpoint: **`PATCH /api/v1/tasks/{task_id}`** (`task_id = 1`).
2. Thay đổi người thực hiện task sang member khác (`assignee_id = 3`):

```json
{
  "assignee_id": 3
}
```

3. Bấm **Execute**.
   - **Kỳ vọng Response:** HTTP `200 OK`.
   - **Background Process:** Hệ thống phát hiện `assignee_id` bị thay đổi so với ban đầu và tự động kích hoạt gửi Email thông báo tới người nhận mới (`id = 3`).
