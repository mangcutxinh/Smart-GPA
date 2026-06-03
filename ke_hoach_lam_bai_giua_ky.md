# Kế Hoạch Làm Bài Giữa Kỳ - SmartGPA

Học phần: Kiến trúc hướng dịch vụ và Điện toán đám mây  
Đề tài: SmartGPA - Hệ thống phân tích điểm học tập, giả lập điểm mục tiêu và cảnh báo nguy cơ rớt môn  
Nền tảng cloud bắt buộc: Databricks  
GitHub: https://github.com/mangcutxinh/Smart-GPA  
Trạng thái tài liệu: dùng để cập nhật liên tục trong quá trình làm bài

## 1. Mục Tiêu Của Bài Giữa Kỳ

Bài giữa kỳ không yêu cầu nộp báo cáo văn bản, chỉ nộp slide 10-12 trang dạng `.pptx` hoặc `.pdf`. Tuy nhiên, file này được dùng làm kế hoạch nội bộ để theo dõi tiến độ và đảm bảo slide đáp ứng đúng yêu cầu.

Mục tiêu cần đạt:

- Trình bày rõ đề tài, nhóm, mục tiêu hệ thống.
- Chốt kiến trúc hệ thống theo hướng SOA/Microservices.
- Chứng minh dự án có triển khai trên Databricks.
- Có minh chứng workspace, cluster/compute, notebook/job, ETL, Delta Lake hoặc pipeline.
- Có link GitHub trực tiếp trong slide.
- Có kế hoạch hoàn thiện đến cuối kỳ.

## 2. Phạm Vi Hệ Thống SmartGPA

SmartGPA là hệ thống hỗ trợ phân tích kết quả học tập và cảnh báo học vụ.

Các chức năng chính:

- Sinh viên xem dữ liệu điểm và giả lập điểm cần đạt để đạt mục tiêu A, B+, C...
- Giảng viên upload file điểm CSV.
- Backend kiểm tra file, validate dữ liệu và đưa dữ liệu vào luồng xử lý.
- Databricks xử lý dữ liệu theo mô hình Bronze -> Silver -> Gold.
- Admin xem danh s?ch sinh vi?n c? nguy c? r?t m?n.
- Hệ thống có thể dùng MLlib/MLflow để dự đoán nguy cơ rớt môn.

## 3. Kiến Trúc Đã Chốt Cho Giữa Kỳ

Kiến trúc này nên được xem là bản chốt để đưa vào slide giữa kỳ. Báo cáo cuối kỳ nên bám theo kiến trúc này, nếu thay đổi cần giải trình.

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
 │      └── Tính điểm cần đạt theo mục tiêu điểm chữ
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
 -> Databricks Auto Loader / PySpark Notebook
 -> Bronze Delta Table
 -> Silver Delta Table
 -> Gold Delta Table
 -> Spark SQL Analytics
```

Ý nghĩa:

- `Bronze`: lưu dữ liệu thô từ file điểm.
- `Silver`: dữ liệu đã làm sạch, chuẩn hóa kiểu dữ liệu, kiểm tra lỗi.
- `Gold`: dữ liệu đã tính toán xong, sẵn sàng cho API, dashboard và ML.

### 4.2. Luồng Sinh Viên Giả Lập Điểm

```text
Student
 -> Web Dashboard
 -> FastAPI API Gateway
 -> Grade Target Simulation Service
 -> Query Gold Delta Table
 -> Calculate required final/practical score
 -> Return simulation result to student
```

### 4.3. Luồng Cảnh Báo Nguy Cơ Rớt Môn

```text
Admin
 -> Web Dashboard
 -> FastAPI API Gateway
 -> Warning / Prediction Service
 -> Query Gold Delta Table
 -> MLlib / MLflow Model
 -> Risk score
 -> Warning list / Analytics Dashboard
