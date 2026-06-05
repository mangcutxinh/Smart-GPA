# SmartGPA

_Hệ thống phân tích học thuật, giả lập điểm mục tiêu và dự báo cảnh báo học vụ dựa trên kiến trúc SOA & nền tảng đám mây Databricks._

---

## 📌 Giới thiệu

**SmartGPA** là hệ thống hỗ trợ sinh viên và nhà trường trong việc:
- Giả lập lộ trình điểm số, xác định số điểm thành phần cần đạt để tới được các mốc GPA hoặc điểm chữ mong muốn.
- Dự báo sinh viên có nguy cơ rớt môn dựa trên dữ liệu lịch sử.
- Quản lý tập trung và phân tích dữ liệu điểm học tập qua nhiều lớp lưu trữ hiện đại (Delta Lake: Bronze - Silver - Gold).
- Kết nối dữ liệu liền mạch giữa các phòng ban, giảng viên, quản trị viên và sinh viên theo kiến trúc hướng dịch vụ (SOA).

Dự án triển khai trên nền tảng đám mây **Databricks**, áp dụng các công nghệ hiện đại về Data Engineering, Machine Learning, API Gateway (FastAPI) và giao diện người dùng trực quan.

---

## 🏗️ Kiến trúc tổng thể

- **Cloud & Data Intelligence (Databricks):** Lưu trữ, xử lý điểm học tập, huấn luyện mô hình Machine Learning dự báo rớt môn và các báo cáo phân tích đa chiều.
- **API Gateway & Logic Core (FastAPI):** Cung cấp các HTTP API cho các nghiệp vụ: giả lập tính điểm ngược, xác thực người dùng, phân quyền, kết nối tới Databricks.
- **Client UI & QA:** Giao diện người dùng (Student, Lecturer, Admin Portal), tích hợp kiểm thử tự động (Pytest), và dashboard báo cáo trên Databricks SQL.

---

## 🚀 Chức năng chính

1. **Sinh viên:**
   - Chọn mục tiêu GPA/điểm chữ → Nhận khuyếns nghị số điểm thành phần cần đạt qua API mô phỏng real-time.
   - Theo dõi lộ trình học thuật và cảnh báo nguy cơ rớt môn cá nhân.

2. **Nhà trường, Quản trị viên:**
   - Quản lý tập trung dữ liệu điểm qua mô hình Delta Lake.
   - Theo dõi, dự báo, và báo động sớm những sinh viên có nguy cơ rớt môn dựa trên ML Service.

3. **Giảng viên:**
   - Gửi file điểm thô, hệ thống tự động chia tầng lưu trữ và xử lý trên Databricks.
   - Truy xuất báo cáo và phân tích học vụ.

4. **Môn tích hợp (Integrated Courses):**
   - Yêu cầu cả cột lý thuyết và thực hành đầy đủ.
   - Điểm thực hành (TH) phải ≥ 3.0 mới cho phép tính điểm cuối kỳ.
   - Công thức tính: T = (LT × chi_lt + TH × chi_th) / tong_chi.

---

## 👩‍💻 Phân chia nhiệm vụ nhóm

- **Data Engineer:** Thiết lập dữ liệu Delta Lake, xây dựng dịch vụ nạp và xử lý điểm (Data Ingestion Service).
- **ML/Cloud Engineer:** Huấn luyện & deploy mô hình dự báo rớt môn, đóng gói thành Prediction Service chạy trên Databricks Serverless Endpoint.
- **SOA Backend Architect (Leader):** Thiết kế kiến trúc dịch vụ, xây dựng API xác thực JWT 4 vai trò, tích hợp Simulation Engine tính điểm ngược, kết nối Databricks.
- **Frontend Developer:** Xây dựng giao diện Student/Lecturer/Admin Portal, thiết kế slide giả lập điểm tương tác real-time với API.
- **QA / Data Analyst:** Viết test tự động với Pytest (Kiểm thử tích hợp), xây dựng dashboard báo cáo Databricks SQL phục vụ quản trị viên.

---

## 🛠️ Công nghệ sử dụng

