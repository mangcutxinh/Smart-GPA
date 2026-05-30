---

# PROJECT PROPOSAL

## THÔNG TIN CHUNG

### Thành viên nhóm

| STT | Họ và tên                        | MSSV      | Vai trò                        |
|-----|----------------------------------|-----------|------------------------------- |
| 1   | Nguyễn Thị Quỳnh Trang           |           | Leader / SOA Backend Architect |
| 2   | Vũ Ngọc Thu Phương               | [MSSV]    | Data Engineer                  |
| 3   | Phan Trần Thảo Vy                | 23670631  | ML / Cloud Engineer            |
| 4   | Lê Hoàng D                       | [MSSV]    | Frontend Developer             |
| 5   | Phạm Minh E                      | [MSSV]    | QA / Data Analyst              |

- **Git Repository**: [https://github.com/TruongTheHaiThinh/SmartGPA-Academic-Analytics-Platform](https://github.com/TruongTheHaiThinh/SmartGPA-Academic-Analytics-Platform)

---

### Cấu trúc nhánh Git & Chức năng

| Nhánh                        | Chức năng/Module                                            | Người phụ trách             |
|------------------------------|-------------------------------------------------------------|-----------------------------|
| `feature/auth-gateway`       | Xác thực, phân quyền JWT (4 vai trò), API Gateway           | Chan                        |
| `feature/databricks-pipeline`| Hạ tầng Delta Lake, Pipeline ETL nạp điểm thô               | Vũ Ngọc Thu Phương          |
| `feature/simulation-engine`  | Logic core tính điểm đảo (LT/TH/Tích hợp)                   | Chan                        |
| `feature/ml-prediction`      | MLflow Model dự báo rớt môn (Điểm F)                        | Phan Trần Thảo Vy           |
| `feature/client-portal`      | Giao diện Web UI tích hợp thanh trượt giả lập               | Lê Hoàng D                  |
| `feature/analytics-dashboard`| Kiểm thử Pytest & Databricks SQL Dashboard                  | người bí ẩn                 |
| `develop`                    | Tích hợp tất cả các feature branch (code ổn định đã review) | Cả nhóm                     |
| `main`                       | Push cuối cùng – Bản hoàn chỉnh để nộp & deploy             | Cả nhóm                     |

> **Quy trình làm việc:**
> - Mỗi thành viên làm việc trên nhánh `feature/*` được phân công.
> - Khi hoàn thành module tạo PR vào `develop`, leader review & approve.
> - Chỉ merge duy nhất 1 lần vào `main` khi toàn hệ thống ổn định, không commit trực tiếp vào `main`.

---

# MÔ TẢ DỰ ÁN: SMARTGPA – HỆ THỐNG PHÂN TÍCH HỌC THUẬT, GIẢ LẬP ĐIỂM MỤC TIÊU VÀ DỰ BÁO CẢNH BÁO HỌC VỤ

## 1. Ý TƯỞNG DỰ ÁN (THE VISION)

**Tổng quan nền tảng**

Trong kỷ nguyên giáo dục số, việc kết nối dữ liệu học thuật giữa Nhà trường và Sinh viên thường gặp tình trạng rời rạc, thiếu tính dự báo thời gian thực. SmartGPA ra đời nhằm đồng bộ hóa và tự động hóa toàn bộ quá trình giả lập điểm số, cảnh báo rớt môn và hỗ trợ cố vấn học vụ.

**3 Trụ cột kỹ thuật của SmartGPA:**

* **Service-Oriented Architecture (SOA):** Tách biệt module giao diện, backend API và pipeline dữ liệu – vận hành linh hoạt quy mô trường lớn.
* **Inverse Calculation Engine:** Thuật toán tính điểm đảo linh động, tự động nhận diện loại học phần và số hóa logic tính điểm, đặc biệt đáp ứng quy chế mới v�� SỐ ĐẦU ĐIỂM và ĐIỂM LIỆT.
* **Predictive Analytics Table:** Tự động hóa kiểm thử, phân tích dự báo qua từng layer (Bronze, Silver, Gold), vận hành trên Databricks Lakehouse.

---

## 2. VAI TRÒ NGƯỜI DÙNG & PHÂN QUYỀN

Hệ thống phân quyền theo vai trò: Sinh viên, Giảng viên, Cố vấn, Quản trị viên – kiểm soát truy cập và workflow nghiệp vụ cho từng đối tượng trên từng module.

---

## 3. CHI TIẾT NGHIỆP VỤ & QUY CHẾ TÍNH ĐIỂM

### 3.1. SỐ HÓA QUY CHẾ ĐẦU ĐIỂM THƯỜNG KỲ VÀ ĐIỂM LIỆT

- **Số đầu điểm Thường kỳ (TK) tỉ lệ chặt với số tín chỉ:**
  - 2 tín chỉ (LT/TH): 2 đầu điểm TK (TK_1, TK_2); ĐTB = (TK_1 + TK_2)/2
  - 3 tín chỉ (LT/TH): 3 đầu điểm TK (TK_1, TK_2, TK_3); ĐTB = (TK_1 + TK_2 + TK_3)/3
  - Môn tích hợp (VD: 2TC LT + 1TC TH): Tách riêng điểm LT, điểm TH đúng số chỉ

- **Điểm liệt thực hành:**
  - Nếu điểm TB thực hành < 3.0 ở môn tích hợp/thực hành, kết quả cuối luôn là F, trạng thái trả về CANH BAO: LIET THUC HANH (ROT MON).
  - Trường hợp này, mọi phép tính, giả lập đều trả về loại F – không cho tính điểm thành phần lý thuyết khi TH đang liệt.
  
- **Mặc định phần mềm khóa tính toán điểm cuối kỳ nhánh lý thuyết khi TH liệt, cho tới lúc TH ≥ 3.0.**

### 3.2. Quy chế tính điểm chi tiết (Theo quy chế mới – áp dụng code thực tế)

**1. Học phần Lý thuyết:**

    ĐTB_TK = (TK_1 + TK_2) / 2 (2 chỉ); (TK_1 + TK_2 + TK_3) / 3 (3 chỉ) v.v
    T = 20% × ĐTB_TK + 30% × Điểm Giữa kỳ + 50% × Điểm Cuối kỳ

**2. Học phần Thực hành:**

    ĐTB_TH = Trung bình cộng điểm thực hành từng tiết/bài
    T = ĐTB_TH
    Nếu ĐTB_TH < 3.0 → F, trạng thái cảnh báo "LIỆT THỰC HÀNH"

**3. Học phần Tích hợp:**

    - Trước tiên kiểm tra ĐTB_TH: Nếu < 3.0 trả về F và cảnh báo liệt (KHÔNG tính tổng kết)
    - Nếu đủ, tính: T = ((Điểm LT × Số chỉ LT) + (ĐTB_TH × Số chỉ TH))/Tổng số chỉ học phần

### 3.3. Quy đổi thang điểm chữ (map điểm chữ)
- A+: >= 9.0
- A: >= 8.5
- B+: >= 8.0
- B: >= 7.0
- C+: >= 6.0
- C: >= 5.5
- D+: >= 5.0
- D: >= 4.0
- F: < 4.0 HOẶC < 3.0 ĐTB_TH với môn có thực hành

---

# ... các mục phía dưới giữ nguyên ...
