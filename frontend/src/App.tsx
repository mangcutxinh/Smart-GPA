import React, { useState, useEffect, useCallback } from "react";

// Types matching backend models
type HocPhanType = "ly_thuyet" | "thuc_hanh" | "tich_hop";
type DiemChuTarget = "A+" | "A" | "B+" | "B" | "C+" | "C" | "D+" | "D";

interface SubjectConfig {
  id: string;
  name: string;
  type: HocPhanType;
  credits: number;
  chiLT?: number;
  chiTH?: number;
}

const SUBJECTS: SubjectConfig[] = [
  { id: "mon_1", name: "Cấu trúc dữ liệu & Giải thuật", type: "ly_thuyet", credits: 3 },
  { id: "mon_2", name: "Mạng máy tính", type: "ly_thuyet", credits: 2 },
  { id: "mon_3", name: "Thực hành Hệ điều hành", type: "thuc_hanh", credits: 2 },
  { id: "mon_4", name: "Thực hành Lập trình hướng đối tượng", type: "thuc_hanh", credits: 3 },
  { id: "mon_5", name: "Cơ sở dữ liệu nâng cao (Tích hợp)", type: "tich_hop", credits: 3, chiLT: 2, chiTH: 1 },
  { id: "mon_6", name: "Điện toán đám mây (Tích hợp)", type: "tich_hop", credits: 4, chiLT: 2, chiTH: 2 },
];

const TARGETS: DiemChuTarget[] = ["D", "D+", "C", "C+", "B", "B+", "A", "A+"];

interface ScoreMappingItem {
  diem_chu: string;
  diem_10_min: number;
  diem_10_max: number;
  diem_he_4: number;
  loai_danh_gia: string;
}

const FALLBACK_SCORE_MAPPING: ScoreMappingItem[] = [
  { diem_chu: "A+", diem_10_min: 9.0, diem_10_max: 10.0, diem_he_4: 4.0, loai_danh_gia: "Đạt" },
  { diem_chu: "A",  diem_10_min: 8.5, diem_10_max: 8.9,  diem_he_4: 4.0, loai_danh_gia: "Đạt" },
  { diem_chu: "B+", diem_10_min: 8.0, diem_10_max: 8.4,  diem_he_4: 3.5, loai_danh_gia: "Đạt" },
  { diem_chu: "B",  diem_10_min: 7.0, diem_10_max: 7.9,  diem_he_4: 3.0, loai_danh_gia: "Đạt" },
  { diem_chu: "C+", diem_10_min: 6.0, diem_10_max: 6.9,  diem_he_4: 2.5, loai_danh_gia: "Đạt" }, // New rule C+
  { diem_chu: "C",  diem_10_min: 5.5, diem_10_max: 5.9,  diem_he_4: 2.0, loai_danh_gia: "Đạt" }, // New rule C
  { diem_chu: "D+", diem_10_min: 5.0, diem_10_max: 5.4,  diem_he_4: 1.5, loai_danh_gia: "Đạt" },
  { diem_chu: "D",  diem_10_min: 4.0, diem_10_max: 4.9,  diem_he_4: 1.0, loai_danh_gia: "Đạt" },
  { diem_chu: "F",  diem_10_min: 0.0, diem_10_max: 3.9,  diem_he_4: 0.0, loai_danh_gia: "Không Đạt" },
];

