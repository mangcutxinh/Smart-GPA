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
* **Inverse Calculation Engine:** Thuật toán tính điểm đảo linh động, tự động nhận diện loại học phần và số hóa logic tính điểm, đặc biệt đáp ��ng quy chế mới về SỐ ĐẦU ĐIỂM và ĐIỂM LIỆT.
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

### 3.2. Quy chế tính điểm chi tiết (Cập nhật 2024 – số hóa theo tín chỉ & điểm liệt TH)

1. **Học phần Lý thuyết:**
   - ĐTB_TK = Tổng các điểm thường kỳ / số cột đầu điểm (tùy số tín chỉ, ví dụ 2 chỉ → 2 cột, 3 chỉ → 3 cột)
   - T = 20% × ĐTB_TK + 30% × Điểm giữa kỳ + 50% × Điểm cuối kỳ

2. **Học phần Thực hành:**
   - ĐTB_TH = Trung bình cộng điểm thực hành từng bài/tiết đúng số tín chỉ
   - T = ĐTB_TH
   - Nếu ĐTB_TH < 3.0 → Loại F bất chấp các điều kiện khác; trạng thái trả về: **CANH BAO: LIET THUC HANH (ROT MON)**

3. **Học phần Tích hợp (LT + TH):**
   - Kiểm tra trước: Nếu ĐTB_TH < 3.0 → luôn trả về F, khóa thực hiện phép toán tổng kết (Không cho phép giả lập/ước lượng điểm LT khi TH liệt)
   - Nếu đủ điều kiện, T = ((Điểm LT × Số chỉ LT) + (ĐTB_TH × Số chỉ TH)) / (Tổng số chỉ học phần)

### 3.3. Quy đổi thang điểm chữ (theo đúng Databricks code)

- A+: >= 9.0
- A:  >= 8.5
- B+: >= 8.0
- B:  >= 7.0
- C+: >= 6.0
- C:  >= 5.5
- D+: >= 5.0
- D:  >= 4.0
- **F:** < 4.0 HOẶC < 3.0 ĐTB_TH với môn có thực hành (bao gồm tích hợp/thực hành đơn thuần)

---

# State Machine – Vòng đời của một bản ghi điểm số

| **Trạng thái từ** | **Trạng thái đến** | **Điều kiện / Tác nhân kích hoạt** |
| --- | --- | --- |
| `[*] (Khởi tạo)` | RAW_UPLOADED | Giảng viên upload file bảng điểm thành phần thô lên hệ thống |
| RAW_UPLOADED | PROCESSING | Databricks Pipeline tự động kích hoạt nạp dữ liệu vào Delta Lake |
| PROCESSING | ACTIVE_CALCULATED | Hoàn thành tính toán ĐTB thành phần hiện tại, làm tròn đến 0.1 và phân loại ban đầu |
| ACTIVE_CALCULATED | SIMULATED | Sinh viên gọi lệnh giả lập chọn mục tiêu điểm mong muốn đạt được |
| SIMULATED | ACTIVE_CALCULATED | Sinh viên thay đổi mức điểm mục tiêu khác trên thanh trượt giao diện |
| ACTIVE_CALCULATED | FINAL_COMPLETED | Nhà trường cập nhật điểm thi cuối kỳ chính thức, khóa điểm vĩnh viễn (Read-only) |
| FINAL_COMPLETED | `[*]` | Cập nhật kết quả vào điểm trung bình tích lũy (GPA) tổng của sinh viên |

```mermaid
stateDiagram-v2
    [*] --> RAW_UPLOADED : Giảng viên upload file điểm thô
    RAW_UPLOADED --> PROCESSING : Databricks pipeline kích hoạt
    PROCESSING --> ACTIVE_CALCULATED : Lưu Delta Lake (Silver), làm tròn 0.1
    ACTIVE_CALCULATED --> SIMULATED : SV chọn mục tiêu điểm chữ (A+ đến D)
    SIMULATED --> ACTIVE_CALCULATED : Thay đổi mục tiêu điểm chữ khác
    ACTIVE_CALCULATED --> FINAL_COMPLETED : Nhập điểm cuối kỳ chính thức (Khóa điểm)
    FINAL_COMPLETED --> [*]
```

---

## 4. CHI TIẾT CÁC MODULE KỸ THUẬT

### Module 1: Quản lý Tài khoản & API Gateway (Chan phụ trách)

Quản lý vòng đời tài khoản và phân quyền truy cập cho hệ thống hướng dịch vụ. Hỗ trợ xác thực tập trung cho **4 vai trò** bằng cơ chế mã hóa mật khẩu bảo mật.

