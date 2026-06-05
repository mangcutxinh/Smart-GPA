"""
SmartGPA – Databricks & Delta Lake Database Layer
Handles connection to Databricks SQL Warehouse and queries the Gold Delta Table.
Supports local-first testing with an intelligent in-memory fallback database.
"""
import logging
import os
from typing import Dict, Any, Optional, List
from app.core.config import settings

logger = logging.getLogger("smartgpa.databricks_db")


def _databricks_connection_settings() -> tuple[str, str, str]:
    server_hostname = (
        os.getenv("DATABRICKS_SERVER_HOSTNAME")
        or settings.DATABRICKS_SERVER_HOSTNAME
        or settings.DATABRICKS_HOST.replace("https://", "")
    )
    http_path = os.getenv("DATABRICKS_HTTP_PATH") or settings.DATABRICKS_HTTP_PATH
    access_token = os.getenv("DATABRICKS_TOKEN") or settings.DATABRICKS_TOKEN
    return server_hostname, http_path, access_token


def _gold_table_name() -> str:
    catalog = os.getenv("DATABRICKS_CATALOG") or settings.DATABRICKS_CATALOG
    schema = os.getenv("DATABRICKS_SCHEMA") or settings.DATABRICKS_SCHEMA
    table = os.getenv("DATABRICKS_GOLD_TABLE") or settings.DATABRICKS_GOLD_TABLE
    return f"{catalog}.{schema}.{table}"

# ─── Mock Delta Lake Gold Table Store (Composite Key: (student_id, ma_mon)) ───
# Seeded with realistic academic data matching test cases (INT1306, INT1340, INT1410)
MOCK_GOLD_DB: Dict[tuple[str, str], Dict[str, Any]] = {

    ("SV123456", "INT1306"): {
        "student_id": "SV123456",
        "ma_mon": "INT1306",
        "diem_thong_thuong": [8.0, 8.0],
        "diem_giua_ky": 9.0,
        "diem_cuoi_ky": None,
        "loai_hoc_phan": "ly_thuyet",
        "so_chi_lt": 2,
        "so_chi_th": 0,
        "tong_so_chi": 2,
        "status_canh_bao": "An toan"
    },
    ("SV123456", "INT1340"): {
        "student_id": "SV123456",
        "ma_mon": "INT1340",
        "diem_thong_thuong": [],
        "diem_giua_ky": None,
        "diem_cuoi_ky": None,
        "diem_thuc_hanh_hien_tai": [7.0, 8.0],
        "loai_hoc_phan": "thuc_hanh",
        "so_chi_lt": 0,
        "so_chi_th": 3,
        "tong_so_chi": 3,
        "status_canh_bao": "An toan"
    },
    ("SV123456", "INT1410"): {
        "student_id": "SV123456",
        "ma_mon": "INT1410",
        "diem_thong_thuong": [],
        "diem_giua_ky": None,
        "diem_cuoi_ky": None,
        "diem_thuc_hanh_tich_hop": 8.0,
        "diem_thuong_ky_lt_list": [8.0, 8.0],
        "diem_giua_ky_lt": 8.0,
        "loai_hoc_phan": "tich_hop",
        "so_chi_lt": 2,
        "so_chi_th": 1,
        "tong_so_chi": 3,
        "status_canh_bao": "An toan"
    }
}



# Mock Silver Table Store (derived from Gold for local Databricks progress demos)
MOCK_SILVER_DB: Dict[tuple[str, str], Dict[str, Any]] = {}


