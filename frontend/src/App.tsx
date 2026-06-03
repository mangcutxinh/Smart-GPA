import { useMemo, useState } from "react";

type TargetGrade = "A+" | "A" | "B+" | "B" | "C+" | "C" | "D+" | "D";

interface LoginResponse {
  access_token: string;
  must_change_password?: boolean;
  username?: string;
}

interface SimulationResult {
  loai_hoc_phan: string;
  muc_tieu: string;
  diem_muc_tieu_nguong: number;
  diem_can_dat: number | null;
  is_kha_thi: boolean;
  message: string;
}

interface StudentLookupResult {
  student_id: string;
  ma_mon: string;
  ten_mon: string;
  loai_hoc_phan: string;
  status_canh_bao: string;
  prediction?: SimulationResult;
  error?: string;
}

interface AdminOverview {
  project?: Record<string, unknown>;
  counts?: Record<string, number>;
  latest_updates?: Array<Record<string, unknown>>;
}

const API_BASE = "http://localhost:8001";
const TARGETS: TargetGrade[] = ["D", "D+", "C", "C+", "B", "B+", "A", "A+"];

const SAMPLE_CSV = `student_id,ma_mon,ma_lop_hoc_phan,loai_hoc_phan,diem_thong_thuong,diem_giua_ky,diem_thuc_hanh_hien_tai,diem_thuc_hanh_tich_hop,diem_thuong_ky_lt_list,diem_giua_ky_lt
SV123456,INT1002,L01,ly_thuyet,"8.0,7.5",7.0,,,,
SV1001,INT1001,L01,tich_hop,,,,8.5,"8.0,9.0",7.5
SV1002,INT1001,L01,tich_hop,,,,2.5,"4.0,4.5",4.0
`;

