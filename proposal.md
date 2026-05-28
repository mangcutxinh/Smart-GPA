---

# PROJECT PROPOSAL

## THÔNG TIN CHUNG

### Thành viên nhóm

| STT | Họ và tên                       | MSSV      | Vai trò                        |
|-----|----------------------------------|-----------|-------------------------------|
| 1   | Trương Thế Hải Thịnh (Chan)     | 23725051  | Leader / SOA Backend Architect |
| 2   | Nguyễn Văn A                     | [MSSV]    | Data Engineer                  |
| 3   | Trần Thị B                       | [MSSV]    | ML / Cloud Engineer            |
| 4   | Lê Hoàng D                       | [MSSV]    | Frontend Developer             |
| 5   | Phạm Minh E                      | [MSSV]    | QA / Data Analyst              |

- **Git Repository**: [https://github.com/TruongTheHaiThinh/SmartGPA-Academic-Analytics-Platform](https://github.com/TruongTheHaiThinh/SmartGPA-Academic-Analytics-Platform)

---

### Cấu trúc nhánh Git & Chức năng

| Nhánh                        | Chức năng/Module                                            | Người phụ trách             |
|------------------------------|-------------------------------------------------------------|-----------------------------|
| `feature/auth-gateway`       | Xác thực, phân quyền JWT (4 vai trò), API Gateway           | Chan                        |
| `feature/databricks-pipeline`| Hạ tầng Delta Lake, Pipeline ETL nạp điểm thô               | Nguyễn Văn A                |
| `feature/simulation-engine`  | Logic core tính điểm đảo (LT/TH/Tích hợp)                   | Chan                        |
| `feature/ml-prediction`      | MLflow Model dự báo rớt môn (Điểm F)                        | Trần Thị B                  |
| `feature/client-portal`      | Giao diện Web UI tích hợp thanh trượt giả lập               | Lê Hoàng D                  |
| `feature/analytics-dashboard`| Kiểm thử Pytest & Databricks SQL Dashboard                  | Phạm Minh E                 |
| `develop`                    | Tích hợp tất cả các feature branch (code ổn định đã review) | Cả nhóm                     |
| `main`                       | Push cuối cùng – Bản hoàn chỉnh để nộp & deploy             | Cả nhóm                     |

> **Quy trình làm việc:**
> - Mỗi thành viên làm việc trên nhánh `feature/*` được phân công.
> - Khi hoàn thành module tạo PR vào `develop`, leader review & approve.
> - Chỉ merge duy nhất 1 lần vào `main` khi toàn hệ thống ổn định, không commit trực tiếp vào `main`.

---

# MÔ TẢ DỰ ÁN: SMARTGPA – HỆ THỐNG PHÂN TÍCH HỌC THUẬT, GIẢ LẬP ĐIỂM MỤC TIÊU VÀ DỰ BÁO CẢNH BÁO HỌC VỤ

[Phần phía sau giữ nguyên nội dung chi tiết cũ]