- **Databricks Cloud Platform**: Nền tảng Delta Lake đám mây lưu trữ dữ liệu (Bronze - Silver - Gold), thực thi ETL PySpark, và phục vụ dự đoán nguy cơ rớt môn qua mô hình ML.
- **FastAPI Backend Gateway**: Xây dựng API Gateway, tích hợp thuật toán giả lập tính ngược điểm thi (Simulation Engine), xác thực phân quyền JWT, kết nối Databricks SQL Warehouse và tự động fallback về Mock Database.
- **ReactJS Frontend (Vite)**: Giao diện Client SPA cao cấp thiết kế theo phong cách Soft Glassmorphism, tone màu Vani ngọt ngào, tích hợp bảng điều khiển tương tác và đồ thị trực quan cho 4 vai trò.
- **Pytest**: Bộ kiểm thử tự động tích hợp, giả lập các tình huống kết nối, nạp file CSV, xác thực JWT và tính ngược điểm thi.

---

## ⚡ Hướng dẫn triển khai (Demo / Development)

1. **Chuẩn bị môi trường Databricks**
   - Tạo máy chủ Databricks workspace.
   - Cấu hình các bảng Delta Lake cho dữ liệu điểm.
   - Deploy Prediction ML model vào serverless endpoint.

2. **Backend (FastAPI)**
   - Di chuyển vào thư mục backend: `cd backend`
   - Cài đặt dependencies: `pip install -r requirements.txt`
   - Cấu hình endpoint Databricks trong file `.env` hoặc biến môi trường (nếu có).
   - Chạy server phát triển:  
     ```bash
     python run.py
     ```
     Server sẽ khởi chạy tại `http://localhost:8001` và tự động reload khi có thay đổi.

3. **Frontend (Vite + React)**
   - Di chuyển vào thư mục frontend: `cd frontend`
   - Cài đặt dependencies:  
     ```bash
     npm install
     ```
   - Khởi động server phát triển:  
     ```bash
     npm run dev
     ```
   - Truy cập các portal tại địa chỉ được hiển thị trong terminal (mặc định là `http://localhost:5173`).

4. **Kiểm thử (QA)**
   - Thực thi test tự động ở thư mục backend:  
     ```bash
     cd backend
     python -m pytest
     ```

---

## 👥 Danh sách tài khoản thử nghiệm (User Accounts)

Dưới đây là danh sách đầy đủ các tài khoản đã được nạp sẵn trong hệ thống phục vụ demo và kiểm thử:

### ⚙️ Tài khoản Admin (System Admin)
| Tên hiển thị | Tên đăng nhập / Email | Mật khẩu | Quyền hạn |
| :--- | :--- | :--- | :--- |
| Admin Đào Tạo | `admin` hoặc `admin@smartgpa.edu` | `Admin@123` | Cấu hình học kỳ, môn học, phân công giảng viên, xem nhật ký hoạt động, xem danh sách cảnh báo toàn trường |

### 🔸 Tài khoản Giảng viên (Lecturer)
| Tên hiển thị | Email đăng nhập | Mật khẩu | Lecturer ID | Khoa phụ trách |
| :--- | :--- | :--- | :--- | :--- |
| TS. Trần Thị Bình | `thibinh.gv1001@smartgpa.edu` | `Gv@123` | `GV1001` | Công nghệ thông tin |
| TS. Nguyễn Minh Triết | `minhtriet.gv1002@smartgpa.edu` | `Gv@123` | `GV1002` | Công nghệ thông tin |

### 🔹 Tài khoản Sinh viên (Student)
- **Mật khẩu chung cho tất cả Sinh viên**: `Sv@123`
- **Tài khoản sinh viên demo:**
  - `student@smartgpa.edu` (MSSV: `SV123456`)
  - `thaoanh.sv1001@gmail.com` (MSSV: `SV1001`)
  - `haivy.sv1002@gmail.com` (MSSV: `SV1002`)
- **Tài khoản sinh viên thực tế (Từ file CSV DHKHDL19A & DHKHDL19B):**
  - **Tên đăng nhập**: **Mã số sinh viên (MSSV)** viết liền chữ thường. Ví dụ:
    - Lớp DHKHDL19A: `23677361` (Nguyễn Tuấn Anh), `23667351` (Trương Tuấn Bình), `23634031` (Trần Vĩnh Cơ)
    - Lớp DHKHDL19B: `23695481` (Muhammad Arifil), `23676071` (Nguyễn Thị Quỳnh Trang), `23696981` (Vũ Ngọc Thu Phương), `23725051` (Trương Thế Hải Thịnh)
  - **Mật khẩu**: `Sv@123`

---

## 📂 Dữ liệu Bảng điểm mẫu (Excel Grade Upload Templates)

