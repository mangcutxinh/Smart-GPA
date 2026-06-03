# Databricks notebook source
# SmartGPA - Databricks Bronze/Silver/Gold grading pipeline
#
# Purpose:
# - diem_cuoi_ky is NOT known at midterm time.
# - The pipeline calculates diem_cuoi_ky_can_dat for target letter grades.
# - This notebook is designed for Databricks Serverless or any available workspace compute.

# COMMAND ----------

from pyspark.sql import functions as F
from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    DoubleType,
    IntegerType,
)

CATALOG = "workspace"
SCHEMA = "smartgpa_db"

spark.sql(f"USE CATALOG {CATALOG}")
spark.sql("CREATE DATABASE IF NOT EXISTS smartgpa_db")
spark.sql(f"USE {SCHEMA}")

# Optional input:
# - Leave csv_path empty to use the sample data embedded in this notebook.
# - Set csv_path to a Databricks-readable CSV path, for example:
#   /FileStore/smartgpa/sample_scores_smartgpa.csv
#   dbfs:/FileStore/smartgpa/sample_scores_smartgpa.csv
try:
    dbutils.widgets.text("csv_path", "", "Optional CSV path")
    CSV_PATH = dbutils.widgets.get("csv_path").strip()
except NameError:
    CSV_PATH = ""

# COMMAND ----------

# Grade rules used in this project
#
# 1. Theory component:
#    LT_QT_CONTRIBUTION = 10% * thuong_xuyen_1
#                       + 10% * thuong_xuyen_2
#                       + 30% * giua_ky
#
#    This contribution has max 5.0 points because final exam owns the other 50%.
#    To combine with practice by credits, normalize it to a 10-point process score:
#
#    LT_QT_10 = LT_QT_CONTRIBUTION / 0.5
#             = 20% * thuong_xuyen_1
#             + 20% * thuong_xuyen_2
#             + 60% * giua_ky
#
# 2. Practice component:
#    TH_QT_10 = (thuc_hanh_1 + thuc_hanh_2 + thuc_hanh_3) / 3
#
# 3. Integrated/course process score:
#    If theory-only:
#       QT_10 = LT_QT_10
#
#    If practice-only:
#       QT_10 = TH_QT_10
#
#    If integrated:
#       QT_10 = (LT_QT_10 * so_chi_lt + TH_QT_10 * so_chi_th) / tong_so_chi
#
# 4. Final total:
#    TONG_KET_10 = 50% * QT_10 + 50% * diem_cuoi_ky
#
# 5. At midterm time, diem_cuoi_ky is unknown.
#    Therefore:
#       diem_cuoi_ky_can_dat = (target_score - 0.5 * QT_10) / 0.5

# COMMAND ----------

schema = StructType([
    StructField("student_id", StringType(), True),
    StructField("student_name", StringType(), True),
    StructField("ma_mon", StringType(), True),
    StructField("ten_mon", StringType(), True),
    StructField("ma_lop_hoc_phan", StringType(), True),
    StructField("loai_hoc_phan", StringType(), True),  # ly_thuyet / thuc_hanh / tich_hop
    StructField("so_chi_lt", IntegerType(), True),
    StructField("so_chi_th", IntegerType(), True),
    StructField("thuong_xuyen_1", DoubleType(), True),
    StructField("thuong_xuyen_2", DoubleType(), True),
    StructField("giua_ky", DoubleType(), True),
    StructField("thuc_hanh_1", DoubleType(), True),
    StructField("thuc_hanh_2", DoubleType(), True),
    StructField("thuc_hanh_3", DoubleType(), True),
])

