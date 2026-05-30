# Databricks Notebook Code Template for Smart-GPA Team

## 1. Mục đích
Dùng chung file này để hướng dẫn các thành viên tải code mẫu, import vào Databricks, chạy ETL với Spark, truy cập dữ liệu từ backend FastAPI. Giúp teamwork chuẩn trên cùng 1 repo.

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

# (Xử lý bóc tách trung bình điểm tuỳ loại học phần ở đây... tuỳ logic custom team bạn)
#

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

### C. ÁNH XẠ THANG ĐIỂM (Từ Silver sang Gold, Databricks SQL Cell)

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
    CASE 
        WHEN diem_tich_luy_hien_tai >= 9.0 THEN 'A+'
        WHEN diem_tich_luy_hien_tai >= 8.5 THEN 'A'
        WHEN diem_tich_luy_hien_tai >= 8.0 THEN 'B+'
        WHEN diem_tich_luy_hien_tai >= 7.0 THEN 'B'
        WHEN diem_tich_luy_hien_tai >= 6.0 THEN 'C+'
        WHEN diem_tich_luy_hien_tai >= 5.5 THEN 'C'
        WHEN diem_tich_luy_hien_tai >= 5.0 THEN 'D+'
        WHEN diem_tich_luy_hien_tai >= 4.0 THEN 'D'
        ELSE 'F'
    END AS diem_chu_hien_tai
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
        SELECT diem_tich_luy_hien_tai, loai_hoc_phan, tong_so_chi 
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