Hệ thống đã tự động tạo sẵn và đóng gói bộ dữ liệu điểm của toàn bộ 39 môn học (từ học kỳ 1 đến học kỳ 9) cho cả hai lớp để kiểm thử và demo:
1. **Lớp DHKHDL19A**:
   - Thư mục nguồn: [DHKHDL19A_grades/](file:///d:/smart-gpa/DHKHDL19A_grades)
   - Tệp nén ZIP: [DHKHDL19A_grades.zip](file:///d:/smart-gpa/DHKHDL19A_grades.zip)
2. **Lớp DHKHDL19B**:
   - Thư mục nguồn: [DHKHDL19B_grades/](file:///d:/smart-gpa/DHKHDL19B_grades)
   - Tệp nén ZIP: [DHKHDL19B_grades.zip](file:///d:/smart-gpa/DHKHDL19B_grades.zip)

**Đặc điểm cấu trúc của các bảng điểm mẫu:**
- Tên tệp tin được định dạng theo chuẩn: `[Mã môn]_[Tên môn]_BangDiem.xlsx` (ví dụ: `[2101539]_[Nhập môn Khoa học Dữ liệu]_BangDiem.xlsx`).
- **Phân kỳ điểm số**:
  - Học kỳ 1 - 7: Đã hoàn thành học phần (có đầy đủ điểm thành phần và điểm cuối kỳ).
  - Học kỳ 8: Đang ở cuối kỳ (đã có điểm thường kỳ, giữa kỳ và điểm thực hành; cột **Điểm cuối kỳ để trống** để phục vụ giả lập tính điểm ngược).
  - Học kỳ 9: Môn học tương lai (tất cả các cột điểm đều trống).
- **Tự động điền điểm thực hành**: Đối với các môn có cấu trúc thực hành hoặc tích hợp, hệ thống tự động điền các cột thực hành tương ứng (TH1, TH2, TH3) khớp với dữ liệu học vụ.

---

## 💡 Hướng dẫn chi tiết sử dụng theo vai trò

### 1. Đối với Sinh viên (Đăng nhập bằng MSSV + Mật khẩu `Sv@123`):
- Vào trang **"Bảng điểm cá nhân"** để xem danh sách môn học đã học.
- Chọn môn học đang học (chưa có điểm cuối kỳ) -> Chọn **Mục tiêu điểm chữ** (ví dụ: mục tiêu đạt điểm `A`).
- Hệ thống sẽ hiển thị điểm cuối kỳ bạn cần đạt (ví dụ: *"Bạn cần đạt 8.4 điểm thi cuối kỳ để đạt mục tiêu điểm A"*).
- Xem hộp thư **Thông báo** ở góc trên cùng để cập nhật các cảnh báo học vụ hoặc thay đổi điểm.

### 2. Đối với Giảng viên:
- Vào trang **"Quản lý lớp học"** -> Chọn lớp giảng dạy -> Tải lên tệp CSV chứa điểm quá trình của sinh viên.
- Nếu tệp tải lên có dòng lỗi (ví dụ điểm > 10.0 hoặc sai định dạng), hệ thống hiển thị chi tiết số dòng bị lỗi để chỉnh sửa nhanh.
- Sau khi tải thành công, giảng viên có thể chọn sinh viên bất kỳ để chỉnh sửa điểm trực tiếp.

### 3. Đối với Admin:
- Vào trang **"Nhật ký hoạt động"** để kiểm tra hoạt động tải điểm/sửa điểm của giảng viên.
- Vào trang **"Danh sách cảnh báo học vụ"** để lọc các sinh viên có nguy cơ cao cần hỗ trợ.

---

## 📑 Đóng góp & Liên hệ

Vui lòng tạo [issue](https://github.com/mangcutxinh/Smart-GPA/issues) hoặc liên hệ trực tiếp nhóm phát triển nếu có góp ý hay nhu cầu hợp tác.

- **Leader:** Nguyễn Thị Quỳnh Trang
- **Email:** mangcutxinh.iuh@gmail.com

---

## English Overview

**SmartGPA** is an academic analysis, GPA simulation, and student risk prediction platform, utilizing SOA architecture and Databricks cloud.  
Key modules include: GPA path simulation, machine learning dropout risk forecast, centralized Delta Lake storage, and multi-role portals (Student, Lecturer, Admin).

See detailed instructions above for project architecture and installation.

---
