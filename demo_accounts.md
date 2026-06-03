# 🎓 SmartGPA – Danh sách Tài khoản Thử nghiệm (Demo Accounts)

Tài liệu này tổng hợp toàn bộ các tài khoản thử nghiệm (demo) đã được thiết lập sẵn trong hệ thống SmartGPA (cấu hình trong `fake_db.py` và giao diện Đăng nhập nhanh). Tất cả tài khoản sử dụng mật khẩu chung là **`password123`**.

---

## 📋 1. Danh sách tài khoản hệ thống

### 🧑‍🎓 Phân hệ Sinh viên (Student Accounts)
*Đồng bộ trực tiếp với danh sách học viên trên cơ sở dữ liệu Delta Lake (Gold Table) của Databricks.*

| Tên Sinh viên | Email Đăng nhập | Mật khẩu | Mã số Sinh viên (MSSV) | Môn học đăng ký trong học kỳ |
|---|---|---|---|---|
| **Nguyễn Thảo Anh** | `thaoanh.sv1001@gmail.com` | `password123` | **`SV1001`** | Lập trình Python (Tích hợp), Cơ sở dữ liệu, Giáo dục quốc phòng |
| **Vũ Hải Vy** | `haivy.sv1002@gmail.com` | `password123` | **`SV1002`** | Lập trình Python (Tích hợp), Cơ sở dữ liệu |
| **Nguyễn Văn An** | `student@smartgpa.edu` | `password123` | **`SV123456`** | Cấu trúc dữ liệu & Giải thuật, Thực hành Hệ điều hành, Mạng máy tính |
> **Note:** Integrated courses require both theory and practice columns; practical score (TH) must be ≥ 3.0 to compute final grade.

> **⭐ Điểm nhấn cao cấp:** Khi Sinh viên đăng nhập, hệ thống sẽ tự động liên kết MSSV của họ vào phiên làm việc. Khi tích chọn **"Đồng bộ điểm thực tế từ Databricks"**, MSSV sẽ tự động điền và khóa lại, giúp trải nghiệm đồng bộ điểm thi cuối kỳ chỉ bằng 1 cái click chuột!

> **🆕 Tự động tạo tài khoản Sinh viên mới khi nạp điểm:** Khi Giảng viên upload bảng điểm lớp học phần (.csv), hệ thống tự động quét danh sách sinh viên. Các sinh viên chưa có tài khoản sẽ được hệ thống đăng ký tự động theo quy chế:
> - **Tài khoản (Email):** `{ten}.{mssv}@smartgpa.edu` (Ví dụ: sinh viên **Nguyễn Trần Khánh Vy** MSSV **23670631** sẽ có tài khoản `khanhvy.23670631@smartgpa.edu`).
> - **Mật khẩu chung:** `password123`

> **🆕 Hệ thống Thông báo Sinh viên (Real-time & Email):** Sinh viên có thể theo dõi trực tiếp các thông báo thời gian thực thông qua biểu tượng **Chuông thông báo** (có Badge số lượng chưa đọc, dropdown kính mờ mượt mà) ở góc trên thanh điều hướng. Đồng thời, hệ thống mô phỏng gửi email thông báo tương ứng ra console logs của FastAPI. Thông báo được tự động gửi khi:
> - Giảng viên nạp bảng điểm môn học mới (`/upload/file`).
> - Giảng viên điều chỉnh điểm số học phần (`/upload/edit`).
> - Admin g?i th? nh?c nh? c?nh b?o h?c v? (`/simulation/send-warning-email`).

---

### 🧑‍🏫 Phân hệ Giảng viên (Lecturer Accounts)
*Giảng viên tương ứng với danh sách môn học được phân công. Mỗi giảng viên phụ trách nhiều môn học, email có định dạng `tengiangvien.magiangvien@smartgpa.edu`.*

| Tên Giảng viên | Email Đăng nhập | Mật khẩu | Mã Giảng viên (Mã GV) | Danh sách học phần phụ trách giảng dạy |
|---|---|---|---|---|
| **TS. Trần Thị Bình** | `thibinh.gv1001@smartgpa.edu` | `password123` | **`GV1001`** | Lập trình Python (`INT1001`), Cơ sở dữ liệu (`INT1002`), Cấu trúc dữ liệu & Giải thuật (`mon_1`) |
| **TS. Nguyễn Minh Triết** | `minhtriet.gv1002@smartgpa.edu` | `password123` | **`GV1002`** | Mạng máy tính (`mon_2`), Thực hành Hệ điều hành (`mon_3`), Thực hành OOP (`mon_4`), Giáo dục QP (`GDQP102`) |

