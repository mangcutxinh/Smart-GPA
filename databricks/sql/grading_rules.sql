-- SmartGPA grading rules for Databricks SQL
-- diem_cuoi_ky is the final exam score to be predicted/simulated.

CREATE DATABASE IF NOT EXISTS smartgpa_db;
USE smartgpa_db;

-- Main formulas:
--
-- Theory process contribution:
--   lt_qt_contribution_5 = 0.1 * thuong_xuyen_1
--                        + 0.1 * thuong_xuyen_2
--                        + 0.3 * giua_ky
--
-- Theory process score normalized to 10:
--   lt_qt_10 = lt_qt_contribution_5 / 0.5
--            = 0.2 * thuong_xuyen_1
--            + 0.2 * thuong_xuyen_2
--            + 0.6 * giua_ky
--
-- Practice process score:
--   th_qt_10 = (thuc_hanh_1 + thuc_hanh_2 + thuc_hanh_3) / 3
--
-- Overall process score:
--   theory-only:   qt_10 = lt_qt_10
--   practice-only: qt_10 = th_qt_10
--   integrated:    qt_10 = (lt_qt_10 * so_chi_lt + th_qt_10 * so_chi_th) / tong_so_chi
--
-- Final total:
--   tong_ket_10 = 0.5 * qt_10 + 0.5 * diem_cuoi_ky
--
-- Since diem_cuoi_ky is unknown:
--   diem_cuoi_ky_can_dat = (diem_muc_tieu_10 - 0.5 * qt_10) / 0.5

CREATE OR REPLACE TEMP VIEW diem_muc_tieu AS
SELECT 'A+' AS diem_chu_muc_tieu, 9.0 AS diem_muc_tieu_10 UNION ALL
SELECT 'A', 8.5 UNION ALL
SELECT 'B+', 8.0 UNION ALL
SELECT 'B', 7.0 UNION ALL
SELECT 'C+', 6.0 UNION ALL
SELECT 'C', 5.5 UNION ALL
SELECT 'D+', 5.0 UNION ALL
SELECT 'D', 4.0;

