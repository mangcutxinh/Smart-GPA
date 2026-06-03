# SmartGPA - Quy Trình Làm Bài Và Triển Khai Databricks

Tài liệu này ghi lại toàn bộ quy trình làm bài giữa kỳ cho đề tài SmartGPA, bao gồm kiến trúc, quy định tính điểm, cách chạy Databricks, các file cần dùng và minh chứng cần chụp.

## 1. Bối Cảnh Bài Làm

Học phần: Kiến trúc hướng dịch vụ và Điện toán đám mây  
Đề tài: SmartGPA - Hệ thống phân tích điểm học tập, giả lập điểm mục tiêu và cảnh báo nguy cơ rớt môn  
Cloud platform bắt buộc: Databricks  
GitHub: https://github.com/mangcutxinh/Smart-GPA

Yêu cầu giữa kỳ:

- Nộp slide 10-12 trang.
- File nộp dạng `.pptx` hoặc `.pdf`.
- Bắt buộc có link GitHub trực tiếp trong slide.
- Bắt buộc thể hiện tiến độ triển khai và minh chứng trên Databricks.
- Kiến trúc trình bày giữa kỳ được xem là kiến trúc đã chốt cho cuối kỳ.

## 2. Ràng Buộc Databricks Hiện Tại

Tài khoản Databricks hiện tại là **Databricks Free Edition**.

Qua giao diện đã kiểm tra:

- Không cần tạo cluster thủ công.
- Notebook có lựa chọn **Serverless**.
- Serverless đang có trạng thái màu xanh.
- Environment version đang là version 5.
- Workspace có thể linked với Git/GitHub.

Do đó, cách triển khai đúng là:

```text
GitHub repo
 -> Databricks workspace linked Git
 -> Open notebook
 -> Select Serverless
 -> Run notebook
 -> Create Bronze/Silver/Gold Delta tables
```

Không ghi trong slide là nhóm tự tạo cluster nếu tài khoản không có quyền tạo cluster.

## 3. Kiến Trúc Hệ Thống Đã Chốt

```text
User
 │
 ▼
Web Dashboard / React Frontend
 │
 ▼
FastAPI API Gateway
 │
 ├── Auth Service
 │      └── Đăng nhập, JWT, phân quyền student / lecturer / admin
 │
 ├── Student Service
 │      └── Xem điểm, xem cảnh báo, nhận thông báo
 │
 ├── Upload / Grade Service
 │      └── Giảng viên upload file điểm CSV
 │
 ├── Grade Target Simulation Service
 │      └── Tính điểm cuối kỳ cần đạt theo mục tiêu điểm chữ
 │
 └── Warning / Prediction Service
        └── Dự báo và cảnh báo nguy cơ rớt môn

                 │
                 ▼

        Databricks Platform
                 │
 ┌───────────────┼────────────────┐
 ▼               ▼                ▼
Delta Lake    ETL Pipeline      ML Model
Bronze        PySpark           MLlib / MLflow
Silver        Notebook / Job    Risk Prediction
Gold
                 │
                 ▼
        Databricks SQL Analytics
                 │
                 ▼
        Dashboard / API Query Results
```

## 4. Luồng Dữ Liệu Chính

### 4.1. Luồng Upload Và ETL Điểm

```text
Lecturer
 -> Web Dashboard
 -> FastAPI API Gateway
 -> Upload / Grade Service
 -> Raw File Storage
 -> Databricks Serverless Notebook / PySpark ETL
 -> Bronze Delta Table
 -> Silver Delta Table
 -> Gold Delta Table
 -> Spark SQL Analytics
```

### 4.2. Luồng Giả Lập Điểm Cuối Kỳ

```text
Student
 -> Web Dashboard
 -> FastAPI API Gateway
 -> Grade Target Simulation Service
 -> Query Gold Delta Table
 -> Calculate diem_cuoi_ky_can_dat
 -> Return result to student
```

### 4.3. Luồng Cảnh Báo Nguy Cơ Rớt Môn

```text
Admin
 -> Web Dashboard
 -> FastAPI API Gateway
 -> Warning / Prediction Service
 -> Query Gold Delta Table
 -> Warning rule / ML model
 -> Risk score and warning list
```