> **⭐ Điểm nhấn cao cấp:** Giảng viên có quyền tải lên bảng điểm CSV cho các lớp mình dạy và sử dụng **Delta Gold Table Editor** chỉnh sửa trực tiếp điểm số của bất kỳ học viên nào.

---

### 🧑‍💼 Phân hệ Quản lý (Admin Account)
*Phụ trách giám sát chất lượng đào tạo, cảnh báo học tập sớm và bảo trì cấu hình.*

| Vai trò | Email Đăng nhập | Mật khẩu | Tên hiển thị | Tính năng phụ trách |
|---|---|---|---|---|
| **Quản trị viên** | `admin@smartgpa.edu` | `password123` | **Admin Đào Tạo** | **System Audit Logs:** Giám sát nhật ký hoạt động hệ thống thời gian thực (ai nạp điểm môn nào, ai sửa điểm của sinh viên nào); Cấu hình bảng quy đổi điểm. |

---

## 🚀 2. Kịch bản chạy thử nghiệm demo (End-to-End Demo Guide)

### 🔹 Kịch bản 1: Giảng viên cập nhật điểm số trực tiếp
1. Đăng nhập tài khoản Giảng viên **TS. Trần Thị Bình** (`thibinh.gv1001@smartgpa.edu`).
2. Cuộn xuống thẻ **Công cụ điều chỉnh điểm trực tiếp (Delta Gold Table Editor)**.
3. Nhập MSSV **`SV1001`** (Nguyễn Thảo Anh), chọn môn **Lập trình Python**, chọn cột **Giữa kỳ (GK)** và cập nhật giá trị mới là **`8.0`**. Bấm **Lưu điểm mới**.
4. Hệ thống báo đồng bộ Gold Delta Table thành công.

### ?? K?ch b?n 2: Admin g?i mail c?nh b?o & ??nh gi? MLflow
2. Quan sát bảng **Danh sách Cảnh báo Học vụ (Silver Table)**. Hệ thống tự động phát hiện sinh viên dính lỗi (ví dụ: điểm thực hành liệt $< 3.0$ hoặc tích lũy quá thấp) và hiển thị xác suất rớt môn (%) tính từ mô hình Random Forest.
3. Nhấp nút **`Gửi Cảnh báo`** trên dòng sinh viên **Nguyễn Trần Khánh Vy** (hoặc Trần Lê Tuấn).
4. Hệ thống thực thi API gửi mail khẩn cấp đến hòm thư sinh viên và phản hồi trạng thái **`Đã gửi Email! ✉️`** thành công.

### 🔹 Kịch bản 3: Admin giám sát hoạt động thời gian thực (Audit Logs)
1. Đăng nhập tài khoản Admin **Admin Đào Tạo** (`admin@smartgpa.edu`).
2. Cuộn xuống bảng **Nhật ký Hoạt động Hệ thống & Giám sát Giáo viên (Audit Logs)**.
3. Quan sát các dòng nhật ký mới nhất: Bạn sẽ lập tức nhìn thấy log chi tiết về hành động sửa điểm ở **Kịch bản 1** và gửi mail cảnh báo ở **Kịch bản 2** được tự động cập nhật thời gian thực chuẩn xác từng giây!

### 🔹 Kịch bản 4: Sinh viên đăng nhập & Giả lập điểm ngược tự động
1. Đăng nhập tài khoản Sinh viên **Nguyễn Thảo Anh** (`thaoanh.sv1001@gmail.com`).
2. Tích chọn ô **`🔌 Đồng bộ điểm thực tế từ Databricks (Gold Table)`**.
3. MSSV **`SV1001`** tự động được điền và khóa lại an toàn. Chọn môn **Lập trình Python**.
4. Toàn bộ điểm thành phần thực tế vừa được cập nhật ở **Kịch bản 1** sẽ tự động được tải về.
5. Sinh viên kéo chọn điểm chữ mục tiêu (ví dụ: **`A`** hoặc **`A+`**) để nhận ngay điểm thi cuối kỳ tối thiểu cần đạt chính xác theo trọng số!