function downloadTemplate() {
  const blob = new Blob([SAMPLE_CSV], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "smartgpa_scores_template.csv";
  a.click();
  URL.revokeObjectURL(url);
}

function statusClass(ok?: boolean) {
  return ok ? "badge badge-success" : "badge badge-danger";
}

export default function App() {
  const [studentId, setStudentId] = useState("SV123456");
  const [studentUsername, setStudentUsername] = useState("SV123456");
  const [studentPassword, setStudentPassword] = useState("password123");
  const [studentToken, setStudentToken] = useState<string | null>(null);
  const [studentName, setStudentName] = useState<string | null>(null);
  const [studentMustChangePassword, setStudentMustChangePassword] = useState(false);
  const [studentLoginError, setStudentLoginError] = useState<string | null>(null);
  const [studentAccountStatus, setStudentAccountStatus] = useState<string | null>(null);
  const [studentEmail, setStudentEmail] = useState("");
  const [studentOtp, setStudentOtp] = useState("");
  const [studentNewPassword, setStudentNewPassword] = useState("");
  const [target, setTarget] = useState<TargetGrade>("A");
  const [results, setResults] = useState<StudentLookupResult[]>([]);
  const [selectedCourseId, setSelectedCourseId] = useState("");
  const [hasPredicted, setHasPredicted] = useState(false);
  const [lookupError, setLookupError] = useState<string | null>(null);
  const [isLookingUp, setIsLookingUp] = useState(false);

  const [lecturerEmail, setLecturerEmail] = useState("thibinh.gv1001@smartgpa.edu");
  const [lecturerPassword, setLecturerPassword] = useState("password123");
  const [lecturerToken, setLecturerToken] = useState<string | null>(null);
  const [lecturerName, setLecturerName] = useState<string | null>(null);
  const [lecturerError, setLecturerError] = useState<string | null>(null);
  const [isLecturerLoggingIn, setIsLecturerLoggingIn] = useState(false);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadStatus, setUploadStatus] = useState<string | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);

  const [adminEmail, setAdminEmail] = useState("admin@smartgpa.edu");
  const [adminPassword, setAdminPassword] = useState("password123");
  const [adminToken, setAdminToken] = useState<string | null>(null);
  const [adminName, setAdminName] = useState<string | null>(null);
  const [adminError, setAdminError] = useState<string | null>(null);
  const [adminStatus, setAdminStatus] = useState<string | null>(null);
  const [isAdminBusy, setIsAdminBusy] = useState(false);
  const [adminOverview, setAdminOverview] = useState<AdminOverview | null>(null);
  const [adminTimeline, setAdminTimeline] = useState<Array<Record<string, unknown>>>([]);
  const [adminUsers, setAdminUsers] = useState<Array<Record<string, unknown>>>([]);
  const [adminGrades, setAdminGrades] = useState<Array<Record<string, unknown>>>([]);
  const [scoreHistory, setScoreHistory] = useState<Array<Record<string, unknown>>>([]);
  const [adminWarnings, setAdminWarnings] = useState<Array<Record<string, unknown>>>([]);
  const [gradingRules, setGradingRules] = useState<Record<string, unknown> | null>(null);
  const [newLecturerEmail, setNewLecturerEmail] = useState("newlecturer@smartgpa.edu");
  const [newLecturerName, setNewLecturerName] = useState("Giang vien moi");
  const [newLecturerId, setNewLecturerId] = useState("GVNEW");
  const [adminStudentId, setAdminStudentId] = useState("SV123456");
  const [adminCourseId, setAdminCourseId] = useState("INT1002");
  const [adminMidterm, setAdminMidterm] = useState("4.5");
  const [timelineTitle, setTimelineTitle] = useState("Cap nhat he thong");
  const [timelineDetails, setTimelineDetails] = useState("Admin cap nhat cau hinh SmartGPA.");

  const selectedResult = useMemo(
    () => results.find((item) => item.ma_mon === selectedCourseId) ?? null,
    [results, selectedCourseId],
  );

  const summary = useMemo(() => {
    const visibleResults = hasPredicted && selectedResult ? [selectedResult] : [];
    const total = results.length;
    const warning = visibleResults.filter((item) => !item.prediction?.is_kha_thi || item.status_canh_bao !== "An toan").length;
    const best = visibleResults[0];
    return { total, warning, best };
  }, [hasPredicted, results.length, selectedResult]);
  const displayedResults = hasPredicted && selectedResult ? [selectedResult] : [];

  async function loadStudentSubjects(token: string, sid: string, targetGrade: TargetGrade = target) {
    setIsLookingUp(true);
    setLookupError(null);
    try {
      const params = new URLSearchParams({ diem_chu_muc_tieu: targetGrade });
      const resp = await fetch(`${API_BASE}/simulation/student-lookup/${sid.trim()}?${params}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await resp.json();
      if (!resp.ok) {
        throw new Error(data.detail || "Không tải được danh sách môn.");
      }
      const subjects = data as StudentLookupResult[];
      setResults(subjects);
      setSelectedCourseId((current) => (
        subjects.some((item) => item.ma_mon === current) ? current : subjects[0]?.ma_mon || ""
      ));
      setHasPredicted(false);
    } catch (err) {
      setLookupError(err instanceof Error ? err.message : "Không tải được danh sách môn.");
    } finally {
      setIsLookingUp(false);
    }
  }

  async function loginStudent() {
    setStudentLoginError(null);
    setStudentAccountStatus(null);
    try {
      const loginResp = await fetch(`${API_BASE}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: studentUsername, password: studentPassword }),
      });
      const loginData = (await loginResp.json()) as LoginResponse;
      if (!loginResp.ok) throw new Error("Đăng nhập sinh viên thất bại.");

      const meResp = await fetch(`${API_BASE}/auth/me`, {
        headers: { Authorization: `Bearer ${loginData.access_token}` },
      });
      const me = await meResp.json();
      if (!meResp.ok || me.role !== "student") throw new Error("Tai khoan nay khong phai sinh vien.");

      setStudentToken(loginData.access_token);
      setStudentName(me.full_name);
      setStudentId(me.student_id || studentId);
      setStudentMustChangePassword(Boolean(me.must_change_password || loginData.must_change_password));
      setStudentAccountStatus("Đã đăng nhập sinh viên.");
      setResults([]);
      setSelectedCourseId("");
      setHasPredicted(false);
      if (!me.must_change_password && !loginData.must_change_password && me.student_id) {
        await loadStudentSubjects(loginData.access_token, me.student_id);
      }
    } catch (err) {
      setStudentLoginError(err instanceof Error ? err.message : "Không đăng nhập được sinh viên.");
    }
  }

  async function requestStudentOtp() {
    setStudentLoginError(null);
    setStudentAccountStatus(null);
    try {
      const resp = await fetch(`${API_BASE}/auth/password/request-otp`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: studentUsername, email: studentEmail }),
      });
      const data = await resp.json();
      if (!resp.ok) throw new Error(data.detail || "Không lấy được OTP.");
      setStudentOtp("");
      setStudentAccountStatus(`Đã gửi OTP đến ${data.email}.`);
    } catch (err) {
      setStudentLoginError(err instanceof Error ? err.message : "Không lấy được OTP.");
    }
  }

  async function changeStudentPassword() {
    setStudentLoginError(null);
    setStudentAccountStatus(null);
    try {
      const resp = await fetch(`${API_BASE}/auth/password/change-with-otp`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: studentUsername, otp: studentOtp, new_password: studentNewPassword }),
      });
      const data = await resp.json();
      if (!resp.ok) throw new Error(data.detail || "Không đổi được mật khẩu.");
      setStudentPassword(studentNewPassword);
      setStudentMustChangePassword(false);
      setStudentAccountStatus("Đã đổi mật khẩu và xác minh email cảnh báo.");
      if (studentToken && studentId) {
        await loadStudentSubjects(studentToken, studentId);
      }
    } catch (err) {
      setStudentLoginError(err instanceof Error ? err.message : "Không đổi được mật khẩu.");
    }
  }

  async function lookupStudent() {
    if (!studentToken) {
      setLookupError("Sinh viên phải đăng nhập trước khi dự báo.");
      return;
    }
    if (!selectedCourseId) {
      setLookupError("Vui lòng chọn môn học cần dự báo.");
      return;
    }
    await loadStudentSubjects(studentToken, studentId, target);
    setHasPredicted(true);
  }

  async function loginLecturer() {
    setIsLecturerLoggingIn(true);
    setLecturerError(null);
    try {
      const loginResp = await fetch(`${API_BASE}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: lecturerEmail, password: lecturerPassword }),
      });
      const loginData = (await loginResp.json()) as LoginResponse;
      if (!loginResp.ok) {
        throw new Error("Đăng nhập giảng viên thất bại.");
      }

      const meResp = await fetch(`${API_BASE}/auth/me`, {
        headers: { Authorization: `Bearer ${loginData.access_token}` },
      });
      const me = await meResp.json();
      if (!meResp.ok || me.role !== "lecturer") {
        throw new Error("Tài khoản này không phải giảng viên.");
      }

      setLecturerToken(loginData.access_token);
      setLecturerName(me.full_name);
    } catch (err) {
      setLecturerError(err instanceof Error ? err.message : "Không đăng nhập được.");
    } finally {
      setIsLecturerLoggingIn(false);
    }
  }

  async function uploadScores() {
    if (!uploadFile || !lecturerToken) return;
    setIsUploading(true);
    setUploadStatus(null);
    setUploadError(null);
    try {
      const form = new FormData();
      form.append("file", uploadFile);
      const resp = await fetch(`${API_BASE}/upload/file`, {
        method: "POST",
        headers: { Authorization: `Bearer ${lecturerToken}` },
        body: form,
      });
      const data = await resp.json();
      if (!resp.ok) {
        const detail = typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail);
        throw new Error(detail || "Upload thất bại.");
      }
      const syncedRows = data.db_synced ?? data.records_processed ?? 0;
      const runText = data.databricks_run_id ? ` Run ID: ${data.databricks_run_id}.` : "";
      const pipelineStatus = data.pipeline_status ? ` Pipeline: ${data.pipeline_status}.` : "";
      const sharedPath = data.workspace_path ? ` Shared: ${data.workspace_path}.` : "";
      setUploadStatus(
        `Đã xử lý ${data.records_processed ?? syncedRows} dòng, ghi Databricks ${syncedRows} dòng. File: ${data.filename}.${sharedPath}${pipelineStatus}${runText}`
      );
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : "Upload thất bại.");
    } finally {
      setIsUploading(false);
    }
  }

  async function adminFetch(path: string, options: RequestInit = {}) {
    if (!adminToken) throw new Error("Chua dang nhap admin.");
    const resp = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${adminToken}`,
        ...(options.headers || {}),
      },
    });
    const data = await resp.json();
    if (!resp.ok) {
      const detail = typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail);
      throw new Error(detail || "Admin request failed.");
    }
    return data;
  }

  async function loadAdminDashboard(tokenOverride?: string) {
    const token = tokenOverride || adminToken;
    if (!token) return;
    setIsAdminBusy(true);
    setAdminError(null);
    try {
      const headers = { Authorization: `Bearer ${token}` };
      const [overview, timeline, users, grades, history, warnings, rules] = await Promise.all([
        fetch(`${API_BASE}/admin/overview`, { headers }).then((r) => r.json()),
        fetch(`${API_BASE}/admin/timeline`, { headers }).then((r) => r.json()),
        fetch(`${API_BASE}/admin/users`, { headers }).then((r) => r.json()),
        fetch(`${API_BASE}/admin/grades`, { headers }).then((r) => r.json()),
        fetch(`${API_BASE}/admin/score-history`, { headers }).then((r) => r.json()),
        fetch(`${API_BASE}/admin/warnings`, { headers }).then((r) => r.json()),
        fetch(`${API_BASE}/admin/grading-rules`, { headers }).then((r) => r.json()),
      ]);
      setAdminOverview(overview);
      setAdminTimeline(Array.isArray(timeline) ? timeline : []);
      setAdminUsers(Array.isArray(users) ? users : []);
      setAdminGrades(Array.isArray(grades) ? grades : []);
      setScoreHistory(Array.isArray(history) ? history : []);
      setAdminWarnings(Array.isArray(warnings) ? warnings : []);
      setGradingRules(rules);
    } catch (err) {
      setAdminError(err instanceof Error ? err.message : "Khong tai duoc dashboard admin.");
    } finally {
      setIsAdminBusy(false);
    }
  }

  async function loginAdmin() {
    setIsAdminBusy(true);
    setAdminError(null);
    setAdminStatus(null);
    try {
      const loginResp = await fetch(`${API_BASE}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: adminEmail, password: adminPassword }),
      });
      const loginData = (await loginResp.json()) as LoginResponse;
      if (!loginResp.ok) throw new Error("Dang nhap admin that bai.");

      const meResp = await fetch(`${API_BASE}/auth/me`, {
        headers: { Authorization: `Bearer ${loginData.access_token}` },
      });
      const me = await meResp.json();
      if (!meResp.ok || me.role !== "admin") throw new Error("Tai khoan nay khong phai admin.");

      setAdminToken(loginData.access_token);
      setAdminName(me.full_name);
      setAdminStatus("Da dang nhap admin.");
      await loadAdminDashboard(loginData.access_token);
    } catch (err) {
      setAdminError(err instanceof Error ? err.message : "Khong dang nhap duoc admin.");
    } finally {
      setIsAdminBusy(false);
    }
  }

  async function createLecturer() {
    try {
      await adminFetch("/admin/lecturers", {
        method: "POST",
        body: JSON.stringify({
          email: newLecturerEmail,
          password: "password123",
          full_name: newLecturerName,
          role: "lecturer",
          lecturer_id: newLecturerId,
          faculty_id: "CNTT",
        }),
      });
      setAdminStatus(`Da tao giang vien ${newLecturerId}.`);
      await loadAdminDashboard();
    } catch (err) {
      setAdminError(err instanceof Error ? err.message : "Khong tao duoc giang vien.");
    }
  }

  async function deleteLecturer(lecturerId: unknown) {
    if (!lecturerId) return;
    try {
      await adminFetch(`/admin/lecturers/${lecturerId}`, { method: "DELETE" });
      setAdminStatus(`Da xoa giang vien ${String(lecturerId)}.`);
      await loadAdminDashboard();
    } catch (err) {
      setAdminError(err instanceof Error ? err.message : "Khong xoa duoc giang vien.");
    }
  }

  async function updateGrade() {
    try {
      await adminFetch(`/admin/grades/${adminStudentId}/${adminCourseId}`, {
        method: "PUT",
        body: JSON.stringify({
          diem_giua_ky: Number(adminMidterm),
          reason: "Admin update from UI",
        }),
      });
      setAdminStatus(`Da cap nhat diem ${adminStudentId} - ${adminCourseId}.`);
      await loadAdminDashboard();
    } catch (err) {
      setAdminError(err instanceof Error ? err.message : "Khong cap nhat duoc bang diem.");
    }
  }

  async function addTimeline() {
    try {
      await adminFetch("/admin/timeline", {
        method: "POST",
        body: JSON.stringify({ title: timelineTitle, category: "admin", details: timelineDetails }),
      });
      setAdminStatus("Da luu timeline update.");
      await loadAdminDashboard();
    } catch (err) {
      setAdminError(err instanceof Error ? err.message : "Khong luu duoc timeline.");
    }
  }

  async function sendFirstWarning() {
    const first = adminWarnings[0];
    if (!first) return;
    try {
      await adminFetch("/admin/warnings/send", {
        method: "POST",
        body: JSON.stringify({
          student_id: first.student_id,
          student_name: first.student_name || `Sinh vien ${first.student_id}`,
          ma_mon: first.ma_mon,
          ten_mon: first.ten_mon || first.ma_mon,
          reason: first.reason || "Canh bao hoc vu",
          fail_risk: Number(first.fail_risk || 0),
          channel: "in_app",
        }),
      });
      setAdminStatus("Da gui canh bao sinh vien dau danh sach.");
      await loadAdminDashboard();
    } catch (err) {
      setAdminError(err instanceof Error ? err.message : "Khong gui duoc canh bao.");
    }
  }

  async function updateGradingRules() {
    try {
      await adminFetch("/admin/grading-rules", {
        method: "PUT",
        body: JSON.stringify({ version: "ui-update", practice_min_pass: 3.0 }),
      });
      setAdminStatus("Da cap nhat cach tinh diem.");
      await loadAdminDashboard();
    } catch (err) {
      setAdminError(err instanceof Error ? err.message : "Khong cap nhat duoc cach tinh diem.");
    }
  }

  return (
    <main style={{ minHeight: "100vh", background: "#f6f8fb" }}>
      <div className="container" style={{ paddingTop: 28, paddingBottom: 44 }}>
        <header style={{ display: "flex", justifyContent: "space-between", gap: 18, alignItems: "center", marginBottom: 22 }}>
          <div>
            <div className="badge badge-info" style={{ marginBottom: 10 }}>SmartGPA</div>
            <h1 style={{ fontFamily: "var(--font-heading)", fontSize: 34, lineHeight: 1.15 }}>
              Tra cứu điểm và dự báo mục tiêu học tập
            </h1>
          </div>
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap", justifyContent: "flex-end" }}>
            <a className="btn btn-outline" href="#lecturer-panel">Giảng viên upload điểm</a>
            <a className="btn btn-primary" href="#admin-panel">Admin</a>
          </div>
        </header>

        <section
          style={{
            display: "grid",
            gridTemplateColumns: "minmax(320px, 0.9fr) minmax(360px, 1.1fr)",
            gap: 20,
            alignItems: "stretch",
            marginBottom: 20,
          }}
        >
          <div className="glass-card glow-card" style={{ borderRadius: 8, padding: 28 }}>
            <h2 style={{ fontSize: 24, marginBottom: 8 }}>Sinh viên tra cứu</h2>
            <p style={{ color: "var(--text-secondary)", lineHeight: 1.55, marginBottom: 22 }}>
              Sinh viên đăng nhập bằng MSSV và mật khẩu. Tài khoản mới có mật khẩu mặc định password123.
            </p>

            {!studentToken ? (
              <div style={{ background: "#fff", border: "1px solid var(--border-glass)", borderRadius: 8, padding: 14, marginBottom: 16 }}>
                <div className="grid grid-2" style={{ gap: 10 }}>
                  <div className="form-group">
                    <label className="form-label">MSSV</label>
                    <input className="form-control" value={studentUsername} onChange={(e) => setStudentUsername(e.target.value.toUpperCase())} placeholder="VD: SV123456" />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Mật khẩu</label>
                    <input className="form-control" type="password" value={studentPassword} onChange={(e) => setStudentPassword(e.target.value)} />
                  </div>
                </div>
                <button className="btn btn-primary" onClick={loginStudent} style={{ width: "100%" }}>Đăng nhập sinh viên</button>
              </div>
            ) : (
              <div style={{ background: "#fff", border: "1px solid var(--border-glass)", borderRadius: 8, padding: 14, marginBottom: 16 }}>
                <div style={{ display: "flex", justifyContent: "space-between", gap: 10, alignItems: "center" }}>
                  <div>
                    <strong>{studentName}</strong>
                    <p style={{ color: "var(--text-secondary)", fontSize: 13, marginTop: 4 }}>{studentUsername}</p>
                  </div>
                  <button className="btn btn-ghost" onClick={() => { setStudentToken(null); setResults([]); }}>Đăng xuất</button>
                </div>
              </div>
            )}

            {studentMustChangePassword && (
              <div style={{ background: "#fff", border: "1px solid var(--border-glass)", borderRadius: 8, padding: 14, marginBottom: 16 }}>
                <h3 style={{ fontSize: 16, marginBottom: 10 }}>Đổi mật khẩu lần đầu</h3>
                <div className="grid grid-2" style={{ gap: 10 }}>
                  <input className="form-control" type="email" value={studentEmail} onChange={(e) => setStudentEmail(e.target.value)} placeholder="Email nhận OTP và cảnh báo" />
                  <button className="btn btn-outline" onClick={requestStudentOtp} disabled={!studentEmail}>Lấy OTP</button>
                  <input className="form-control" value={studentOtp} onChange={(e) => setStudentOtp(e.target.value)} placeholder="OTP" />
                  <input className="form-control" type="password" value={studentNewPassword} onChange={(e) => setStudentNewPassword(e.target.value)} placeholder="Mật khẩu mới" />
                </div>
                <button className="btn btn-primary" onClick={changeStudentPassword} disabled={!studentOtp || !studentNewPassword} style={{ width: "100%", marginTop: 10 }}>Xác nhận đổi mật khẩu</button>
              </div>
            )}

            {(studentAccountStatus || studentLoginError) && (
              <div className={studentLoginError ? "badge badge-danger" : "badge badge-success"} style={{ marginBottom: 14, width: "100%", justifyContent: "center" }}>
                {studentLoginError || studentAccountStatus}
              </div>
            )}

            {studentToken && !studentMustChangePassword && (
              <>
                <div className="form-group">
                  <label className="form-label">MSSV</label>
                  <input className="form-control" type="text" value={studentId} readOnly style={{ fontSize: 18, height: 48 }} />
                </div>

                <div className="form-group">
                  <label className="form-label">Môn học</label>
                  <select
                    className="form-control"
                    value={selectedCourseId}
                    onChange={(e) => {
                      setSelectedCourseId(e.target.value);
                      setHasPredicted(false);
                    }}
                    disabled={isLookingUp || results.length === 0}
                    style={{ height: 46 }}
                  >
                    {results.length === 0 ? (
                      <option value="">Chưa có môn học</option>
                    ) : (
                      results.map((item) => (
                        <option key={`${item.student_id}-${item.ma_mon}`} value={item.ma_mon}>
                          {item.ma_mon} - {item.ten_mon}
                        </option>
                      ))
                    )}
                  </select>
                </div>

                <div className="form-group">
                  <label className="form-label">Mục tiêu điểm chữ</label>
                  <select
                    className="form-control"
                    value={target}
                    onChange={(e) => {
                      setTarget(e.target.value as TargetGrade);
                      setHasPredicted(false);
                    }}
                    style={{ height: 46 }}
                  >
                    {TARGETS.map((grade) => (
                      <option key={grade} value={grade}>{grade}</option>
                    ))}
                  </select>
                </div>

                <button className="btn btn-primary" onClick={lookupStudent} disabled={isLookingUp || !selectedCourseId} style={{ width: "100%", height: 46 }}>
                  {isLookingUp ? "Đang dự báo..." : "Dự báo môn đã chọn"}
                </button>
              </>
            )}
            {lookupError && <div className="badge badge-danger" style={{ marginTop: 16, width: "100%", justifyContent: "center" }}>{lookupError}</div>}
          </div>

          <div className="glass-card" style={{ borderRadius: 8, padding: 28 }}>
            <h2 style={{ fontSize: 24, marginBottom: 18 }}>Tổng quan kết quả</h2>
            {!hasPredicted ? (
              <div style={{ display: "grid", gap: 14 }}>
                <div style={{ padding: 18, border: "1px solid var(--border-glass)", borderRadius: 8, background: "#fff" }}>
                  <strong>{studentToken ? "Chọn môn học để dự báo" : "Sinh viên cần đăng nhập"}</strong>
                  <p style={{ color: "var(--text-secondary)", marginTop: 6, lineHeight: 1.55 }}>
                    {studentToken
                      ? "Chọn một môn trong danh sách, chọn mục tiêu điểm chữ, rồi bấm dự báo."
                      : "Đăng nhập bằng tài khoản sinh viên để vào trang tra cứu dự báo."}
                  </p>
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 10 }}>
                  {["Tổng môn", "Cần chú ý", "Mục tiêu"].map((label) => (
                    <div key={label} style={{ background: "#fff", border: "1px solid var(--border-glass)", borderRadius: 8, padding: 14 }}>
                      <p style={{ color: "var(--text-muted)", fontSize: 12 }}>{label}</p>
                      <strong style={{ fontSize: 22 }}>-</strong>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div style={{ display: "grid", gap: 16 }}>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 10 }}>
                  <div style={{ background: "#fff", border: "1px solid var(--border-glass)", borderRadius: 8, padding: 14 }}>
                    <p style={{ color: "var(--text-muted)", fontSize: 12 }}>Tổng môn</p>
                    <strong style={{ fontSize: 28 }}>{summary.total}</strong>
                  </div>
                  <div style={{ background: "#fff", border: "1px solid var(--border-glass)", borderRadius: 8, padding: 14 }}>
                    <p style={{ color: "var(--text-muted)", fontSize: 12 }}>Cần chú ý</p>
                    <strong style={{ fontSize: 28, color: summary.warning ? "var(--color-danger)" : "var(--color-success)" }}>{summary.warning}</strong>
                  </div>
                  <div style={{ background: "#fff", border: "1px solid var(--border-glass)", borderRadius: 8, padding: 14 }}>
                    <p style={{ color: "var(--text-muted)", fontSize: 12 }}>Mục tiêu</p>
                    <strong style={{ fontSize: 28 }}>{target}</strong>
                  </div>
                </div>

                <div style={{ background: "#fff", border: "1px solid var(--border-glass)", borderRadius: 8, padding: 16 }}>
                  <p style={{ color: "var(--text-muted)", fontSize: 12, marginBottom: 6 }}>Môn dễ đạt mục tiêu nhất</p>
                  <strong>{summary.best ? `${summary.best.ma_mon} - cần ${summary.best.prediction?.diem_can_dat} điểm` : "Chưa có môn khả thi"}</strong>
                </div>
              </div>
            )}
          </div>
        </section>

        <section className="glass-card" style={{ borderRadius: 8, padding: 0, overflow: "hidden", marginBottom: 26 }}>
          <div style={{ padding: "18px 22px", borderBottom: "1px solid var(--border-glass)", display: "flex", justifyContent: "space-between", gap: 12, alignItems: "center" }}>
            <div>
              <h2 style={{ fontSize: 22 }}>Bảng điểm và dự báo theo môn</h2>
              <p style={{ color: "var(--text-secondary)", marginTop: 4 }}>Mỗi dòng là một học phần đã có dữ liệu điểm.</p>
            </div>
            <span className="badge badge-info">MSSV: {studentId || "-"}</span>
          </div>

          {displayedResults.length === 0 ? (
            <div style={{ padding: 28, color: "var(--text-secondary)" }}>
              {studentToken ? "Chưa có kết quả. Hãy chọn môn học và bấm dự báo." : "Sinh viên cần đăng nhập để xem dự báo."}
            </div>
          ) : (
            <div style={{ overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 14 }}>
                <thead>
                  <tr style={{ background: "#fff", color: "var(--text-secondary)", textAlign: "left" }}>
                    <th style={{ padding: 14 }}>Mã môn</th>
                    <th style={{ padding: 14 }}>Tên môn</th>
                    <th style={{ padding: 14 }}>Loại</th>
                    <th style={{ padding: 14 }}>Điểm cần đạt</th>
                    <th style={{ padding: 14 }}>Đánh giá</th>
                    <th style={{ padding: 14 }}>Thông điệp</th>
                  </tr>
                </thead>
                <tbody>
                  {displayedResults.map((item) => (
                    <tr key={`${item.student_id}-${item.ma_mon}`} style={{ borderTop: "1px solid var(--border-glass)", background: "#fff" }}>
                      <td style={{ padding: 14, fontWeight: 700 }}>{item.ma_mon}</td>
                      <td style={{ padding: 14 }}>{item.ten_mon}</td>
                      <td style={{ padding: 14 }}>{item.prediction?.loai_hoc_phan || item.loai_hoc_phan}</td>
                      <td style={{ padding: 14, fontSize: 20, fontWeight: 800 }}>
                        {item.prediction?.diem_can_dat ?? "Không khả thi"}
                      </td>
                      <td style={{ padding: 14 }}>
                        <span className={statusClass(item.prediction?.is_kha_thi)}>
                          {item.prediction?.is_kha_thi ? "Khả thi" : "Cảnh báo"}
                        </span>
                      </td>
                      <td style={{ padding: 14, color: "var(--text-secondary)", minWidth: 300 }}>
                        {item.prediction?.message || item.error || "Không tính được dự báo"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>

        <section id="lecturer-panel" className="glass-card" style={{ borderRadius: 8 }}>
          <div style={{ display: "grid", gridTemplateColumns: "minmax(280px, 0.9fr) minmax(320px, 1.1fr)", gap: 22, alignItems: "start" }}>
            <div>
              <h2 style={{ fontSize: 24, marginBottom: 8 }}>Khu vực giảng viên</h2>
              <p style={{ color: "var(--text-secondary)", lineHeight: 1.55 }}>
                Giảng viên đăng nhập riêng để upload bảng điểm CSV. Sau upload, sinh viên có thể tra cứu ngay bằng MSSV.
              </p>
            </div>

            <div style={{ background: "#fff", border: "1px solid var(--border-glass)", borderRadius: 8, padding: 18 }}>
              {!lecturerToken ? (
                <>
                  <div className="grid grid-2" style={{ gap: 12 }}>
                    <div className="form-group">
                      <label className="form-label">Email giảng viên</label>
                      <input className="form-control" type="text" value={lecturerEmail} onChange={(e) => setLecturerEmail(e.target.value)} />
                    </div>
                    <div className="form-group">
                      <label className="form-label">Mật khẩu</label>
                      <input className="form-control" type="password" value={lecturerPassword} onChange={(e) => setLecturerPassword(e.target.value)} />
                    </div>
                  </div>
                  <button className="btn btn-primary" onClick={loginLecturer} disabled={isLecturerLoggingIn}>
                    {isLecturerLoggingIn ? "Đang đăng nhập..." : "Đăng nhập giảng viên"}
                  </button>
                  {lecturerError && <div className="badge badge-danger" style={{ marginTop: 12 }}>{lecturerError}</div>}
                </>
              ) : (
                <>
                  <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "center", marginBottom: 14 }}>
                    <div>
                      <strong>{lecturerName}</strong>
                      <p style={{ color: "var(--text-secondary)", fontSize: 13, marginTop: 4 }}>Đã đăng nhập giảng viên</p>
                    </div>
                    <button className="btn btn-ghost" onClick={() => setLecturerToken(null)}>Đăng xuất</button>
                  </div>
                  <div className="form-group">
                    <label className="form-label">File CSV bảng điểm</label>
                    <input className="form-control" type="file" accept=".csv" onChange={(e) => setUploadFile(e.target.files?.[0] ?? null)} />
                  </div>
                  <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
                    <button className="btn btn-primary" disabled={!uploadFile || isUploading} onClick={uploadScores}>
                      {isUploading ? "Đang upload..." : "Upload bảng điểm"}
                    </button>
                    <button className="btn btn-outline" onClick={downloadTemplate}>Tải CSV mẫu</button>
                  </div>
                  {uploadStatus && <div className="badge badge-success" style={{ marginTop: 12 }}>{uploadStatus}</div>}
                  {uploadError && <div className="badge badge-danger" style={{ marginTop: 12 }}>{uploadError}</div>}
                </>
              )}
            </div>
          </div>
        </section>

        <section id="admin-panel" className="glass-card" style={{ borderRadius: 8, marginTop: 26 }}>
          <div style={{ display: "flex", justifyContent: "space-between", gap: 14, alignItems: "flex-start", marginBottom: 18 }}>
            <div>
              <div className="badge badge-info" style={{ marginBottom: 10 }}>Admin</div>
              <h2 style={{ fontSize: 24, marginBottom: 6 }}>Quản trị toàn bộ SmartGPA</h2>
              <p style={{ color: "var(--text-secondary)", lineHeight: 1.55 }}>
                Quản lý thông tin dự án, tài khoản giảng viên, timeline, bảng điểm, cảnh báo, cách tính điểm và lịch sử điểm.
              </p>
            </div>
            {adminToken && (
              <button className="btn btn-ghost" onClick={() => { setAdminToken(null); setAdminName(null); }}>
                Đăng xuất admin
              </button>
            )}
          </div>

          {!adminToken ? (
            <div style={{ background: "#fff", border: "1px solid var(--border-glass)", borderRadius: 8, padding: 18 }}>
              <div className="grid grid-2" style={{ gap: 12 }}>
                <div className="form-group">
                  <label className="form-label">Email admin</label>
                  <input className="form-control" type="text" value={adminEmail} onChange={(e) => setAdminEmail(e.target.value)} />
                </div>
                <div className="form-group">
                  <label className="form-label">Mật khẩu</label>
                  <input className="form-control" type="password" value={adminPassword} onChange={(e) => setAdminPassword(e.target.value)} />
                </div>
              </div>
              <button className="btn btn-primary" onClick={loginAdmin} disabled={isAdminBusy}>
                {isAdminBusy ? "Đang đăng nhập..." : "Đăng nhập admin"}
              </button>
              {adminError && <div className="badge badge-danger" style={{ marginTop: 12 }}>{adminError}</div>}
            </div>
          ) : (
            <div style={{ display: "grid", gap: 18 }}>
              <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
                <div>
                  <strong>{adminName}</strong>
                  <p style={{ color: "var(--text-secondary)", fontSize: 13, marginTop: 4 }}>Đang quản trị hệ thống</p>
                </div>
                <button className="btn btn-outline" onClick={() => loadAdminDashboard()} disabled={isAdminBusy}>
                  {isAdminBusy ? "Đang tải..." : "Làm mới dữ liệu"}
                </button>
              </div>

              {(adminStatus || adminError) && (
                <div className={adminError ? "badge badge-danger" : "badge badge-success"}>
                  {adminError || adminStatus}
                </div>
              )}

              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))", gap: 10 }}>
                {Object.entries(adminOverview?.counts || {}).map(([key, value]) => (
                  <div key={key} style={{ background: "#fff", border: "1px solid var(--border-glass)", borderRadius: 8, padding: 14 }}>
                    <p style={{ color: "var(--text-muted)", fontSize: 12 }}>{key.replaceAll("_", " ")}</p>
                    <strong style={{ fontSize: 24 }}>{value}</strong>
                  </div>
                ))}
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "minmax(280px, 1fr) minmax(280px, 1fr)", gap: 16 }}>
                <div style={{ background: "#fff", border: "1px solid var(--border-glass)", borderRadius: 8, padding: 16 }}>
                  <h3 style={{ fontSize: 18, marginBottom: 12 }}>Tài khoản giảng viên</h3>
                  <div className="grid grid-2" style={{ gap: 10 }}>
                    <input className="form-control" value={newLecturerEmail} onChange={(e) => setNewLecturerEmail(e.target.value)} placeholder="Email" />
                    <input className="form-control" value={newLecturerId} onChange={(e) => setNewLecturerId(e.target.value.toUpperCase())} placeholder="Mã GV" />
                    <input className="form-control" value={newLecturerName} onChange={(e) => setNewLecturerName(e.target.value)} placeholder="Họ tên" />
                    <button className="btn btn-primary" onClick={createLecturer}>Thêm giảng viên</button>
                  </div>
                  <div style={{ marginTop: 14, display: "grid", gap: 8, maxHeight: 220, overflow: "auto" }}>
                    {adminUsers.filter((user) => user.role === "lecturer").map((user) => (
                      <div key={String(user.email)} style={{ display: "flex", justifyContent: "space-between", gap: 10, alignItems: "center", borderTop: "1px solid var(--border-glass)", paddingTop: 8 }}>
                        <div>
                          <strong>{String(user.full_name || user.email)}</strong>
                          <p style={{ color: "var(--text-secondary)", fontSize: 12 }}>{String(user.lecturer_id || "-")} · {String(user.email)}</p>
                        </div>
                        <button className="btn btn-outline" onClick={() => deleteLecturer(user.lecturer_id)}>Xóa</button>
                      </div>
                    ))}
                  </div>
                </div>

                <div style={{ background: "#fff", border: "1px solid var(--border-glass)", borderRadius: 8, padding: 16 }}>
                  <h3 style={{ fontSize: 18, marginBottom: 12 }}>Timeline update</h3>
                  <input className="form-control" value={timelineTitle} onChange={(e) => setTimelineTitle(e.target.value)} placeholder="Tiêu đề" style={{ width: "100%", marginBottom: 10 }} />
                  <input className="form-control" value={timelineDetails} onChange={(e) => setTimelineDetails(e.target.value)} placeholder="Nội dung cập nhật" style={{ width: "100%", marginBottom: 10 }} />
                  <button className="btn btn-primary" onClick={addTimeline}>Lưu timeline</button>
                  <div style={{ marginTop: 14, display: "grid", gap: 8, maxHeight: 210, overflow: "auto" }}>
                    {adminTimeline.slice(0, 6).map((item) => (
                      <div key={String(item.id)} style={{ borderTop: "1px solid var(--border-glass)", paddingTop: 8 }}>
                        <strong>{String(item.title || "-")}</strong>
                        <p style={{ color: "var(--text-secondary)", fontSize: 12 }}>{String(item.timestamp || "")}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "minmax(280px, 1fr) minmax(280px, 1fr)", gap: 16 }}>
                <div style={{ background: "#fff", border: "1px solid var(--border-glass)", borderRadius: 8, padding: 16 }}>
                  <h3 style={{ fontSize: 18, marginBottom: 12 }}>Sửa bảng điểm</h3>
                  <div className="grid grid-2" style={{ gap: 10 }}>
                    <input className="form-control" value={adminStudentId} onChange={(e) => setAdminStudentId(e.target.value.toUpperCase())} placeholder="MSSV" />
                    <input className="form-control" value={adminCourseId} onChange={(e) => setAdminCourseId(e.target.value.toUpperCase())} placeholder="Mã môn" />
                    <input className="form-control" type="number" min="0" max="10" step="0.1" value={adminMidterm} onChange={(e) => setAdminMidterm(e.target.value)} placeholder="Điểm giữa kỳ" />
                    <button className="btn btn-primary" onClick={updateGrade}>Cập nhật điểm</button>
                  </div>
                  <p style={{ color: "var(--text-secondary)", fontSize: 13, marginTop: 12 }}>
                    {adminGrades.length} bảng điểm · {scoreHistory.length} sự kiện lịch sử điểm
                  </p>
                </div>

                <div style={{ background: "#fff", border: "1px solid var(--border-glass)", borderRadius: 8, padding: 16 }}>
                  <h3 style={{ fontSize: 18, marginBottom: 12 }}>Cảnh báo sinh viên</h3>
                  <div style={{ display: "flex", justifyContent: "space-between", gap: 10, alignItems: "center", marginBottom: 10 }}>
                    <span className="badge badge-danger">{adminWarnings.length} cảnh báo</span>
                    <button className="btn btn-primary" onClick={sendFirstWarning} disabled={!adminWarnings.length}>Gửi cảnh báo đầu</button>
                  </div>
                  <div style={{ display: "grid", gap: 8, maxHeight: 190, overflow: "auto" }}>
                    {adminWarnings.slice(0, 5).map((warning) => (
                      <div key={`${String(warning.student_id)}-${String(warning.ma_mon)}`} style={{ borderTop: "1px solid var(--border-glass)", paddingTop: 8 }}>
                        <strong>{String(warning.student_id)} · {String(warning.ma_mon)}</strong>
                        <p style={{ color: "var(--text-secondary)", fontSize: 12 }}>{String(warning.reason || warning.record || "Nguy cơ học vụ")}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              <div style={{ background: "#fff", border: "1px solid var(--border-glass)", borderRadius: 8, padding: 16 }}>
                <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
                  <div>
                    <h3 style={{ fontSize: 18, marginBottom: 4 }}>Cách tính điểm</h3>
                    <p style={{ color: "var(--text-secondary)", fontSize: 13 }}>
                      Version: {String(gradingRules?.version || "-")} · Điểm liệt TH: {String(gradingRules?.practice_min_pass || "-")}
                    </p>
                  </div>
                  <button className="btn btn-outline" onClick={updateGradingRules}>Cập nhật rule mẫu</button>
                </div>
              </div>
            </div>
          )}
        </section>
      </div>
    </main>
  );
}