sample_raw_data = [
    # Theory-only course: QT = 0.2*TX1 + 0.2*TX2 + 0.6*GK
    (
        "SV001", "Nguyen Van A", "INT1002", "Co so du lieu", "L01", "ly_thuyet",
        3, 0,
        8.0, 7.5, 7.0,
        None, None, None,
    ),
    # Practice-only course: QT = average of three practice scores
    (
        "SV002", "Tran Thi B", "INT1003", "Thuc hanh He dieu hanh", "L02", "thuc_hanh",
        0, 2,
        None, None, None,
        7.0, 8.0, 8.5,
    ),
    # Integrated course: QT weighted by theory/practice credits
    (
        "SV003", "Le Van C", "INT1001", "Lap trinh Python", "L01", "tich_hop",
        2, 1,
        8.0, 7.5, 7.0,
        8.0, 8.5, 9.0,
    ),
    # At-risk integrated course, useful for warning evidence
    (
        "SV004", "Pham Thi D", "INT1001", "Lap trinh Python", "L01", "tich_hop",
        2, 1,
        4.0, 4.5, 4.0,
        2.0, 2.5, 3.0,
    ),
]

if CSV_PATH:
    df_raw = (
        spark.read
        .option("header", True)
        .schema(schema)
        .csv(CSV_PATH)
    )
else:
    df_raw = spark.createDataFrame(sample_raw_data, schema=schema)

display(df_raw)

# COMMAND ----------

# Bronze: raw uploaded/ingested score data
(
    df_raw.write
    .format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable("smartgpa_db.bronze_diem_sinh_vien")
)

display(spark.table("smartgpa_db.bronze_diem_sinh_vien"))

# COMMAND ----------

df_bronze = spark.table("smartgpa_db.bronze_diem_sinh_vien")

score_cols = [
    "thuong_xuyen_1",
    "thuong_xuyen_2",
    "giua_ky",
    "thuc_hanh_1",
    "thuc_hanh_2",
    "thuc_hanh_3",
]

valid_score_condition = F.lit(True)
for col_name in score_cols:
    valid_score_condition = valid_score_condition & (
        F.col(col_name).isNull() | F.col(col_name).between(0.0, 10.0)
    )

df_silver = (
    df_bronze
    .withColumn("tong_so_chi", F.col("so_chi_lt") + F.col("so_chi_th"))
    .withColumn("is_valid_score_range", valid_score_condition)
    .withColumn(
        "lt_qt_contribution_5",
        F.when(
            F.col("thuong_xuyen_1").isNotNull()
            & F.col("thuong_xuyen_2").isNotNull()
            & F.col("giua_ky").isNotNull(),
            0.1 * F.col("thuong_xuyen_1")
            + 0.1 * F.col("thuong_xuyen_2")
            + 0.3 * F.col("giua_ky"),
        )
    )
    .withColumn(
        "lt_qt_10",
        F.when(F.col("lt_qt_contribution_5").isNotNull(), F.col("lt_qt_contribution_5") / 0.5)
    )
    .withColumn(
        "th_qt_10",
        F.when(
            F.col("thuc_hanh_1").isNotNull()
            & F.col("thuc_hanh_2").isNotNull()
            & F.col("thuc_hanh_3").isNotNull(),
            (F.col("thuc_hanh_1") + F.col("thuc_hanh_2") + F.col("thuc_hanh_3")) / 3,
        )
    )
    .withColumn(
        "qt_10",
        F.when(F.col("loai_hoc_phan") == "ly_thuyet", F.col("lt_qt_10"))
        .when(F.col("loai_hoc_phan") == "thuc_hanh", F.col("th_qt_10"))
        .when(
            F.col("loai_hoc_phan") == "tich_hop",
            (
                F.col("lt_qt_10") * F.col("so_chi_lt")
                + F.col("th_qt_10") * F.col("so_chi_th")
            ) / F.col("tong_so_chi"),
        )
    )
    .withColumn("qt_10", F.round(F.col("qt_10"), 2))
    .withColumn(
        "data_quality_status",
        F.when(~F.col("is_valid_score_range"), "invalid_score_range")
        .when(F.col("tong_so_chi") <= 0, "invalid_credit")
        .when(F.col("qt_10").isNull(), "missing_required_scores")
        .otherwise("valid"),
    )
)

(
    df_silver.write
    .format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable("smartgpa_db.silver_diem_sinh_vien")
)

display(spark.table("smartgpa_db.silver_diem_sinh_vien"))

# COMMAND ----------