## 5. Quy Định Tính Điểm

Điểm cuối kỳ là điểm chưa có tại thời điểm giữa kỳ, nên hệ thống không lưu `diem_cuoi_ky` như điểm thật. Thay vào đó, hệ thống tính:

```text
diem_cuoi_ky_can_dat
```

để biết sinh viên cần đạt bao nhiêu điểm cuối kỳ cho từng mục tiêu điểm chữ.

### 5.1. Môn Lý Thuyết

Quy định:

```text
10% thường xuyên 1
10% thường xuyên 2
30% giữa kỳ
50% cuối kỳ
```

Công thức tổng kết:

```text
T = 0.1 * thuong_xuyen_1
  + 0.1 * thuong_xuyen_2
  + 0.3 * giua_ky
  + 0.5 * diem_cuoi_ky
```

Vì phần quá trình lý thuyết chiếm tối đa 5 điểm, khi cần kết hợp với thực hành theo tín chỉ thì quy về thang 10:

```text
lt_qt_10 = (0.1 * thuong_xuyen_1
          + 0.1 * thuong_xuyen_2
          + 0.3 * giua_ky) / 0.5
```

Rút gọn:

```text
lt_qt_10 = 0.2 * thuong_xuyen_1
         + 0.2 * thuong_xuyen_2
         + 0.6 * giua_ky
```

### 5.2. Môn Thực Hành

Thực hành gồm 3 điểm:

```text
thuc_hanh_1
thuc_hanh_2
thuc_hanh_3
```

Điểm quá trình thực hành:

```text
th_qt_10 = (thuc_hanh_1 + thuc_hanh_2 + thuc_hanh_3) / 3
```

Điểm tổng kết môn thực hành:

```text
T = 0.5 * th_qt_10 + 0.5 * diem_cuoi_ky
```

### 5.3. Môn Tích Hợp

Môn tích hợp gồm lý thuyết và thực hành. Điểm quá trình được tính theo tín chỉ:

```text
qt_10 = (lt_qt_10 * so_chi_lt + th_qt_10 * so_chi_th) / tong_so_chi
```

Trong đó:

```text
tong_so_chi = so_chi_lt + so_chi_th
```

Điểm tổng kết môn tích hợp:

```text
T = 0.5 * qt_10 + 0.5 * diem_cuoi_ky
```

### 5.4. Dự Báo Điểm Cuối Kỳ Cần Đạt

Vì:

```text
T = 0.5 * qt_10 + 0.5 * diem_cuoi_ky
```

nên với mục tiêu điểm `diem_muc_tieu_10`:

```text
diem_cuoi_ky_can_dat = (diem_muc_tieu_10 - 0.5 * qt_10) / 0.5
```

Nếu:

```text
diem_cuoi_ky_can_dat > 10
```

thì mục tiêu không khả thi.

Nếu:

```text
diem_cuoi_ky_can_dat <= 10
```

thì mục tiêu khả thi.

### 5.5. Bảng Mục Tiêu Điểm Chữ

| Điểm chữ | Ngưỡng hệ 10 |
|---|---:|
| A+ | 9.0 |
| A | 8.5 |
| B+ | 8.0 |
| B | 7.0 |
| C+ | 6.0 |
| C | 5.5 |
| D+ | 5.0 |
| D | 4.0 |

## 6. Cấu Trúc Dữ Liệu

### 6.1. Input Raw Data

File mẫu:

```text
data/sample_scores_smartgpa.csv
```

Các cột chính:

| Cột | Ý nghĩa |
|---|---|
| `student_id` | Mã sinh viên |
| `student_name` | Họ tên sinh viên |
| `ma_mon` | Mã môn |
| `ten_mon` | Tên môn |
| `ma_lop_hoc_phan` | Mã lớp học phần |
| `loai_hoc_phan` | `ly_thuyet`, `thuc_hanh`, `tich_hop` |
| `so_chi_lt` | Số tín chỉ lý thuyết |
| `so_chi_th` | Số tín chỉ thực hành |
| `thuong_xuyen_1` | Điểm thường xuyên 1 |
| `thuong_xuyen_2` | Điểm thường xuyên 2 |
| `giua_ky` | Điểm giữa kỳ |
| `thuc_hanh_1` | Điểm thực hành 1 |
| `thuc_hanh_2` | Điểm thực hành 2 |
| `thuc_hanh_3` | Điểm thực hành 3 |