### Module 2: Databricks Pipeline & Hạ tầng Delta Lake

Thiết lập hạ tầng xử lý dữ liệu lớn trên nền tảng **Databricks 3.2**. Xây dựng quy trình xử lý dữ liệu Medallion (Bronze: Lưu log file điểm thô; Silver: Làm sạch/tính toán điểm thành phần, chuẩn hoá quy chế; Gold: Bảng điểm đa thang chuẩn), ETL kiểm thử tự động.

### Module 3: Real-time Simulation Engine (Chan phụ trách)

Phát triển hệ thống API tính toán thời gian thực bằng **FastAPI**. Khi sinh viên kích hoạt thanh trượt chọn điểm chữ mục tiêu (A+ đến D), module này sẽ tự động kiểm tra điểm thành phần để tư vấn ngược số điểm cần đạt các kỳ vọng và nhận diện mọi trường hợp liệt.

### Module 4: Mô hình Máy học Dự báo Cảnh báo Học vụ

Sử dụng Databricks Notebook để huấn luyện mô hình phân loại (Random Forest/XGBoost) dựa trên tập dữ liệu lịch sử điểm số sinh viên khóa cũ. Đóng gói mô hình & inference serverless.

### Module 5: Cổng giao tiếp Client Portal

Phát triển giao diện ứng dụng Web UI responsive bằng React.js / Next.js chia làm 4 phân hệ cổng thông tin (Student, Lecturer, Advisor, Admin). Tích hợp các bộ kéo trượt giả lập và dashboard phân tích học vụ linh hoạt.

### Module 6: Databricks SQL Dashboard & Testing

Xây dựng tập dữ liệu lớn giả lập (Mock data) của 5.000 sinh viên để thực hiện load test hệ thống. Viết bộ mã kiểm thử tự động Pytest (Integration Test) để kiểm chứng toàn bộ flow nghiệp vụ.

---

## PHÂN TÍCH & THIẾT KẾ SYSTEM

### 1. Yêu cầu chức năng hệ thống – Phân loại MoSCoW

#### Nhóm MUST-HAVE (Bắt buộc – MVP):

* Hệ thống xác thực đăng ký/đăng nhập phân quyền rõ ràng cho 4 vai trò bằng mã hóa bảo mật JWT.
* **Giảng viên:** Cấu hình thuộc tính học phần (Số tín chỉ lý thuyết, thực hành) và upload file điểm thành phần.
* **Sinh viên:** Tra cứu điểm thành phần hiện tại, kéo trượt giả lập mục tiêu để nhận ngay gợi ý điểm thi cần đạt.
* **Hệ thống xử lý đám mây:** Đồng bộ hóa quy chế tính điểm 3 loại học phần (Lý thuyết, Thực hành, Tích hợp), làm tròn điểm số đến 0.1 và tự động cảnh báo học vụ.
* Tự động hiển thị nhãn `Cảnh báo học vụ` nếu điểm số dự báo rơi vào thang điểm loại F (0.0 - 3.9).

#### Nhóm SHOULD-HAVE:

* Tích hợp mô hình máy học trên Databricks để hiển thị tỷ lệ % xác suất rớt môn của sinh viên thay vì chỉ dùng công thức tính toán tĩnh.
* Tự động kích hoạt Webhook bắn thông báo đến màn hình của Cố vấn học tập khi số lượng sinh viên trong lớp dính điểm cảnh báo vượt quá 20%.

#### Nhóm COULD-HAVE:

* Dashboard phân tích nâng cao, so sánh hiệu suất học tập và phổ điểm giữa các khóa học hoặc các khoa đào tạo với nhau.

---

### 2. Yêu cầu Phi chức năng

* **Bảo mật & Tính nhất quán đám mây:**
  * Toàn bộ dữ liệu điểm số lưu trữ trên đám mây phải ứng dụng công nghệ Delta Lake để đảm bảo tính toàn vẹn dữ liệu thông qua cơ chế ACID Transaction.
  * Phân tách quyền truy cập dữ liệu nghiêm ngặt: Sinh viên tuyệt đối không có quyền chỉnh sửa dữ liệu điểm gốc trên Delta Lake, chỉ được quyền gửi yêu cầu giả lập/nguyện vọng qua backend API.

* **Hiệu năng:**
  * Điểm chạm API phục vụ giả lập điểm thời gian thực (Simulation Request) phải đạt tốc độ xử lý và phản hồi dưới 150ms để đảm bảo trải nghiệm người dùng tối ưu.

* **Tính bảo trì:**
  * Source code Backend FastAPI tổ chức theo kiến trúc phân tầng chuẩn dịch vụ (Router → Service → Databricks Call Layer), độc lập hoàn toàn với mã nguồn tính toán.

