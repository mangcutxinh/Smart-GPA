"""
SmartGPA – Simulation Engine Service
Thuật toán tính điểm ngược (Inverse Calculation) real-time theo 3 loại học phần.

Công thức:
  - Lý thuyết:  T = 0.2×TK + 0.3×GK + 0.5×CK
  - Thực hành:  T = mean(TH_1, ..., TH_x)
  - Tích hợp:   T = (T_LT × chi_lt + T_TH × chi_th) / tổng_chi

Bảng quy đổi theo tài liệu quy chế đào tạo (image_4.png):
  A+ (9.0–10.0), A (8.5–8.9), B+ (8.0–8.4), B (7.0–7.9),
  C+ (6.5–6.9), C (5.5–6.4), D+ (5.0–5.4), D (4.0–4.9), F (0.0–3.9)
"""
import math
from typing import Optional

from app.models.schemas import (
    DiemChuTarget,
    HocPhanType,
    ScoreMappingItem,
    SimulationRequest,
    SimulationResult,
)

# ─── Bảng quy đổi điểm (từ image_4.png) ─────────────────────
SCORE_MAPPING: list[dict] = [
    {"diem_chu": "A+", "diem_10_min": 9.0, "diem_10_max": 10.0, "diem_he_4": 4.0, "loai_danh_gia": "Đạt"},
    {"diem_chu": "A",  "diem_10_min": 8.5, "diem_10_max":  8.9, "diem_he_4": 4.0, "loai_danh_gia": "Đạt"},
    {"diem_chu": "B+", "diem_10_min": 8.0, "diem_10_max":  8.4, "diem_he_4": 3.5, "loai_danh_gia": "Đạt"},
    {"diem_chu": "B",  "diem_10_min": 7.0, "diem_10_max":  7.9, "diem_he_4": 3.0, "loai_danh_gia": "Đạt"},
    {"diem_chu": "C+", "diem_10_min": 6.0, "diem_10_max":  6.9, "diem_he_4": 2.5, "loai_danh_gia": "Đạt"}, # Updated
    {"diem_chu": "C",  "diem_10_min": 5.5, "diem_10_max":  5.9, "diem_he_4": 2.0, "loai_danh_gia": "Đạt"}, # Updated
    {"diem_chu": "D+", "diem_10_min": 5.0, "diem_10_max":  5.4, "diem_he_4": 1.5, "loai_danh_gia": "Đạt"},
    {"diem_chu": "D",  "diem_10_min": 4.0, "diem_10_max":  4.9, "diem_he_4": 1.0, "loai_danh_gia": "Đạt"},
    {"diem_chu": "F",  "diem_10_min": 0.0, "diem_10_max":  3.9, "diem_he_4": 0.0, "loai_danh_gia": "Không Đạt"},
]

_SCORE_MAP_DICT: dict[str, dict] = {item["diem_chu"]: item for item in SCORE_MAPPING}


# ─── Helpers ─────────────────────────────────────────────────

def _ceil_1dec(value: float) -> float:
    """Làm tròn lên đến 1 chữ số thập phân (ceiling to 0.1)"""
    return math.ceil(value * 10) / 10


def _get_threshold(diem_chu: str) -> float:
    """Lấy ngưỡng điểm tối thiểu (diem_10_min) của mục tiêu điểm chữ"""
    return _SCORE_MAP_DICT[diem_chu]["diem_10_min"]


def _build_infeasible(
    loai: str, muc_tieu: str, threshold: float, raw_score: float, chi_tiet: dict
) -> SimulationResult:
    return SimulationResult(
        loai_hoc_phan=loai,
        muc_tieu=muc_tieu,
        diem_muc_tieu_nguong=threshold,
        diem_can_dat=None,
        is_kha_thi=False,
        message=(
            f"Mục tiêu Bất khả thi! "
            f"Điểm cần đạt ({raw_score:.2f}) vượt quá thang điểm tối đa (10.0)."
        ),
        chi_tiet=chi_tiet,
    )