def query_gold_diem_sinh_vien(student_id: str, ma_mon: str) -> Optional[Dict[str, Any]]:
    """
    Tra cứu thông tin điểm sinh viên từ bảng gold_diem_sinh_vien trên Databricks Delta Lake.
    Nếu cấu hình trống hoặc lỗi kết nối, tự động fallback về Database giả lập local.
    """
    host = settings.DATABRICKS_HOST
    http_path = settings.DATABRICKS_HTTP_PATH
    token = settings.DATABRICKS_TOKEN
    catalog = settings.DATABRICKS_CATALOG
    schema = settings.DATABRICKS_SCHEMA

    # Kiểm tra xem có cấu hình Databricks không
    if host and http_path and token:
        try:
            from databricks import sql
            logger.info(f"Kết nối tới Databricks SQL Warehouse: {host}...")
            
            with sql.connect(
                server_hostname=host.replace("https://", ""),
                http_path=http_path,
                access_token=token
            ) as connection:
                with connection.cursor() as cursor:
                    # Truy vấn SQL an toàn tham số hóa để lấy điểm từ bảng Gold
                    query = f"""
                    SELECT 
                        student_id, ma_mon, diem_thong_thuong, diem_giua_ky, diem_cuoi_ky,
                        loai_hoc_phan, so_chi_lt, so_chi_th, tong_so_chi, status_canh_bao
                    FROM {catalog}.{schema}.gold_diem_sinh_vien
                    WHERE student_id = ? AND ma_mon = ?
                    LIMIT 1
                    """
                    try:
                        cursor.execute(query, (student_id, ma_mon))
                        row = cursor.fetchone()
                        if row:
                            # Map row sang dictionary tương ứng
                            columns = [desc[0] for desc in cursor.description]
                            result = dict(zip(columns, row))
                            logger.info(f"Đã truy xuất thành công dữ liệu từ Databricks cho SV {student_id} môn {ma_mon}")
                            return result
                    except Exception as sql_err:
                        logger.warning(f"Lỗi truy vấn gold_diem_sinh_vien: {sql_err}. Đang thử fallback truy vấn silver_diem_sinh_vien...")
                        try:
                            # Truy vấn từ bảng Silver và ánh xạ trường dữ liệu sang Gold
                            query_silver = f"""
                            SELECT 
                                student_id, student_name, ma_mon, ten_mon, ma_lop_hoc_phan, loai_hoc_phan, 
                                so_chi_lt, so_chi_th, tong_so_chi, thuong_xuyen_1, thuong_xuyen_2, giua_ky,
                                thuc_hanh_1, thuc_hanh_2, thuc_hanh_3, qt_10
                            FROM {catalog}.{schema}.silver_diem_sinh_vien
                            WHERE student_id = ? AND ma_mon = ?
                            LIMIT 1
                            """
                            cursor.execute(query_silver, (student_id, ma_mon))
                            row_s = cursor.fetchone()
                            if row_s:
                                columns_s = [desc[0] for desc in cursor.description]
                                silver_row = dict(zip(columns_s, row_s))
                                
                                tx1 = silver_row.get("thuong_xuyen_1")
                                tx2 = silver_row.get("thuong_xuyen_2")
                                tx_list = [x for x in (tx1, tx2) if x is not None]
                                
                                th1 = silver_row.get("thuc_hanh_1")
                                th2 = silver_row.get("thuc_hanh_2")
                                th3 = silver_row.get("thuc_hanh_3")
                                th_list = [x for x in (th1, th2, th3) if x is not None]
                                
                                mapped = {
                                    "student_id": silver_row.get("student_id"),
                                    "student_name": silver_row.get("student_name"),
                                    "ma_mon": silver_row.get("ma_mon"),
                                    "ten_mon": silver_row.get("ten_mon"),
                                    "ma_lop_hoc_phan": silver_row.get("ma_lop_hoc_phan"),
                                    "loai_hoc_phan": silver_row.get("loai_hoc_phan"),
                                    "so_chi_lt": silver_row.get("so_chi_lt"),
                                    "so_chi_th": silver_row.get("so_chi_th"),
                                    "tong_so_chi": silver_row.get("tong_so_chi"),
                                    "diem_thong_thuong": tx_list,
                                    "diem_giua_ky": silver_row.get("giua_ky"),
                                    "diem_cuoi_ky": None,
                                    "diem_thuc_hanh_hien_tai": th_list,
                                    "diem_thuc_hanh_tich_hop": th1 if th1 is not None else (th_list[0] if th_list else None),
                                    "diem_thuong_ky_lt_list": tx_list,
                                    "diem_giua_ky_lt": silver_row.get("giua_ky"),
                                    "status_canh_bao": "An toan" if (silver_row.get("qt_10") or 10.0) >= 4.0 else "Nguy co",
                                }
                                logger.info(f"Đã truy xuất và ánh xạ thành công dữ liệu từ silver_diem_sinh_vien cho SV {student_id} môn {ma_mon}")
                                return mapped
                        except Exception as silver_err:
                            logger.error(f"Lỗi truy vấn silver_diem_sinh_vien: {silver_err}")
                    
                    logger.warning(f"Không tìm thấy bản ghi cho SV {student_id} môn {ma_mon} trên Databricks")
                        
        except Exception as e:
            logger.error(f"Lỗi kết nối Databricks SQL: {e}. Tự động fallback về dữ liệu giả lập.", exc_info=True)
    else:
        logger.info("Cấu hình Databricks trống. Đang sử dụng Mock Database để thử nghiệm cục bộ.")

    # ─── Fallback về In-Memory Database ──────────────────────────────────────
    key = (student_id, ma_mon)
    return MOCK_GOLD_DB.get(key)


