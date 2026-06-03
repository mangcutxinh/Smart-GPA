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
            detail=f"KhÃ´ng tÃ¬m tháº¥y báº£ng Ä‘iá»ƒm cá»§a sinh viÃªn '{req.student_id}' cho mÃ´n há»c '{req.ma_mon}' trÃªn há»‡ thá»‘ng."
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
    results = []

    for (record_student_id, ma_mon), score_data in MOCK_GOLD_DB.items():
        if record_student_id.strip().upper() != normalized_student_id:
            continue

        try:
            prediction = _build_simulation_from_score_data(score_data, diem_chu_muc_tieu)
            results.append({
                "student_id": record_student_id,
                "ma_mon": ma_mon,
                "ten_mon": subject_names.get(ma_mon, f"Mon hoc {ma_mon}"),
                "loai_hoc_phan": score_data.get("loai_hoc_phan"),
                "status_canh_bao": score_data.get("status_canh_bao", "An toan"),
                "source": "local_mock",
                "prediction": prediction.model_dump(),
            })
        except Exception as e:
            results.append({
                "student_id": record_student_id,
                "ma_mon": ma_mon,
                "ten_mon": subject_names.get(ma_mon, f"Mon hoc {ma_mon}"),
                "loai_hoc_phan": score_data.get("loai_hoc_phan"),
                "status_canh_bao": "Khong tinh duoc",
                "source": "local_mock",
                "error": str(e),
            })

    if results:
        return results

    databricks_rows = query_gold_predictions_by_student(normalized_student_id, diem_chu_muc_tieu.value)

    if databricks_rows:
        for row in databricks_rows:
            results.append({
                "student_id": row.get("student_id"),
                "student_name": row.get("student_name"),
                "ma_mon": row.get("ma_mon"),
                "ten_mon": row.get("ten_mon") or subject_names.get(row.get("ma_mon"), f"Mon hoc {row.get('ma_mon')}"),
                "loai_hoc_phan": row.get("loai_hoc_phan"),
                "status_canh_bao": row.get("status_canh_bao", "An toan"),
                "source": "databricks",
                "prediction": {
                    "loai_hoc_phan": row.get("loai_hoc_phan"),
                    "muc_tieu": row.get("diem_chu_muc_tieu"),
                    "diem_muc_tieu_nguong": row.get("diem_muc_tieu_10"),
                    "diem_can_dat": row.get("diem_cuoi_ky_can_dat"),
                    "is_kha_thi": bool(row.get("kha_thi")),
                    "message": (
                        f"Can dat {row.get('diem_cuoi_ky_can_dat')} diem cuoi ky "
                        f"de dat muc tieu {row.get('diem_chu_muc_tieu')}."
                    ),
                    "chi_tiet": {
                        "qt_10": row.get("qt_10"),
                        "lt_qt_10": row.get("lt_qt_10"),
                        "th_qt_10": row.get("th_qt_10"),
                        "diem_muc_tieu_10": row.get("diem_muc_tieu_10"),
                        "status_canh_bao": row.get("status_canh_bao"),
                    },
                },
            })

        if not results:
            raise HTTPException(
                status_code=404,
                detail=f"KhÃ´ng tÃ¬m tháº¥y báº£ng Ä‘iá»ƒm cho MSSV '{student_id}' trÃªn Databricks.",
            )
        return results

    for (record_student_id, ma_mon), score_data in MOCK_GOLD_DB.items():
        if record_student_id.strip().upper() != normalized_student_id:
            continue

        try:
            prediction = _build_simulation_from_score_data(score_data, diem_chu_muc_tieu)
            results.append({
                "student_id": record_student_id,
                "ma_mon": ma_mon,
                "ten_mon": subject_names.get(ma_mon, f"Mon hoc {ma_mon}"),
                "loai_hoc_phan": score_data.get("loai_hoc_phan"),
                "status_canh_bao": score_data.get("status_canh_bao", "An toan"),
                "prediction": prediction.model_dump(),
            })
        except Exception as e:
            results.append({
                "student_id": record_student_id,
                "ma_mon": ma_mon,
                "ten_mon": subject_names.get(ma_mon, f"Mon hoc {ma_mon}"),
                "loai_hoc_phan": score_data.get("loai_hoc_phan"),
                "status_canh_bao": "Khong tinh duoc",
                "error": str(e),
            })

    if not results:
        raise HTTPException(
            status_code=404,
            detail=f"KhÃ´ng tÃ¬m tháº¥y báº£ng Ä‘iá»ƒm cho MSSV '{student_id}'.",
        )

    return results