```

## 5. Kế Hoạch Làm Bài Theo Từng Bước

| Bước | Công việc | Kết quả cần có | Trạng thái | Ghi chú cập nhật |
|---|---|---|---|---|
| 1 | Chốt đề tài và mục tiêu hệ thống | Tên đề tài, mục tiêu, phạm vi rõ ràng | Đang làm | Dùng đề tài SmartGPA |
| 2 | Chốt kiến trúc SOA | Sơ đồ tổng thể services, APIs, data flow | Đang làm | Dùng kiến trúc trong mục 3 |
| 3 | Chuẩn hóa repo GitHub | README, backend, frontend, Databricks docs rõ ràng | Đang làm | GitHub phải xuất hiện trong slide |
| 4 | Chuẩn bị Databricks workspace | Có ảnh workspace và compute/cluster | Chưa làm | Cần chụp màn hình |
| 5 | Tạo notebook ETL trên Databricks | Notebook đọc dữ liệu và ghi Bronze/Silver/Gold | Chưa làm | Có thể dùng PySpark |
| 6 | Tạo Delta tables | `bronze_diem_sinh_vien`, `silver_diem_sinh_vien`, `gold_diem_sinh_vien` | Chưa làm | Cần ảnh table preview |
| 7 | Chạy thử ETL pipeline | Notebook/job chạy thành công | Chưa làm | Cần ảnh run status |
| 8 | Kiểm tra backend API | Swagger chạy được, API upload/simulation hoạt động | Đang làm | Đã có FastAPI và test |
| 9 | Kiểm tra frontend demo | Giao diện student/lecturer/admin hoạt động | Đang làm | Cần ảnh giao diện |
| 10 | Thu thập minh chứng | Ảnh Databricks, Swagger, UI, GitHub | Chưa làm | Đưa trực tiếp vào slide |
| 11 | Làm slide 10-12 trang | File `.pptx` hoặc `.pdf` | Chưa làm | Bám bảng 12 slide bên dưới |
| 12 | Kiểm tra lần cuối trước khi nộp | Đủ GitHub link, đủ ảnh, đúng yêu cầu | Chưa làm | Nộp LMS đúng hạn |

Quy ước trạng thái:

- `Chưa làm`: chưa bắt đầu.
- `Đang làm`: đã có một phần, cần hoàn thiện.
- `Xong`: đã có minh chứng và có thể đưa vào slide.
- `Cần sửa`: đã làm nhưng chưa đạt yêu cầu.

## 6. Bảng 12 Slide Cập Nhật Liên Tục

| Slide | Tên slide | Nội dung bắt buộc | Minh chứng cần chèn | Trạng thái | Việc cần làm tiếp |
|---|---|---|---|---|---|
| 1 | Tên đề tài | SmartGPA, tên học phần, nền tảng Databricks, link GitHub | Link GitHub trực tiếp | Đang làm | Thêm tên nhóm và ngày báo cáo |
| 2 | Thông tin nhóm | Danh sách 1-5 thành viên, vai trò từng người | Không bắt buộc ảnh | Chưa làm | Điền họ tên, MSSV, phân công |
| 3 | Mục tiêu hệ thống | Vấn đề cần giải quyết, người dùng chính, chức năng chính | Có thể dùng icon/diagram nhỏ | Đang làm | Viết ngắn gọn 3-5 ý |
| 4 | Kiến trúc SOA | Web Dashboard, API Gateway, các service nghiệp vụ | Sơ đồ kiến trúc tổng thể | Đang làm | Vẽ lại sơ đồ bằng draw.io/Mermaid |
| 5 | Data flow tổng thể | Upload điểm -> Databricks -> Delta Lake -> API/dashboard | Sơ đồ luồng dữ liệu | Đang làm | Làm rõ Bronze/Silver/Gold |
| 6 | Databricks setup | Workspace, compute/cluster, SQL Warehouse | Ảnh Databricks workspace và cluster | Chưa làm | Tạo/chụp Databricks workspace |
| 7 | ETL Pipeline | Notebook/job xử lý dữ liệu bằng PySpark | Ảnh notebook output hoặc job status | Chưa làm | Chạy notebook Databricks thật |
| 8 | Delta Lake | Bronze, Silver, Gold tables | Ảnh preview các bảng Delta | Chưa làm | Tạo bảng và chụp màn hình |
| 9 | Backend/API progress | FastAPI, auth, upload, simulation, warning endpoints | Ảnh Swagger `/docs`, test result | Đang làm | Chụp Swagger và kết quả test |
| 10 | Frontend progress | React dashboard cho student/lecturer/admin | Ảnh giao diện demo | Đang làm | Chạy frontend và chụp màn hình |
| 11 | Khó khăn và tồn đọng | Lỗi kỹ thuật, phần chưa hoàn thành, nguyên nhân | Có thể dùng bảng ngắn | Chưa làm | Cập nhật sau khi chạy Databricks |
| 12 | Kế hoạch cuối kỳ | Công việc còn lại, timeline, cam kết bám kiến trúc | Timeline ngắn | Chưa làm | Chốt timeline đến cuối kỳ |

## 7. Checklist Minh Chứng Bắt Buộc

| Minh chứng | Bắt buộc? | Trạng thái | Ghi chú |
|---|---:|---|---|
| Link GitHub trong slide | Có | Đang làm | Nên đặt ở slide 1 và slide minh chứng |
| Ảnh Databricks workspace | Có | Chưa làm | Chụp màn hình workspace |
| Ảnh cluster/compute | Có | Chưa làm | Chụp trạng thái running/available |
| Ảnh notebook ETL | Có | Chưa làm | Có output thành công |
| Ảnh job/pipeline status | Nên có | Chưa làm | Nếu chưa có job thì dùng notebook run |
| Ảnh Bronze table | Có | Chưa làm | Preview dữ liệu thô |
| Ảnh Silver table | Có | Chưa làm | Preview dữ liệu đã làm sạch |
| Ảnh Gold table | Có | Chưa làm | Preview dữ liệu phục vụ API/ML |
| Ảnh FastAPI Swagger | Nên có | Chưa làm | `/docs` hiển thị endpoints |
| Ảnh React dashboard | Nên có | Chưa làm | Student/lecturer/admin |
| Kết quả test backend | Nên có | Đang làm | Có thể ghi `57 passed` nếu vẫn đúng |

## 8. Nội Dung Databricks Cần Làm

### Ràng buộc hiện tại

Tài khoản Databricks hiện tại không có quyền tạo cluster/compute mới. Nhóm chỉ sử dụng được workspace đã linked với GitHub.

Điều này ảnh hưởng đến cách triển khai:

- Không tự tạo được cluster để chạy notebook.
- Vẫn có thể quản lý notebook/code trong Databricks workspace thông qua Git.
- Giao diện Databricks hiện có lựa chọn `Serverless` trong notebook, trạng thái màu xanh, Environment version 5.
- Vì vậy nhóm có thể chạy notebook bằng Serverless thay vì tạo cluster thủ công.
- Cần chụp minh chứng notebook đang chọn `Serverless` để giải thích nền tảng triển khai.

Phương án làm bài giữa kỳ theo quyền hiện tại:

1. Push toàn bộ notebook, SQL script và data mẫu lên GitHub.
2. Mở repo đã linked trong Databricks workspace.
3. Import/mở notebook từ Git trong Databricks.
4. Chọn `Serverless` trong compute selector của notebook.
5. Chạy ETL notebook để tạo Bronze/Silver/Gold Delta tables.
6. Chụp minh chứng notebook output, table preview và Spark SQL query result.

Tối thiểu cần có:

```text
smartgpa_db.bronze_diem_sinh_vien
smartgpa_db.silver_diem_sinh_vien
smartgpa_db.gold_du_bao_diem_cuoi_ky
```

Notebook Databricks nên có các phần:

1. Tạo database/schema.
2. Đọc file điểm CSV.
3. Ghi dữ liệu thô vào Bronze.
4. Làm sạch dữ liệu sang Silver.
5. Tính điểm quá trình và dự báo điểm cuối kỳ cần đạt sang Gold.
6. Query thử Gold bằng Spark SQL.

File đã chuẩn bị trong repo:

- `databricks/notebooks/smartgpa_grading_pipeline.py`
- `databricks/sql/grading_rules.sql`
- `data/sample_scores_smartgpa.csv`

### Quy định tính điểm đang dùng trong notebook

Điểm cuối kỳ là điểm chưa có ở giữa kỳ, nên hệ thống dự báo/giả lập `diem_cuoi_ky_can_dat`.

Môn lý thuyết:

```text
T = 0.1 * thuong_xuyen_1
  + 0.1 * thuong_xuyen_2
  + 0.3 * giua_ky
  + 0.5 * diem_cuoi_ky
