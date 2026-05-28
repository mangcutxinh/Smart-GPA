# SmartGPA

_Hệ thống phân tích học thuật, giả lập điểm mục tiêu và dự báo cảnh báo học vụ dựa trên kiến trúc SOA & nền tảng đám mây Databricks._

---

## 📌 Giới thiệu

**SmartGPA** là hệ thống hỗ trợ sinh viên và nhà trường trong việc:
- Giả lập lộ trình điểm số, xác định số điểm thành phần cần đạt để tới được các mốc GPA hoặc điểm chữ mong muốn.
- Dự báo sinh viên có nguy cơ rớt môn dựa trên dữ liệu lịch sử.
- Quản lý tập trung và phân tích dữ liệu điểm học tập qua nhiều lớp lưu trữ hiện đại (Delta Lake: Bronze - Silver - Gold).
- Kết nối dữ liệu liền mạch giữa các phòng ban, giảng viên, cố vấn và sinh viên theo kiến trúc hướng dịch vụ (SOA).

Dự án triển khai trên nền tảng đám mây **Databricks**, áp dụng các công nghệ hiện đại về Data Engineering, Machine Learning, API Gateway (FastAPI) và giao diện người dùng trực quan.

---

## 🏗️ Kiến trúc tổng thể

- **Cloud & Data Intelligence (Databricks):** Lưu trữ, xử lý điểm học tập, huấn luyện mô hình Machine Learning dự báo rớt môn và các báo cáo phân tích đa chiều.
- **API Gateway & Logic Core (FastAPI):** Cung cấp các HTTP API cho các nghiệp vụ: giả lập tính điểm ngược, xác thực người dùng, phân quyền, kết nối tới Databricks.
- **Client UI & QA:** Giao diện người dùng (Student, Lecturer, Advisor Portal), tích hợp kiểm thử tự động (Pytest), và dashboard báo cáo trên Databricks SQL.

---

## 🚀 Chức năng chính

1. **Sinh viên:**
   - Chọn mục tiêu GPA/điểm chữ → Nhận khuyến nghị số điểm thành phần cần đạt qua API mô phỏng real-time.
   - Theo dõi lộ trình học thuật và cảnh báo nguy cơ rớt môn cá nhân.

2. **Nhà trường, Cố vấn học tập:**
   - Quản lý tập trung dữ liệu điểm qua mô hình Delta Lake.
   - Theo dõi, dự báo, và báo động sớm những sinh viên có nguy cơ rớt môn dựa trên ML Service.

3. **Giảng viên:**
   - Gửi file điểm thô, hệ thống tự động chia tầng lưu trữ và xử lý trên Databricks.
   - Truy xuất báo cáo và phân tích học vụ.

---

## 👩‍💻 Phân chia nhiệm vụ nhóm

- **Data Engineer:** Thiết lập dữ liệu Delta Lake, xây dựng dịch vụ nạp và xử lý điểm (Data Ingestion Service).
- **ML/Cloud Engineer:** Huấn luyện & deploy mô hình dự báo rớt môn, đóng gói thành Prediction Service chạy trên Databricks Serverless Endpoint.
- **SOA Backend Architect (Leader):** Thiết kế kiến trúc dịch vụ, xây dựng API xác thực JWT 4 vai trò, tích hợp Simulation Engine tính điểm ngược, kết nối Databricks.
- **Frontend Developer:** Xây dựng giao diện Student/Lecturer/Advisor Portal, thiết kế slide giả lập điểm tương tác real-time với API.
- **QA / Data Analyst:** Viết test tự động với Pytest (Kiểm thử tích hợp), xây dựng dashboard báo cáo Databricks SQL phục vụ quản trị viên.

---

## 🛠️ Công nghệ sử dụng

- **Databricks**: Dữ liệu, tính toán, ML, Databricks SQL Dashboard, Delta Lake.
- **FastAPI**: Xây dựng và vận hành API gateway/logic core; xác thực JWT.
- **Pytest**: Kiểm thử tích hợp và hiệu năng dịch vụ.
- **Frontend**: ReactJS/VueJS với các UI Portal cho từng đối tượng người dùng.

---

## ⚡ Hướng dẫn triển khai (Demo / Development)

1. **Chuẩn bị môi trường Databricks**
   - Tạo máy chủ Databricks workspace.
   - Cấu hình các bảng Delta Lake cho dữ liệu điểm.
   - Deploy Prediction ML model vào serverless endpoint.

2. **Backend (FastAPI)**
   - Cài đặt dependencies: `pip install -r requirements.txt`
   - Cấu hình endpoint Databricks trong biến môi trường.
   - Chạy server:  
     ```bash
     uvicorn app.main:app --reload
     ```

3. **Frontend**
   - Chạy ở thư mục client:  
     ```bash
     npm install
     npm start
     ```
   - Truy cập các portal tại `localhost:3000`.

4. **Kiểm thử (QA)**
   - Thực thi test tự động ở thư mục backend:  
     ```bash
     pytest tests/
     ```

---

## 📑 Đóng góp & Liên hệ

Vui lòng tạo [issue](https://github.com/mangcutxinh/Smart-GPA/issues) hoặc liên hệ trực tiếp nhóm phát triển nếu có góp ý hay nhu cầu hợp tác.

- **Leader:** Chan
- **Email:** [Điền thông tin nhóm của bạn ở đây]

---

## English Overview

**SmartGPA** is an academic analysis, GPA simulation, and student risk prediction platform, utilizing SOA architecture and Databricks cloud.  
Key modules include: GPA path simulation, machine learning dropout risk forecast, centralized Delta Lake storage, and multi-role portals (Student, Lecturer, Advisor, Admin).

See detailed instructions above for project architecture and installation.

---