grade_targets = [
    ("A+", 9.0),
    ("A", 8.5),
    ("B+", 8.0),
    ("B", 7.0),
    ("C+", 6.0),
    ("C", 5.5),
    ("D+", 5.0),
    ("D", 4.0),
]

target_schema = StructType([
    StructField("diem_chu_muc_tieu", StringType(), False),
    StructField("diem_muc_tieu_10", DoubleType(), False),
])

df_targets = spark.createDataFrame(grade_targets, schema=target_schema)
(
    df_targets.write
    .format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable("smartgpa_db.dim_diem_muc_tieu")
)
display(df_targets)

# COMMAND ----------

df_silver = spark.table("smartgpa_db.silver_diem_sinh_vien")
df_targets = spark.table("smartgpa_db.dim_diem_muc_tieu")

df_gold = (
    df_silver
    .where(F.col("data_quality_status") == "valid")
    .crossJoin(df_targets)
    .withColumn(
        "diem_cuoi_ky_can_dat_raw",
        (F.col("diem_muc_tieu_10") - 0.5 * F.col("qt_10")) / 0.5,
    )
    .withColumn(
        "diem_cuoi_ky_can_dat",
        F.ceil(F.col("diem_cuoi_ky_can_dat_raw") * 10) / 10,
    )
    .withColumn(
        "kha_thi",
        (F.col("diem_cuoi_ky_can_dat") >= 0.0) & (F.col("diem_cuoi_ky_can_dat") <= 10.0),
    )
    .withColumn(
        "status_canh_bao",
        F.when(
            (F.col("loai_hoc_phan").isin("thuc_hanh", "tich_hop")) & (F.col("th_qt_10") < 3.0),
            "Nguy co - liet thuc hanh",
        )
        .when(F.col("diem_cuoi_ky_can_dat") > 10.0, "Nguy co - muc tieu khong kha thi")
        .when(F.col("qt_10") < 4.0, "Nguy co - qua trinh thap")
        .otherwise("An toan"),
    )
    .select(
        "student_id",
        "student_name",
        "ma_mon",
        "ten_mon",
        "ma_lop_hoc_phan",
        "loai_hoc_phan",
        "so_chi_lt",
        "so_chi_th",
        "tong_so_chi",
        "thuong_xuyen_1",
        "thuong_xuyen_2",
        "giua_ky",
        "thuc_hanh_1",
        "thuc_hanh_2",
        "thuc_hanh_3",
        "lt_qt_10",
        "th_qt_10",
        "qt_10",
        "diem_chu_muc_tieu",
        "diem_muc_tieu_10",
        "diem_cuoi_ky_can_dat",
        "kha_thi",
        "status_canh_bao",
    )
)

(
    df_gold.write
    .format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable("smartgpa_db.gold_du_bao_diem_cuoi_ky")
)

display(spark.table("smartgpa_db.gold_du_bao_diem_cuoi_ky"))

# COMMAND ----------

# Completion check: these counts are useful evidence that all layers were created.
spark.sql("""
SELECT 'bronze_diem_sinh_vien' AS table_name, COUNT(*) AS row_count
FROM smartgpa_db.bronze_diem_sinh_vien
UNION ALL
SELECT 'silver_diem_sinh_vien', COUNT(*)
FROM smartgpa_db.silver_diem_sinh_vien
UNION ALL
SELECT 'dim_diem_muc_tieu', COUNT(*)
FROM smartgpa_db.dim_diem_muc_tieu
UNION ALL
SELECT 'gold_du_bao_diem_cuoi_ky', COUNT(*)
FROM smartgpa_db.gold_du_bao_diem_cuoi_ky
""").show(truncate=False)

# COMMAND ----------

# Useful slide evidence query: final exam score needed for each student to reach target A.
spark.sql("""
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
ORDER BY student_id, ma_mon
""").show(truncate=False)

# COMMAND ----------

# Useful slide evidence query: warning list.
spark.sql("""
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
ORDER BY student_id, diem_muc_tieu_10 DESC
""").show(truncate=False)