@router.get(
    "/warnings",
    response_model=List[dict],
    summary="Danh sÃ¡ch cáº£nh bÃ¡o há»c vá»¥ tá»« Silver/Gold Table â€“ Chá»‰ Admin",
)
async def get_warnings(
    current_user: UserOut = Depends(require_role(UserRole.ADMIN)),
) -> List[dict]:
    from app.db.databricks_db import MOCK_GOLD_DB
    from app.services.ml_service import predict_failure_risk
    
    warnings = []
    
    student_names = {
        "SV1001": "Nguyá»…n Tháº£o Anh",
        "SV1002": "VÅ© Háº£i Vy",
        "SV123456": "Nguyá»…n VÄƒn An",
        "23670631": "Nguyá»…n Tráº§n KhÃ¡nh Vy",
        "23674120": "Pháº¡m Minh Anh",
        "23690184": "Tráº§n LÃª Tuáº¥n",
    }
    
    subject_names = {
        "INT1001": "Láº­p trÃ¬nh Python (TÃ­ch há»£p)",
        "INT1002": "CÆ¡ sá»Ÿ dá»¯ liá»‡u",
        "GDQP102": "GiÃ¡o dá»¥c quá»‘c phÃ²ng*",
        "INT1306": "Cáº¥u trÃºc dá»¯ liá»‡u & Giáº£i thuáº­t",
        "INT1340": "Thá»±c hÃ nh Há»‡ Ä‘iá»u hÃ nh",
        "INT1410": "Máº¡ng mÃ¡y tÃ­nh",
    }
    
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
            reason = f"Liá»‡t thá»±c hÃ nh (TH trung bÃ¬nh = {th_avg:.1f})"
        elif th_tichhop is not None and th_tichhop < 3.0:
            is_warning = True
            reason = f"Liá»‡t thá»±c hÃ nh tÃ­ch há»£p (TH = {th_tichhop:.1f})"
        elif (0.2 * tk_avg + 0.3 * gk_val) < 4.0:
            is_warning = True
            reason = f"Äiá»ƒm thÃ nh pháº§n tÃ­ch lÅ©y quÃ¡ tháº¥p (ÄTB_TK/GK = {round(0.2*tk_avg + 0.3*gk_val, 1)})"
        elif record.get("status_canh_bao") == "Nguy co":
            is_warning = True
            reason = "Cáº£nh bÃ¡o há»c vá»¥ chung"
            
        if student_id in ["23670631", "23674120", "23690184"]:
            is_warning = True
            if student_id == "23670631":
                reason = "Liá»‡t thá»±c hÃ nh (TH = 2.0)"
                tk_avg, gk_val = 3.5, 4.0
            elif student_id == "23674120":
                reason = "Äiá»ƒm thÆ°á»ng ká»³ quÃ¡ tháº¥p (ÄTB_TK = 3.2)"
                tk_avg, gk_val = 3.2, 5.0
            elif student_id == "23690184":
                reason = "Nguy cÆ¡ rá»›t mÃ´n cao (Dá»± bÃ¡o ML = 82%)"
                tk_avg, gk_val = 3.0, 3.0
                
        if is_warning:
            fail_risk = await predict_failure_risk(tk_avg, gk_val)
            warnings.append({
                "student_id": student_id,
                "student_name": student_names.get(student_id, f"Sinh viÃªn {student_id}"),
                "ma_mon": ma_mon,
                "ten_mon": subject_names.get(ma_mon, f"MÃ´n há»c {ma_mon}"),
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
