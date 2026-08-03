# Hướng dẫn Test Đặc trưng 1 & 2 (Auth & User)

> Server đang chạy tại **http://localhost:8000**

## Mở Swagger UI

Truy cập: **http://localhost:8000/docs**

---

## Feature 1 — Auth (Xác thực)

### Test 1.1: Đăng ký tài khoản (Register) - Thành công

Mở **POST `/api/v1/auth/register`** → **Try it out** → nhập:

```json
{
  "email": "user1@test.com",
  "full_name": "Test User 1",
  "password": "Password123!"
}
```

→ **Execute** → Kỳ vọng: `201 Created`
```json
{
  "id": 1,
  "email": "user1@test.com",
  "full_name": "Test User 1",
  "role": "MEMBER",
  "is_active": true,
  "created_at": "..."
}
```

---

### Test 1.2: Đăng ký trùng Email - Thất bại

Gọi lại **POST `/api/v1/auth/register`** với cùng email `user1@test.com`.

→ Kỳ vọng: `400 Bad Request` — *"Email already registered"*.

---

### Test 1.3: Đăng nhập (Login) - Thành công

Mở **POST `/api/v1/auth/login`** → nhập:

```json
{
  "email": "user1@test.com",
  "password": "Password123!"
}
```

→ Kỳ vọng: `200 OK`
```json
{
  "access_token": "eyJhbGciOi...",
  "refresh_token": "eyJhbGciOi...",
  "token_type": "bearer"
}
```

> Copy `access_token` và `refresh_token` để dùng ở các bước tiếp theo.

---

### Test 1.4: Gắn Token vào Swagger UI

1. Click nút **Authorize** ở góc trên bên phải Swagger UI.
2. Nhập `Bearer <access_token_vừa_copy>` vào ô Value.
3. Nhấp **Authorize** → **Close**.

---

### Test 1.5: Refresh Token - Thành công

Mở **POST `/api/v1/auth/refresh`** → nhập Body:

```json
{
  "refresh_token": "<refresh_token_vừa_copy>"
}
```

→ Kỳ vọng: `200 OK`, nhận cặp `access_token` và `refresh_token` mới.

---

### Test 1.6: Đăng xuất (Logout) - Thành công

Mở **POST `/api/v1/auth/logout`** với Token đã authorize.

→ Kỳ vọng: `200 OK` — *"Successfully logged out"*.

Thử lại endpoint refresh với `refresh_token` cũ:
→ Kỳ vọng: `401 Unauthorized` (do refresh token đã bị thu hồi/revoke).

---

## Feature 2 — User (Quản lý cá nhân)

> **Lưu ý:** Đăng nhập lại bằng **POST `/api/v1/auth/login`** và cập nhật `access_token` mới vào nút Authorize.

### Test 2.1: Xem thông tin cá nhân (Get Profile) - Thành công

Mở **GET `/api/v1/users/me`** → **Execute**

→ Kỳ vọng: `200 OK` trả về thông tin user hiện tại.

---

### Test 2.2: Cập nhật thông tin cá nhân (Update Profile) - Thành công

Mở **PATCH `/api/v1/users/me`** → nhập:

```json
{
  "full_name": "Test User Updated"
}
```

→ Kỳ vọng: `200 OK`, `full_name` đã thay đổi thành `"Test User Updated"`.

---

### Test 2.3: Đổi mật khẩu (Change Password) - Thành công

Mở **POST `/api/v1/users/me/change-password`** (hoặc PATCH tương ứng) → nhập:

```json
{
  "old_password": "Password123!",
  "new_password": "NewPassword123!"
}
```

→ Kỳ vọng: `200 OK` — *"Password updated successfully"*.

*Kiểm tra lại:* Thử login với `Password123!` sẽ thất bại (`401`), login bằng `NewPassword123!` sẽ thành công.