def query_gold_predictions_by_student(student_id: str, target_grade: str = "A") -> Optional[List[Dict[str, Any]]]:
    """
    Query Databricks Gold prediction table created by the notebook:
    workspace.smartgpa_db.gold_du_bao_diem_cuoi_ky.

    Returns None when Databricks is not configured or cannot be reached, so callers can
    fallback to the local mock store.
    """
    server_hostname, http_path, access_token = _databricks_connection_settings()
    if not (server_hostname and http_path and access_token):
        logger.info("Databricks SQL is not configured. Falling back to local mock data.")
        return None

    try:
        from databricks import sql

        query = f"""
            SELECT
                student_id,
                student_name,
                ma_mon,
                ten_mon,
                ma_lop_hoc_phan,
                loai_hoc_phan,
                so_chi_lt,
                so_chi_th,
                tong_so_chi,
                thuong_xuyen_1,
                thuong_xuyen_2,
                giua_ky,
                thuc_hanh_1,
                thuc_hanh_2,
                thuc_hanh_3,
                lt_qt_10,
                th_qt_10,
                qt_10,
                diem_chu_muc_tieu,
                diem_muc_tieu_10,
                diem_cuoi_ky_can_dat,
                kha_thi,
                status_canh_bao
            FROM {_gold_table_name()}
            WHERE upper(student_id) = upper(?)
              AND diem_chu_muc_tieu = ?
            ORDER BY ma_mon
        """

        with sql.connect(
            server_hostname=server_hostname,
            http_path=http_path,
            access_token=access_token,
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, (student_id, target_grade))
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in rows]
    except Exception as e:
        logger.error("Could not query Databricks Gold prediction table: %s", e, exc_info=True)
        return None