export default function App() {
  interface User {
    email: string;
    role: "student" | "lecturer" | "advisor" | "admin";
    full_name: string;
  }
  const [user, setUser] = useState<User | null>(null);

  // Login input states
  const [loginEmail, setLoginEmail] = useState<string>("");
  const [loginPassword, setLoginPassword] = useState<string>("");
  const [loginError, setLoginError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [showPassword, setShowPassword] = useState<boolean>(false);

  // Landing Page & Modal Navigation
  const [isAuthModalOpen, setIsAuthModalOpen] = useState<boolean>(false);
  const [isScrolled, setIsScrolled] = useState<boolean>(false);

  // Navigation & Role switcher
  const [activeRole, setActiveRole] = useState<"student" | "lecturer" | "advisor" | "admin">("student");
  
  // API Authentication Token (Mocked or real)
  const [token, setToken] = useState<string | null>(null);
  const [isBackendOnline, setIsBackendOnline] = useState<boolean>(false);
  const [scoreMapping, setScoreMapping] = useState<ScoreMappingItem[]>(FALLBACK_SCORE_MAPPING);

  // ─── Student State ──────────────────────────────────────────
  const [selectedSubject, setSelectedSubject] = useState<SubjectConfig>(SUBJECTS[0]);
  const [targetGrade, setTargetGrade] = useState<DiemChuTarget>("A");
  
  // Inputs for Theory
  const [tkScores, setTkScores] = useState<number[]>([8.0, 8.0, 8.0]);
  const [gkScore, setGkScore] = useState<number>(8.0);
  
  // Inputs for Practical
  const [thScores, setThScores] = useState<number[]>([8.0, 8.0]);
  const [completedSessions, setCompletedSessions] = useState<number>(2);

  // Inputs for Integrated
  const [thTichHop, setThTichHop] = useState<number>(8.0);
  const [drillDownLT, setDrillDownLT] = useState<boolean>(false);
  const [tkScoresLT, setTkScoresLT] = useState<number[]>([8.0, 8.0]);
  const [gkScoreLT, setGkScoreLT] = useState<number>(8.0);

  // Result state
  const [isKhaThi, setIsKhaThi] = useState<boolean>(true);
  const [diemCanDat, setDiemCanDat] = useState<number | null>(8.4);
  const [diemMucTieuNguong, setDiemMucTieuNguong] = useState<number>(8.5);
  const [resultMessage, setResultMessage] = useState<string>("Bạn cần đạt tối thiểu 8.4 điểm cuối kỳ để đạt mục tiêu A (≥8.5 điểm)");
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [resultDetails, setResultDetails] = useState<any>({});

  // ─── Lecturer State ─────────────────────────────────────────
  const [lecturerMon, setLecturerMon] = useState<string>(SUBJECTS[0].id);
  const [lecturerFile, setLecturerFile] = useState<string>("");
  const [lecturerSuccessMsg, setLecturerSuccessMsg] = useState<string | null>(null);

  // ─── Initial Connection Check ──────────────────────────────
  useEffect(() => {
    async function initConnection() {
      try {
        // Ping score map to check if backend is online (even if it returns 401, it means the server is reachable)
        const resp = await fetch("http://localhost:8000/simulation/score-map");
        if (resp.ok || resp.status === 401) {
          setIsBackendOnline(true);
        }
      } catch {
        setIsBackendOnline(false);
      }
    }
    initConnection();
  }, []);

  // ─── Navbar Scroll Effect ──────────────────────────────────
  useEffect(() => {
    const handleScroll = () => {
      if (window.scrollY > 80) {
        setIsScrolled(true);
      } else {
        setIsScrolled(false);
      }
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  // ─── Login handler ──────────────────────────────────────────
  const handleLogin = async (emailInput: string, passwordInput: string) => {
    setIsLoading(true);
    setLoginError(null);
    try {
      // Step 1: Login using credentials to get real token
      const loginResp = await fetch("http://localhost:8000/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: emailInput, password: passwordInput }),
      });
      
      if (loginResp.ok) {
        const authData = await loginResp.json();
        setToken(authData.access_token);
        setIsBackendOnline(true);

        // Step 2: Fetch actual profile from backend
        const userResp = await fetch("http://localhost:8000/auth/me", {
          headers: { "Authorization": `Bearer ${authData.access_token}` },
        });
        if (userResp.ok) {
          const userData = await userResp.json();
          setUser({
            email: userData.email,
            role: userData.role,
            full_name: userData.full_name,
          });
          setActiveRole(userData.role);

          // Step 3: Fetch actual score mapping from backend
          const mappingResp = await fetch("http://localhost:8000/simulation/score-map", {
            headers: { "Authorization": `Bearer ${authData.access_token}` },
          });
          if (mappingResp.ok) {
            const mapData = await mappingResp.json();
            setScoreMapping(mapData);
          }
          setIsLoading(false);
          setIsAuthModalOpen(false);
          return;
        }
      }
    } catch {
      // Catch empty block
    }

    // Fallback local verification for demo accounts if backend is unreachable or returns error
    const demoUsers: Record<string, { role: "student" | "lecturer" | "advisor" | "admin", name: string }> = {
      "student@smartgpa.edu": { role: "student", name: "Nguyễn Văn An" },
      "lecturer@smartgpa.edu": { role: "lecturer", name: "TS. Trần Minh Bình" },
      "advisor@smartgpa.edu": { role: "advisor", name: "ThS. Lê Thị Chi" },
      "admin@smartgpa.edu": { role: "admin", name: "Hệ Thống Admin" }
    };

    const normalizedEmail = emailInput.trim().toLowerCase();
    if (demoUsers[normalizedEmail] && passwordInput === "password123") {
      const matched = demoUsers[normalizedEmail];
      setToken("local-mock-token");
      setIsBackendOnline(false);
      setUser({
        email: normalizedEmail,
        role: matched.role,
        full_name: matched.name,
      });
      setActiveRole(matched.role);
      setScoreMapping(FALLBACK_SCORE_MAPPING);
      setIsLoading(false);
      setIsAuthModalOpen(false);
    } else {
      setIsLoading(false);
      setLoginError("Sai email hoặc mật khẩu. Vui lòng kiểm tra lại thông tin đăng nhập.");
    }
  };

  const onSubmitLogin = (e: React.FormEvent) => {
    e.preventDefault();
    handleLogin(loginEmail, loginPassword);
  };

  const handleQuickLogin = (emailInput: string, passwordInput: string) => {
    setLoginEmail(emailInput);
    setLoginPassword(passwordInput);
    handleLogin(emailInput, passwordInput);
  };

  const handleLogout = () => {
    setUser(null);
    setToken(null);
    setLoginEmail("");
    setLoginPassword("");
    setLoginError(null);
    setIsAuthModalOpen(false);
  };

  // ─── Math Calculation Fallback (Pure TSX Client Side) ──────
  const runLocalSimulation = useCallback(() => {
    const targetMin = FALLBACK_SCORE_MAPPING.find(m => m.diem_chu === targetGrade)?.diem_10_min ?? 8.5;
    setDiemMucTieuNguong(targetMin);

    if (selectedSubject.type === "ly_thuyet") {
      const activeTkList = tkScores.slice(0, selectedSubject.credits);
      const dtb_tk = activeTkList.reduce((a, b) => a + b, 0) / selectedSubject.credits;
      const gk = gkScore;
      
      const base = 0.2 * dtb_tk + 0.3 * gk;
      const ck_raw = (targetMin - base) / 0.5;
      const ck_needed = Math.max(0.0, Math.ceil(ck_raw * 10) / 10);

      const details = {
        cong_thuc: "T = 0.2×TK + 0.3×GK + 0.5×CK",
        diem_thuong_ky_trung_binh: Number(dtb_tk.toFixed(2)),
        diem_giua_ky: gk,
        diem_hien_tai_khong_ck: Number(base.toFixed(2)),
        ck_can_dat_chinh_xac: Number(ck_raw.toFixed(4)),
        diem_thuong_ky_list: activeTkList,
        so_tin_chi: selectedSubject.credits
      };

      setResultDetails(details);

      if (ck_needed > 10.0) {
        setIsKhaThi(false);
        setDiemCanDat(null);
        setResultMessage(`Mục tiêu Bất khả thi! Điểm cần đạt (${ck_raw.toFixed(2)}) vượt quá thang điểm tối đa (10.0).`);
      } else if (ck_needed === 0.0) {
        setIsKhaThi(true);
        setDiemCanDat(0.0);
        setResultMessage(`Bạn đã chắc chắn đạt mục tiêu ${targetGrade} mà không cần thêm điểm!`);
      } else {
        setIsKhaThi(true);
        setDiemCanDat(ck_needed);
        setResultMessage(`Bạn cần đạt tối thiểu ${ck_needed} điểm cuối kỳ để đạt loại ${targetGrade} (≥${targetMin} điểm)`);
      }
    } 
    
    else if (selectedSubject.type === "thuc_hanh") {
      const total = selectedSubject.credits;
      const activeThList = thScores.slice(0, completedSessions);
      const remaining = total - completedSessions;

      if (remaining <= 0) {
        const avg = activeThList.length ? activeThList.reduce((a, b) => a + b, 0) / activeThList.length : 0.0;
        const roundedAvg = Number(avg.toFixed(1));
        
        if (roundedAvg < 3.0) {
          setIsKhaThi(false);
          setDiemCanDat(null);
          setResultMessage("CANH BAO: LIET THUC HANH (ROT MON)");
          setResultDetails({ diem_trung_binh: roundedAvg, tong_so_buoi: total, diem_hien_tai: activeThList });
          return;
        }

        const passed = roundedAvg >= targetMin;
        const grade = FALLBACK_SCORE_MAPPING.find(m => roundedAvg >= m.diem_10_min && roundedAvg <= m.diem_10_max)?.diem_chu ?? "F";
        
        setIsKhaThi(passed);
        setDiemCanDat(null);
        setResultMessage(passed 
          ? `Tất cả buổi TH đã hoàn thành. ĐTB = ${roundedAvg} → ${grade} (Đạt mục tiêu ${targetGrade})`
          : `Tất cả buổi TH đã hoàn thành. ĐTB = ${roundedAvg} → ${grade} (Không đạt mục tiêu ${targetGrade})`
        );
        setResultDetails({ diem_trung_binh: roundedAvg, tong_so_buoi: total, diem_hien_tai: activeThList });
      } else {
        const currentSum = activeThList.reduce((a, b) => a + b, 0);
        const maxPossible = (currentSum + remaining * 10.0) / total;
        
        if (maxPossible < 3.0) {
          setIsKhaThi(false);
          setDiemCanDat(null);
          setResultMessage("CANH BAO: LIET THUC HANH (ROT MON)");
          setResultDetails({ diem_trung_binh_hien_tai: Number((currentSum / (activeThList.length || 1)).toFixed(2)), tong_so_buoi: total, diem_hien_tai: activeThList });
          return;
        }

        const score_raw = (targetMin * total - currentSum) / remaining;
        const score_needed = Math.max(0.0, Math.ceil(score_raw * 10) / 10);

        const details = {
          cong_thuc: "T = trung bình cộng tất cả điểm TH",
          tong_so_buoi: total,
          so_buoi_hien_tai: activeThList.length,
          so_buoi_con_lai: remaining,
          diem_hien_tai: activeThList,
          diem_can_dat_chinh_xac: Number(score_raw.toFixed(4)),
        };
        setResultDetails(details);

        if (score_needed > 10.0) {
          setIsKhaThi(false);
          setDiemCanDat(null);
          setResultMessage(`Mục tiêu Bất khả thi! Điểm cần đạt (${score_raw.toFixed(2)}) vượt quá thang điểm tối đa (10.0).`);
        } else if (score_needed === 0.0) {
          setIsKhaThi(true);
          setDiemCanDat(0.0);
          setResultMessage(`Bạn đã chắc chắn đạt mục tiêu ${targetGrade} mà không cần thêm điểm!`);
        } else {
          setIsKhaThi(true);
          setDiemCanDat(score_needed);
          setResultMessage(`Bạn cần đạt trung bình tối thiểu ${score_needed} điểm cho ${remaining} buổi thực hành còn lại để đạt loại ${targetGrade}`);
        }
      }
    } 
    
    else { // Integrated course
      const chi_lt = selectedSubject.chiLT ?? 2;
      const chi_th = selectedSubject.chiTH ?? 1;
      const t_th = thTichHop;

      if (t_th < 3.0) {
        setIsKhaThi(false);
        setDiemCanDat(null);
        setResultMessage("CANH BAO: LIET THUC HANH (ROT MON)");
        setResultDetails({});
        return;
      }

      const tong_chi = chi_lt + chi_th;
      const t_lt_raw = (targetMin * tong_chi - t_th * chi_th) / chi_lt;
      const t_lt_needed = Math.max(0.0, Math.ceil(t_lt_raw * 10) / 10);

      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const details: any = {
        cong_thuc: `T = (T_LT×${chi_lt} + T_TH×${chi_th}) / ${tong_chi}`,
        so_chi_lt: chi_lt,
        so_chi_th: chi_th,
        diem_thuc_hanh: t_th,
        t_lt_can_dat_chinh_xac: Number(t_lt_raw.toFixed(4)),
      };

      if (t_lt_needed > 10.0) {
        setIsKhaThi(false);
        setDiemCanDat(null);
        setResultMessage(`Mục tiêu Bất khả thi! Điểm tổng kết nhánh lý thuyết cần đạt (${t_lt_raw.toFixed(2)}) vượt quá 10.0.`);
        setResultDetails(details);
        return;
      }

      const base_message = `Điểm tổng kết nhánh lý thuyết phải đạt từ ${t_lt_needed} trở lên để đạt loại ${targetGrade}`;

      if (drillDownLT) {
        const activeTkLtList = tkScoresLT.slice(0, chi_lt);
        const dtb_tk_lt = activeTkLtList.reduce((a, b) => a + b, 0) / chi_lt;
        const gk_lt = gkScoreLT;
        
        const base_lt = 0.2 * dtb_tk_lt + 0.3 * gk_lt;
        const ck_lt_raw = (t_lt_needed - base_lt) / 0.5;
        const ck_lt_needed = Math.max(0.0, Math.ceil(ck_lt_raw * 10) / 10);

        details.diem_thuong_ky_lt_trung_binh = Number(dtb_tk_lt.toFixed(2));
        details.diem_giua_ky_lt = gk_lt;
        details.ck_lt_can_dat_chinh_xac = Number(ck_lt_raw.toFixed(4));
        details.t_lt_can_dat = t_lt_needed;
        details.diem_thuong_ky_lt_list = activeTkLtList;

        setResultDetails(details);

        if (ck_lt_needed > 10.0) {
          setIsKhaThi(false);
          setDiemCanDat(null);
          setResultMessage(`${base_message}. Tuy nhiên mục tiêu lý thuyết này Bất khả thi vì cần thi cuối kỳ lý thuyết đạt ${ck_lt_raw.toFixed(2)}.`);
        } else if (ck_lt_needed === 0.0) {
          setIsKhaThi(true);
          setDiemCanDat(0.0);
          setResultMessage(`${base_message}. Bạn đã chắc chắn đạt mục tiêu mà không cần điểm thi cuối kỳ lý thuyết!`);
        } else {
          setIsKhaThi(true);
          setDiemCanDat(ck_lt_needed);
          setResultMessage(`${base_message}. Điểm cuối kỳ lý thuyết cần đạt tối thiểu ${ck_lt_needed}`);
        }
      } else {
        setIsKhaThi(true);
        setDiemCanDat(t_lt_needed);
        setResultMessage(base_message);
        setResultDetails(details);
      }
    }
  }, [selectedSubject, targetGrade, tkScores, gkScore, thScores, completedSessions, thTichHop, drillDownLT, tkScoresLT, gkScoreLT]);

  // ─── Trigger Simulation (API + Fallback) ───────────────────
  useEffect(() => {
    async function getSimulation() {
      // Build request body
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const payload: any = {
        loai_hoc_phan: selectedSubject.type,
        muc_tieu: targetGrade,
      };

      if (selectedSubject.type === "ly_thuyet") {
        payload.so_tin_chi = selectedSubject.credits;
        payload.diem_thuong_ky_list = tkScores.slice(0, selectedSubject.credits);
        payload.diem_giua_ky = gkScore;
      } else if (selectedSubject.type === "thuc_hanh") {
        payload.so_tin_chi = selectedSubject.credits;
        payload.diem_thuc_hanh_hien_tai = thScores.slice(0, completedSessions);
      } else { // tich_hop
        payload.so_chi_lt = selectedSubject.chiLT;
        payload.so_chi_th = selectedSubject.chiTH;
        payload.diem_thuc_hanh_tich_hop = thTichHop;
        if (drillDownLT) {
          payload.diem_thuong_ky_lt_list = tkScoresLT.slice(0, selectedSubject.chiLT);
          payload.diem_giua_ky_lt = gkScoreLT;
        }
      }

      if (isBackendOnline && token) {
        try {
          const resp = await fetch("http://localhost:8000/simulation/simulate", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "Authorization": `Bearer ${token}`,
            },
            body: JSON.stringify(payload),
          });
          
          if (resp.ok) {
            const data = await resp.json();
            setIsKhaThi(data.is_kha_thi);
            setDiemCanDat(data.diem_can_dat);
            setDiemMucTieuNguong(data.diem_muc_tieu_nguong);
            setResultMessage(data.message);
            setResultDetails(data.chi_tiet);
            return;
          }
        } catch {
          // If fetch fails mid-way, trigger fallback
        }
      }
      
      // Fallback
      runLocalSimulation();
    }
    getSimulation();
  }, [selectedSubject, targetGrade, tkScores, gkScore, thScores, completedSessions, thTichHop, drillDownLT, tkScoresLT, gkScoreLT, isBackendOnline, token, runLocalSimulation]);

  // Adjust scores lists when subjects change
  useEffect(() => {
    if (selectedSubject.type === "ly_thuyet") {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setTkScores(Array(selectedSubject.credits).fill(8.0));
    } else if (selectedSubject.type === "thuc_hanh") {
      setThScores(Array(selectedSubject.credits).fill(8.0));
      setCompletedSessions(Math.max(1, selectedSubject.credits - 1));
    } else { // tich_hop
      setTkScoresLT(Array(selectedSubject.chiLT).fill(8.0));
    }
  }, [selectedSubject]);

  if (!user) {
    return (
      <div style={{ position: "relative", minHeight: "100vh", background: "var(--bg-primary)", color: "var(--text-primary)", overflowX: "hidden" }}>
        {/* Floating Ambient Blobs */}
        <div className="blob blob-1"></div>
        <div className="blob blob-2"></div>
        <div className="blob blob-3"></div>

        {/* ─── Floating Navbar (MedBook inspired) ─── */}
        <nav className={`navbar ${isScrolled ? "scrolled" : ""}`}>
          <div className="nav-container">
            <div className="logo" onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}>
              <i className="pi pi-graduation-cap"></i>
              <span>Smart<span style={{ color: "var(--color-primary)" }}>GPA</span></span>
            </div>

            <div className="nav-links">
              <a href="#features">Tính năng</a>
              <a href="#roles">Các vai trò</a>
              <a href="#how-it-works">Cách hoạt động</a>
              <a href="#contact">Liên hệ</a>
            </div>

            <div className="auth-buttons">
              <button className="btn btn-ghost" onClick={() => setIsAuthModalOpen(true)}>Đăng nhập</button>
              <button className="btn btn-primary btn-sm" onClick={() => setIsAuthModalOpen(true)}>
                <i className="pi pi-bolt"></i> Bắt đầu ngay
              </button>
            </div>
          </div>
        </nav>

        {/* ─── HERO SECTION ─── */}
        <header className="hero">
          <div className="container hero-perspective">
            <div className="hero-card-3d animate-fade-in">
              {/* Floating Academic Icons */}
              <i className="pi pi-chart-line floating" style={{ position: "absolute", top: "40px", right: "60px", fontSize: "2.5rem", color: "var(--color-primary)", opacity: 0.15 }}></i>
              <i className="pi pi-percentage floating-delayed" style={{ position: "absolute", bottom: "50px", right: "80px", fontSize: "2rem", color: "var(--color-secondary)", opacity: 0.12 }}></i>
              <i className="pi pi-verified floating-slow" style={{ position: "absolute", top: "50%", left: "40px", fontSize: "2.2rem", color: "var(--color-success)", opacity: 0.1 }}></i>

              {/* Badge */}
              <div className="mb-6">
                <span className="badge badge-info" style={{ padding: "8px 20px" }}>
                  <i className="pi pi-sparkles"></i> EDUCATION 4.0
                </span>
              </div>

              {/* Title */}
              <h1 className="hero-title">
                Trải nghiệm<br />
                <span className="gradient-text">Giả lập điểm ngược</span><br />
                chưa bao giờ mượt mà đến thế.
              </h1>

              {/* Subtitle */}
              <p className="hero-subtitle">
                Hệ thống Phân tích Học thuật & Giả lập Điểm ngược (SOA - Databricks) thông minh, bảo mật và hiện đại. 
                Tối ưu hóa lộ trình học tập của bạn chỉ trong vài giây.
              </p>

              {/* CTA Buttons */}
              <div style={{ display: "flex", gap: "16px", justifyContent: "center", flexWrap: "wrap" }}>
                <button className="btn btn-primary" onClick={() => setIsAuthModalOpen(true)}>
                  <i className="pi pi-play"></i> Bắt đầu ngay
                </button>
                <button className="btn btn-outline" onClick={() => {
                  const target = document.getElementById("features");
                  if (target) target.scrollIntoView({ behavior: "smooth" });
                }}>
                  <i className="pi pi-arrow-down"></i> Khám phá
                </button>
              </div>
            </div>
          </div>
        </header>

        {/* ─── FEATURES SECTION ─── */}
        <section id="features" className="section container">
          <div className="text-center mb-12">
            <span className="badge badge-info mb-4 uppercase tracking-wider">Tại sao chọn SmartGPA?</span>
            <h2 style={{ fontFamily: "var(--font-heading)", fontWeight: 800, fontSize: "36px", color: "var(--text-primary)" }}>
              Công nghệ <span className="gradient-text">vượt trội</span>
            </h2>
            <p className="text-gray text-lg mx-auto" style={{ maxWidth: "600px", marginTop: "12px" }}>
              Ba trụ cột cốt lõi mang đến quy trình tối ưu hóa học thuật toàn diện.
            </p>
          </div>

          <div className="grid grid-3">
            <div className="glass-card hover-float" style={{ padding: "32px", textAlign: "left" }}>
              <div className="icon-box"><i className="pi pi-server"></i></div>
              <h3 className="font-bold mb-4" style={{ fontSize: "18px" }}>Phân tích Medallion</h3>
              <p className="text-gray text-sm" style={{ lineHeight: 1.5 }}>
                Đồng bộ hóa dữ liệu điểm số qua ba tầng Delta Lake (Bronze, Silver, Gold). Spark ETL làm sạch và tự động làm tròn điểm số đến 0.1 chính xác.
              </p>
            </div>
            <div className="glass-card hover-float" style={{ padding: "32px", textAlign: "left" }}>
              <div className="icon-box"><i className="pi pi-sliders-h"></i></div>
              <h3 className="font-bold mb-4" style={{ fontSize: "18px" }}>Giả lập ngược 10 giây</h3>
              <p className="text-gray text-sm" style={{ lineHeight: 1.5 }}>
                Quy trình tối giản: Sinh viên chọn môn học → Đặt mục tiêu điểm chữ → Nhận ngay điểm thi cuối kỳ tối thiểu cần đạt chính xác theo trọng số.
              </p>
            </div>
            <div className="glass-card hover-float" style={{ padding: "32px", textAlign: "left" }}>
              <div className="icon-box"><i className="pi pi-shield"></i></div>
              <h3 className="font-bold mb-4" style={{ fontSize: "18px" }}>Dự báo MLflow RF</h3>
              <p className="text-gray text-sm" style={{ lineHeight: 1.5 }}>
                Học máy Random Forest được huấn luyện trên MLflow giúp dự báo sớm 82% nguy cơ rớt môn và lập tức khóa tính toán nếu dính điểm liệt thực hành.
              </p>
            </div>
          </div>
        </section>

        {/* ─── ROLES SECTION (Các vai trò) ─── */}
        <section id="roles" className="section container" style={{ borderTop: "1px solid var(--border-glass)", paddingTop: "100px" }}>
          <div className="text-center mb-12">
            <span className="badge badge-success mb-4 uppercase tracking-wider">Phân quyền thông minh</span>
            <h2 style={{ fontFamily: "var(--font-heading)", fontWeight: 800, fontSize: "36px", color: "var(--text-primary)" }}>
              Các vai trò trong <span className="gradient-text">SmartGPA</span>
            </h2>
            <p className="text-gray text-lg mx-auto" style={{ maxWidth: "600px", marginTop: "12px" }}>
              Hệ thống được thiết kế chuyên biệt và bảo mật cho từng phân cấp người dùng.
            </p>
          </div>

          <div className="grid grid-3">
            <div className="glass-card hover-float" style={{ padding: "28px", textAlign: "left", display: "flex", flexDirection: "column" }}>
              <div className="badge badge-success" style={{ alignSelf: "flex-start", marginBottom: "16px" }}>
                <i className="pi pi-user"></i> Sinh viên (Student)
              </div>
              <h3 className="font-bold mb-4" style={{ fontSize: "18px" }}>GPA Inverse Portal</h3>
              <p className="text-gray text-sm mb-6" style={{ flexGrow: 1, lineHeight: 1.5 }}>
                Giả lập điểm thi học phần lý thuyết, thực hành, tích hợp. Theo dõi trực quan tỷ lệ khả thi qua biểu đồ circular ring sinh động.
              </p>
              <button className="btn btn-outline btn-sm" onClick={() => setIsAuthModalOpen(true)}>Trải nghiệm</button>
            </div>
            <div className="glass-card hover-float" style={{ padding: "28px", textAlign: "left", display: "flex", flexDirection: "column" }}>
              <div className="badge badge-info" style={{ alignSelf: "flex-start", marginBottom: "16px" }}>
                <i className="pi pi-file-excel"></i> Giảng viên (Lecturer)
              </div>
              <h3 className="font-bold mb-4" style={{ fontSize: "18px" }}>Delta Lake Workspace</h3>
              <p className="text-gray text-sm mb-6" style={{ flexGrow: 1, lineHeight: 1.5 }}>
                Nạp tệp tin điểm thô (.csv/.xlsx) lớp học phần quản lý lên hồ Bronze. Tự động kích hoạt luồng Spark ETL và Medallion pipeline.
              </p>
              <button className="btn btn-outline btn-sm" onClick={() => setIsAuthModalOpen(true)}>Trải nghiệm</button>
            </div>
            <div className="glass-card hover-float" style={{ padding: "28px", textAlign: "left", display: "flex", flexDirection: "column" }}>
              <div className="badge badge-warning" style={{ alignSelf: "flex-start", marginBottom: "16px" }}>
                <i className="pi pi-users"></i> Cố vấn học vụ (Advisor)
              </div>
              <h3 className="font-bold mb-4" style={{ fontSize: "18px" }}>Academic Warning Monitor</h3>
              <p className="text-gray text-sm mb-6" style={{ flexGrow: 1, lineHeight: 1.5 }}>
                Theo dõi danh sách sinh viên dính cảnh báo học vụ từ Silver table. Tra cứu tỷ lệ rớt môn dự báo bằng mô hình máy học Random Forest.
              </p>
              <button className="btn btn-outline btn-sm" onClick={() => setIsAuthModalOpen(true)}>Trải nghiệm</button>
            </div>
            <div className="glass-card hover-float" style={{ padding: "28px", textAlign: "left", display: "flex", flexDirection: "column", gridColumn: "span 3" }}>
              <div className="badge badge-danger" style={{ alignSelf: "flex-start", marginBottom: "16px" }}>
                <i className="pi pi-cog"></i> Quản trị viên (Admin)
              </div>
              <h3 className="font-bold mb-4" style={{ fontSize: "18px" }}>System Configuration</h3>
              <p className="text-gray text-sm mb-6" style={{ flexGrow: 1, lineHeight: 1.5 }}>
                Cấu hình bảng quy đổi điểm chữ Score Mapping toàn hệ thống, theo dõi tình trạng mã hóa JWT và uvicorn server.
              </p>
              <button className="btn btn-outline btn-sm" style={{ width: "100%" }} onClick={() => setIsAuthModalOpen(true)}>Trải nghiệm</button>
            </div>
          </div>
        </section>

        {/* ─── HOW IT WORKS SECTION ─── */}
        <section id="how-it-works" className="section container" style={{ borderTop: "1px solid var(--border-glass)", paddingTop: "100px" }}>
          <div className="text-center mb-12">
            <span className="badge badge-warning mb-4 uppercase tracking-wider">Hướng dẫn sử dụng</span>
            <h2 style={{ fontFamily: "var(--font-heading)", fontWeight: 800, fontSize: "36px", color: "var(--text-primary)" }}>
              Bắt đầu trong <span className="gradient-text">3 bước</span>
            </h2>
          </div>

          <div className="grid grid-3">
            <div className="glass-card text-center hover-float" style={{ padding: "32px" }}>
              <div style={{ fontSize: "32px", fontWeight: 900, color: "var(--color-primary)", opacity: 0.6, marginBottom: "16px", fontFamily: "var(--font-heading)" }}>01</div>
              <h3 className="font-bold mb-2" style={{ fontSize: "17px" }}>Đăng nhập tài khoản</h3>
              <p className="text-gray text-sm" style={{ lineHeight: 1.5 }}>Chọn vai trò phù hợp trong mục tài khoản thử nghiệm và đăng nhập an toàn.</p>
            </div>
            <div className="glass-card text-center hover-float" style={{ padding: "32px" }}>
              <div style={{ fontSize: "32px", fontWeight: 900, color: "var(--color-primary)", opacity: 0.6, marginBottom: "16px", fontFamily: "var(--font-heading)" }}>02</div>
              <h3 className="font-bold mb-2" style={{ fontSize: "17px" }}>Thiết lập mục tiêu</h3>
              <p className="text-gray text-sm" style={{ lineHeight: 1.5 }}>Chọn môn học giả lập lộ trình học tập và lựa chọn dải điểm chữ mong muốn đạt.</p>
            </div>
            <div className="glass-card text-center hover-float" style={{ padding: "32px" }}>
              <div style={{ fontSize: "32px", fontWeight: 900, color: "var(--color-primary)", opacity: 0.6, marginBottom: "16px", fontFamily: "var(--font-heading)" }}>03</div>
              <h3 className="font-bold mb-2" style={{ fontSize: "17px" }}>Nhận kết quả giả lập</h3>
              <p className="text-gray text-sm" style={{ lineHeight: 1.5 }}>Hệ thống tự động tính toán điểm số tối thiểu thi cuối kỳ cần nỗ lực.</p>
            </div>
          </div>
        </section>

        {/* ─── CTA BANNER ─── */}
        <section className="section container">
          <div className="glass-card text-center" style={{ padding: "80px 40px", border: "1px solid var(--border-glass-glow)" }}>
            <h2 style={{ fontFamily: "var(--font-heading)", fontWeight: 800, fontSize: "36px", color: "var(--text-primary)", marginBottom: "16px" }}>
              Sẵn sàng tối ưu hóa điểm số?
            </h2>
            <p className="text-gray text-lg mb-8 mx-auto" style={{ maxWidth: "500px", lineHeight: 1.6 }}>
              Hàng nghìn sinh viên đã sử dụng SmartGPA để định hướng và đạt mục tiêu. Đăng nhập và bắt đầu ngay.
            </p>
            <button className="btn btn-primary" onClick={() => setIsAuthModalOpen(true)} style={{ padding: "12px 40px", fontSize: "16px" }}>
              <i className="pi pi-user-plus"></i> Sử dụng tài khoản Demo
            </button>
          </div>
        </section>

        {/* ─── FOOTER SECTION ─── */}
        <footer id="contact" className="footer">
          <div className="container">
            <div className="grid grid-3" style={{ textAlign: "left" }}>
              <div>
                <div className="logo mb-4" style={{ cursor: "default" }}>
                  <i className="pi pi-graduation-cap" style={{ color: "var(--color-primary)" }}></i> SmartGPA
                </div>
                <p className="text-sm text-gray" style={{ lineHeight: 1.6 }}>
                  Hệ thống Phân tích Học thuật & Giả lập Điểm ngược thông minh. Áp dụng kỹ nghệ xử lý luồng Spark Medallion Pipeline hiện đại.
                </p>
              </div>
              <div>
                <h4 className="footer-link-title">Hạ tầng & Công nghệ</h4>
                <ul style={{ padding: 0 }}>
                  <li><a href="#features">Spark Medallion</a></li>
                  <li><a href="#features">Inverse GPA Calculator</a></li>
                  <li><a href="#features">MLflow Serverless</a></li>
                </ul>
              </div>
              <div>
                <h4 className="footer-link-title">Thông tin liên hệ</h4>
                <p className="text-sm text-gray mb-4"><i className="pi pi-map-marker" style={{ color: "var(--color-primary)", marginRight: "8px" }}></i> 12 Nguyễn Văn Bảo, Gò Vấp, TP.HCM</p>
                <p className="text-sm text-gray"><i className="pi pi-phone" style={{ color: "var(--color-primary)", marginRight: "8px" }}></i> Hotline: 1900 6688</p>
              </div>
            </div>
            <div className="footer-bottom">
              Bản quyền thuộc về SmartGPA Enterprise. Được xây dựng bởi Nguyễn Thị Quỳnh Trang.
            </div>
          </div>
        </footer>

        {/* ─── AUTH MODAL OVERLAY (MedBook inspired) ─── */}
        <div className={`modal-overlay ${isAuthModalOpen ? "active" : ""}`} onClick={(e) => e.target === e.currentTarget && setIsAuthModalOpen(false)}>
          <div className="modal-content">
            <button className="close-btn" onClick={() => setIsAuthModalOpen(false)}>
              <i className="pi pi-times"></i>
            </button>

            {/* Circular avatar box */}
            <div style={{ 
              width: "56px", 
              height: "56px", 
              borderRadius: "50%", 
              background: "linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(99, 102, 241, 0.2) 100%)", 
              display: "flex", 
              alignItems: "center", 
              justifyContent: "center",
              margin: "0 auto 16px auto",
              border: "1px solid var(--border-glass-glow)",
              boxShadow: "0 4px 12px rgba(99, 102, 241, 0.05)"
            }}>
              <i className="pi pi-user" style={{ fontSize: "20px", color: "var(--color-primary)" }}></i>
            </div>

            {/* Header */}
            <div style={{ marginBottom: "28px" }}>
              <h2 style={{ fontSize: "22px", fontWeight: 800, margin: 0, fontFamily: "var(--font-heading)", color: "var(--text-primary)" }}>
                Chào mừng trở lại
              </h2>
              <p style={{ color: "var(--text-secondary)", fontSize: "13.5px", marginTop: "6px" }}>
                Đăng nhập để tiếp tục hành trình học thuật
              </p>
            </div>

            {/* Connection status tag */}
            <div style={{ display: "flex", justifyContent: "center", marginBottom: "20px" }}>
              {isBackendOnline ? (
                <span className="badge badge-success">
                  <i className="pi pi-check-circle"></i> Kết nối máy chủ ổn định
                </span>
              ) : (
                <span className="badge badge-warning">
                  <i className="pi pi-exclamation-triangle"></i> Máy chủ offline (Dùng chế độ Demo)
                </span>
              )}
            </div>

            {/* Login Form */}
            <form onSubmit={onSubmitLogin} style={{ display: "flex", flexDirection: "column", gap: "16px", textAlign: "left" }}>
              {loginError && (
                <div className="badge badge-danger animate-fade-in" style={{ padding: "10px 12px", borderRadius: "8px", width: "100%", justifyContent: "flex-start", lineHeight: "1.4" }}>
                  <i className="pi pi-times-circle" style={{ flexShrink: 0 }}></i> {loginError}
                </div>
              )}

              <div className="form-group">
                <label className="form-label">Email đăng nhập:</label>
                <div style={{ position: "relative" }}>
                  <i className="pi pi-envelope" style={{ position: "absolute", left: "14px", top: "50%", transform: "translateY(-50%)", color: "var(--text-muted)" }}></i>
                  <input 
                    type="text" 
                    placeholder="ví dụ: student@smartgpa.edu"
                    value={loginEmail}
                    onChange={(e) => {
                      setLoginEmail(e.target.value);
                      if (loginError) setLoginError(null);
                    }}
                    style={{ paddingLeft: "42px", width: "100%" }}
                    required
                  />
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Mật khẩu:</label>
                <div style={{ position: "relative" }}>
                  <i className="pi pi-lock" style={{ position: "absolute", left: "14px", top: "50%", transform: "translateY(-50%)", color: "var(--text-muted)" }}></i>
                  <input 
                    type={showPassword ? "text" : "password"} 
                    placeholder="••••••••"
                    value={loginPassword}
                    onChange={(e) => {
                      setLoginPassword(e.target.value);
                      if (loginError) setLoginError(null);
                    }}
                    style={{ paddingLeft: "42px", paddingRight: "40px", width: "100%" }}
                    required
                  />
                  <i 
                    className={`pi ${showPassword ? "pi-eye-slash" : "pi-eye"}`}
                    onClick={() => setShowPassword(!showPassword)}
                    style={{ 
                      position: "absolute", 
                      right: "14px", 
                      top: "50%", 
                      transform: "translateY(-50%)", 
                      color: "var(--text-muted)", 
                      cursor: "pointer",
                      transition: "color 0.2s ease"
                    }}
                    onMouseEnter={(e) => e.currentTarget.style.color = "var(--color-primary)"}
                    onMouseLeave={(e) => e.currentTarget.style.color = "var(--text-muted)"}
                  ></i>
                </div>
              </div>

              <button 
                type="submit" 
                className="btn btn-primary"
                disabled={isLoading}
                style={{ 
                  width: "100%", 
                  padding: "12px", 
                  borderRadius: "8px", 
                  marginTop: "8px",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  gap: "8px"
                }}
              >
                {isLoading ? (
                  <>
                    <i className="pi pi-spin pi-spinner"></i> Đang xác thực...
                  </>
                ) : (
                  <>
                    <i className="pi pi-sign-in"></i> Đăng nhập
                  </>
                )}
              </button>
            </form>

            {/* Quick Login Section */}
            <div style={{ marginTop: "24px", paddingTop: "20px", borderTop: "1px solid var(--border-glass)" }}>
              <p style={{ fontSize: "12px", color: "var(--text-muted)", marginBottom: "12px", textTransform: "uppercase", letterSpacing: "0.5px", fontWeight: 600, textAlign: "left" }}>
                Đăng nhập nhanh tài khoản thử nghiệm:
              </p>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px" }}>
                <button
                  type="button"
                  className="badge badge-success hover-scale"
                  onClick={() => handleQuickLogin("student@smartgpa.edu", "password123")}
                  style={{ padding: "8px 10px", justifyContent: "flex-start", cursor: "pointer", borderRadius: "8px", border: "1px solid rgba(5, 150, 105, 0.2)", width: "100%" }}
                >
                  <i className="pi pi-user" style={{ marginRight: "6px" }}></i> Sinh viên
                </button>
                <button
                  type="button"
                  className="badge badge-info hover-scale"
                  onClick={() => handleQuickLogin("lecturer@smartgpa.edu", "password123")}
                  style={{ padding: "8px 10px", justifyContent: "flex-start", cursor: "pointer", borderRadius: "8px", border: "1px solid rgba(8, 145, 178, 0.2)", width: "100%" }}
                >
                  <i className="pi pi-file-excel" style={{ marginRight: "6px" }}></i> Giảng viên
                </button>
                <button
                  type="button"
                  className="badge badge-warning hover-scale"
                  onClick={() => handleQuickLogin("advisor@smartgpa.edu", "password123")}
                  style={{ padding: "8px 10px", justifyContent: "flex-start", cursor: "pointer", borderRadius: "8px", border: "1px solid rgba(217, 119, 6, 0.2)", width: "100%" }}
                >
                  <i className="pi pi-users" style={{ marginRight: "6px" }}></i> Cố vấn học vụ
                </button>
                <button
                  type="button"
                  className="badge badge-danger hover-scale"
                  onClick={() => handleQuickLogin("admin@smartgpa.edu", "password123")}
                  style={{ padding: "8px 10px", justifyContent: "flex-start", cursor: "pointer", borderRadius: "8px", border: "1px solid rgba(220, 38, 38, 0.2)", width: "100%" }}
                >
                  <i className="pi pi-cog" style={{ marginRight: "6px" }}></i> Quản trị viên
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="container" style={{ paddingBottom: "50px" }}>
      {/* ─── Luxury Header ────────────────────────────────────────── */}
      <header className="glass-card" style={{ marginTop: "30px", marginBottom: "30px", textAlign: "left", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <h1 className="gradient-text" style={{ fontSize: "32px", fontWeight: 800, margin: 0, fontFamily: "var(--font-heading)" }}>
            SmartGPA
          </h1>
          <p style={{ color: "var(--text-secondary)", fontSize: "14px", marginTop: "4px" }}>
            Hệ thống Phân tích Học thuật & Giả lập Điểm ngược (SOA - Databricks)
          </p>
        </div>
        
        {/* Connection status tag */}
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          {isBackendOnline ? (
            <span className="badge badge-success animate-fade-in">
              <i className="pi pi-check-circle"></i> Live API Online
            </span>
          ) : (
            <span className="badge badge-warning animate-fade-in">
              <i className="pi pi-exclamation-triangle"></i> Local Demo Session
            </span>
          )}
        </div>
      </header>

      {/* ─── User Profile & Session Navigation ────────────────────── */}
      <nav className="glass-card animate-fade-in" style={{ padding: "16px 24px", marginBottom: "30px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
          <div style={{ 
            width: "48px", 
            height: "48px", 
            borderRadius: "50%", 
            background: "linear-gradient(135deg, var(--color-primary) 0%, var(--color-secondary) 100%)", 
            display: "flex", 
            alignItems: "center", 
            justifyContent: "center",
            color: "#ffffff",
            fontWeight: 800,
            fontSize: "20px",
            fontFamily: "var(--font-heading)"
          }}>
            {user.full_name.charAt(0)}
          </div>
          <div style={{ textAlign: "left" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <span style={{ fontWeight: 700, fontSize: "16px", color: "var(--text-primary)" }}>{user.full_name}</span>
              <span className={`badge ${
                user.role === "student" ? "badge-success" : 
                user.role === "lecturer" ? "badge-info" : 
                user.role === "advisor" ? "badge-warning" : "badge-danger"
              }`} style={{ fontSize: "11px", padding: "3px 10px" }}>
                <i className={`pi ${
                  user.role === "student" ? "pi-user" : 
                  user.role === "lecturer" ? "pi-file-excel" : 
                  user.role === "advisor" ? "pi-users" : "pi-cog"
                }`} style={{ fontSize: "10px" }}></i> {
                  user.role === "student" ? "Sinh viên" : 
                  user.role === "lecturer" ? "Giảng viên" : 
                  user.role === "advisor" ? "Cố vấn học vụ" : "Quản trị viên"
                }
              </span>
            </div>
            <div style={{ fontSize: "13px", color: "var(--text-secondary)", marginTop: "2px" }}>{user.email}</div>
          </div>
        </div>

        <button 
          className="badge badge-danger hover-scale"
          onClick={handleLogout}
          style={{ width: "auto", height: "auto", padding: "10px 20px", borderRadius: "10px", border: "1px solid rgba(220, 38, 38, 0.2)", cursor: "pointer", display: "flex", alignItems: "center", gap: "8px" }}
        >
          <i className="pi pi-sign-out"></i> Đăng xuất
        </button>
      </nav>

      {/* ─── Render Portals ──────────────────────────────────────── */}
      <div className="animate-fade-in">
        
        {/* ─── 1. STUDENT PORTAL ──────────────────────────────────── */}
        {activeRole === "student" && (
          <div style={{ display: "grid", gridTemplateColumns: "1.2fr 1fr", gap: "24px" }}>
            
            {/* Input Parameters column */}
            <div className="glass-card" style={{ textAlign: "left" }}>
              <h2 style={{ fontFamily: "var(--font-heading)", fontWeight: 600, marginBottom: "20px" }}>
                Tham số giả lập lộ trình
              </h2>
              
              {/* Select subject */}
              <div style={{ display: "flex", flexDirection: "column", gap: "6px", marginBottom: "20px" }}>
                <label style={{ fontSize: "14px", color: "var(--text-secondary)" }}>Chọn học phần giả lập:</label>
                <select 
                  value={selectedSubject.id} 
                  onChange={(e) => {
                    const found = SUBJECTS.find(s => s.id === e.target.value);
                    if (found) setSelectedSubject(found);
                  }}
                >
                  {SUBJECTS.map((s) => (
                    <option key={s.id} value={s.id}>{s.name} ({s.type === "ly_thuyet" ? "Lý thuyết" : s.type === "thuc_hanh" ? "Thực hành" : "Tích hợp"})</option>
                  ))}
                </select>
              </div>

              {/* Sub-inputs: THEORY */}
              {selectedSubject.type === "ly_thuyet" && (
                <div className="animate-fade-in" style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
                  <div className="badge badge-info" style={{ alignSelf: "flex-start" }}>
                    Cấu hình điểm theo quy chế: Môn {selectedSubject.credits} tín chỉ có {selectedSubject.credits} đầu điểm thường kỳ
                  </div>
                  {/* Generate TK inputs */}
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(100px, 1fr))", gap: "12px" }}>
                    {Array.from({ length: selectedSubject.credits }).map((_, i) => (
                      <div key={i} style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                        <label style={{ fontSize: "12px", color: "var(--text-secondary)" }}>TK lần {i + 1}:</label>
                        <input 
                          type="number" 
                          step="0.1" 
                          min="0" 
                          max="10"
                          value={tkScores[i] ?? 8.0}
                          onChange={(e) => {
                            const val = Math.min(10, Math.max(0, parseFloat(e.target.value) || 0));
                            const updated = [...tkScores];
                            updated[i] = val;
                            setTkScores(updated);
                          }}
                        />
                      </div>
                    ))}
                  </div>

                  <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                    <label style={{ fontSize: "14px", color: "var(--text-secondary)" }}>Điểm thi Giữa kỳ (GK):</label>
                    <input 
                      type="number" 
                      step="0.1" 
                      min="0" 
                      max="10" 
                      value={gkScore}
                      onChange={(e) => setGkScore(Math.min(10, Math.max(0, parseFloat(e.target.value) || 0)))}
                    />
                  </div>
                </div>
              )}

              {/* Sub-inputs: PRACTICAL */}
              {selectedSubject.type === "thuc_hanh" && (
                <div className="animate-fade-in" style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
                  <div className="badge badge-info" style={{ alignSelf: "flex-start" }}>
                    Cấu hình điểm theo quy chế: Môn {selectedSubject.credits} tín chỉ thực hành, tối đa {selectedSubject.credits} bài nộp
                  </div>
                  
                  <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                    <label style={{ fontSize: "14px", color: "var(--text-secondary)" }}>Số buổi thực hành đã hoàn thành:</label>
                    <select 
                      value={completedSessions}
                      onChange={(e) => setCompletedSessions(parseInt(e.target.value))}
                    >
                      {Array.from({ length: selectedSubject.credits }).map((_, i) => (
                        <option key={i} value={i + 1}>{i + 1} / {selectedSubject.credits} buổi</option>
                      ))}
                    </select>
                  </div>

                  <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(100px, 1fr))", gap: "12px" }}>
                    {Array.from({ length: completedSessions }).map((_, i) => (
                      <div key={i} style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                        <label style={{ fontSize: "12px", color: "var(--text-secondary)" }}>Điểm buổi {i + 1}:</label>
                        <input 
                          type="number" 
                          step="0.1" 
                          min="0" 
                          max="10"
                          value={thScores[i] ?? 8.0}
                          onChange={(e) => {
                            const val = Math.min(10, Math.max(0, parseFloat(e.target.value) || 0));
                            const updated = [...thScores];
                            updated[i] = val;
                            setThScores(updated);
                          }}
                        />
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Sub-inputs: INTEGRATED */}
              {selectedSubject.type === "tich_hop" && (
                <div className="animate-fade-in" style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
                  <div className="badge badge-info" style={{ alignSelf: "flex-start" }}>
                    Cấu hình môn học: {selectedSubject.chiLT} Tín chỉ lý thuyết + {selectedSubject.chiTH} Tín chỉ thực hành
                  </div>

                  <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                    <label style={{ fontSize: "14px", color: "var(--text-secondary)" }}>Điểm trung bình thực hành (TH):</label>
                    <input 
                      type="number" 
                      step="0.1" 
                      min="0" 
                      max="10"
                      value={thTichHop}
                      onChange={(e) => setThTichHop(Math.min(10, Math.max(0, parseFloat(e.target.value) || 0)))}
                    />
                    <small style={{ color: "var(--text-muted)" }}>Hệ thống sẽ lập tức khóa tính toán nếu điểm này dưới 3.0 (điểm liệt).</small>
                  </div>

                  {/* Drill down checkbox */}
                  <label style={{ display: "flex", alignItems: "center", gap: "10px", cursor: "pointer", marginTop: "10px", fontSize: "14px" }}>
                    <input 
                      type="checkbox" 
                      checked={drillDownLT}
                      onChange={(e) => setDrillDownLT(e.target.checked)}
                      style={{ width: "16px", height: "16px" }}
                    />
                    Ước lượng sâu hơn: tính điểm thi cuối kỳ nhánh lý thuyết cần đạt
                  </label>

                  {drillDownLT && (
                    <div className="animate-fade-in" style={{ padding: "16px", background: "rgba(255,255,255,0.02)", borderRadius: "10px", border: "1px solid var(--border-glass)", display: "flex", flexDirection: "column", gap: "16px" }}>
                      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(100px, 1fr))", gap: "12px" }}>
                        {Array.from({ length: selectedSubject.chiLT ?? 2 }).map((_, i) => (
                          <div key={i} style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                            <label style={{ fontSize: "12px", color: "var(--text-secondary)" }}>TK Lý thuyết {i + 1}:</label>
                            <input 
                              type="number" 
                              step="0.1" 
                              min="0" 
                              max="10"
                              value={tkScoresLT[i] ?? 8.0}
                              onChange={(e) => {
                                const val = Math.min(10, Math.max(0, parseFloat(e.target.value) || 0));
                                const updated = [...tkScoresLT];
                                updated[i] = val;
                                setTkScoresLT(updated);
                              }}
                            />
                          </div>
                        ))}
                      </div>

                      <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                        <label style={{ fontSize: "12px", color: "var(--text-secondary)" }}>Giữa kỳ Lý thuyết (GK_lt):</label>
                        <input 
                          type="number" 
                          step="0.1" 
                          min="0" 
                          max="10"
                          value={gkScoreLT}
                          onChange={(e) => setGkScoreLT(Math.min(10, Math.max(0, parseFloat(e.target.value) || 0)))}
                        />
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* ─── Premium Target Grade Selector ─── */}
              <div style={{ marginTop: "30px" }}>
                <label style={{ fontSize: "14px", color: "var(--text-secondary)", display: "block", marginBottom: "10px" }}>
                  Thiết lập điểm chữ mục tiêu:
                </label>
                <div className="grade-slider-container">
                  <div className="grade-slider-track">
                    <div 
                      className="grade-slider-fill" 
                      style={{ width: `${(TARGETS.indexOf(targetGrade) / (TARGETS.length - 1)) * 100}%` }}
                    ></div>
                  </div>
                  {TARGETS.map((grade) => (
                    <div 
                      key={grade} 
                      className={`grade-node ${targetGrade === grade ? "active" : ""}`}
                      onClick={() => setTargetGrade(grade)}
                    >
                      {grade}
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Results and visualization column */}
            <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
              
              {/* Main Gauge / Result Ring card */}
              <div className={`glass-card ${isKhaThi ? (diemCanDat === 0.0 ? "" : "glow-card") : "pulse-card"}`} style={{ 
                border: !isKhaThi ? "1px solid var(--color-danger)" : diemCanDat === 0.0 ? "1px solid var(--color-success)" : "1px solid var(--border-glass-glow)",
                textAlign: "center", 
                padding: "32px",
                display: "flex", 
                flexDirection: "column", 
                alignItems: "center" 
              }}>
                <h2 style={{ fontFamily: "var(--font-heading)", fontWeight: 600, fontSize: "18px", marginBottom: "20px", color: "var(--text-secondary)" }}>
                  Kết quả giả lập mục tiêu {targetGrade}
                </h2>

                {/* Score Circular Ring Visualizer */}
                <div style={{ position: "relative", width: "160px", height: "160px", marginBottom: "24px" }}>
                  <svg width="160" height="160" viewBox="0 0 160 160">
                    {/* Background track circle */}
                    <circle cx="80" cy="80" r="70" stroke="rgba(255,255,255,0.03)" strokeWidth="12" fill="transparent" />
                    {/* Active progress circle */}
                    <circle 
                      cx="80" 
                      cy="80" 
                      r="70" 
                      stroke={!isKhaThi ? "var(--color-danger)" : diemCanDat === 0.0 ? "var(--color-success)" : "var(--color-primary)"} 
                      strokeWidth="12" 
                      fill="transparent" 
                      strokeDasharray="440"
                      strokeDashoffset={isKhaThi && diemCanDat !== null ? 440 - (440 * diemCanDat) / 10 : 440}
                      strokeLinecap="round"
                      style={{ transition: "stroke-dashoffset 0.6s cubic-bezier(0.4, 0, 0.2, 1)" }}
                      transform="rotate(-90 80 80)"
                    />
                  </svg>
                  {/* Center Text */}
                  <div style={{ 
                    position: "absolute", 
                    top: "50%", 
                    left: "50%", 
                    transform: "translate(-50%, -50%)", 
                    textAlign: "center" 
                  }}>
                    {isKhaThi ? (
                      <div>
                        <span style={{ fontSize: "38px", fontWeight: 800, fontFamily: "var(--font-heading)" }}>
                          {diemCanDat !== null ? diemCanDat.toFixed(1) : "0.0"}
                        </span>
                        <div style={{ fontSize: "10px", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "1px" }}>Điểm cần đạt</div>
                      </div>
                    ) : (
                      <div>
                        <i className="pi pi-times-circle" style={{ fontSize: "40px", color: "var(--color-danger)" }}></i>
                        <div style={{ fontSize: "10px", color: "var(--text-danger)", textTransform: "uppercase", letterSpacing: "1px", marginTop: "4px" }}>Thất bại</div>
                      </div>
                    )}
                  </div>
                </div>

                {/* Response Text Message */}
                <div style={{ padding: "16px", borderRadius: "10px", background: "rgba(255,255,255,0.02)", width: "100%", marginBottom: "15px", border: "1px solid var(--border-glass)" }}>
                  <p style={{ fontSize: "15px", fontWeight: 500, lineHeight: 1.4, color: !isKhaThi ? "var(--color-danger)" : "var(--text-primary)" }}>
                    {resultMessage}
                  </p>
                </div>

                {/* Status Badge */}
                <div style={{ display: "flex", gap: "10px" }}>
                  {isKhaThi ? (
                    diemCanDat === 0.0 ? (
                      <span className="badge badge-success">
                        <i className="pi pi-verified"></i> Đã đủ điểm
                      </span>
                    ) : (
                      <span className="badge badge-info">
                        <i className="pi pi-sliders-h"></i> Khả thi
                      </span>
                    )
                  ) : (
                    <span className="badge badge-danger">
                      <i className="pi pi-shield"></i> Điểm liệt / Bất khả thi
                    </span>
                  )}
                </div>
              </div>

              {/* Composition Detail Card */}
              {Object.keys(resultDetails).length > 0 && (
                <div className="glass-card" style={{ textAlign: "left" }}>
                  <h3 style={{ fontSize: "16px", fontFamily: "var(--font-heading)", marginBottom: "15px", fontWeight: 600 }}>
                    Chi tiết phân rã học phần
                  </h3>
                  <div style={{ display: "flex", flexDirection: "column", gap: "10px", fontSize: "14px" }}>
                    
                    {/* Theory detail */}
                    {selectedSubject.type === "ly_thuyet" && (
                      <>
                        <div style={{ display: "flex", justifyContent: "space-between" }}>
                          <span style={{ color: "var(--text-secondary)" }}>ĐTB Thường kỳ (20%):</span>
                          <span style={{ fontWeight: 600 }}>{resultDetails.diem_thuong_ky_trung_binh} / 10.0</span>
                        </div>
                        <div style={{ display: "flex", justifyContent: "space-between" }}>
                          <span style={{ color: "var(--text-secondary)" }}>Điểm Giữa kỳ (30%):</span>
                          <span style={{ fontWeight: 600 }}>{resultDetails.diem_giua_ky} / 10.0</span>
                        </div>
                        <div style={{ display: "flex", justifyContent: "space-between" }}>
                          <span style={{ color: "var(--text-secondary)" }}>Ngưỡng mục tiêu:</span>
                          <span style={{ fontWeight: 600, color: "var(--color-primary)" }}>≥ {diemMucTieuNguong}</span>
                        </div>
                      </>
                    )}

                    {/* Practical detail */}
                    {selectedSubject.type === "thuc_hanh" && (
                      <>
                        <div style={{ display: "flex", justifyContent: "space-between" }}>
                          <span style={{ color: "var(--text-secondary)" }}>Tổng số bài thực hành:</span>
                          <span style={{ fontWeight: 600 }}>{resultDetails.tong_so_buoi} bài</span>
                        </div>
                        <div style={{ display: "flex", justifyContent: "space-between" }}>
                          <span style={{ color: "var(--text-secondary)" }}>Số bài đã hoàn thành:</span>
                          <span style={{ fontWeight: 600 }}>{resultDetails.so_buoi_hien_tai} bài</span>
                        </div>
                        <div style={{ display: "flex", justifyContent: "space-between" }}>
                          <span style={{ color: "var(--text-secondary)" }}>Số bài còn lại:</span>
                          <span style={{ fontWeight: 600, color: "var(--color-secondary)" }}>{resultDetails.so_buoi_con_lai} bài</span>
                        </div>
                      </>
                    )}

                    {/* Integrated detail */}
                    {selectedSubject.type === "tich_hop" && (
                      <>
                        <div style={{ display: "flex", justifyContent: "space-between" }}>
                          <span style={{ color: "var(--text-secondary)" }}>Trọng số Lý thuyết:</span>
                          <span style={{ fontWeight: 600 }}>{selectedSubject.chiLT} Tín chỉ</span>
                        </div>
                        <div style={{ display: "flex", justifyContent: "space-between" }}>
                          <span style={{ color: "var(--text-secondary)" }}>Trọng số Thực hành:</span>
                          <span style={{ fontWeight: 600 }}>{selectedSubject.chiTH} Tín chỉ</span>
                        </div>
                        <div style={{ display: "flex", justifyContent: "space-between" }}>
                          <span style={{ color: "var(--text-secondary)" }}>ĐTB Thực hành (TH):</span>
                          <span style={{ fontWeight: 600, color: resultDetails.diem_thuc_hanh < 3.0 ? "var(--color-danger)" : "var(--text-primary)" }}>
                            {resultDetails.diem_thuc_hanh ?? thTichHop} / 10.0
                          </span>
                        </div>
                        {drillDownLT && resultDetails.diem_thuong_ky_lt_trung_binh !== undefined && (
                          <div style={{ marginTop: "10px", padding: "10px 0 0 0", borderTop: "1px dashed var(--border-glass)", display: "flex", flexDirection: "column", gap: "8px" }}>
                            <div style={{ display: "flex", justifyContent: "space-between" }}>
                              <span style={{ color: "var(--text-secondary)", fontSize: "13px" }}>ĐTB Thường kỳ LT (20%):</span>
                              <span style={{ fontWeight: 600, fontSize: "13px" }}>{resultDetails.diem_thuong_ky_lt_trung_binh} / 10.0</span>
                            </div>
                            <div style={{ display: "flex", justifyContent: "space-between" }}>
                              <span style={{ color: "var(--text-secondary)", fontSize: "13px" }}>Điểm Giữa kỳ LT (30%):</span>
                              <span style={{ fontWeight: 600, fontSize: "13px" }}>{resultDetails.diem_giua_ky_lt} / 10.0</span>
                            </div>
                          </div>
                        )}
                      </>
                    )}

                  </div>
                </div>
              )}
            </div>

          </div>
        )}

        {/* ─── 2. LECTURER PORTAL ─────────────────────────────────── */}
        {activeRole === "lecturer" && (
          <div className="glass-card" style={{ textAlign: "left" }}>
            <h2 style={{ fontFamily: "var(--font-heading)", fontWeight: 600, marginBottom: "20px" }}>
              Không gian Giảng viên: Nạp điểm lớp học phần
            </h2>
            
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1.5fr", gap: "24px" }}>
              
              {/* Form columns */}
              <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
                <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                  <label style={{ fontSize: "14px", color: "var(--text-secondary)" }}>Lớp học phần quản lý:</label>
                  <select 
                    value={lecturerMon}
                    onChange={(e) => setLecturerMon(e.target.value)}
                  >
                    {SUBJECTS.map((s) => (
                      <option key={s.id} value={s.id}>{s.name} - Lớp L01</option>
                    ))}
                  </select>
                </div>

                <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                  <label style={{ fontSize: "14px", color: "var(--text-secondary)" }}>Tải lên file bảng điểm thô (.csv/.xlsx):</label>
                  <input 
                    type="text" 
                    placeholder="Đường dẫn file thô / Chọn file"
                    value={lecturerFile}
                    onChange={(e) => setLecturerFile(e.target.value)}
                    style={{ background: "rgba(255,255,255,0.02)" }}
                  />
                  <small style={{ color: "var(--text-muted)" }}>Hệ thống tự động kích hoạt Databricks Pipeline Medallion khi upload.</small>
                </div>

                <button 
                  className="grade-node active"
                  onClick={() => {
                    setLecturerSuccessMsg("Tải dữ liệu thành công! Databricks pipeline đã được kích hoạt ở trạng thái PROCESSING.");
                    setTimeout(() => setLecturerSuccessMsg(null), 5000);
                  }}
                  style={{ width: "100%", height: "auto", padding: "12px", borderRadius: "8px", marginTop: "10px" }}
                >
                  <i className="pi pi-cloud-upload" style={{ marginRight: "8px" }}></i> Tải lên Delta Lake (Bronze)
                </button>

                {lecturerSuccessMsg && (
                  <div className="badge badge-success animate-fade-in" style={{ padding: "12px", display: "block", textAlign: "center" }}>
                    {lecturerSuccessMsg}
                  </div>
                )}
              </div>

              {/* Instruction column */}
              <div className="glass-card" style={{ background: "rgba(255,255,255,0.01)", borderStyle: "dashed" }}>
                <h3 style={{ fontSize: "15px", fontWeight: 600, marginBottom: "12px", color: "var(--color-primary)" }}>
                  Quy trình Medallion Pipeline (Databricks 3.2):
                </h3>
                <ul style={{ listStyleType: "none", fontSize: "13.5px", display: "flex", flexDirection: "column", gap: "10px", color: "var(--text-secondary)" }}>
                  <li>
                    <strong>Bước 1 (Bronze Table):</strong> Lưu trữ log file điểm thô nguyên bản của giảng viên tải lên.
                  </li>
                  <li>
                    <strong>Bước 2 (Silver Table):</strong> ETL Spark clean dữ liệu, đồng bộ hóa cột điểm thường kỳ đúng số tín chỉ và tự động làm tròn điểm số đến 0.1.
                  </li>
                  <li>
                    <strong>Bước 3 (Gold Table):</strong> Bảng điểm đa thang điểm chuẩn quy đổi đầy đủ thang 10, thang điểm chữ và thang 4.
                  </li>
                </ul>
              </div>

            </div>
          </div>
        )}

        {/* ─── 3. ADVISOR PORTAL ──────────────────────────────────── */}
        {activeRole === "advisor" && (
          <div style={{ display: "flex", flexDirection: "column", gap: "24px", textAlign: "left" }}>
            
            {/* Quick stats dashboard */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "20px" }}>
              <div className="glass-card text-center" style={{ textAlign: "center" }}>
                <div style={{ fontSize: "28px", fontWeight: 800, color: "var(--color-primary)" }}>1,240</div>
                <div style={{ fontSize: "12px", color: "var(--text-secondary)", marginTop: "4px" }}>Tổng số Sinh viên quản lý</div>
              </div>
              <div className="glass-card text-center" style={{ textAlign: "center", borderLeft: "3px solid var(--color-warning)" }}>
                <div style={{ fontSize: "28px", fontWeight: 800, color: "var(--color-warning)" }}>12.4 %</div>
                <div style={{ fontSize: "12px", color: "var(--text-secondary)", marginTop: "4px" }}>Sinh viên dính cảnh báo (Silver Table)</div>
              </div>
              <div className="glass-card text-center" style={{ textAlign: "center", borderLeft: "3px solid var(--color-danger)" }}>
                <div style={{ fontSize: "28px", fontWeight: 800, color: "var(--color-danger)" }}>5.2 %</div>
                <div style={{ fontSize: "12px", color: "var(--text-secondary)", marginTop: "4px" }}>Dự báo nguy cơ rớt môn (MLflow RF)</div>
              </div>
            </div>

            {/* List of flagged students */}
            <div className="glass-card">
              <h2 style={{ fontFamily: "var(--font-heading)", fontWeight: 600, fontSize: "18px", marginBottom: "20px" }}>
                Danh sách Sinh viên nhận Cảnh báo Học vụ (Học kỳ hiện tại)
              </h2>
              
              <div style={{ overflowX: "auto" }}>
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "14px" }}>
                  <thead>
                    <tr style={{ borderBottom: "1px solid var(--border-glass)", color: "var(--text-secondary)", textAlign: "left" }}>
                      <th style={{ padding: "12px" }}>MSSV</th>
                      <th style={{ padding: "12px" }}>Họ & tên</th>
                      <th style={{ padding: "12px" }}>Môn học</th>
                      <th style={{ padding: "12px" }}>Lý do cảnh báo</th>
                      <th style={{ padding: "12px" }}>Trạng thái</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr style={{ borderBottom: "1px solid var(--border-glass)" }}>
                      <td style={{ padding: "12px", fontWeight: 600 }}>23670631</td>
                      <td style={{ padding: "12px" }}>Nguyễn Trần Khánh Vy</td>
                      <td style={{ padding: "12px" }}>Cơ sở dữ liệu nâng cao</td>
                      <td style={{ padding: "12px", color: "var(--color-danger)" }}>
                        <i className="pi pi-times-circle" style={{ marginRight: "6px" }}></i> Liệt thực hành (TH = 2.0)
                      </td>
                      <td style={{ padding: "12px" }}><span className="badge badge-danger">Lọc từ Silver</span></td>
                    </tr>
                    <tr style={{ borderBottom: "1px solid var(--border-glass)" }}>
                      <td style={{ padding: "12px", fontWeight: 600 }}>23674120</td>
                      <td style={{ padding: "12px" }}>Phạm Minh Anh</td>
                      <td style={{ padding: "12px" }}>Cấu trúc dữ liệu & Giải thuật</td>
                      <td style={{ padding: "12px", color: "var(--color-warning)" }}>
                        <i className="pi pi-chart-bar" style={{ marginRight: "6px" }}></i> Điểm thường kỳ quá thấp (ĐTB_TK = 3.2)
                      </td>
                      <td style={{ padding: "12px" }}><span className="badge badge-warning">Lọc từ Silver</span></td>
                    </tr>
                    <tr style={{ borderBottom: "1px solid var(--border-glass)" }}>
                      <td style={{ padding: "12px", fontWeight: 600 }}>23690184</td>
                      <td style={{ padding: "12px" }}>Trần Lê Tuấn</td>
                      <td style={{ padding: "12px" }}>Thực hành Hệ điều hành</td>
                      <td style={{ padding: "12px", color: "var(--color-danger)" }}>
                        <i className="pi pi-times" style={{ marginRight: "6px" }}></i> Nguy cơ rớt môn cao (ML model dự báo 82% F)
                      </td>
                      <td style={{ padding: "12px" }}><span className="badge badge-danger">MLflow Predict</span></td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

          </div>
        )}

        {/* ─── 4. ADMIN PORTAL ────────────────────────────────────── */}
        {activeRole === "admin" && (
          <div className="glass-card" style={{ textAlign: "left" }}>
            <h2 style={{ fontFamily: "var(--font-heading)", fontWeight: 600, marginBottom: "20px" }}>
              Cấu hình hệ thống & Quy đổi thang điểm chữ (Score Mapping)
            </h2>
            
            <div style={{ display: "grid", gridTemplateColumns: "1.5fr 1fr", gap: "24px" }}>
              
              {/* Score mapping table */}
              <div>
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "13.5px" }}>
                  <thead>
                    <tr style={{ borderBottom: "1px solid var(--border-glass)", color: "var(--text-secondary)", textAlign: "left" }}>
                      <th style={{ padding: "8px 12px" }}>Thang 10 Min</th>
                      <th style={{ padding: "8px 12px" }}>Thang 10 Max</th>
                      <th style={{ padding: "8px 12px" }}>Điểm chữ</th>
                      <th style={{ padding: "8px 12px" }}>Hệ 4</th>
                      <th style={{ padding: "8px 12px" }}>Đánh giá</th>
                    </tr>
                  </thead>
                  <tbody>
                    {scoreMapping.map((item, idx) => (
                      <tr key={idx} style={{ borderBottom: "1px solid var(--border-glass)" }}>
                        <td style={{ padding: "8px 12px" }}>{item.diem_10_min.toFixed(1)}</td>
                        <td style={{ padding: "8px 12px" }}>{item.diem_10_max.toFixed(1)}</td>
                        <td style={{ padding: "8px 12px", fontWeight: 700, color: "var(--color-primary)" }}>{item.diem_chu}</td>
                        <td style={{ padding: "8px 12px" }}>{item.diem_he_4.toFixed(1)}</td>
                        <td style={{ padding: "8px 12px" }}>
                          <span className={`badge ${item.loai_danh_gia === "Đạt" ? "badge-success" : "badge-danger"}`}>
                            {item.loai_danh_gia}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Server info / settings */}
              <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
                <div className="glass-card" style={{ background: "rgba(255,255,255,0.01)" }}>
                  <h3 style={{ fontSize: "14px", fontWeight: 600, marginBottom: "10px", color: "var(--color-secondary)" }}>
                    Thông tin máy chủ logic
                  </h3>
                  <div style={{ display: "flex", flexDirection: "column", gap: "8px", fontSize: "13px" }}>
                    <div style={{ display: "flex", justifyContent: "space-between" }}>
                      <span style={{ color: "var(--text-secondary)" }}>Hạ tầng:</span>
                      <span>FastAPI + Uvicorn</span>
                    </div>
                    <div style={{ display: "flex", justifyContent: "space-between" }}>
                      <span style={{ color: "var(--text-secondary)" }}>Hệ mã hóa JWT:</span>
                      <span>HS256 (Access/Refresh)</span>
                    </div>
                    <div style={{ display: "flex", justifyContent: "space-between" }}>
                      <span style={{ color: "var(--text-secondary)" }}>Hệ thống ML:</span>
                      <span>Databricks MLflow Serverless</span>
                    </div>
                  </div>
                </div>

                <div className="glass-card" style={{ background: "rgba(255,255,255,0.01)" }}>
                  <h3 style={{ fontSize: "14px", fontWeight: 600, marginBottom: "10px", color: "var(--color-primary)" }}>
                    Lưu ý Quy chế mới C/C+ (2024):
                  </h3>
                  <p style={{ fontSize: "13px", color: "var(--text-secondary)", lineHeight: 1.4 }}>
                    Dải điểm chữ **C+** hiện tại đã được thiết lập theo quy định mới thành từ **6.0 đến 6.9**, và **C** là từ **5.5 đến 5.9** (như hiển thị trên bảng ánh xạ thực tế). Điều này giúp tối ưu hóa phổ điểm tích lũy GPA cho sinh viên.
                  </p>
                </div>
              </div>

            </div>
          </div>
        )}

      </div>
    </div>
  );
}
