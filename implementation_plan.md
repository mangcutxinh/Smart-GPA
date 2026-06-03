# SmartGPA – Chan's Modules Implementation Plan

## Mục tiêu
Triển khai 2 module của Chan trong dự án SmartGPA:
1. **`feature/auth-gateway`** — Xác thực JWT 4 vai trò + API Gateway
2. **`feature/simulation-engine`** — Engine tính điểm ngược (Inverse Calculation) real-time

---

## Proposed Changes

### Cấu trúc thư mục tổng thể

```
Smart-GPA/
├── backend/
│   ├── app/
│   │   ├── main.py                   # FastAPI entry point, CORS, routers
│   │   ├── core/
│   │   │   ├── config.py             # Settings từ .env
│   │   │   ├── security.py           # bcrypt + JWT utilities
│   │   │   └── dependencies.py       # get_current_user, require_role decorators
│   │   ├── models/
│   │   │   └── schemas.py            # Pydantic models (User, Token, SimRequest…)
│   │   ├── db/
│   │   │   └── fake_db.py            # In-memory DB (thay Databricks lúc dev)
│   │   ├── routers/
│   │   │   ├── auth.py               # /auth/* endpoints
│   │   │   └── simulation.py         # /simulation/* endpoints
│   │   └── services/
│   │       ├── auth_service.py       # register, login, refresh logic
│   │       └── simulation_service.py # Inverse calc logic (3 loại HP)
│   ├── requirements.txt
│   ├── .env.example
│   └── run.py                        # uvicorn launcher
└── tests/
    ├── test_auth.py                  # TC-01, TC-02
    └── test_simulation.py            # TC-05, TC-06, TC-07
```

---

### Module 1 — Auth Gateway (`feature/auth-gateway`)

#### [NEW] `backend/app/core/config.py`
- Load env vars: `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `REFRESH_TOKEN_EXPIRE_DAYS`

#### [NEW] `backend/app/core/security.py`
- `hash_password(plain)` → bcrypt
- `verify_password(plain, hashed)` → bcrypt verify
- `create_access_token(data, expires_delta)` → JWT HS256, 30 phút
- `create_refresh_token(data)` → JWT HS256, 7 ngày
- `decode_token(token)` → trả payload hoặc raise 401

#### [NEW] `backend/app/core/dependencies.py`
- `get_current_user(token: str)` → decode JWT → trả User object
- `require_role(*roles)` → dependency factory kiểm tra role

#### [NEW] `backend/app/db/fake_db.py`
- Dict in-memory `USERS_DB` để dev/test độc lập với Databricks
- Seed sẵn 4 tài khoản demo (student, lecturer, admin)

#### [NEW] `backend/app/models/schemas.py`
- `UserRole` Enum: student / lecturer / admin
- `UserCreate`, `UserLogin`, `UserOut`
- `Token` (access_token, refresh_token, token_type)
- `RefreshRequest`
- `SimulationRequest`, `SimulationResult`

#### [NEW] `backend/app/routers/auth.py`
| Endpoint | Method | Mô tả |
|---|---|---|
| `/auth/register` | POST | Tạo tài khoản, hash bcrypt, kiểm tra email trùng |
| `/auth/login` | POST | Xác thực → trả access + refresh token |
| `/auth/refresh` | POST | Dùng refresh token → trả access token mới |
| `/auth/logout` | POST | Blacklist refresh token (in-memory set) |
| `/auth/me` | GET | Trả thông tin user hiện tại (Protected) |

#### [NEW] `backend/app/services/auth_service.py`
- Toàn bộ business logic của auth module

---

### Module 2 — Simulation Engine (`feature/simulation-engine`)

#### [NEW] `backend/app/services/simulation_service.py`
Thuật toán tính điểm ngược theo 3 loại học phần:

**Lý thuyết:** `T = 0.2×TK + 0.3×GK + 0.5×CK`
→ Inverse: `CK_min = (target - 0.2×TK - 0.3×GK) / 0.5`

**Thực hành:** Trả về điểm TH trung bình cần đạt.

**Tích hợp:** `T = (LT×chi_lt + TH×chi_th) / tong_chi`
→ Inverse: tính ngược `LT_min` khi biết `TH` hiện tại

- Score mapping table (A+→F theo `image_4.png`)
- Feasibility check: `CK_needed > 10.0` → `"Bất khả thi"`

#### [NEW] `backend/app/routers/simulation.py`
| Endpoint | Method | Auth | Mô tả |
|---|---|---|---|
| `/simulation/simulate` | POST | Student only | Tính điểm ngược real-time |
| `/simulation/score-map` | GET | All authenticated | Trả bảng quy đổi A+→F |

---

### Entry point & Config

#### [NEW] `backend/app/main.py`
- FastAPI app với CORS, lifespan
- Include routers: `/auth`, `/simulation`
- Swagger UI tại `/docs`

#### [NEW] `backend/requirements.txt`
```
fastapi==0.111.0
uvicorn[standard]==0.29.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-dotenv==1.0.1
pydantic[email]==2.7.1
httpx==0.27.0   # for tests
pytest==8.2.0
```

#### [NEW] `backend/.env.example`
```
SECRET_KEY=your-super-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

---

### Tests (TC từ proposal)

#### [NEW] `tests/test_auth.py`
- TC-01: Token hết hạn / sai role → 401/403
- TC-02: Upload file sai format → 422 (placeholder)

#### [NEW] `tests/test_simulation.py`
- TC-05: Môn LT, TK=8.0, GK=9.0, mục tiêu A → CK cần ≥ 8.5 ✓
- TC-06: Môn Tích hợp (2LT+1TH), TH=8.0, mục tiêu A → LT cần ≥ 8.8 ✓
- TC-07: Điểm quá thấp, mục tiêu A+ → "Bất khả thi" ✓

---

## Bảng quy đổi điểm (Score Mapping từ image_4.png)

| Điểm 10 | Điểm 4 | Điểm chữ | Đánh giá |
|---|---|---|---|
| 9.0 – 10.0 | 4.0 | A+ | Đạt |
| 8.5 – 8.9 | 4.0 | A | Đạt |
| 8.0 – 8.4 | 3.5 | B+ | Đạt |
| 7.0 – 7.9 | 3.0 | B | Đạt |
| 6.5 – 6.9 | 2.5 | C+ | Đạt |
| 5.5 – 6.4 | 2.0 | C | Đạt |
| 5.0 – 5.4 | 1.5 | D+ | Đạt |
| 4.0 – 4.9 | 1.0 | D | Đạt |
| 0.0 – 3.9 | 0.0 | F | Không Đạt |

---

## Verification Plan

### Automated Tests
```bash
cd backend
pip install -r requirements.txt
pytest tests/ -v
```

### Manual Verification
```bash
uvicorn app.main:app --reload
# → Swagger tại http://localhost:8000/docs
# Test: POST /auth/login → copy token → POST /simulation/simulate
```

### Kiểm tra TC quan trọng
- TC-05: TK=8.0, GK=9.0, mục tiêu A → expect CK_min = 8.5
- TC-06: Tích hợp 2LT+1TH, TH=8.0, mục tiêu A → expect LT_min = 8.833...
- TC-07: TK=3.0, GK=3.0, mục tiêu A+ → expect "Bất khả thi"