def lay_diem_sinh_vien_tu_cloud(student_id: str, ma_mon: str):
    """
    Tra cứu điểm sinh viên trực tiếp từ Cloud Databricks SQL Warehouse.
    Có chế độ tự động fallback về Mock Database in-memory nếu không cấu hình/lỗi kết nối.
    """
    server_hostname = os.getenv("DATABRICKS_SERVER_HOSTNAME") or settings.DATABRICKS_SERVER_HOSTNAME or settings.DATABRICKS_HOST.replace("https://", "")
    http_path = os.getenv("DATABRICKS_HTTP_PATH") or settings.DATABRICKS_HTTP_PATH
    access_token = os.getenv("DATABRICKS_TOKEN") or settings.DATABRICKS_TOKEN
    catalog = os.getenv("DATABRICKS_CATALOG") or settings.DATABRICKS_CATALOG or "workspace"
    schema = os.getenv("DATABRICKS_SCHEMA") or settings.DATABRICKS_SCHEMA or "smartgpa_db"

    if server_hostname and http_path and access_token:
        try:
            from databricks import sql
            logger.info(f"Kết nối tới Databricks (lay_diem_sinh_vien_tu_cloud): {server_hostname}...")
            with sql.connect(  
                server_hostname=server_hostname.replace("https://", ""),
                http_path=http_path,
                access_token=access_token
            ) as connection:
                with connection.cursor() as cursor:
                    # 1. Thử truy vấn bảng gold_diem_sinh_vien
                    query = f"""
                        SELECT diem_tich_luy_hien_tai, loai_hoc_phan, tong_so_chi, 
                               diem_trung_binh_thuc_hanh, diem_chu_hien_tai, status_canh_bao_final
                        FROM {catalog}.{schema}.gold_diem_sinh_vien 
                        WHERE student_id = ? AND ma_mon = ?
                    """
                    try:
                        cursor.execute(query, (student_id, ma_mon))
                        result = cursor.fetchone()
                        if result:
                            logger.info(f"Đã lấy thành công điểm từ Cloud Gold Table cho SV {student_id} môn {ma_mon}")
                            return result
                    except Exception as gold_err:
                        logger.warning(f"Lỗi truy vấn gold_diem_sinh_vien: {gold_err}. Đang thử fallback truy vấn silver_diem_sinh_vien...")
                        # 2. Fallback sang truy vấn bảng silver_diem_sinh_vien
                        query_silver = f"""
                            SELECT 
                                student_id, student_name, ma_mon, ten_mon, ma_lop_hoc_phan, loai_hoc_phan, 
                                so_chi_lt, so_chi_th, tong_so_chi, thuong_xuyen_1, thuong_xuyen_2, giua_ky,
                                thuc_hanh_1, thuc_hanh_2, thuc_hanh_3, qt_10
                            FROM {catalog}.{schema}.silver_diem_sinh_vien
                            WHERE student_id = ? AND ma_mon = ?
                            LIMIT 1
                        """
                        cursor.execute(query_silver, (student_id, ma_mon))
                        row_s = cursor.fetchone()
                        if row_s:
                            columns_s = [desc[0] for desc in cursor.description]
                            silver_row = dict(zip(columns_s, row_s))
                            
                            loai_hp = silver_row.get("loai_hoc_phan", "ly_thuyet")
                            tong_so_chi = silver_row.get("tong_so_chi", 2)
                            
                            tx1 = silver_row.get("thuong_xuyen_1")
                            tx2 = silver_row.get("thuong_xuyen_2")
                            tx_list = [x for x in (tx1, tx2) if x is not None]
                            
                            th1 = silver_row.get("thuc_hanh_1")
                            th2 = silver_row.get("thuc_hanh_2")
                            th3 = silver_row.get("thuc_hanh_3")
                            th_list = [x for x in (th1, th2, th3) if x is not None]
                            
                            diem_trung_binh_th = round(sum(th_list) / len(th_list), 2) if th_list else 0.0
                            
                            # Tính điểm tích luỹ hiện tại
                            if loai_hp == "ly_thuyet":
                                tk_avg = sum(tx_list) / len(tx_list) if tx_list else 0.0
                                gk_val = silver_row.get("giua_ky") or 0.0
                                diem_tich_luy = round(0.2 * tk_avg + 0.3 * gk_val, 2)
                            elif loai_hp == "thuc_hanh":
                                diem_tich_luy = diem_trung_binh_th
                            else: # tich_hop
                                tk_avg = sum(tx_list) / len(tx_list) if tx_list else 0.0
                                gk_val = silver_row.get("giua_ky") or 0.0
                                lt_val = 0.2 * tk_avg + 0.3 * gk_val
                                chi_lt = silver_row.get("so_chi_lt") or 2
                                chi_th = silver_row.get("so_chi_th") or 1
                                diem_tich_luy = round((lt_val * chi_lt + diem_trung_binh_th * chi_th) / (chi_lt + chi_th), 2)
                            
                            # Tính điểm chữ hiện tại từ qt_10 (nếu có) hoặc điểm tích luỹ
                            qt_10 = silver_row.get("qt_10")
                            qt_val = qt_10 if qt_10 is not None else diem_tich_luy
                            
                            if loai_hp in ("thuc_hanh", "tich_hop") and diem_trung_binh_th < 3.0:
                                diem_chu = "F"
                            elif qt_val >= 9.0:
                                diem_chu = "A+"
                            elif qt_val >= 8.5:
                                diem_chu = "A"
                            elif qt_val >= 8.0:
                                diem_chu = "B+"
                            elif qt_val >= 7.0:
                                diem_chu = "B"
                            elif qt_val >= 6.0:
                                diem_chu = "C+"
                            elif qt_val >= 5.5:
                                diem_chu = "C"
                            elif qt_val >= 5.0:
                                diem_chu = "D+"
                            elif qt_val >= 4.0:
                                diem_chu = "D"
                            else:
                                diem_chu = "F"
                            
                            # Tính status_canh_bao_final
                            if loai_hp in ("thuc_hanh", "tich_hop") and diem_trung_binh_th < 3.0:
                                status_canh_bao_final = "CANH BAO: LIET THUC HANH (ROT MON)"
                            elif qt_val < 4.0:
                                status_canh_bao_final = "Nguy co rot mon"
                            else:
                                status_canh_bao_final = "An toan"
                            
                            result = (diem_tich_luy, loai_hp, tong_so_chi, diem_trung_binh_th, diem_chu, status_canh_bao_final)
                            logger.info(f"Đã lấy và ánh xạ thành công điểm từ silver_diem_sinh_vien cho SV {student_id} môn {ma_mon}: {result}")
                            return result
            
            logger.warning(f"Không tìm thấy bản ghi cho SV {student_id} môn {ma_mon} trên Cloud Databricks (cả Gold & Silver). Fallback về mock database cục bộ.")
        except Exception as e:
            logger.error(f"Lỗi kết nối hoặc truy vấn Databricks trong lay_diem_sinh_vien_tu_cloud: {e}. Fallback về mock data.", exc_info=True)
    else:
        logger.info("Chưa cấu hình Databricks Cloud. Fallback về Mock Database cục bộ.")

    # ─── Fallback về Mock Database ──────────────────────────────────────
    key = (student_id, ma_mon)
    mock_record = MOCK_GOLD_DB.get(key)
    if not mock_record:
        return None

    # Ánh xạ thông minh từ mock record sang cấu trúc tuple của câu SELECT
    loai_hp = mock_record.get("loai_hoc_phan", "ly_thuyet")
    tong_so_chi = mock_record.get("tong_so_chi", 2)
    status_canh_bao = mock_record.get("status_canh_bao", "An toan")
    status_canh_bao_final = "An toan" if status_canh_bao == "An toan" else "Nguy co"

    # Tính toán các đầu điểm giả lập tương ứng
    if loai_hp == "ly_thuyet":
        tk_list = mock_record.get("diem_thong_thuong") or []
        tk_avg = sum(tk_list) / len(tk_list) if tk_list else 8.0
        gk = mock_record.get("diem_giua_ky")
        gk_val = gk if gk is not None else 8.0
        diem_tich_luy = round(0.2 * tk_avg + 0.3 * gk_val, 2)
        diem_trung_binh_th = 0.0
        diem_chu = "B+"
    elif loai_hp == "thuc_hanh":
        th_list = mock_record.get("diem_thuc_hanh_hien_tai") or []
        th_avg = sum(th_list) / len(th_list) if th_list else 8.0
        diem_tich_luy = round(th_avg, 2)
        diem_trung_binh_th = round(th_avg, 2)
        diem_chu = "B+"
    else: # tich_hop
        th = mock_record.get("diem_thuc_hanh_tich_hop")
        th_val = th if th is not None else 8.0
        tk_lt_list = mock_record.get("diem_thuong_ky_lt_list") or []
        tk_lt_avg = sum(tk_lt_list) / len(tk_lt_list) if tk_lt_list else 8.0
        gk_lt = mock_record.get("diem_giua_ky_lt")
        gk_lt_val = gk_lt if gk_lt is not None else 8.0
        lt_val = 0.2 * tk_lt_avg + 0.3 * gk_lt_val
        chi_lt = mock_record.get("so_chi_lt", 2)
        chi_th = mock_record.get("so_chi_th", 1)
        diem_tich_luy = round((lt_val * chi_lt + th_val * chi_th) / (chi_lt + chi_th), 2)
        diem_trung_binh_th = round(th_val, 2)
        diem_chu = "B+"

    return (diem_tich_luy, loai_hp, tong_so_chi, diem_trung_binh_th, diem_chu, status_canh_bao_final)