```

Phần quá trình lý thuyết quy về thang 10:

```text
lt_qt_10 = 0.2 * thuong_xuyen_1
         + 0.2 * thuong_xuyen_2
         + 0.6 * giua_ky
```

Môn thực hành:

```text
th_qt_10 = (thuc_hanh_1 + thuc_hanh_2 + thuc_hanh_3) / 3
T = 0.5 * th_qt_10 + 0.5 * diem_cuoi_ky
```

Môn tích hợp:

```text
qt_10 = (lt_qt_10 * so_chi_lt + th_qt_10 * so_chi_th) / tong_so_chi
T = 0.5 * qt_10 + 0.5 * diem_cuoi_ky
```

Dự báo điểm cuối kỳ cần đạt:

```text
diem_cuoi_ky_can_dat = (diem_muc_tieu_10 - 0.5 * qt_10) / 0.5
```

## 9. Nội Dung Backend Cần Chứng Minh

Các file/code chính:

- `backend/app/main.py`: FastAPI entry point.
- `backend/app/routers/auth.py`: đăng nhập và phân quyền.
- `backend/app/routers/upload.py`: upload file điểm.
- `backend/app/routers/simulation.py`: giả lập điểm và cảnh báo.
- `backend/app/db/databricks_db.py`: kết nối Databricks SQL Warehouse hoặc fallback local.
- `backend/tests/`: test xác thực, upload, simulation, tích hợp dữ liệu.

Các API nên demo:

```text
POST /auth/login
POST /upload/file
POST /simulation/calc
GET  /simulation/warnings
```

## 10. Nội Dung Frontend Cần Chứng Minh

Các màn hình nên chụp:

- Màn hình đăng nhập.
- Student dashboard: chọn môn, chọn mục tiêu điểm, xem kết quả cần đạt.
- Lecturer dashboard: upload file điểm.
- Admin dashboard: danh sách cảnh báo nguy cơ rớt môn.
- Admin dashboard nếu có đủ thời gian.

## 11. Khó Khăn Dự Kiến

| Vấn đề | Ảnh hưởng | Hướng xử lý |
|---|---|---|
| Chưa có Databricks credential thật | Backend chưa query trực tiếp Gold table thật | Dùng `.env`, SQL Warehouse, token service principal |
| File upload local chưa phải cloud storage thật | Chưa đủ giống pipeline production | Trình bày là MVP/midterm, cuối kỳ tích hợp cloud storage |
| Dữ liệu mẫu nhỏ | ML chưa có độ chính xác cao | Giữa kỳ tập trung pipeline, cuối kỳ mở rộng dataset |
| Slide cần nhiều ảnh minh chứng | Thiếu ảnh sẽ bị trừ điểm | Chụp từng bước khi làm Databricks |

## 12. Timeline Đến Cuối Kỳ

| Giai đoạn | Công việc | Kết quả |
|---|---|---|
| Tuần 1 | Hoàn thiện Databricks workspace, notebook ETL, Delta tables | Có minh chứng Databricks giữa kỳ |
| Tuần 2 | Kết nối FastAPI với Databricks SQL Warehouse | API query Gold table thật |
| Tuần 3 | Hoàn thiện frontend demo theo vai trò | Demo end-to-end rõ ràng |
| Tuần 4 | Cải thiện warning/ML model và dashboard phân tích | Có cảnh báo học vụ tốt hơn |
| Tuần 5 | Test, sửa lỗi, chụp minh chứng, làm slide cuối kỳ | Sẵn sàng báo cáo cuối kỳ |

## 13. Ghi Chú Cập Nhật Hằng Ngày

| Ngày | Việc đã làm | Kết quả | Việc tiếp theo |
|---|---|---|---|
| 2026-06-02 | Tạo kế hoạch làm bài và bảng 12 slide | Có file Markdown theo dõi tiến độ | Điền thông tin nhóm và bắt đầu làm Databricks |