---

### 3. Mô hình Thực thể Dữ liệu (Lược đồ mức Logic trên Delta Lake)

Hệ thống lưu trữ cấu trúc hóa dữ liệu trên Delta Lake thông qua 5 thực thể cốt lõi:

| **Thực thể dữ liệu** | **Mô tả các trường thông tin chính** |
| --- | --- |
| **Users** | `id` (PK), `email` (Unique), `password_hash`, `full_name`, `role` (student/lecturer/advisor/admin), `is_active`, `created_at` |
| **Subjects (Cấu hình môn)** | `ma_mon` (PK), `ten_mon`, `loai_hoc_phan` (ly_thuyet/thuc_hanh/tich_hop), `tong_so_chi`, `so_chi_lt`, `so_chi_th` |
| **Class_Sections (Lớp)** | `ma_lop_hoc_phan` (PK), `ma_mon` (FK), `id_lecturer` (FK), `nam_hoc`, `hoc_ky` |
| **Student_Scores (Bảng điểm)** | `id_score` (PK), `id_student` (FK), `ma_lop_hoc_phan` (FK), `diem_thong_thuong` (Array/List), `diem_giua_ky`, `diem_cuoi_ky`, `diem_tong_ket_10`, `diem_he_4`, `diem_chu`, `status_canh_bao` |
| **Score_Mapping (Quy đổi)** | `diem_10_min`, `diem_10_max`, `diem_he_4`, `diem_chu`, `loai_danh_gia` (Dat/Khong Dat) |

```mermaid
erDiagram
    Users ||--o{ Class_Sections : "quản lý giảng dạy (lecturer)"
    Users ||--o{ Student_Scores : "tra cứu / giả lập (student)"
    Subjects ||--o{ Class_Sections : "phân loại cấu hình học phần"
    Class_Sections ||--o{ Student_Scores : "lưu trữ danh sách điểm lớp"
    Student_Scores }o--|| Score_Mapping : "ánh xạ quy đổi thang điểm chữ"
    Users {
        string id PK
        string email "Unique"
        string password_hash
        string full_name
        string role "student/lecturer/advisor/admin"
        timestamp created_at
    }
    Subjects {
        string ma_mon PK
        string ten_mon
        string loai_hoc_phan "ly_thuyet/thuc_hanh/tich_hop"
        int tong_so_chi
        int so_chi_lt
        int so_chi_th
    }
    Class_Sections {
        string ma_lop_hoc_phan PK
        string ma_mon FK
        string id_lecturer FK
        string nam_hoc
        int hoc_ky
    }
    Student_Scores {
        string id_score PK
        string id_student FK
        string ma_lop_hoc_phan FK
        float diem_giua_ky
        float diem_cuoi_ky
        float diem_tong_ket_10 "Làm tròn 0.1"
        float diem_he_4
        string diem_chu "A+ đến F"
        string status_canh_bao "An toan / Nguy co"
    }
    Score_Mapping {
        float diem_10_min PK
        float diem_10_max
        float diem_he_4
        string diem_chu
        string loai_danh_gia
    }
```

---

### 4. Sơ đồ Kiến trúc Hệ thống hướng Dịch vụ (SOA) trên Đám mây

