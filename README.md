# 🚀 TaskHub — Task Management API

**TaskHub** là hệ thống quản lý công việc (Task Management) được xây dựng trên nền tảng **FastAPI**, hỗ trợ làm việc nhóm thông qua Workspace, Project và Task với hệ thống phân quyền RBAC hoàn chỉnh.

---

## 📋 Mục lục

- [Tính năng](#-tính-năng)
- [Tech Stack](#-tech-stack)
- [Cấu trúc dự án](#-cấu-trúc-dự-án)
- [Cài đặt & Chạy](#-cài-đặt--chạy)
- [Biến môi trường](#-biến-môi-trường)
- [API Endpoints](#-api-endpoints)
- [Phân quyền (RBAC)](#-phân-quyền-rbac)
- [Database Schema](#-database-schema)
- [Testing](#-testing)

---

## ✨ Tính năng

| #  | Module        | Mô tả                                                                 | Trạng thái |
|----|---------------|------------------------------------------------------------------------|:----------:|
| 1  | **Auth**      | Register, Login (JWT access + refresh token), Logout (revoke token)    | ✅         |
| 2  | **User**      | Get profile, Update profile (PATCH), Change password                   | ✅         |
| 3  | **Workspace** | CRUD workspace, Invite/Remove member, Phân quyền theo role             | ✅         |
| 4  | **Project**   | CRUD trong workspace, Archive project                                  | ✅         |
| 5  | Task          | CRUD trong project, Assign, Chuyển status, Priority & due_date         | 🔲         |
| 6  | Label         | CRUD per project, Gán/bỏ label cho task                                | 🔲         |
| 7  | Comment       | Thêm/xóa comment trên task                                            | 🔲         |
| 8  | Filter & Page | Lọc task theo status, priority, assignee; pagination                   | 🔲         |
| 9  | Caching       | Cache GET tasks với Redis, invalidate khi có thay đổi                  | 🔲         |
| 10 | Background    | Gửi email notification khi được assign task                            | 🔲         |
| 11 | RBAC          | Phân quyền ADMIN / OWNER / EDITOR / VIEWER theo resource               | ✅         |
| 12 | Swagger/ReDoc | Đầy đủ docs, Bearer auth scheme                                       | ✅         |
| 13 | Docker        | `docker compose up` chạy toàn bộ stack                                 | ✅         |

---

## 🛠 Tech Stack

| Thành phần     | Công nghệ                        |
|----------------|----------------------------------|
| Framework      | FastAPI 0.140+                   |
| ORM            | SQLAlchemy 2.x (async)           |
| Migration      | Alembic                          |
| Validation     | Pydantic v2                      |
| Auth           | JWT (PyJWT) — Access + Refresh   |
| Database       | PostgreSQL 16                    |
| Cache / Revoke | Redis 7                          |
| Container      | Docker & Docker Compose          |
| Language       | Python 3.11+                     |

---

## 📁 Cấu trúc dự án

```
TaskHub/
├── app/
│   ├── main.py                    # FastAPI application entry point
│   ├── core/
│   │   ├── config.py              # Pydantic Settings (env)
│   │   ├── database.py            # SQLAlchemy async engine & session
│   │   ├── redis.py               # Redis async client
│   │   └── security.py            # JWT encode/decode, password hashing
│   ├── models/
│   │   ├── __init__.py            # Export all models
│   │   ├── user.py                # User model (ADMIN/MEMBER)
│   │   ├── workspace.py           # Workspace + WorkspaceMember models
│   │   └── project.py             # Project model (ACTIVE/ARCHIVED)
│   ├── schemas/
│   │   ├── __init__.py            # Export all schemas
│   │   ├── auth.py                # Token, LoginRequest, RefreshTokenRequest
│   │   ├── user.py                # UserCreate, UserUpdate, UserResponse
│   │   ├── workspace.py           # WorkspaceCreate/Update/Response, MemberAdd
│   │   └── project.py             # ProjectCreate, ProjectUpdate, ProjectResponse
│   └── api/
│       └── v1/
│           ├── router.py          # API router aggregation
│           ├── deps.py            # Dependencies (get_current_user, OAuth2)
│           └── endpoints/
│               ├── auth.py        # Register, Login, Refresh, Logout
│               ├── users.py       # Profile, Update, Change password
│               ├── workspaces.py  # Workspace CRUD + Member management
│               └── projects.py    # Project CRUD + Archive
├── alembic/                       # Database migrations
├── alembic.ini
├── docker-compose.yml             # PostgreSQL 16 + Redis 7 + App
├── Dockerfile
├── requirements.txt
├── .env.example
├── conftest.py                    # Pytest config (async event loop)
├── pytest.ini
├── test_auth_user.py              # Auth & User integration tests
└── test_workspace_project.py      # Workspace & Project integration tests
```

---

## 🚀 Cài đặt & Chạy

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

## 🔐 Biến môi trường

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
```

> ⚠️ **Lưu ý:** Thay đổi `SECRET_KEY` trước khi deploy lên production.

---

## 📡 API Endpoints

### Auth (`/api/v1/auth`)

| Method | Endpoint              | Mô tả                          | Auth |
|--------|-----------------------|---------------------------------|:----:|
| POST   | `/auth/register`      | Đăng ký tài khoản mới          | ❌   |
| POST   | `/auth/login`         | Đăng nhập, nhận JWT tokens     | ❌   |
| POST   | `/auth/refresh`       | Làm mới access token           | ❌   |
| POST   | `/auth/logout`        | Đăng xuất, revoke refresh token| ❌   |

### User (`/api/v1/users`)

| Method | Endpoint                  | Mô tả                | Auth |
|--------|---------------------------|-----------------------|:----:|
| GET    | `/users/me`               | Xem profile cá nhân  | ✅   |
| PATCH  | `/users/me`               | Cập nhật profile      | ✅   |
| POST   | `/users/me/change-password` | Đổi mật khẩu       | ✅   |

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

---

## 🛡 Phân quyền (RBAC)

### System-level Roles (User)

| Role     | Mô tả                               |
|----------|--------------------------------------|
| `ADMIN`  | Quản trị hệ thống                   |
| `MEMBER` | Người dùng thông thường (mặc định)  |

### Workspace-level Roles

| Role     | Workspace          | Project            | Member Management  |
|----------|--------------------|--------------------|-------------------|
| `OWNER`  | CRUD               | CRUD + Delete      | Invite / Remove   |
| `EDITOR` | Xem                | Create + Update    | ❌                |
| `VIEWER` | Xem                | Xem                | ❌                |

**Luồng phân quyền:**
1. Người tạo Workspace tự động trở thành **OWNER**.
2. OWNER invite member với role **EDITOR** hoặc **VIEWER**.
3. EDITOR có thể tạo/sửa Project, nhưng không xóa được Project hay quản lý member.
4. VIEWER chỉ xem, không tạo/sửa/xóa bất kỳ tài nguyên nào.

---

## 🗄 Database Schema

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
                          │   └──────────────────────────┘
```

---

## 🧪 Testing

Dự án sử dụng **pytest** + **pytest-asyncio** + **httpx** cho integration test.

```bash
# Cài dependencies test
pip install pytest pytest-asyncio httpx

# Chạy toàn bộ test
python -m pytest -v

# Chạy từng file
python -m pytest test_auth_user.py -v
python -m pytest test_workspace_project.py -v
```

### Test Suites hiện có

| File                          | Mô tả                                        | Scenarios |
|-------------------------------|-----------------------------------------------|:---------:|
| `test_auth_user.py`          | Register → Login → Profile → Update → Logout | 7         |
| `test_workspace_project.py`  | Workspace CRUD, Member mgmt, Project CRUD     | 10        |

---

## 📄 License

MIT License — Xem file [LICENSE](LICENSE) để biết thêm chi tiết.