def _build_guaranteed(
    loai: str, muc_tieu: str, threshold: float, chi_tiet: dict
) -> SimulationResult:
    return SimulationResult(
        loai_hoc_phan=loai,
        muc_tieu=muc_tieu,
        diem_muc_tieu_nguong=threshold,
        diem_can_dat=0.0,
        is_kha_thi=True,
        message=f"Bạn đã chắc chắn đạt mục tiêu {muc_tieu} mà không cần thêm điểm!",
        chi_tiet=chi_tiet,
    )


# ─── Public API ───────────────────────────────────────────────

def simulate(req: SimulationRequest) -> SimulationResult:
    """Điều phối tính điểm ngược theo loại học phần"""
    threshold = _get_threshold(req.muc_tieu.value)

    if req.loai_hoc_phan == HocPhanType.LY_THUYET:
        return _simulate_ly_thuyet(req, threshold)
    elif req.loai_hoc_phan == HocPhanType.THUC_HANH:
        return _simulate_thuc_hanh(req, threshold)
    else:  # TICH_HOP
        return _simulate_tich_hop(req, threshold)


def get_score_mapping() -> list[dict]:
    """Trả về bảng quy đổi điểm đầy đủ"""
    return SCORE_MAPPING


# ─── Lý thuyết ───────────────────────────────────────────────

def _simulate_ly_thuyet(req: SimulationRequest, threshold: float) -> SimulationResult:
    """
    T = 0.2×TK + 0.3×GK + 0.5×CK
    → CK_min = (threshold - 0.2×TK - 0.3×GK) / 0.5
    """
    loai_str = "Lý thuyết"
    gk = req.diem_giua_ky

    if gk is None:
        return SimulationResult(
            loai_hoc_phan=loai_str,
            muc_tieu=req.muc_tieu.value,
            diem_muc_tieu_nguong=threshold,
            diem_can_dat=None,
            is_kha_thi=False,
            message="Vui lòng cung cấp điểm giữa kỳ (diem_giua_ky)",
            chi_tiet={},
        )

    # Tính toán ĐTB thường kỳ (ĐTB_TK) theo số tín chỉ
    if req.diem_thuong_ky_list is not None:
        so_tin_chi = req.so_tin_chi
        if so_tin_chi not in (2, 3):
            return SimulationResult(
                loai_hoc_phan=loai_str,
                muc_tieu=req.muc_tieu.value,
                diem_muc_tieu_nguong=threshold,
                diem_can_dat=None,
                is_kha_thi=False,
                message="Vui lòng cung cấp số tín chỉ (so_tin_chi) là 2 hoặc 3",
                chi_tiet={},
            )
        if len(req.diem_thuong_ky_list) != so_tin_chi:
            return SimulationResult(
                loai_hoc_phan=loai_str,
                muc_tieu=req.muc_tieu.value,
                diem_muc_tieu_nguong=threshold,
                diem_can_dat=None,
                is_kha_thi=False,
                message=f"Số lượng đầu điểm thường kỳ phải bằng đúng số tín chỉ ({so_tin_chi})",
                chi_tiet={},
            )
        dtb_tk = sum(req.diem_thuong_ky_list) / so_tin_chi
    elif req.diem_thuong_ky is not None:
        dtb_tk = req.diem_thuong_ky
    else:
        return SimulationResult(
            loai_hoc_phan=loai_str,
            muc_tieu=req.muc_tieu.value,
            diem_muc_tieu_nguong=threshold,
            diem_can_dat=None,
            is_kha_thi=False,
            message="Vui lòng cung cấp danh sách điểm thường kỳ (diem_thuong_ky_list) hoặc điểm thường kỳ (diem_thuong_ky)",
            chi_tiet={},
        )

    base = 0.2 * dtb_tk + 0.3 * gk        # Phần điểm không có CK
    ck_raw = (threshold - base) / 0.5  # Điểm CK cần thiết (chính xác)
    ck_needed = _ceil_1dec(ck_raw)

    chi_tiet = {
        "cong_thuc": "T = 0.2×TK + 0.3×GK + 0.5×CK",
        "diem_thuong_ky_trung_binh": round(dtb_tk, 2),
        "diem_giua_ky": gk,
        "diem_hien_tai_khong_ck": round(base, 2),
        "ck_can_dat_chinh_xac": round(ck_raw, 4),
    }
    if req.diem_thuong_ky_list is not None:
        chi_tiet["diem_thuong_ky_list"] = req.diem_thuong_ky_list
        chi_tiet["so_tin_chi"] = req.so_tin_chi

    if ck_needed > 10.0:
        return _build_infeasible(loai_str, req.muc_tieu.value, threshold, ck_raw, chi_tiet)

    if ck_needed <= 0.0:
        return _build_guaranteed(loai_str, req.muc_tieu.value, threshold, chi_tiet)

    return SimulationResult(
        loai_hoc_phan=loai_str,
        muc_tieu=req.muc_tieu.value,
        diem_muc_tieu_nguong=threshold,
        diem_can_dat=ck_needed,
        is_kha_thi=True,
        message=(
            f"Bạn cần đạt tối thiểu {ck_needed} điểm cuối kỳ "
            f"để đạt loại {req.muc_tieu.value} (≥{threshold} điểm)"
        ),
        chi_tiet=chi_tiet,
    )


