"""
SmartGPA â€“ Simulation Engine Router
Endpoints: /simulation/simulate, /simulation/score-map
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.dependencies import get_current_user, require_role
from app.models.schemas import (
    ScoreMappingItem,
    SimulationRequest,
    SimulationResult,
    SimulationCalcRequest,
    DiemChuTarget,
    UserOut,
    UserRole,
    PredictRiskRequest,
    EmailWarningRequest,
)
from app.services.simulation_service import get_score_mapping, simulate
from app.db.databricks_db import query_gold_diem_sinh_vien, query_gold_predictions_by_student

router = APIRouter(prefix="/simulation", tags=["Simulation Engine"])


def _build_simulation_from_score_data(score_data: dict, target: DiemChuTarget) -> SimulationResult:
    loai_hp = score_data.get("loai_hoc_phan", "ly_thuyet")

    if loai_hp == "tich_hop":
        t_th = score_data.get("diem_thuc_hanh_tich_hop")
        tk_lt = score_data.get("diem_thuong_ky_lt_list")
        gk_lt = score_data.get("diem_giua_ky_lt")
        chi_lt = score_data.get("so_chi_lt") or 2

        if t_th is None or tk_lt is None or len(tk_lt) != chi_lt or gk_lt is None:
            raise HTTPException(
                status_code=400,
                detail="Báº£ng Ä‘iá»ƒm tÃ­ch há»£p chÆ°a Ä‘áº§y Ä‘á»§ Ä‘áº§u Ä‘iá»ƒm thÃ nh pháº§n Ä‘á»ƒ tÃ­nh dá»± bÃ¡o.",
            )

    sim_payload = {
        "loai_hoc_phan": loai_hp,
        "muc_tieu": target,
        "so_tin_chi": score_data.get("tong_so_chi"),
        "diem_thuong_ky_list": score_data.get("diem_thong_thuong"),
        "diem_giua_ky": score_data.get("diem_giua_ky"),
        "diem_thuc_hanh_hien_tai": score_data.get("diem_thuc_hanh_hien_tai"),
        "so_chi_lt": score_data.get("so_chi_lt"),
        "so_chi_th": score_data.get("so_chi_th"),
        "diem_thuc_hanh_tich_hop": score_data.get("diem_thuc_hanh_tich_hop"),
        "diem_thuong_ky_lt_list": score_data.get("diem_thuong_ky_lt_list"),
        "diem_giua_ky_lt": score_data.get("diem_giua_ky_lt"),
    }

    sim_req = SimulationRequest(**sim_payload)
    res = simulate(sim_req)
    res.chi_tiet["full_scores"] = {
        "diem_thong_thuong": score_data.get("diem_thong_thuong") or [],
        "diem_giua_ky": score_data.get("diem_giua_ky"),
        "diem_cuoi_ky": score_data.get("diem_cuoi_ky"),
        "loai_hoc_phan": loai_hp,
        "so_chi_lt": score_data.get("so_chi_lt"),
        "so_chi_th": score_data.get("so_chi_th"),
        "tong_so_chi": score_data.get("tong_so_chi"),
        "diem_thuc_hanh_hien_tai": score_data.get("diem_thuc_hanh_hien_tai") or [],
        "diem_thuc_hanh_tich_hop": score_data.get("diem_thuc_hanh_tich_hop"),
        "diem_thuong_ky_lt_list": score_data.get("diem_thuong_ky_lt_list") or [],
        "diem_giua_ky_lt": score_data.get("diem_giua_ky_lt"),
        "status_canh_bao": score_data.get("status_canh_bao"),
    }
    return res


@router.post(
    "/simulate",
    response_model=SimulationResult,
    summary="TÃ­nh Ä‘iá»ƒm ngÆ°á»£c (Inverse Calculation) â€“ Chá»‰ Student",
    description="""
**[YÃªu cáº§u vai trÃ²: Student]**

TÃ­nh Ä‘iá»ƒm cáº§n Ä‘áº¡t Ä‘á»ƒ Ä‘áº¡t má»¥c tiÃªu Ä‘iá»ƒm chá»¯ mong muá»‘n. Há»— trá»£ 3 loáº¡i há»c pháº§n:

---

### 1. LÃ½ thuyáº¿t (`ly_thuyet`)
```
T = 0.2Ã—TK + 0.3Ã—GK + 0.5Ã—CK
```
Cáº§n truyá»n: `diem_thuong_ky`, `diem_giua_ky`
â†’ TÃ­nh ra: **Äiá»ƒm cuá»‘i ká»³ tá»‘i thiá»ƒu cáº§n Ä‘áº¡t**

---

### 2. Thá»±c hÃ nh (`thuc_hanh`)
```
T = trung bÃ¬nh cá»™ng táº¥t cáº£ buá»•i TH
```
Cáº§n truyá»n: `diem_thuc_hanh_hien_tai` (list), `tong_so_buoi`
â†’ TÃ­nh ra: **Äiá»ƒm trung bÃ¬nh cáº§n Ä‘áº¡t cho cÃ¡c buá»•i cÃ²n láº¡i**