def save_uploaded_scores_mock(rows: List[Dict[str, Any]]) -> int:
    """
    Lưu dữ liệu điểm vừa nạp vào Mock Database cục bộ để phục vụ giả lập tức thì.
    Đồng thời tự động sinh tài khoản cho các sinh viên chưa có tài khoản trong hệ thống.
    Trả về số dòng đã được xử lý/lưu.
    """
    from app.db.real_db import USERS_DB, build_student_username
    from app.core.security import hash_password
    from datetime import datetime, timezone
    from uuid import uuid4

    saved_count = 0
    for row in rows:
        student_id = row.get("student_id")
        ma_mon = row.get("ma_mon")
        if not student_id or not ma_mon:
            continue
            
        # 1. Tự động kiểm tra và sinh tài khoản sinh viên mới nếu chưa tồn tại
        existing_user = None
        for u in USERS_DB.values():
            if u.get("role") == "student" and u.get("student_id") == student_id:
                existing_user = u
                break
                
        if not existing_user:
            # Xác định họ tên đầy đủ
            raw_name = row.get("full_name") or row.get("student_name") or row.get("ho_ten") or row.get("name")
            if not raw_name:
                student_names_map = {
                    "SV1001": "Nguyễn Thảo Anh",
                    "SV1002": "Vũ Hải Vy",
                    "SV123456": "Nguyễn Văn An",
                    "23670631": "Nguyễn Trần Khánh Vy",
                    "23674120": "Phạm Minh Anh",
                    "23690184": "Trần Lê Tuấn",
                }
                raw_name = student_names_map.get(student_id, f"Sinh Viên {student_id}")
                
            # Tạo email theo dạng ten.mssv@smartgpa.edu
            username = build_student_username(student_id, raw_name)
            
            # Đăng ký vào database giả lập
            USERS_DB[username] = {
                "id": str(uuid4()),
                "email": "",
                "username": username,
                "password_hash": hash_password("Sv@123"),
                "full_name": raw_name,
                "role": "student",
                "is_active": True,
                "created_at": datetime.now(timezone.utc),
                "student_id": student_id,
                "notifications": [],
                "must_change_password": True,
                "email_verified": False,
            }
            logger.info(f"Auto-created student account: {username} for student_id: {student_id}")

        # Chuẩn hóa dữ liệu thô sang cấu trúc Gold Table tương thích
        mock_record = {
            "student_id": student_id,
            "ma_mon": ma_mon,
            "ma_lop_hoc_phan": row.get("ma_lop_hoc_phan"),
            "diem_thong_thuong": row.get("diem_thong_thuong_list") or [],
            "diem_giua_ky": row.get("diem_giua_ky"),
            "diem_cuoi_ky": row.get("diem_cuoi_ky"),
            "loai_hoc_phan": row.get("loai_hoc_phan", "ly_thuyet"),
            "so_chi_lt": row.get("so_chi_lt", 2),
            "so_chi_th": row.get("so_chi_th", 0),
            "tong_so_chi": row.get("so_chi_lt", 2) + row.get("so_chi_th", 0),
            "diem_thuc_hanh_hien_tai": row.get("diem_thuc_hanh_hien_tai") or [],
            "diem_thuc_hanh_tich_hop": row.get("diem_thuc_hanh_tich_hop"),
            "diem_thuong_ky_lt_list": row.get("diem_thuong_ky_lt_list") or [],
            "diem_giua_ky_lt": row.get("diem_giua_ky_lt"),
            "status_canh_bao": "An toan"
        }
        
        # Đánh giá cảnh báo học vụ sơ bộ (nếu có điểm quá thấp)
        scores_to_check = []
        if mock_record["diem_giua_ky"] is not None:
            scores_to_check.append(mock_record["diem_giua_ky"])
        if mock_record["diem_thong_thuong"]:
            scores_to_check.extend(mock_record["diem_thong_thuong"])
        if mock_record["diem_thuc_hanh_hien_tai"]:
            scores_to_check.extend(mock_record["diem_thuc_hanh_hien_tai"])
        if mock_record["diem_thuc_hanh_tich_hop"] is not None:
            scores_to_check.append(mock_record["diem_thuc_hanh_tich_hop"])
            
        if scores_to_check and (sum(scores_to_check) / len(scores_to_check)) < 4.0:
            mock_record["status_canh_bao"] = "Nguy co"

        MOCK_GOLD_DB[(student_id, ma_mon)] = mock_record
        saved_count += 1
        
        logger.info(f"Đã cập nhật {saved_count} bản ghi vào Mock Delta Gold Table.")

    sync_gold_to_silver()
    return saved_count