# ─── Thực hành ───────────────────────────────────────────────

def _simulate_thuc_hanh(req: SimulationRequest, threshold: float) -> SimulationResult:
    """
    T = mean(TH_1, ..., TH_x)
    → score_needed = (threshold × total - sum_existing) / remaining
    """
    loai_str = "Thực hành"
    existing = req.diem_thuc_hanh_hien_tai or []
    
    # Xác định tổng số buổi (số tín chỉ)
    if req.so_tin_chi is not None:
        total = req.so_tin_chi
    elif req.tong_so_buoi is not None:
        total = req.tong_so_buoi
    else:
        return SimulationResult(
            loai_hoc_phan=loai_str,
            muc_tieu=req.muc_tieu.value,
            diem_muc_tieu_nguong=threshold,
            diem_can_dat=None,
            is_kha_thi=False,
            message="Vui lòng cung cấp số tín chỉ (so_tin_chi) hoặc tổng số buổi (tong_so_buoi)",
            chi_tiet={},
        )

    remaining = total - len(existing)

    # Đã hoàn thành tất cả các buổi
    if remaining <= 0:
        avg = round(sum(existing) / len(existing), 1) if existing else 0.0
        if avg < 3.0:
            return SimulationResult(
                loai_hoc_phan=loai_str,
                muc_tieu=req.muc_tieu.value,
                diem_muc_tieu_nguong=threshold,
                diem_can_dat=None,
                is_kha_thi=False,
                message="CANH BAO: LIET THUC HANH (ROT MON)",
                chi_tiet={"diem_trung_binh": avg, "tong_so_buoi": total, "diem_hien_tai": existing},
            )
        
        passed = avg >= threshold
        grade = next((m["diem_chu"] for m in SCORE_MAPPING if m["diem_10_min"] <= avg <= m["diem_10_max"]), "F")
        return SimulationResult(
            loai_hoc_phan=loai_str,
            muc_tieu=req.muc_tieu.value,
            diem_muc_tieu_nguong=threshold,
            diem_can_dat=None,
            is_kha_thi=passed,
            message=f"Tất cả buổi TH đã hoàn thành. ĐTB = {avg} → {grade}",
            chi_tiet={"diem_trung_binh": avg, "tong_so_buoi": total, "diem_hien_tai": existing},
        )

    # Chưa hoàn thành: Kiểm tra xem có bị liệt thực hành bắt buộc (< 3.0) bất kể đạt điểm tối đa
    max_possible_avg = (sum(existing) + remaining * 10.0) / total
    if max_possible_avg < 3.0:
        return SimulationResult(
            loai_hoc_phan=loai_str,
            muc_tieu=req.muc_tieu.value,
            diem_muc_tieu_nguong=threshold,
            diem_can_dat=None,
            is_kha_thi=False,
            message="CANH BAO: LIET THUC HANH (ROT MON)",
            chi_tiet={"diem_trung_binh_hien_tai": round(sum(existing) / len(existing), 2) if existing else 0.0, "tong_so_buoi": total, "diem_hien_tai": existing},
        )

    score_raw = (threshold * total - sum(existing)) / remaining
    score_needed = _ceil_1dec(score_raw)

    chi_tiet = {
        "cong_thuc": "T = trung bình cộng tất cả điểm TH",
        "tong_so_buoi": total,
        "so_buoi_hien_tai": len(existing),
        "so_buoi_con_lai": remaining,
        "diem_hien_tai": existing,
        "diem_can_dat_chinh_xac": round(score_raw, 4),
    }

    if score_needed > 10.0:
        return _build_infeasible(loai_str, req.muc_tieu.value, threshold, score_raw, chi_tiet)

    if score_needed <= 0.0:
        return _build_guaranteed(loai_str, req.muc_tieu.value, threshold, chi_tiet)

    return SimulationResult(
        loai_hoc_phan=loai_str,
        muc_tieu=req.muc_tieu.value,
        diem_muc_tieu_nguong=threshold,
        diem_can_dat=score_needed,
        is_kha_thi=True,
        message=(
            f"Bạn cần đạt trung bình tối thiểu {score_needed} điểm "
            f"cho {remaining} buổi thực hành còn lại để đạt loại {req.muc_tieu.value}"
        ),
        chi_tiet=chi_tiet,
    )