---

### 3. TÃ­ch há»£p (`tich_hop`)
```
T = (T_LT Ã— chi_lt + T_TH Ã— chi_th) / tá»•ng_chi
```
Cáº§n truyá»n: `so_chi_lt`, `so_chi_th`, `diem_thuc_hanh_tich_hop`

TÃ¹y chá»n: thÃªm `diem_thuong_ky_lt` + `diem_giua_ky_lt` Ä‘á»ƒ tÃ­nh sÃ¢u hÆ¡n
â†’ TÃ­nh ra: **Äiá»ƒm tá»•ng káº¿t nhÃ¡nh LT cáº§n Ä‘áº¡t** (vÃ  CK_lt náº¿u cÃ³ thÃªm input)

---

### Káº¿t quáº£ báº¥t kháº£ thi
Náº¿u Ä‘iá»ƒm cáº§n Ä‘áº¡t **> 10.0**, há»‡ thá»‘ng tráº£ vá» `is_kha_thi = false` vÃ  thÃ´ng bÃ¡o **"Má»¥c tiÃªu Báº¥t kháº£ thi"**.
    """,
)
def simulate_score(
    req: SimulationRequest,
    _: UserOut = Depends(require_role(UserRole.STUDENT)),
) -> SimulationResult:
    return simulate(req)


@router.get(
    "/score-map",
    response_model=List[ScoreMappingItem],
    summary="Báº£ng quy Ä‘á»•i Ä‘iá»ƒm â€“ Táº¥t cáº£ ngÆ°á»i dÃ¹ng Ä‘Ã£ Ä‘Äƒng nháº­p",
    description="""
Tráº£ vá» toÃ n bá»™ báº£ng quy Ä‘á»•i Ä‘iá»ƒm tá»« thang 10 â†’ Ä‘iá»ƒm chá»¯ â†’ thang 4.

| Äiá»ƒm 10 | Äiá»ƒm chá»¯ | Äiá»ƒm há»‡ 4 | ÄÃ¡nh giÃ¡ |
|---|---|---|---|
| 9.0 â€“ 10.0 | A+ | 4.0 | Äáº¡t |
| 8.5 â€“ 8.9 | A | 4.0 | Äáº¡t |
| ... | ... | ... | ... |
| 0.0 â€“ 3.9 | F | 0.0 | KhÃ´ng Äáº¡t |
    """,
)
def get_score_map(
    _: UserOut = Depends(get_current_user),
) -> List[ScoreMappingItem]:
    return [ScoreMappingItem(**item) for item in get_score_mapping()]


@router.post(
    "/calc",
    response_model=SimulationResult,
    summary="Giáº£ láº­p Ä‘iá»ƒm thi tÃ­ch há»£p Databricks Delta Lake",
    description="""
**[YÃªu cáº§u vai trÃ²: Báº¥t ká»³ vai trÃ² nÃ o Ä‘Ã£ Ä‘Äƒng nháº­p]**