def sync_gold_to_silver() -> None:
    """Derive a simple Silver view from the Gold Mock DB.
    For each (student_id, ma_mon) compute average TK, GK and a risk flag.
    """
    MOCK_SILVER_DB.clear()
    for (student_id, ma_mon), record in MOCK_GOLD_DB.items():
        # Compute average of regular scores (TK) – could be either diem_thong_thuong or diem_thuong_ky_lt_list
        tk_list = record.get("diem_thong_thuong") or record.get("diem_thuong_ky_lt_list") or []
        tk_avg = sum(tk_list) / len(tk_list) if tk_list else 0.0
        # Determine GK (midterm) – could be diem_giua_ky or diem_giua_ky_lt
        gk = record.get("diem_giua_ky") or record.get("diem_giua_ky_lt")
        gk_val = gk if gk is not None else 0.0
        # Simple risk calculation similar to warnings logic
        risk = (0.2 * tk_avg + 0.3 * gk_val) < 4.0 or record.get("status_canh_bao") == "Nguy co"
        MOCK_SILVER_DB[(student_id, ma_mon)] = {
            "avg_tk": round(tk_avg, 2),
            "gk": round(gk_val, 2),
            "risk_flag": risk,
            "status_canh_bao": record.get("status_canh_bao", "An toan"),
        }


