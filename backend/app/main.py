"""
SmartGPA API – FastAPI Application Entry Point
Module: feature/auth-gateway + feature/simulation-engine
Author: Chan (SOA Backend Architect)
# Force reload for CSV database update: 2026-06-05
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, simulation, upload, admin, lecturer

# ─── App instance ─────────────────────────────────────────────
app = FastAPI(
    title="SmartGPA API",
    description="""
## SmartGPA – Hệ thống Phân tích Học thuật & Giả lập Điểm Mục tiêu

Nền tảng hướng dịch vụ (SOA) kết hợp **FastAPI** + **Databricks Cloud**.

---

### Modules
| Module | Prefix | Mô tả |
|---|---|---|
| **Auth Gateway** | `/auth` | Xác thực JWT 3 vai tro (bcrypt + HS256) |
| **Simulation Engine** | `/simulation` | Tính điểm ngược real-time theo 3 loại học phần |

---

### Tài khoản Demo (Development)

| Email | Password | Vai trò |
|---|---|---|
| student@smartgpa.edu | Sv@123 | Student |
| thibinh.gv1001@smartgpa.edu | Gv@123 | Lecturer |
| admin@smartgpa.edu | Admin@123 | Admin |

---

### Cách xác thực
1. Gọi `POST /auth/login` → lấy `access_token`
2. Click **Authorize** (ổ khóa) → nhập `Bearer <access_token>`
3. Gọi các protected endpoints

---

### Công thức tính điểm
- **Lý thuyết**: `T = 0.2×TK + 0.3×GK + 0.5×CK`
- **Thực hành**: `T = mean(TH_1, ..., TH_x)`
- **Tích hợp**: `T = (T_LT × chi_lt + T_TH × chi_th) / tổng_chi`
    """,
    version="1.0.0",
    contact={
        "name": "Chan – SOA Backend Architect",
        "url": "https://github.com/mangcutxinh/Smart-GPA",
    },
    license_info={
        "name": "MIT",
    },
    openapi_tags=[
        {
            "name": "Authentication",
            "description": "Đăng ký, đăng nhập, refresh token, logout",
        },
        {
            "name": "Simulation Engine",
            "description": "Tính điểm ngược real-time & bảng quy đổi điểm",
        },
        {
            "name": "System",
            "description": "Health check & thông tin hệ thống",
        },
    ],
)

# ─── CORS ────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers ─────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(simulation.router)
app.include_router(upload.router)
app.include_router(admin.router)
app.include_router(lecturer.router)


# ─── System endpoints ─────────────────────────────────────────
@app.get("/", tags=["System"], summary="Root")
def root() -> dict:
    return {
        "service": "SmartGPA API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "modules": {
            "auth_gateway": "/auth",
            "simulation_engine": "/simulation",
        },
        "demo_accounts": {
            "student": "student@smartgpa.edu / Sv@123",
            "lecturer": "thibinh.gv1001@smartgpa.edu / Gv@123",
            "admin": "admin@smartgpa.edu / Admin@123",
        },
    }


@app.get("/health", tags=["System"], summary="Health check")
def health_check() -> dict:
    return {"status": "healthy", "service": "SmartGPA API"}