```mermaid
graph TD
    classDef client fill:#dbeafe,stroke:#3b82f6,stroke-width:2px,color:#1e3a8a;
    classDef frontend fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#3b0764;
    classDef backend fill:#dcfce7,stroke:#22c55e,stroke-width:2px,color:#14532d;
    classDef databricks fill:#ffedd5,stroke:#f97316,stroke-width:2px,color:#7c2d12;
    classDef external fill:#f3f4f6,stroke:#9ca3af,stroke-width:2px,color:#374151,stroke-dasharray: 5 5;

    subgraph Client_Tier ["Tầng Client Interface"]
        A["👤 Users\n(Sinh viên/Giảng viên)"]:::client
    end

    subgraph Frontend_Tier ["Tầng Cổng dịch vụ (Frontend UI Portal)"]
        A --> |"HTTPS"| FE["SmartGPA Web Portals\n(Student / Lecturer / Advisor / Admin Dashboards)"]:::frontend
        FE --> |"fetch() + JWT Token"| B
    end

    subgraph Application_Tier ["Tầng Điều phối API (FastAPI Backend Gateway)"]
        B("Auth Gateway\n(JWT Verification & Role Check)"):::backend
        B --> C["Simulation Core\n(Xử lý tham số mục tiêu điểm chữ)"]:::backend
        B --> D["Data Ingestion Router\n(Tiếp nhận file điểm từ Giảng viên)"]:::backend
    end

    subgraph Databricks_Tier ["Tầng Nền tảng Đám mây (Databricks 3.2 Lakehouse)"]
        C --> |"REST Call"| E["Databricks Serverless Endpoint\n(Hàm tính toán điểm đảo thời gian thực)"]:::databricks
        D --> |"Stream nạp dữ liệu"| F["Bronze Table\n(Lưu log file điểm thô)"]:::databricks
        F --> |"Spark Job ETL\nMap cấu hình số chỉ"| G["Silver Table\n(Tính toán quy chế & Làm tròn 0.1)"]:::databricks
        G --> |"Ánh xạ bảng quy đổi"| H["Gold Table\n(Bảng điểm đa thang điểm chuẩn chuẩn)"]:::databricks
        G -.-> |"Huấn luyện / Dự báo"| I["MLflow Serving\n(Mô hình dự đoán xác suất rớt môn)"]:::databricks
        I -.-> |Trả kết quả nguy cơ| C
        H --> |Cung cấp dữ liệu báo cáo| K["Databricks SQL Dashboard\n(BI Reports cho Nhà trường)"]:::databricks
    end

    subgraph External_Tier ["Dịch vụ Cảnh báo Đám mây"]
        K -.-> |"Trigger Alert >20% F"| L["Notification Service\n(Webhook bắn cảnh báo học vụ)"]:::external
    end
```

---

## KẾ HOẠCH PHÁT TRIỂN DỰ ÁN (MVP PHASE)

**1. Kế hoạch kiểm thử dịch vụ tích hợp**

| Mã TC | Module dịch vụ | Hành động kiểm thử | Kết quả mong đợi tối ưu |
| --- | --- | --- | --- |
| TC-01 | Auth Gateway | Gọi endpoint yêu cầu giả lập điểm nhưng truyền token hết hạn hoặc sai quyền | Hệ thống trả về mã lỗi `401 Unauthorized` hoặc `403 Forbidden`. |
| TC-02 | Ingestion Service | Giảng viên upload file danh sách điểm định dạng không hợp lệ | Hệ thống chặn từ tầng Gateway, trả về `422 Unprocessable Entity`. |
| TC-03 | Data Rounding | Điểm tổng kết thực tế tính ra là 8.44 hoặc 8.46 | Databricks xử lý lưu vào Silver Table làm tròn chính xác thành 8.4 và 8.5. |
| TC-04 | Grade Mapping | Điểm học phần tính ra đạt mốc 8.0 | Hệ thống tự động map chính xác sang điểm hệ chữ **B+** và hệ 4 là **3.5** theo đúng `image_4.png`. |
| TC-05 | Inverse Calc (LT) | Môn Lý thuyết: Điểm TK=8.0, GK=9.0; Chọn mục tiêu đạt loại **A** (Mốc 8.5) | Simulation Engine tính đảo, trả về kết quả điểm cuối kỳ cần đạt |
| TC-06 | Inverse Calc (TH) | Môn Tích hợp (2 chỉ LT, 1 chỉ TH): Điểm thực hành=8.0; Chọn mục tiêu đạt loại **A** (Mốc 8.5) | Simulation Engine tính toán đảo, thông báo sinh viên cần đạt mức tối thiểu ở các nhánh |
| TC-07 | Feasibility Alert | Sinh viên điểm hiện tại quá thấp, chọn mục tiêu đạt loại **A+** | Hệ thống nhận diện điểm cuối kỳ cần đạt > 10.0, hiện thông báo không khả thi |
| TC-08 | ML Prediction | Sinh viên có điểm giữa kỳ và thường kỳ dưới mốc 3.5 | MLflow Endpoint ghi nhận dữ liệu, trả về xác suất nguy cơ rớt môn cao (>70%). |

---

## CÂU HỎI PHẢN BIỆN DÀNH CHO HỘI ĐỒNG

1. **Về tối ưu chi phí hạ tầng Cloud:** Vì tính năng kéo trượt "Giả lập mục tiêu" của sinh viên đòi hỏi hệ thống phải tính toán ngược và trả kết quả nhanh nên sẽ hạn chế số lần gọi pipeline thực tế bằng cách cache kết quả tạm/tối ưu job Databricks serverless endpoint.
2. **Về thiết kế cấu trúc lưu trữ lớn trên Delta Lake:** Để phục vụ cho phân hệ Cố vấn học tập truy vấn và lọc nhanh danh sách sinh viên dính cờ cảnh báo, nhóm áp dụng kỹ thuật partition phân cụm dữ liệu theo năm/khoa/học kỳ, tăng tốc truy vấn ...

