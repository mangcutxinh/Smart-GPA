# Databricks Notebook Code Template for Smart-GPA Team

## 1. Mục đích
Dùng chung file này để hướng dẫn các thành viên tải code mẫu, import vào Databricks, chạy ETL với Spark, truy cập dữ liệu từ backend FastAPI. Giúp teamwork chuẩn trên mọi môi trường: Data Engineer (ETL), Backend (API), QA (Test pipeline), ...

---

## 2. Hướng dẫn clone & import notebook trên Databricks

**Bước 1:** Clone repo về máy (hoặc tải riêng file này):
```bash
git clone https://github.com/mangcutxinh/Smart-GPA.git
```

**Bước 2:** Đổi tên file `databricks-code-template.md` → `databricks-code-template.ipynb` **(hoặc tạo notebook mới trên Databricks, copy/paste code bên dưới)**

**Bước 3:** Import notebook vào Databricks Workspace (Shared/Smart-GPA), bắt đầu teamwork/coding!

---

## 3. Code mẫu: Xử lý real trên hệ thống Databricks (Python + Spark SQL)

### 3.1. BỔ SUNG QUY CHẾ ĐIỂM LIỆT & SỐ HÓA SỐ ĐẦU ĐIỂM THƯỜNG KỲ (Áp dụng từ 2024)

#### A. Số đầu điểm Thường kỳ (TK) theo số tín chỉ:
- Môn 2 tín chỉ (LT hoặc TH): bắt buộc 2 đầu điểm TK (TK_1, TK_2). Điểm TB = (TK_1 + TK_2)/2
- Môn 3 tín chỉ (LT hoặc TH): bắt buộc 3 đầu điểm TK (TK_1, TK_2, TK_3). Điểm TB = (TK_1 + TK_2 + TK_3)/3
- Môn tích hợp (LT+TH): Số hóa tách biệt đầu điểm cho mỗi nhánh (VD: 2TC LT → 2 TK LT, 1TC TH → 1 TK TH)

#### B. Quy chế điểm liệt thực hành:
- Môn tích hợp hoặc thực hành, nếu điểm TB Thực hành < 3.0 → luôn trả về F bất kể các thành phần khác
- Trạng thái cảnh báo phải bổ sung lý do "LIỆT THỰC HÀNH"

---

### A. Tạo bảng cấu hình môn học tự động trên Databricks (Data Engineer)

```sql
CREATE TABLE smartgpa_db.danh_muc_mon_hoc AS
SELECT 
    ma_mon, 
    ten_mon,
    so_tiet_lt,
    so_tiet_th,
    (so_tiet_lt / 15) AS so_chi_lt,
    (so_tiet_th / 30) AS so_chi_th,
    ((so_tiet_lt / 15) + (so_tiet_th / 30)) AS tong_so_chi,
    CASE 
        WHEN so_tiet_lt > 0 AND so_tiet_th = 0 THEN 'ly_thuyet'
        WHEN so_tiet_lt = 0 AND so_tiet_th > 0 THEN 'thuc_hanh'
        ELSE 'tich_hop'
    END AS loai_hoc_phan,
    CASE 
        WHEN ten_mon LIKE '%*%' THEN true 
        ELSE false 
    END AS loai_tru_gpa
FROM smartgpa_db.bronze_diem_sinh_vien
GROUP BY ma_mon, ten_mon, so_tiet_lt, so_tiet_th;
```

---

### B. Xử lý dữ liệu tầng Silver (Python/SQL Databricks)

```python
from pyspark.sql import functions as F

# Đọc dữ liệu tầng Bronze
df_bronze = spark.table("smartgpa_db.bronze_diem_sinh_vien")

# Tính số tín chỉ, làm sạch
df_silver_pre = df_bronze.withColumn("so_chi_lt", F.col("so_tiet_lt") / 15) \
                         .withColumn("so_chi_th", F.col("so_tiet_th") / 30) \
                         .withColumn("tong_so_chi", F.col("so_chi_lt") + F.col("so_chi_th"))

# --- BỔ SUNG: Tính cột điểm trung bình thực hành (nếu có nhiều cột thực hành)
ten_cot_th = ["diem_th1", "diem_th2"]  # Ví dụ: tuỳ môn truyền động danh sách cột
if all(col in df_silver_pre.columns for col in ten_cot_th):
    df_silver_pre = df_silver_pre.withColumn(
        "diem_trung_binh_thuc_hanh",
        sum([F.col(c) for c in ten_cot_th]) / len(ten_cot_th)
    )
else:
    df_silver_pre = df_silver_pre.withColumn("diem_trung_binh_thuc_hanh", F.lit(None))

# Xử lý điểm tích luỹ hiện tại (giả lập/chuẩn)
df_silver = df_silver_pre.withColumn(
    "diem_tich_luy_hien_tai",
    F.lit(8.2).cast("float") # demo: hardcode, thực tế dùng công thức cụ thể
).withColumn(
    "status_canh_bao",
    F.when(F.col("diem_tich_luy_hien_tai") < 4.0, "Nguy co rot mon")
     .otherwise("An toan")
)

df_silver.write.format("delta").mode("overwrite").saveAsTable("smartgpa_db.silver_diem_sinh_vien")
print("--- Đã nạp dữ liệu tầng Silver ---")
```