def query_silver_warnings_from_cloud() -> Optional[List[Dict[str, Any]]]:
    """
    Truy vấn toàn bộ dữ liệu từ bảng silver_diem_sinh_vien để làm giàu thông tin cảnh báo học vụ.
    Trả về None nếu không cấu hình/lỗi kết nối để fallback về Mock DB.
    """
    server_hostname, http_path, access_token = _databricks_connection_settings()
    catalog = os.getenv("DATABRICKS_CATALOG") or settings.DATABRICKS_CATALOG or "workspace"
    schema = os.getenv("DATABRICKS_SCHEMA") or settings.DATABRICKS_SCHEMA or "smartgpa_db"

    if not (server_hostname and http_path and access_token):
        logger.info("Chưa cấu hình Databricks Cloud. Fallback về Mock Database cục bộ.")
        return None

    try:
        from databricks import sql
        logger.info(f"Kết nối tới Databricks để lấy bảng Silver cho cảnh báo học vụ...")
        
        query = f"""
            SELECT 
                student_id, student_name, ma_mon, ten_mon, ma_lop_hoc_phan, loai_hoc_phan, 
                so_chi_lt, so_chi_th, tong_so_chi, thuong_xuyen_1, thuong_xuyen_2, giua_ky,
                thuc_hanh_1, thuc_hanh_2, thuc_hanh_3, qt_10
            FROM {catalog}.{schema}.silver_diem_sinh_vien
        """
        
        with sql.connect(
            server_hostname=server_hostname.replace("https://", ""),
            http_path=http_path,
            access_token=access_token,
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in rows]
    except Exception as e:
        logger.error(f"Lỗi truy vấn silver_diem_sinh_vien từ Databricks: {e}.", exc_info=True)
        return None


def query_course_grades_from_cloud(ma_mon: str) -> Optional[List[Dict[str, Any]]]:
    """
    Truy vấn toàn bộ điểm sinh viên cho môn học từ bảng silver_diem_sinh_vien trên Databricks.
    """
    server_hostname, http_path, access_token = _databricks_connection_settings()
    catalog = os.getenv("DATABRICKS_CATALOG") or settings.DATABRICKS_CATALOG or "workspace"
    schema = os.getenv("DATABRICKS_SCHEMA") or settings.DATABRICKS_SCHEMA or "smartgpa_db"

    if not (server_hostname and http_path and access_token):
        return None

    try:
        from databricks import sql
        query = f"""
            SELECT 
                student_id, student_name, ma_mon, ten_mon, ma_lop_hoc_phan, loai_hoc_phan, 
                so_chi_lt, so_chi_th, tong_so_chi, thuong_xuyen_1, thuong_xuyen_2, giua_ky,
                thuc_hanh_1, thuc_hanh_2, thuc_hanh_3, qt_10, diem_cuoi_ky
            FROM {catalog}.{schema}.silver_diem_sinh_vien
            WHERE ma_mon = ?
        """
        with sql.connect(
            server_hostname=server_hostname.replace("https://", ""),
            http_path=http_path,
            access_token=access_token,
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, (ma_mon,))
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in rows]
    except Exception as e:
        logger.error(f"Lỗi truy vấn điểm môn {ma_mon} từ Databricks: {e}")
        return None