### 6.2. Bronze Table

Tên bảng:

```text
smartgpa_db.bronze_diem_sinh_vien
```

Ý nghĩa:

- Lưu dữ liệu thô.
- Cấu trúc gần giống dữ liệu upload ban đầu.
- Dùng làm minh chứng tầng Bronze trong Delta Lake.

### 6.3. Silver Table

Tên bảng:

```text
smartgpa_db.silver_diem_sinh_vien
```

Ý nghĩa:

- Chuẩn hóa dữ liệu.
- Kiểm tra điểm có nằm trong khoảng 0-10 hay không.
- Tính:
  - `lt_qt_contribution_5`
  - `lt_qt_10`
  - `th_qt_10`
  - `qt_10`
  - `data_quality_status`

### 6.4. Gold Table

Tên bảng:

```text
smartgpa_db.gold_du_bao_diem_cuoi_ky
```

Ý nghĩa:

- Phục vụ API, dashboard và báo cáo.
- Tính điểm cuối kỳ cần đạt cho từng mục tiêu điểm chữ.
- Có các cột quan trọng:
  - `diem_chu_muc_tieu`
  - `diem_muc_tieu_10`
  - `diem_cuoi_ky_can_dat`
  - `kha_thi`
  - `status_canh_bao`

## 7. File Đã Chuẩn Bị Trong Repo

```text
databricks/notebooks/smartgpa_grading_pipeline.py
databricks/sql/grading_rules.sql
data/sample_scores_smartgpa.csv
ke_hoach_lam_bai_giua_ky.md
docs/process.md
```

## 8. Cách Chạy Trên Databricks

### Bước 1: Mở Workspace

Vào Databricks:

```text
Workspace
```

Mở repo Smart-GPA đã linked với GitHub.

Chụp ảnh:

```text
Databricks workspace linked GitHub repo
```

### Bước 2: Mở Notebook

Mở file:

```text
databricks/notebooks/smartgpa_grading_pipeline.py
```

Nếu Databricks chưa tự nhận dạng thành notebook, có thể tạo notebook mới rồi copy nội dung file này vào.

### Bước 3: Chọn Serverless

Ở góc trên notebook, chọn:

```text
Serverless
```

Chụp ảnh:

```text
Notebook đang chọn Serverless, trạng thái xanh
```

### Bước 4: Chạy Từng Cell

Chạy lần lượt:

1. Import thư viện và tạo database.
2. Tạo raw data mẫu.
3. Ghi Bronze table.
4. Tạo Silver table.
5. Tạo bảng mục tiêu điểm chữ.
6. Tạo Gold table dự báo điểm cuối kỳ.
7. Query kết quả mục tiêu A.
8. Query danh sách cảnh báo.

### Bước 5: Kiểm Tra Bảng

Trong notebook hoặc SQL editor, query:

```sql
SELECT * FROM smartgpa_db.bronze_diem_sinh_vien;
SELECT * FROM smartgpa_db.silver_diem_sinh_vien;
SELECT * FROM smartgpa_db.gold_du_bao_diem_cuoi_ky;
```

## 9. Query Dùng Cho Slide

### 9.1. Query Điểm Cuối Kỳ Cần Đạt Mục Tiêu A

```sql
SELECT
  student_id,
  student_name,
  ma_mon,
  ten_mon,
  loai_hoc_phan,
  qt_10,
  diem_chu_muc_tieu,
  diem_muc_tieu_10,
  diem_cuoi_ky_can_dat,
  kha_thi,
  status_canh_bao
FROM smartgpa_db.gold_du_bao_diem_cuoi_ky
WHERE diem_chu_muc_tieu = 'A'
ORDER BY student_id, ma_mon;
```

### 9.2. Query Danh Sách Cảnh Báo