---

### C. ÁNH XẠ THANG ĐIỂM (Silver sang Gold, cập nhật logic tính điểm tích hợp)

```sql
CREATE OR REPLACE TABLE smartgpa_db.gold_diem_sinh_vien AS
SELECT 
    student_id,
    student_name,
    ma_mon,
    ten_mon,
    loai_hoc_phan,
    tong_so_chi,
    diem_tich_luy_hien_tai,
    status_canh_bao,
    diem_trung_binh_thuc_hanh,
    -- Tính điểm cuối kỳ cho môn tích hợp dựa trên công thức T = ((LT * chi_lt) + (TH * chi_th)) / (chi_lt + chi_th)
    CASE 
        WHEN loai_hoc_phan = 'tich_hop' THEN
            ((diem_trung_binh_lt * so_chi_lt) + (diem_trung_binh_thuc_hanh * so_chi_th)) / (so_chi_lt + so_chi_th)
        ELSE diem_tich_luy_hien_tai
    END AS diem_cuoi_ky_tich_hop,
    CASE 
        -- Điểm liệt thực hành ở môn tích hợp hoặc thực hành nếu TH < 3.0
        WHEN loai_hoc_phan IN ('thuc_hanh', 'tich_hop') AND diem_trung_binh_thuc_hanh < 3.0 THEN 'F'
        -- Nếu không liệt thì quy đổi thông thường dựa trên diem_tich_luy_hien_tai (hoặc diem_cuoi_ky_tich_hop cho tích hợp)
        WHEN COALESCE(diem_cuoi_ky_tich_hop, diem_tich_luy_hien_tai) >= 9.0 THEN 'A+'
        WHEN COALESCE(diem_cuoi_ky_tich_hop, diem_tich_luy_hien_tai) >= 8.5 THEN 'A'
        WHEN COALESCE(diem_cuoi_ky_tich_hop, diem_tich_luy_hien_tai) >= 8.0 THEN 'B+'
        WHEN COALESCE(diem_cuoi_ky_tich_hop, diem_tich_luy_hien_tai) >= 7.0 THEN 'B'
        WHEN COALESCE(diem_cuoi_ky_tich_hop, diem_tich_luy_hien_tai) >= 6.0 THEN 'C+'
        WHEN COALESCE(diem_cuoi_ky_tich_hop, diem_tich_luy_hien_tai) >= 5.5 THEN 'C'
        WHEN COALESCE(diem_cuoi_ky_tich_hop, diem_tich_luy_hien_tai) >= 5.0 THEN 'D+'
        WHEN COALESCE(diem_cuoi_ky_tich_hop, diem_tich_luy_hien_tai) >= 4.0 THEN 'D'
        ELSE 'F'
    END AS diem_chu_hien_tai,
    CASE 
        WHEN (loai_hoc_phan IN ('thuc_hanh', 'tich_hop') AND diem_trung_binh_thuc_hanh < 3.0) 
        THEN 'CANH BAO: LIET THUC HANH (ROT MON)'
        ELSE status_canh_bao
    END AS status_canh_bao_final
FROM smartgpa_db.silver_diem_sinh_vien;
```

---

### D. Kết nối từ backend FastAPI tới Databricks SQL Warehouse
```python
from databricks import sql
import os

def lay_diem_sinh_vien_tu_cloud(student_id: str, ma_mon: str):
    connection = sql.connect(
        server_hostname=os.getenv("DATABRICKS_SERVER_HOSTNAME"),
        http_path=os.getenv("DATABRICKS_HTTP_PATH"),
        access_token=os.getenv("DATABRICKS_TOKEN")
    )
    cursor = connection.cursor()
    query = f"""
        SELECT diem_tich_luy_hien_tai, loai_hoc_phan, tong_so_chi, diem_trung_binh_thuc_hanh, diem_chu_hien_tai, status_canh_bao_final
        FROM smartgpa_db.gold_diem_sinh_vien 
        WHERE student_id = '{student_id}' AND ma_mon = '{ma_mon}'
    """
    cursor.execute(query)
    result = cursor.fetchone()
    cursor.close()
    connection.close()
    return result
```

---

## 4. TEAMWORK NOTE
- Khi làm module mới, hãy nhân bản file này thành file riêng cho nhóm bạn trên Databricks/GitHub.
- Tạo notebook theo module: vd: `feature-simulation-engine.ipynb`, `ml-prediction-flow.ipynb`...
- Khi chạy pipeline, hãy push file lên GitHub để đồng bộ version.

**Template này giúp Dev backend, Data Engineer, QA test... đều dễ dàng clone, teamwork và chạy Data pipeline/ETL trên Databricks!**
