# TaskHub — Task Management API

**TaskHub** là hệ thống quản lý công việc (Task Management) được xây dựng trên nền tảng **FastAPI**, hỗ trợ làm việc nhóm thông qua Workspace, Project và Task với hệ thống phân quyền RBAC hoàn chỉnh.

---

## Mục lục

- [Tính năng](#tính-năng)
- [Tech Stack](#tech-stack)
- [Cấu trúc dự án](#cấu-trúc-dự-án)
- [Cài đặt & Chạy](#cài-đặt--chạy)
- [Biến môi trường](#biến-môi-trường)
- [Hướng dẫn cấu hình Redis](#hướng-dẫn-cấu-hình-redis)
- [Hướng dẫn cấu hình Gmail SMTP](#hướng-dẫn-cấu-hình-gmail-smtp)
- [Cache Strategy](#cache-strategy)
- [Background Email Notification](#background-email-notification)
- [API Endpoints](#api-endpoints)
- [Phân quyền (RBAC)](#phân-quyền-rbac)
- [Database Schema](#database-schema)
- [Testing](#testing)

---

## Tính năng

| #  | Module        | Mô tả                                                                 | Trạng thái |
|----|---------------|------------------------------------------------------------------------|:----------:|
| 1  | **Auth**      | Register, Login (JWT access + refresh token), Logout (revoke token)    | Thành công |
| 2  | **User**      | Get profile, Update profile (PATCH), Change password                   | Thành công |
| 3  | **Workspace** | CRUD workspace, Invite/Remove member, Phân quyền theo role             | Thành công |
| 4  | **Project**   | CRUD trong workspace, Archive project                                  | Thành công |
| 5  | **Task**      | CRUD trong project, Assign, Chuyển status, Priority & due_date         | Thành công |
| 6  | **Label**     | CRUD per project, Gán/bỏ label cho task                                | Thành công |
| 7  | **Comment**   | Thêm/xóa comment trên task                                            | Thành công |
| 8  | **Filter & Page** | Lọc task theo status, priority, assignee; pagination               | Thành công |
| 9  | **Caching**   | Cache GET tasks với Redis, invalidate khi có thay đổi                  | Thành công |
| 10 | **Background**| Gửi email notification khi được assign task (Gmail SMTP)               | Thành công |
| 11 | **RBAC**      | Phân quyền ADMIN / OWNER / EDITOR / VIEWER theo resource               | Thành công |
| 12 | **Swagger/ReDoc** | Đầy đủ docs, Bearer auth scheme                                   | Thành công |
| 13 | **Docker**    | `docker compose up` chạy toàn bộ stack                                 | Thành công |

---

## Tech Stack

| Thành phần     | Công nghệ                        |
|----------------|----------------------------------|
| Framework      | FastAPI 0.140+                   |
| ORM            | SQLAlchemy 2.x (async)           |
| Migration      | Alembic                          |
| Validation     | Pydantic v2                      |
| Auth           | JWT (PyJWT) — Access + Refresh   |
| Database       | PostgreSQL 16                    |
| Cache / Revoke | Redis 7                          |
| Email          | aiosmtplib (Gmail SMTP)          |
| Container      | Docker & Docker Compose          |
| Language       | Python 3.11+                     |

---

## Cấu trúc dự án

```
TaskHub/
├── app/
│   ├── main.py                    # FastAPI application entry point
│   ├── core/
│   │   ├── config.py              # Pydantic Settings (env)
│   │   ├── database.py            # SQLAlchemy async engine & session
│   │   ├── redis.py               # Redis async client
│   │   ├── cache.py               # Redis cache layer (get/set/invalidate)
│   │   ├── email.py               # Email notification service (Gmail SMTP)
│   │   └── security.py            # JWT encode/decode, password hashing
│   ├── models/
│   │   ├── __init__.py            # Export all models
│   │   ├── user.py                # User model (ADMIN/MEMBER)
│   │   ├── workspace.py           # Workspace + WorkspaceMember models
│   │   ├── project.py             # Project model (ACTIVE/ARCHIVED)
│   │   ├── label.py               # Label model
│   │   ├── task.py                # Task model + task_labels
│   │   └── comment.py             # Comment model
│   ├── schemas/
│   │   ├── __init__.py            # Export all schemas
│   │   ├── auth.py                # Token, LoginRequest, RefreshTokenRequest
│   │   ├── user.py                # UserCreate, UserUpdate, UserResponse
│   │   ├── workspace.py           # WorkspaceCreate/Update/Response, MemberAdd
│   │   ├── project.py             # ProjectCreate, ProjectUpdate, ProjectResponse
│   │   ├── label.py               # LabelCreate, LabelUpdate, LabelResponse
│   │   ├── task.py                # TaskCreate, TaskUpdate, TaskResponse
│   │   └── comment.py             # CommentCreate, CommentResponse
│   └── api/
│       └── v1/
│           ├── router.py          # API router aggregation
│           ├── deps.py            # Dependencies (get_current_user, OAuth2)
│           └── endpoints/
│               ├── auth.py        # Register, Login, Refresh, Logout
│               ├── users.py       # Profile, Update, Change password
│               ├── workspaces.py  # Workspace CRUD + Member management
│               ├── projects.py    # Project CRUD + Archive
│               ├── labels.py      # Label CRUD
│               ├── tasks.py       # Task CRUD + Filter + Cache + Email
│               └── comments.py    # Comment CRUD
├── alembic/                       # Database migrations
├── alembic.ini
├── docker-compose.yml             # PostgreSQL 16 + Redis 7 + App
├── Dockerfile
├── requirements.txt
├── .env.example
├── conftest.py                    # Pytest config (async event loop)
├── pytest.ini
├── test_auth_user.py              # Auth & User integration tests
├── test_workspace_project.py      # Workspace & Project integration tests
├── test_task_label.py             # Task & Label integration tests
├── test_comment_pagination.py     # Comment & Pagination integration tests
└── test_cache_background.py       # Cache & Background Task integration tests
```

---

## Cài đặt & Chạy

### Cách 1: Docker Compose (Khuyến nghị)

```bash
# Clone project
git clone https://github.com/<your-username>/TaskHub.git
cd TaskHub

# Tạo file .env từ template
cp .env.example .env

# Khởi chạy toàn bộ stack
docker compose up --build
```

API sẽ chạy tại: **http://localhost:8000**

### Cách 2: Chạy local (Development)

**Yêu cầu:** PostgreSQL 16 và Redis 7 đã chạy sẵn trên máy.

```bash
# Tạo virtual environment
python -m venv venv

# Kích hoạt venv
# Windows:
.\venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Cài đặt dependencies
pip install -r requirements.txt

# Tạo file .env
cp .env.example .env
# Chỉnh sửa DATABASE_URL và REDIS_URL cho phù hợp

# Chạy server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Truy cập API Docs

| Tài liệu    | URL                              |
|--------------|----------------------------------|
| Swagger UI   | http://localhost:8000/docs       |
| ReDoc        | http://localhost:8000/redoc      |
| OpenAPI JSON | http://localhost:8000/api/v1/openapi.json |

---

## Biến môi trường

Tạo file `.env` tại thư mục gốc dự án (tham khảo `.env.example`):

```env
PROJECT_NAME=TaskHub
API_V1_STR=/api/v1
SECRET_KEY=supersecretkey_change_me_in_production_123456789
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/taskhub_db
REDIS_URL=redis://localhost:6379/0

# SMTP Settings (Gmail)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_16_char_app_password
SMTP_FROM=your_email@gmail.com
SMTP_TLS=true

# Cache TTL (seconds)
CACHE_TTL_SECONDS=300
```

> **Lưu ý:** Thay đổi `SECRET_KEY` trước khi deploy lên production.

---

## Hướng dẫn cấu hình Redis

Redis được sử dụng cho 2 mục đích: **cache task listing** và **revoke refresh token**.

### Cài đặt Redis trên Windows

**Cách 1: Dùng Docker (Khuyến nghị)**

```bash
# Chạy Redis container
docker run -d --name redis -p 6379:6379 redis:7-alpine

# Kiểm tra Redis đã chạy
docker exec -it redis redis-cli ping
# Kết quả: PONG
```

**Cách 2: Dùng Memurai (Redis alternative cho Windows)**

1. Tải Memurai từ: https://www.memurai.com/get-memurai
2. Cài đặt và chạy theo hướng dẫn
3. Memurai chạy mặc định trên port 6379

### Kiểm tra Redis hoạt động

```bash
# Nếu dùng Docker
docker exec -it redis redis-cli

# Trong redis-cli:
127.0.0.1:6379> ping
PONG
127.0.0.1:6379> SET test "hello"
OK
127.0.0.1:6379> GET test
"hello"
127.0.0.1:6379> DEL test
(integer) 1
```

### Kiểm tra cache keys của TaskHub

```bash
# Liệt kê tất cả cache keys
127.0.0.1:6379> KEYS "taskhub:*"

# Xóa toàn bộ cache (nếu cần)
127.0.0.1:6379> FLUSHDB
```

---

## Hướng dẫn cấu hình Gmail SMTP

Hệ thống sử dụng **Gmail SMTP** để gửi email notification khi user được assign task.

### Bước 1: Bật Xác minh 2 bước (2-Step Verification)

1. Truy cập: https://myaccount.google.com/security
2. Tìm mục **"Xác minh 2 bước"** (2-Step Verification)
3. Nhấn **"Bắt đầu"** và làm theo hướng dẫn
4. Xác nhận bằng số điện thoại

### Bước 2: Tạo App Password (Mật khẩu ứng dụng)

1. Truy cập: https://myaccount.google.com/apppasswords
2. Đặt tên cho app, ví dụ: `TaskHub`
3. Nhấn **"Tạo"** (Create)
4. Google sẽ hiện **mật khẩu 16 ký tự** (ví dụ: `abcd efgh ijkl mnop`)
5. **Copy mật khẩu này** (bỏ khoảng trắng) → đây là giá trị cho `SMTP_PASSWORD`

> ⚠️ **Quan trọng:** Mật khẩu này chỉ hiện **một lần**. Hãy copy ngay.

### Bước 3: Cập nhật file .env

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_real_email@gmail.com
SMTP_PASSWORD=abcdefghijklmnop
SMTP_FROM=your_real_email@gmail.com
SMTP_TLS=true
```

### Bước 4: Kiểm tra

Sau khi cấu hình xong, tạo một task với `assignee_id` qua Swagger UI. Email sẽ được gửi tự động cho người được assign.

> **Lưu ý:** Nếu chưa cấu hình SMTP, hệ thống vẫn hoạt động bình thường — chỉ log warning thay vì gửi email.

---

## Cache Strategy

### Cách hoạt động

```
Client GET /projects/{id}/tasks?status=TODO&page=1&limit=10
         │
         ▼
┌──────────────────┐
│  Check Redis     │──── Cache HIT ────► Return cached JSON
│  Cache           │
└──────────────────┘
         │
    Cache MISS
         │
         ▼
┌──────────────────┐
│  Query Database  │
│  (PostgreSQL)    │
└──────────────────┘
         │
         ▼
┌──────────────────┐
│  Store in Redis  │ ← TTL = 300s (5 phút)
│  Cache           │
└──────────────────┘
         │
         ▼
    Return JSON
```

### Cache Key Pattern

```
taskhub:project:{project_id}:tasks:{md5_of_query_params}
```

### Cache Invalidation

Cache tự động bị xóa khi:
- **Tạo task** (`POST /projects/{id}/tasks`)
- **Cập nhật task** (`PATCH /tasks/{id}`)
- **Xóa task** (`DELETE /tasks/{id}`)
- **Gán label cho task** (`POST /tasks/{id}/labels/{label_id}`)
- **Bỏ label khỏi task** (`DELETE /tasks/{id}/labels/{label_id}`)

---

## Background Email Notification

### Khi nào email được gửi?

| Sự kiện                          | Email gửi cho |
|----------------------------------|---------------|
| Tạo task với `assignee_id`       | Assignee      |
| Cập nhật task, thay đổi assignee | Assignee mới  |

### Cơ chế hoạt động

- Sử dụng **FastAPI BackgroundTasks** — email gửi async, không block API response
- Sử dụng **aiosmtplib** — async SMTP client
- **Graceful degradation**: nếu SMTP chưa cấu hình hoặc gửi thất bại, hệ thống log warning và tiếp tục hoạt động bình thường

---

## API Endpoints

### Auth (`/api/v1/auth`)

| Method | Endpoint              | Mô tả                          | Auth |
|--------|-----------------------|---------------------------------|:----:|
| POST   | `/auth/register`      | Đăng ký tài khoản mới          | Không |
| POST   | `/auth/login`         | Đăng nhập, nhận JWT tokens     | Không |
| POST   | `/auth/refresh`       | Làm mới access token           | Không |
| POST   | `/auth/logout`        | Đăng xuất, revoke refresh token| Không |

### User (`/api/v1/users`)

| Method | Endpoint                  | Mô tả                | Auth |
|--------|---------------------------|-----------------------|:----:|
| GET    | `/users/me`               | Xem profile cá nhân  | Có   |
| PATCH  | `/users/me`               | Cập nhật profile      | Có   |
| POST   | `/users/me/change-password` | Đổi mật khẩu       | Có   |

### Workspace (`/api/v1/workspaces`)

| Method | Endpoint                                  | Mô tả                    | Quyền       |
|--------|-------------------------------------------|---------------------------|-------------|
| POST   | `/workspaces`                             | Tạo workspace mới         | Authenticated |
| GET    | `/workspaces`                             | Danh sách workspace của tôi | Authenticated |
| GET    | `/workspaces/{id}`                        | Chi tiết workspace        | Member      |
| PATCH  | `/workspaces/{id}`                        | Cập nhật workspace        | OWNER       |
| DELETE | `/workspaces/{id}`                        | Xóa workspace             | OWNER       |
| GET    | `/workspaces/{id}/members`                | Danh sách members         | Member      |
| POST   | `/workspaces/{id}/members`                | Mời member mới            | OWNER       |
| DELETE | `/workspaces/{id}/members/{user_id}`      | Xóa member                | OWNER       |

### Project (`/api/v1`)

| Method | Endpoint                              | Mô tả                   | Quyền          |
|--------|---------------------------------------|--------------------------|----------------|
| POST   | `/workspaces/{id}/projects`           | Tạo project trong workspace | OWNER / EDITOR |
| GET    | `/workspaces/{id}/projects`           | Danh sách projects       | Member         |
| GET    | `/projects/{id}`                      | Chi tiết project         | Member         |
| PATCH  | `/projects/{id}`                      | Cập nhật / Archive project | OWNER / EDITOR |
| DELETE | `/projects/{id}`                      | Xóa project              | OWNER          |

### Label (`/api/v1`)

| Method | Endpoint                      | Mô tả                      | Quyền          |
|--------|-------------------------------|-----------------------------|----------------|
| POST   | `/projects/{id}/labels`       | Tạo label trong project     | OWNER / EDITOR |
| GET    | `/projects/{id}/labels`       | Danh sách label trong project| Member        |
| PATCH  | `/labels/{id}`                | Cập nhật label              | OWNER / EDITOR |
| DELETE | `/labels/{id}`                | Xóa label                   | OWNER / EDITOR |

### Task (`/api/v1`)

| Method | Endpoint                              | Mô tả                                       | Quyền          |
|--------|---------------------------------------|----------------------------------------------|----------------|
| POST   | `/projects/{id}/tasks`                | Tạo task trong project                       | OWNER / EDITOR |
| GET    | `/projects/{id}/tasks`                | Danh sách task (filter + pagination + **cache**) | Member     |
| GET    | `/tasks/{id}`                         | Chi tiết task                                | Member         |
| PATCH  | `/tasks/{id}`                         | Cập nhật task (status/priority/assignee/...) | OWNER / EDITOR |
| DELETE | `/tasks/{id}`                         | Xóa task                                     | OWNER / EDITOR |
| POST   | `/tasks/{id}/labels/{label_id}`       | Gán label cho task                           | OWNER / EDITOR |
| DELETE | `/tasks/{id}/labels/{label_id}`       | Bỏ label khỏi task                           | OWNER / EDITOR |

### Comment (`/api/v1`)

| Method | Endpoint                              | Mô tả                                       | Quyền          |
|--------|---------------------------------------|----------------------------------------------|----------------|
| POST   | `/tasks/{id}/comments`                | Thêm comment vào task                        | Member         |
| GET    | `/tasks/{id}/comments`                | Xem danh sách comment của task               | Member         |
| DELETE | `/comments/{id}`                      | Xóa comment                                  | Author / OWNER |

---

## Phân quyền (RBAC)

### System-level Roles (User)

| Role     | Mô tả                               |
|----------|--------------------------------------|
| `ADMIN`  | Quản trị hệ thống                   |
| `MEMBER` | Người dùng thông thường (mặc định)  |

### Workspace-level Roles

| Role     | Workspace          | Project            | Member Management  |
|----------|--------------------|--------------------|-------------------|
| `OWNER`  | CRUD               | CRUD + Delete      | Invite / Remove   |
| `EDITOR` | Xem                | Create + Update    | Không có quyền    |
| `VIEWER` | Xem                | Xem                | Không có quyền    |

**Luồng phân quyền:**
1. Người tạo Workspace tự động trở thành **OWNER**.
2. OWNER invite member với role **EDITOR** hoặc **VIEWER**.
3. EDITOR có thể tạo/sửa Project, nhưng không xóa được Project hay quản lý member.
4. VIEWER chỉ xem, không tạo/sửa/xóa bất kỳ tài nguyên nào.

---

## Database Schema

```
┌─────────────────────┐       ┌──────────────────────────┐
│       users         │       │       workspaces          │
├─────────────────────┤       ├──────────────────────────┤
│ id (PK)             │◄──┐   │ id (PK)                  │
│ email (UNIQUE)      │   │   │ name                     │
│ full_name           │   ├───│ owner_id (FK → users)    │
│ hashed_password     │   │   │ created_at               │
│ role (ADMIN/MEMBER) │   │   └──────────┬───────────────┘
│ is_active           │   │              │
│ created_at          │   │              │ 1:N
└─────────────────────┘   │              │
         ▲                │   ┌──────────┴───────────────┐
         │                │   │   workspace_members       │
         │                │   ├──────────────────────────┤
         └────────────────┼───│ workspace_id (FK)        │
                          │   │ user_id (FK → users)     │
                          │   │ role (OWNER/EDITOR/VIEWER)│
                          │   │ created_at               │
                          │   │ UNIQUE(workspace_id,     │
                          │   │        user_id)          │
                          │   └──────────────────────────┘
                          │
                          │   ┌──────────────────────────┐
                          │   │       projects            │
                          │   ├──────────────────────────┤
                          │   │ id (PK)                  │
                          │   │ workspace_id (FK)        │
                          │   │ name                     │
                          │   │ description              │
                          │   │ status (ACTIVE/ARCHIVED) │
                          │   │ created_at               │
                          │   └──────────┬───────────────┘
                                         │
                        ┌────────────────┴────────────────┐
                        │ 1:N                             │ 1:N
                        ▼                                 ▼
         ┌──────────────────────────┐      ┌──────────────────────────┐
         │          tasks           │      │          labels          │
         ├──────────────────────────┤      ├──────────────────────────┤
         │ id (PK)                  │      │ id (PK)                  │
         │ project_id (FK)          │      │ project_id (FK)          │
         │ assignee_id (FK → users) │      │ name                     │
         │ title                    │      │ color                    │
         │ description              │      └────────────┬─────────────┘
         │ status (TODO/IN_PROGRESS)│                   │
         │ priority (LOW/URGENT...) │                   │
         │ due_date                 │                   │
         │ created_by (FK → users)  │                   │
         │ created_at               │                   │
         └──────────────┬───────────┘                   │
                        │                               │
                        └───────────────┬───────────────┘
                                        ▼ N:M
                         ┌─────────────────────────────┐
                         │         task_labels         │
                         ├─────────────────────────────┤
                         │ task_id (PK, FK)            │
                         │ label_id (PK, FK)           │
                         └─────────────────────────────┘
```

---

## Testing

Dự án sử dụng **pytest** + **pytest-asyncio** + **httpx** cho integration test.

```bash
# Cài dependencies test
pip install pytest pytest-asyncio httpx

# Chạy toàn bộ test
python -m pytest -v

# Chạy từng file
python -m pytest test_auth_user.py -v
python -m pytest test_workspace_project.py -v
python -m pytest test_task_label.py -v
python -m pytest test_comment_pagination.py -v
python -m pytest test_cache_background.py -v
```

### Test Suites hiện có

| File                          | Mô tả                                        | Scenarios |
|-------------------------------|-----------------------------------------------|:---------:|
| `test_auth_user.py`          | Register → Login → Profile → Update → Logout | 7         |
| `test_workspace_project.py`  | Workspace CRUD, Member mgmt, Project CRUD     | 10        |
| `test_task_label.py`         | Task & Label CRUD, Assignee, Filter, RBAC     | 15        |
| `test_comment_pagination.py` | Comment CRUD, Task Filtering & Pagination     | 8         |
| `test_cache_background.py`   | Redis Cache hit/miss/invalidation, Email notify | 11      |

---

## License

MIT License — Xem file [LICENSE](LICENSE) để biết thêm chi tiết.