```sql
SELECT
  student_id,
  student_name,
  ma_mon,
  ten_mon,
  loai_hoc_phan,
  qt_10,
  diem_chu_muc_tieu,
  diem_cuoi_ky_can_dat,
  status_canh_bao
FROM smartgpa_db.gold_du_bao_diem_cuoi_ky
WHERE status_canh_bao != 'An toan'
ORDER BY student_id, diem_muc_tieu_10 DESC;
```

## 10. Minh Chứng Cần Chụp Cho Slide

| Minh chứng | Mục đích |
|---|---|
| Databricks workspace | Chứng minh đã dùng Databricks |
| GitHub repo linked trong workspace | Chứng minh code được đồng bộ |
| Notebook chọn Serverless | Giải thích không dùng cluster thủ công |
| Notebook chạy thành công | Chứng minh ETL pipeline |
| Bronze table preview | Chứng minh tầng dữ liệu thô |
| Silver table preview | Chứng minh tầng dữ liệu đã xử lý |
| Gold table preview | Chứng minh dữ liệu phục vụ dự báo |
| Query mục tiêu A | Chứng minh tính `diem_cuoi_ky_can_dat` |
| Query cảnh báo | Chứng minh cảnh báo nguy cơ |
| FastAPI Swagger | Chứng minh API Gateway |
| React dashboard | Chứng minh giao diện người dùng |
| GitHub link trong slide | Bắt buộc theo yêu cầu nộp bài |

## 11. Nội Dung Nên Ghi Trong Slide Databricks

Đoạn mô tả ngắn:

```text
Nhóm triển khai pipeline xử lý dữ liệu điểm trên Databricks Serverless.
Dữ liệu được tổ chức theo mô hình Delta Lake Medallion Architecture:
Bronze lưu dữ liệu thô, Silver chuẩn hóa và tính điểm quá trình, Gold tính điểm cuối kỳ cần đạt theo từng mục tiêu điểm chữ.
Gold table được dùng cho API giả lập điểm, dashboard và cảnh báo nguy cơ rớt môn.
```

## 12. Bảng 12 Slide Theo Yêu Cầu

| Slide | Tên slide | Nội dung chính | Minh chứng cần chèn | Trạng thái |
|---|---|---|---|---|
| 1 | Tên đề tài | SmartGPA, học phần, Databricks, GitHub link | Link GitHub | Đang làm |
| 2 | Thông tin nhóm | Thành viên, MSSV, vai trò | Không bắt buộc | Chưa làm |
| 3 | M?c ti?u h? th?ng | Sinh vi?n, gi?ng vi?n, admin | S? ?? ng?n | ?ang l?m |
| 4 | Kiến trúc SOA | React, FastAPI Gateway, các service | Sơ đồ kiến trúc | Đang làm |
| 5 | Data flow | Upload -> Bronze -> Silver -> Gold -> API | Sơ đồ data flow | Đang làm |
| 6 | Databricks setup | Workspace, Serverless, Git linked | Ảnh workspace và Serverless | Chưa làm |
| 7 | ETL Pipeline | PySpark notebook, xử lý dữ liệu | Ảnh notebook output | Chưa làm |
| 8 | Delta Lake | Bronze/Silver/Gold tables | Ảnh preview bảng | Chưa làm |
| 9 | Gold prediction | `diem_cuoi_ky_can_dat`, `kha_thi`, cảnh báo | Ảnh Gold/query | Chưa làm |
| 10 | Backend/Frontend | API Gateway, upload, simulation, dashboard | Swagger/UI screenshot | Đang làm |
| 11 | Khó khăn | Không tạo cluster, dùng Serverless, còn thiếu gì | Bảng khó khăn | Đang làm |
| 12 | Kế hoạch cuối kỳ | Kết nối API thật, MLflow, dashboard, test | Timeline | Chưa làm |

## 13. Khó Khăn Và Cách Trình Bày

Khó khăn hiện tại:

```text
Tài khoản Databricks Free Edition không tạo cluster thủ công.
```

Cách trình bày đúng:

```text
Nhóm sử dụng Databricks Serverless để chạy notebook ETL thay cho cluster tự quản lý.
Pipeline vẫn được triển khai trên Databricks và tạo các Delta tables Bronze/Silver/Gold.
```

Không nên ghi:

```text
Nhóm đã tạo cluster riêng
```

nếu thực tế không có quyền tạo cluster.