# ─── Tích hợp ────────────────────────────────────────────────

def _simulate_tich_hop(req: SimulationRequest, threshold: float) -> SimulationResult:
    """
    T = (T_LT × chi_lt + T_TH × chi_th) / tổng_chi
    → T_LT_min = (threshold × tổng_chi - T_TH × chi_th) / chi_lt

    Nếu có TK_lt + GK_lt: tiếp tục tính sâu → CK_lt cần đạt
    """
    loai_str = "Tích hợp"
    chi_lt = req.so_chi_lt
    chi_th = req.so_chi_th
    t_th = req.diem_thuc_hanh_tich_hop

    if chi_lt is None or chi_th is None or t_th is None:
        return SimulationResult(
            loai_hoc_phan=loai_str,
            muc_tieu=req.muc_tieu.value,
            diem_muc_tieu_nguong=threshold,
            diem_can_dat=None,
            is_kha_thi=False,
            message=(
                "Vui lòng cung cấp: so_chi_lt, so_chi_th và diem_thuc_hanh_tich_hop"
            ),
            chi_tiet={},
        )

    # Kiểm tra trước: Nếu ĐTB_TH < 3.0 -> luôn trả về F và khóa phép toán (cảnh báo LIET THUC HANH)
    if t_th < 3.0:
        return SimulationResult(
            loai_hoc_phan=loai_str,
            muc_tieu=req.muc_tieu.value,
            diem_muc_tieu_nguong=threshold,
            diem_can_dat=None,
            is_kha_thi=False,
            message="CANH BAO: LIET THUC HANH (ROT MON)",
            chi_tiet={},
        )

    tong_chi = chi_lt + chi_th
    t_lt_raw = (threshold * tong_chi - t_th * chi_th) / chi_lt
    t_lt_needed = _ceil_1dec(t_lt_raw)

    chi_tiet_base: dict = {
        "cong_thuc": f"T = (T_LT×{chi_lt} + T_TH×{chi_th}) / {tong_chi}",
        "so_chi_lt": chi_lt,
        "so_chi_th": chi_th,
        "diem_thuc_hanh": t_th,
        "t_lt_can_dat_chinh_xac": round(t_lt_raw, 4),
    }

    if t_lt_needed > 10.0:
        return _build_infeasible(loai_str, req.muc_tieu.value, threshold, t_lt_raw, chi_tiet_base)

    base_message = (
        f"Điểm tổng kết nhánh lý thuyết phải đạt từ {t_lt_needed} trở lên "
        f"để đạt loại {req.muc_tieu.value}"
    )

    # ── Drill-down: tính CK của nhánh LT nếu có các điểm thành phần LT ──
    has_lt_list = req.diem_thuong_ky_lt_list is not None
    has_lt_legacy = req.diem_thuong_ky_lt is not None
    has_gk_lt = req.diem_giua_ky_lt is not None

    if (has_lt_list or has_lt_legacy) and has_gk_lt:
        gk_lt = req.diem_giua_ky_lt
        
        # Tính toán ĐTB thường kỳ lý thuyết (ĐTB_TK_LT) theo số tín chỉ lý thuyết
        if has_lt_list:
            if len(req.diem_thuong_ky_lt_list) != chi_lt:
                return SimulationResult(
                    loai_hoc_phan=loai_str,
                    muc_tieu=req.muc_tieu.value,
                    diem_muc_tieu_nguong=threshold,
                    diem_can_dat=None,
                    is_kha_thi=False,
                    message=f"Số lượng đầu điểm thường kỳ lý thuyết phải bằng đúng số tín chỉ lý thuyết ({chi_lt})",
                    chi_tiet={},
                )
            dtb_tk_lt = sum(req.diem_thuong_ky_lt_list) / chi_lt
        else:
            dtb_tk_lt = req.diem_thuong_ky_lt

        base_lt = 0.2 * dtb_tk_lt + 0.3 * gk_lt
        ck_lt_raw = (t_lt_needed - base_lt) / 0.5
        ck_lt_needed = _ceil_1dec(ck_lt_raw)

        chi_tiet_base.update({
            "diem_thuong_ky_lt_trung_binh": round(dtb_tk_lt, 2),
            "diem_giua_ky_lt": gk_lt,
            "ck_lt_can_dat_chinh_xac": round(ck_lt_raw, 4),
            "t_lt_can_dat": t_lt_needed,
        })
        if has_lt_list:
            chi_tiet_base["diem_thuong_ky_lt_list"] = req.diem_thuong_ky_lt_list

        if ck_lt_needed > 10.0:
            return _build_infeasible(loai_str, req.muc_tieu.value, threshold, ck_lt_raw, chi_tiet_base)

        if ck_lt_needed <= 0.0:
            return SimulationResult(
                loai_hoc_phan=loai_str,
                muc_tieu=req.muc_tieu.value,
                diem_muc_tieu_nguong=threshold,
                diem_can_dat=0.0,
                is_kha_thi=True,
                message=base_message + ". Bạn đã chắc chắn đạt mục tiêu mà không cần điểm thi cuối kỳ lý thuyết!",
                chi_tiet=chi_tiet_base,
            )

        return SimulationResult(
            loai_hoc_phan=loai_str,
            muc_tieu=req.muc_tieu.value,
            diem_muc_tieu_nguong=threshold,
            diem_can_dat=ck_lt_needed,
            is_kha_thi=True,
            message=base_message + f". Điểm cuối kỳ lý thuyết cần đạt tối thiểu {ck_lt_needed}",
            chi_tiet=chi_tiet_base,
        )

    # Trả về T_LT cần đạt (không drill-down CK)
    return SimulationResult(
        loai_hoc_phan=loai_str,
        muc_tieu=req.muc_tieu.value,
        diem_muc_tieu_nguong=threshold,
        diem_can_dat=t_lt_needed,
        is_kha_thi=True,
        message=base_message,
        chi_tiet=chi_tiet_base,
    )