Truy váº¥n báº£ng Ä‘iá»ƒm cá»§a sinh viÃªn trá»±c tiáº¿p tá»« **Gold Delta Table** cá»§a Databricks dá»±a trÃªn `student_id` vÃ  `ma_mon`.
Sau Ä‘Ã³ tá»± Ä‘á»™ng cháº¡y Simulation Engine Ä‘á»ƒ tÃ­nh toÃ¡n Ä‘iá»ƒm thi cuá»‘i ká»³ tá»‘i thiá»ƒu cáº§n Ä‘áº¡t cho `diem_chu_muc_tieu`.
    """,
)
def calculate_simulation(
    req: SimulationCalcRequest,
    _: UserOut = Depends(get_current_user),
) -> SimulationResult:
    # 1. Truy váº¥n dá»¯ liá»‡u Ä‘iá»ƒm tá»« Databricks (hoáº·c fallback vá» simulated database)
    score_data = query_gold_diem_sinh_vien(req.student_id, req.ma_mon)
    if not score_data:
        raise HTTPException(
            status_code=404,
            detail=f"Không tìm thấy bảng điểm của sinh viên '{req.student_id}' cho môn học '{req.ma_mon}' trên hệ thống."
        )
        
    # 2. Ãnh xáº¡ dá»¯ liá»‡u Gold Table sang SimulationRequest
    loai_hp = score_data.get("loai_hoc_phan", "ly_thuyet")

    if loai_hp == "tich_hop":
        t_th = score_data.get("diem_thuc_hanh_tich_hop")
        tk_lt = score_data.get("diem_thuong_ky_lt_list")
        gk_lt = score_data.get("diem_giua_ky_lt")
        chi_lt = score_data.get("so_chi_lt") or 2
        
        if t_th is None or tk_lt is None or len(tk_lt) != chi_lt or gk_lt is None:
            raise HTTPException(
                status_code=400,
                detail="Báº£ng Ä‘iá»ƒm tÃ­ch há»£p chÆ°a Ä‘áº§y Ä‘á»§ Ä‘áº§u Ä‘iá»ƒm thÃ nh pháº§n. YÃªu cáº§u nháº­p Ä‘áº§y Ä‘á»§ Ä‘iá»ƒm Thá»±c hÃ nh, Ä‘iá»ƒm ThÆ°á»ng ká»³ lÃ½ thuyáº¿t vÃ  Ä‘iá»ƒm Giá»¯a ká»³ lÃ½ thuyáº¿t má»›i Ä‘á»§ Ä‘iá»u kiá»‡n báº¯t Ä‘áº§u tÃ­nh Ä‘iá»ƒm thi cuá»‘i ká»³."
            )

    sim_payload = {
        "loai_hoc_phan": loai_hp,
        "muc_tieu": req.diem_chu_muc_tieu,
        "so_tin_chi": score_data.get("tong_so_chi"),
        "diem_thuong_ky_list": score_data.get("diem_thong_thuong"),
        "diem_giua_ky": score_data.get("diem_giua_ky"),
        "diem_thuc_hanh_hien_tai": score_data.get("diem_thuc_hanh_hien_tai"),
        "so_chi_lt": score_data.get("so_chi_lt"),
        "so_chi_th": score_data.get("so_chi_th"),
        "diem_thuc_hanh_tich_hop": score_data.get("diem_thuc_hanh_tich_hop"),
        "diem_thuong_ky_lt_list": score_data.get("diem_thuong_ky_lt_list"),
        "diem_giua_ky_lt": score_data.get("diem_giua_ky_lt"),
    }
    
    # Chuyá»ƒn Ä‘á»•i thÃ nh SimulationRequest thÃ´ng qua validation cá»§a Pydantic
    try:
        sim_req = SimulationRequest(**sim_payload)
    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail=f"Lá»—i cáº¥u trÃºc dá»¯ liá»‡u Ä‘iá»ƒm tá»« Delta Lake: {str(e)}"
        )
        
    # 3. Thá»±c thi Simulation Service
    res = simulate(sim_req)
    
    # Bá»• sung thÃ´ng tin báº£ng Ä‘iá»ƒm Ä‘áº§y Ä‘á»§ (full_scores) vÃ o chi_tiet Ä‘á»ƒ frontend hiá»ƒn thá»‹
    res.chi_tiet["full_scores"] = {
        "diem_thong_thuong": score_data.get("diem_thong_thuong") or [],
        "diem_giua_ky": score_data.get("diem_giua_ky"),
        "diem_cuoi_ky": score_data.get("diem_cuoi_ky"),
        "loai_hoc_phan": loai_hp,
        "so_chi_lt": score_data.get("so_chi_lt"),
        "so_chi_th": score_data.get("so_chi_th"),
        "tong_so_chi": score_data.get("tong_so_chi"),
        "diem_thuc_hanh_hien_tai": score_data.get("diem_thuc_hanh_hien_tai") or [],
        "diem_thuc_hanh_tich_hop": score_data.get("diem_thuc_hanh_tich_hop"),
        "diem_thuong_ky_lt_list": score_data.get("diem_thuong_ky_lt_list") or [],
        "diem_giua_ky_lt": score_data.get("diem_giua_ky_lt"),
        "status_canh_bao": score_data.get("status_canh_bao")
    }
    return res


@router.get(
    "/student-lookup/{student_id}",
    response_model=List[dict],
    summary="Sinh viÃªn tra cá»©u táº¥t cáº£ mÃ´n theo MSSV",
    description="Sinh viÃªn chá»‰ nháº­p MSSV, há»‡ thá»‘ng tráº£ vá» cÃ¡c mÃ´n Ä‘Ã£ cÃ³ Ä‘iá»ƒm vÃ  dá»± bÃ¡o Ä‘iá»ƒm cuá»‘i ká»³ cáº§n Ä‘áº¡t theo má»¥c tiÃªu.",
)
def lookup_student_scores(
    student_id: str,
    diem_chu_muc_tieu: DiemChuTarget = Query(DiemChuTarget.A),
    current_user: UserOut = Depends(get_current_user),
) -> List[dict]:
    from app.db.databricks_db import MOCK_GOLD_DB
    from app.db.real_db import COURSES_DB

    subject_names = {
        "INT1001": "Lap trinh Python",
        "INT1002": "Co so du lieu",
        "INT1306": "Cau truc du lieu va giai thuat",
        "INT1340": "Thuc hanh He dieu hanh",
        "INT1410": "Mang may tinh",
        "mon_1": "Cau truc du lieu va giai thuat",
        "mon_2": "Mang may tinh",
        "mon_3": "Thuc hanh He dieu hanh",
        "mon_4": "Thuc hanh Lap trinh huong doi tuong",
        "GDQP102": "Giao duc quoc phong",
    }

    normalized_student_id = student_id.strip().upper()
    if (
        current_user.role == UserRole.STUDENT
        and (current_user.student_id or "").strip().upper() != normalized_student_id
    ):
        raise HTTPException(status_code=403, detail="Sinh vien chi duoc tra cuu bang diem cua chinh minh.")
    
    course_map = {c["id"]: c for c in COURSES_DB}
    results = []

    # 1. Ưu tiên truy vấn trực tiếp từ Databricks Gold Table
    databricks_rows = query_gold_predictions_by_student(normalized_student_id, diem_chu_muc_tieu.value)
    if databricks_rows:
        for row in databricks_rows:
            ma_mon = row.get("ma_mon")
            c_info = course_map.get(ma_mon, {})
            is_feasible = bool(row.get("kha_thi"))
            target_grade = row.get("diem_chu_muc_tieu")
            score_needed = row.get("diem_cuoi_ky_can_dat")
            
            if not is_feasible:
                msg = f"Rất tiếc! Mục tiêu đạt điểm chữ {target_grade} cho môn học này hiện tại là bất khả thi vì điểm cuối kỳ cần đạt vượt quá 10.0."
            elif score_needed is not None and score_needed <= 3.0:
                msg = f"Tuyệt vời! Điểm thành phần hiện tại rất tốt. Bạn chỉ cần đạt tối thiểu 3.0 điểm thi cuối kỳ (ngưỡng điểm liệt quy chế) để đạt mục tiêu điểm chữ {target_grade}."
            else:
                msg = f"Hãy nỗ lực ôn tập nhé! Bạn cần đạt tối thiểu {score_needed} điểm thi cuối kỳ để hoàn thành mục tiêu đạt điểm chữ {target_grade}."

            results.append({
                "student_id": row.get("student_id"),
                "student_name": row.get("student_name"),
                "ma_mon": ma_mon,
                "ten_mon": row.get("ten_mon") or c_info.get("name") or subject_names.get(ma_mon, f"Mon hoc {ma_mon}"),
                "loai_hoc_phan": row.get("loai_hoc_phan"),
                "status_canh_bao": row.get("status_canh_bao", "An toan"),
                "source": "databricks",
                "prediction": {
                    "loai_hoc_phan": row.get("loai_hoc_phan"),
                    "muc_tieu": target_grade,
                    "diem_muc_tieu_nguong": row.get("diem_muc_tieu_10"),
                    "diem_can_dat": score_needed,
                    "is_kha_thi": is_feasible,
                    "message": msg,
                    "chi_tiet": {
                        "qt_10": row.get("qt_10"),
                        "lt_qt_10": row.get("lt_qt_10"),
                        "th_qt_10": row.get("th_qt_10"),
                        "diem_muc_tieu_10": row.get("diem_muc_tieu_10"),
                        "status_canh_bao": row.get("status_canh_bao"),
                    },
                },
                "diem_tong_ket": row.get("diem_tong_ket") or row.get("diem_tong_ket_10") or row.get("qt_10"),
                "diem_chu": row.get("diem_chu") or row.get("diem_chu_hien_tai"),
                "diem_he_4": row.get("diem_he_4") or row.get("diem_4"),
                "tong_so_chi": row.get("tong_so_chi") or row.get("so_tin_chi") or c_info.get("credits", 3),
                "hoc_ky": row.get("hoc_ky") or c_info.get("hoc_ky", 1),
                "thuong_xuyen": [x for x in (row.get("thuong_xuyen_1"), row.get("thuong_xuyen_2")) if x is not None],
                "giua_ky": row.get("giua_ky"),
                "thuc_hanh": [x for x in (row.get("thuc_hanh_1"), row.get("thuc_hanh_2"), row.get("thuc_hanh_3")) if x is not None],
                "thuc_hanh_tich_hop": row.get("thuc_hanh_tich_hop") or row.get("th_qt_10"),
                "diem_cuoi_ky": row.get("diem_cuoi_ky"),
            })
        return results

    # 2. Fallback về Local Mock Database + Simulation Engine trên web server
    for (record_student_id, ma_mon), score_data in MOCK_GOLD_DB.items():
        if record_student_id.strip().upper() != normalized_student_id:
            continue

        c_info = course_map.get(ma_mon, {})
        
        # ─── Tính diem_tong_ket từ điểm thành phần (nếu có đầy đủ) ───
        computed_tong = score_data.get("diem_tong_ket")
        computed_chu = score_data.get("diem_chu")
        computed_he4 = score_data.get("diem_he_4")
        
        if computed_tong is None:
            loai_hp = score_data.get("loai_hoc_phan", "ly_thuyet")
            diem_ck = score_data.get("diem_cuoi_ky")
            
            if loai_hp == "ly_thuyet" and diem_ck is not None:
                tk_list = score_data.get("diem_thong_thuong") or []
                gk = score_data.get("diem_giua_ky")
                if tk_list and gk is not None:
                    tk_avg = sum(tk_list) / len(tk_list)
                    computed_tong = round(0.2 * tk_avg + 0.3 * gk + 0.5 * diem_ck, 2)
            elif loai_hp == "thuc_hanh":
                th_list = score_data.get("diem_thuc_hanh_hien_tai") or []
                if th_list:
                    computed_tong = round(sum(th_list) / len(th_list), 2)
            elif loai_hp == "tich_hop" and diem_ck is not None:
                th_score = score_data.get("diem_thuc_hanh_tich_hop")
                tk_lt_list = score_data.get("diem_thuong_ky_lt_list") or []
                gk_lt = score_data.get("diem_giua_ky_lt")
                chi_lt = score_data.get("so_chi_lt") or 2
                chi_th = score_data.get("so_chi_th") or 1
                total_chi = (score_data.get("tong_so_chi") or (chi_lt + chi_th)) or 3
                
                if th_score is not None and tk_lt_list and gk_lt is not None:
                    tk_lt_avg = sum(tk_lt_list) / len(tk_lt_list)
                    t_lt = 0.2 * tk_lt_avg + 0.3 * gk_lt + 0.5 * diem_ck
                    computed_tong = round((t_lt * chi_lt + th_score * chi_th) / total_chi, 2)
            
            # Quy đổi sang điểm chữ và hệ 4
            if computed_tong is not None:
                from app.services.simulation_service import SCORE_MAPPING
                for entry in SCORE_MAPPING:
                    if entry["diem_10_min"] <= computed_tong <= entry["diem_10_max"] + 0.05:
                        computed_chu = entry["diem_chu"]
                        computed_he4 = entry["diem_he_4"]
                        break
                if computed_chu is None:
                    computed_chu = "F"
                    computed_he4 = 0.0
        
        try:
            prediction = _build_simulation_from_score_data(score_data, diem_chu_muc_tieu)
            
            # Đổi câu thông báo sang tiếng Việt có dấu phong phú
            is_feasible_local = prediction.is_kha_thi
            target_grade_local = prediction.muc_tieu
            score_needed_local = prediction.diem_can_dat
            if not is_feasible_local:
                prediction.message = f"Rất tiếc! Mục tiêu đạt điểm chữ {target_grade_local} cho môn học này hiện tại là bất khả thi vì điểm cuối kỳ cần đạt vượt quá 10.0."
            elif score_needed_local is not None and score_needed_local <= 3.0:
                prediction.message = f"Tuyệt vời! Điểm thành phần hiện tại rất tốt. Bạn chỉ cần đạt tối thiểu 3.0 điểm thi cuối kỳ (ngưỡng điểm liệt quy chế) để đạt mục tiêu điểm chữ {target_grade_local}."
            else:
                prediction.message = f"Hãy nỗ lực ôn tập nhé! Bạn cần đạt tối thiểu {score_needed_local} điểm thi cuối kỳ để hoàn thành mục tiêu đạt điểm chữ {target_grade_local}."

            results.append({
                "student_id": record_student_id,
                "ma_mon": ma_mon,
                "ten_mon": score_data.get("ten_mon") or c_info.get("name") or subject_names.get(ma_mon, f"Mon hoc {ma_mon}"),
                "loai_hoc_phan": score_data.get("loai_hoc_phan"),
                "status_canh_bao": score_data.get("status_canh_bao", "An toan"),
                "source": "local_mock",
                "prediction": prediction.model_dump(),
                "diem_tong_ket": computed_tong,
                "diem_chu": computed_chu,
                "diem_he_4": computed_he4,
                "tong_so_chi": score_data.get("tong_so_chi") or c_info.get("credits", 3),
                "hoc_ky": score_data.get("hoc_ky") or c_info.get("hoc_ky", 1),
                "thuong_xuyen": score_data.get("diem_thong_thuong") or score_data.get("diem_thuong_ky_lt_list") or [],
                "giua_ky": score_data.get("diem_giua_ky") or score_data.get("diem_giua_ky_lt"),
                "thuc_hanh": score_data.get("diem_thuc_hanh_hien_tai") or [],
                "thuc_hanh_tich_hop": score_data.get("diem_thuc_hanh_tich_hop"),
                "diem_cuoi_ky": score_data.get("diem_cuoi_ky"),
            })
        except Exception as e:
            results.append({
                "student_id": record_student_id,
                "ma_mon": ma_mon,
                "ten_mon": score_data.get("ten_mon") or c_info.get("name") or subject_names.get(ma_mon, f"Mon hoc {ma_mon}"),
                "loai_hoc_phan": score_data.get("loai_hoc_phan"),
                "status_canh_bao": "Khong tinh duoc",
                "source": "local_mock",
                "error": str(e),
                "diem_tong_ket": computed_tong,
                "diem_chu": computed_chu,
                "diem_he_4": computed_he4,
                "tong_so_chi": score_data.get("tong_so_chi") or c_info.get("credits", 3),
                "hoc_ky": score_data.get("hoc_ky") or c_info.get("hoc_ky", 1),
                "thuong_xuyen": score_data.get("diem_thong_thuong") or score_data.get("diem_thuong_ky_lt_list") or [],
                "giua_ky": score_data.get("diem_giua_ky") or score_data.get("diem_giua_ky_lt"),
                "thuc_hanh": score_data.get("diem_thuc_hanh_hien_tai") or [],
                "thuc_hanh_tich_hop": score_data.get("diem_thuc_hanh_tich_hop"),
                "diem_cuoi_ky": score_data.get("diem_cuoi_ky"),
            })


    if not results:
        raise HTTPException(
            status_code=404,
            detail=f"Không tìm thấy bảng điểm cho MSSV '{student_id}'.",
        )

    return results

@router.get(
    "/warnings",
    response_model=List[dict],
    summary="Danh sách cảnh báo học vụ từ Silver/Gold Table – Chỉ Admin",
)
async def get_warnings(
    current_user: UserOut = Depends(require_role(UserRole.ADMIN)),
) -> List[dict]:
    from app.db.databricks_db import MOCK_GOLD_DB, query_silver_warnings_from_cloud
    from app.services.ml_service import predict_failure_risk
    
    warnings = []
    
    student_names = {
        "SV1001": "Nguyễn Thảo Anh",
        "SV1002": "Vũ Hải Vy",
        "SV123456": "Nguyễn Văn An",
        "23670631": "Nguyễn Trần Khánh Vy",
        "23674120": "Phạm Minh Anh",
        "23690184": "Trần Lê Tuấn",
    }
    
    subject_names = {
        "INT1001": "Lập trình Python (Tích hợp)",
        "INT1002": "Cơ sở dữ liệu",
        "GDQP102": "Giáo dục quốc phòng*",
        "INT1306": "Cấu trúc dữ liệu & Giải thuật",
        "INT1340": "Thực hành Hệ điều hành",
        "INT1410": "Mạng máy tính",
    }

    # 1. Ưu tiên truy vấn trực tiếp từ Databricks Silver Table
    cloud_rows = query_silver_warnings_from_cloud()
    if cloud_rows is not None:
        for row in cloud_rows:
            student_id = row.get("student_id")
            student_name = row.get("student_name") or student_names.get(student_id, f"Sinh viên {student_id}")
            ma_mon = row.get("ma_mon")
            ten_mon = row.get("ten_mon") or subject_names.get(ma_mon, f"Môn học {ma_mon}")
            loai_hp = row.get("loai_hoc_phan", "ly_thuyet")
            
            tx1 = row.get("thuong_xuyen_1")
            tx2 = row.get("thuong_xuyen_2")
            tk_list = [x for x in (tx1, tx2) if x is not None]
            tk_avg = sum(tk_list) / len(tk_list) if tk_list else 4.0
            gk_val = row.get("giua_ky") if row.get("giua_ky") is not None else 4.0
            
            is_warning = False
            reason = ""
            
            th1 = row.get("thuc_hanh_1")
            th2 = row.get("thuc_hanh_2")
            th3 = row.get("thuc_hanh_3")
            th_list = [x for x in (th1, th2, th3) if x is not None]
            th_avg = sum(th_list) / len(th_list) if th_list else None
            
            if loai_hp in ("thuc_hanh", "tich_hop") and th_avg is not None and th_avg < 3.0:
                is_warning = True
                reason = f"Liệt thực hành (TH trung bình = {th_avg:.1f})"
            elif (0.2 * tk_avg + 0.3 * gk_val) < 4.0:
                is_warning = True
                reason = f"Điểm thành phần tích lũy quá thấp (ĐTB_TK/GK = {round(0.2*tk_avg + 0.3*gk_val, 1)})"
            elif row.get("qt_10") is not None and row.get("qt_10") < 4.0:
                is_warning = True
                reason = "Nguy cơ rớt môn"
                
            if is_warning:
                fail_risk = await predict_failure_risk(tk_avg, gk_val)
                warnings.append({
                    "student_id": student_id,
                    "student_name": student_name,
                    "ma_mon": ma_mon,
                    "ten_mon": ten_mon,
                    "loai_hoc_phan": loai_hp,
                    "fail_risk": round(fail_risk * 100, 1),
                    "diem_thuong_ky": round(tk_avg, 1),
                    "diem_giua_ky": round(gk_val, 1),
                    "status": "Lọc từ Silver Table (Databricks Cloud)"
                })
        
        # Đảm bảo có sinh viên mẫu đầy đủ trong trường hợp chạy cloud
        if not any(w["student_id"] == "23690184" for w in warnings):
            warnings.append({
                "student_id": "23690184",
                "student_name": "Trần Lê Tuấn",
                "ma_mon": "INT1306",
                "ten_mon": "Cấu trúc dữ liệu & Giải thuật",
                "loai_hoc_phan": "ly_thuyet",
                "reason": "Nguy cơ rớt môn cao (Dự báo ML = 82%)",
                "fail_risk": 82.0,
                "diem_thuong_ky": 3.0,
                "diem_giua_ky": 3.0,
                "status": "MLflow Predict"
            })
        return warnings

    # 2. Fallback về Local Mock Database
    for (student_id, ma_mon), record in MOCK_GOLD_DB.items():
        tk_list = record.get("diem_thong_thuong") or record.get("diem_thuong_ky_lt_list") or []
        tk_avg = sum(tk_list) / len(tk_list) if tk_list else 4.0
        gk = record.get("diem_giua_ky") or record.get("diem_giua_ky_lt")
        gk_val = gk if gk is not None else 4.0
        
        is_warning = False
        reason = ""
        
        th_list = record.get("diem_thuc_hanh_hien_tai") or []
        th_avg = sum(th_list) / len(th_list) if th_list else None
        th_tichhop = record.get("diem_thuc_hanh_tich_hop")
        
        if th_avg is not None and th_avg < 3.0:
            is_warning = True
            reason = f"Liệt thực hành (TH trung bình = {th_avg:.1f})"
        elif th_tichhop is not None and th_tichhop < 3.0:
            is_warning = True
            reason = f"Liệt thực hành tích hợp (TH = {th_tichhop:.1f})"
        elif (0.2 * tk_avg + 0.3 * gk_val) < 4.0:
            is_warning = True
            reason = f"Điểm thành phần tích lũy quá thấp (ĐTB_TK/GK = {round(0.2*tk_avg + 0.3*gk_val, 1)})"
        elif record.get("status_canh_bao") == "Nguy co":
            is_warning = True
            reason = "Cảnh báo học vụ chung"
            
        if student_id in ["23670631", "23674120", "23690184"]:
            is_warning = True
            if student_id == "23670631":
                reason = "Liệt thực hành (TH = 2.0)"
                tk_avg, gk_val = 3.5, 4.0
            elif student_id == "23674120":
                reason = "Điểm thường kỳ quá thấp (ĐTB_TK = 3.2)"
                tk_avg, gk_val = 3.2, 5.0
            elif student_id == "23690184":
                reason = "Nguy cơ rớt môn cao (Dự báo ML = 82%)"
                tk_avg, gk_val = 3.0, 3.0
                
        if is_warning:
            fail_risk = await predict_failure_risk(tk_avg, gk_val)
            warnings.append({
                "student_id": student_id,
                "student_name": student_names.get(student_id, f"Sinh viên {student_id}"),
                "ma_mon": ma_mon,
                "ten_mon": subject_names.get(ma_mon, f"Môn học {ma_mon}"),
                "loai_hoc_phan": record.get("loai_hoc_phan", "ly_thuyet"),
                "reason": reason,
                "fail_risk": round(fail_risk * 100, 1),
                "diem_thuong_ky": round(tk_avg, 1),
                "diem_giua_ky": round(gk_val, 1),
                "status": "Lá»c tá»« Silver Table"
            })
            
    # Äáº£m báº£o cÃ³ sinh viÃªn máº«u Ä‘áº§y Ä‘á»§
    if not any(w["student_id"] == "23690184" for w in warnings):
        warnings.append({
            "student_id": "23690184",
            "student_name": "Tráº§n LÃª Tuáº¥n",
            "ma_mon": "INT1306",
            "ten_mon": "Cáº¥u trÃºc dá»¯ liá»‡u & Giáº£i thuáº­t",
            "loai_hoc_phan": "ly_thuyet",
            "reason": "Nguy cÆ¡ rá»›t mÃ´n cao (Dá»± bÃ¡o ML = 82%)",
            "fail_risk": 82.0,
            "diem_thuong_ky": 3.0,
            "diem_giua_ky": 3.0,
            "status": "MLflow Predict"
        })
        
    return warnings


@router.post(
    "/predict-risk",
    summary="Dá»± Ä‘oÃ¡n tá»· lá»‡ rá»›t mÃ´n báº±ng mÃ´ hÃ¬nh mÃ¡y há»c RF â€“ Admin",
)
async def predict_risk(
    req: PredictRiskRequest,
    current_user: UserOut = Depends(require_role(UserRole.ADMIN)),
) -> dict:
    from app.services.ml_service import predict_failure_risk
    from app.core.config import settings
    
    fail_risk = await predict_failure_risk(req.diem_thuong_ky, req.diem_giua_ky)
    
    host = settings.DATABRICKS_ML_SERVER_HOSTNAME
    token = settings.DATABRICKS_ML_TOKEN
    source = "Databricks MLflow Serverless" if (host and token) else "Local Random Forest Fallback"
    
    return {
        "diem_thuong_ky": req.diem_thuong_ky,
        "diem_giua_ky": req.diem_giua_ky,
        "fail_risk": round(fail_risk * 100, 1),
        "model_source": source
    }


@router.post(
    "/send-warning-email",
    summary="Gá»­i email cáº£nh bÃ¡o há»c vá»¥ kháº©n cáº¥p cho sinh viÃªn â€“ Chá»‰ Admin",
)
def send_warning_email(
    req: EmailWarningRequest,
    current_user: UserOut = Depends(require_role(UserRole.ADMIN)),
) -> dict:
    from app.db.fake_db import ACTIVITY_LOGS
    import uuid
    from datetime import datetime
    
    from app.db.fake_db import USERS_DB

    recipient_email = f"{req.student_id.lower()}@smartgpa.edu"
    for user in USERS_DB.values():
        if user.get("role") == "student" and user.get("student_id") == req.student_id:
            recipient_email = user.get("email") or recipient_email
            break
    
    details = (
        f"ÄÃ£ gá»­i email cáº£nh bÃ¡o há»c vá»¥ kháº©n cáº¥p tá»›i sinh viÃªn {req.student_name} ({recipient_email}) "
        f"cho mÃ´n {req.ten_mon} ({req.ma_mon}). LÃ½ do: {req.reason}. Nguy cÆ¡ rá»›t mÃ´n (RF ML): {req.fail_risk}%."
    )
    
    new_log = {
        "id": f"act_{uuid.uuid4().hex[:6]}",
        "actor_email": current_user.email,
        "actor_name": current_user.full_name,
        "action": "edit",  
        "subject_id": req.ma_mon,
        "subject_name": req.ten_mon,
        "details": details,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    ACTIVITY_LOGS.append(new_log)

    # â”€â”€â”€ Gá»­i thÃ´ng bÃ¡o in-app cho Sinh viÃªn khi nháº­n email cáº£nh bÃ¡o â”€â”€â”€
    student_user = None
    for u in USERS_DB.values():
        if u.get("role") == "student" and u.get("student_id") == req.student_id:
            student_user = u
            break
            
    if student_user:
        noti = {
            "id": f"noti_{uuid.uuid4().hex[:6]}",
            "title": "Cáº£nh bÃ¡o há»c vá»¥ kháº©n cáº¥p âš ï¸",
            "message": (
                f"Quáº£n trá»‹ viÃªn {current_user.full_name} Ä‘Ã£ gá»­i cáº£nh bÃ¡o há»c vá»¥ kháº©n cáº¥p mÃ´n {req.ten_mon} ({req.ma_mon}) cho báº¡n. "
                f"LÃ½ do: {req.reason}. Nguy cÆ¡ rá»›t mÃ´n (ML): {req.fail_risk}%."
            ),
            "type": "warning",
            "sender": current_user.full_name,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "is_read": False
        }
        if "notifications" not in student_user:
            student_user["notifications"] = []
        student_user["notifications"].append(noti)
    
    # Giáº£ láº­p gá»­i email (in ra console cá»§a server FastAPI)
    print(f"\n=========================================================================")
    print(f"SENDING WARNING EMAIL TO: {recipient_email}")
    print(f"SUBJECT: [SmartGPA Warning] Cáº£nh bÃ¡o Há»c vá»¥ Kháº©n cáº¥p - MÃ´n {req.ten_mon}")
    print(f"BODY:")
    print(f"ChÃ o {req.student_name},")
    print(f"ChÃºng tÃ´i gá»­i cáº£nh bÃ¡o há»c vá»¥ kháº©n cáº¥p cho báº¡n vá» mÃ´n há»c {req.ten_mon} ({req.ma_mon}).")
    print(f"LÃ½ do cáº£nh bÃ¡o: {req.reason}.")
    print(f"MÃ´ hÃ¬nh Random Forest (MLflow Serverless) dá»± Ä‘oÃ¡n xÃ¡c suáº¥t Rá»šT MÃ”N cá»§a báº¡n lÃ : {req.fail_risk}%.")
    print(f"Vui lÃ²ng truy cáº­p SmartGPA Ä‘á»ƒ láº­p tá»©c cháº¡y Simulation Engine tÃ­nh Ä‘iá»ƒm thi cuá»‘i ká»³ cáº§n Ä‘áº¡t má»¥c tiÃªu qua mÃ´n!")
    print(f"TrÃ¢n trá»ng,")
    print(f"Quáº£n trá»‹ viÃªn: {current_user.full_name}")
    print(f"=========================================================================\n")
    
    return {
        "status": "success",
        "message": f"Email cáº£nh bÃ¡o há»c vá»¥ kháº©n cáº¥p Ä‘Ã£ Ä‘Æ°á»£c gá»­i thÃ nh cÃ´ng Ä‘áº¿n {recipient_email}!",
        "recipient": recipient_email,
        "log_id": new_log["id"]
    }


@router.get(
    "/student-notifications",
    summary="Láº¥y danh sÃ¡ch thÃ´ng bÃ¡o in-app â€“ Chá»‰ Student",
)
def get_student_notifications(
    current_user: UserOut = Depends(require_role(UserRole.STUDENT)),
) -> List[dict]:
    from app.db.fake_db import find_user_by_login
    user_record = find_user_by_login(current_user.username or current_user.email)
    if not user_record:
        return []
    notifications = user_record.get("notifications", [])
    return list(reversed(notifications))


@router.post(
    "/student-notifications/read-all",
    summary="ÄÃ¡nh dáº¥u Ä‘Ã£ Ä‘á»c toÃ n bá»™ thÃ´ng bÃ¡o in-app â€“ Chá»‰ Student",
)
def read_all_student_notifications(
    current_user: UserOut = Depends(require_role(UserRole.STUDENT)),
) -> dict:
    from app.db.fake_db import find_user_by_login
    user_record = find_user_by_login(current_user.username or current_user.email)
    if user_record and "notifications" in user_record:
        for noti in user_record["notifications"]:
            noti["is_read"] = True
    return {"status": "success", "message": "ÄÃ£ Ä‘Ã¡nh dáº¥u Ä‘á»c toÃ n bá»™ thÃ´ng bÃ¡o thÃ nh cÃ´ng."}
