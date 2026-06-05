import { useMemo, useState, useEffect } from "react";

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
  chi_tiet?: any;
}

interface StudentLookupResult {
  student_id: string;
  ma_mon: string;
  ten_mon: string;
  loai_hoc_phan: string;
  status_canh_bao: string;
  source: string;
  prediction?: SimulationResult;
  error?: string;
  diem_tong_ket?: number | null;
  diem_chu?: string | null;
  diem_he_4?: number | null;
  tong_so_chi?: number;
  hoc_ky?: number;
}

interface AdminOverview {
  project?: Record<string, any>;
  counts?: Record<string, number>;
  latest_updates?: Array<Record<string, any>>;
}

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8002";
const TARGETS: TargetGrade[] = ["D", "D+", "C", "C+", "B", "B+", "A", "A+"];

const SAMPLE_CSV = `student_id,ma_mon,ma_lop_hoc_phan,loai_hoc_phan,diem_thong_thuong,diem_giua_ky,diem_thuc_hanh_hien_tai,diem_thuc_hanh_tich_hop,diem_thuong_ky_lt_list,diem_giua_ky_lt
SV123456,INT1002,L01,ly_thuyet,"8.0,7.5",7.0,,,,
SV1001,INT1001,L01,tich_hop,,,,8.5,"8.0,9.0",7.5
SV1002,INT1001,L01,tich_hop,,,,2.5,"4.0,4.5",4.0
`;

export default function App() {
  // Navigation & UI States
  const [activeTab, setActiveTab] = useState<"student" | "lecturer" | "admin">(() => {
    return (localStorage.getItem("activeTab") as "student" | "lecturer" | "admin") || "student";
  });
  const [isScrolled, setIsScrolled] = useState(false);
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [predictSemester, setPredictSemester] = useState<number>(1);
  const [studentWorkspaceTab, setStudentWorkspaceTab] = useState<"dashboard" | "curriculum" | "simulation" | "calculator">("dashboard");
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  // Student States
  const [studentId, setStudentId] = useState(() => localStorage.getItem("studentId") || "23677361");
  const [studentUsername, setStudentUsername] = useState(() => localStorage.getItem("studentId") || "23677361");
  const [studentPassword, setStudentPassword] = useState("Sv@123");
  const [studentToken, setStudentToken] = useState<string | null>(() => localStorage.getItem("studentToken"));
  const [studentName, setStudentName] = useState<string | null>(() => localStorage.getItem("studentName"));
  const [studentMustChangePassword, setStudentMustChangePassword] = useState(() => localStorage.getItem("studentMustChangePassword") === "true");
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
  const [studentNotifications, setStudentNotifications] = useState<any[]>([]);
  const [showNotificationsDropdown, setShowNotificationsDropdown] = useState(false);

  // Student Calculator States (TBMH, TBHK, TBTL)
  const [calcType, setCalcType] = useState<"ly_thuyet" | "thuc_hanh" | "tich_hop">("ly_thuyet");
  const [calcResult, setCalcResult] = useState<any | null>(null);

  // Redesigned Calculator states (TBMH, TBHK, TBTL)
  const [calcSubTab, setCalcSubTab] = useState<"TBMH" | "TBHK" | "TBTL">("TBMH");
  
  // TBMH Individual Inputs
  const [tx1Input, setTx1Input] = useState("");
  const [tx2Input, setTx2Input] = useState("");
  const [tx3Input, setTx3Input] = useState("");
  const [tx4Input, setTx4Input] = useState("");
  const [gkInput, setGkInput] = useState("");
  const [ckInput, setCkInput] = useState("");
  
  // TH Inputs
  const [th1Input, setTh1Input] = useState("");
  const [th2Input, setTh2Input] = useState("");
  const [th3Input, setTh3Input] = useState("");
  const [th4Input, setTh4Input] = useState("");
  
  // GPA Rows for TBHK/TBTL
  const [gpaRows, setGpaRows] = useState<Array<{ id: number; name: string; credits: number; grade: string }>>([
    { id: 1, name: "Môn A", credits: 3, grade: "" },
    { id: 2, name: "Môn B", credits: 2, grade: "" },
  ]);
  const [gpaResult, setGpaResult] = useState<{
    totalCredits: number;
    gpa10: number;
    gpa4: number;
    letterGrade: string;
    classification: string;
  } | null>(null);

  // Lecturer States
  const [lecturerEmail, setLecturerEmail] = useState("thibinh.gv1001@smartgpa.edu");
  const [lecturerPassword, setLecturerPassword] = useState("Gv@123");
  const [lecturerToken, setLecturerToken] = useState<string | null>(() => localStorage.getItem("lecturerToken"));
  const [lecturerName, setLecturerName] = useState<string | null>(() => localStorage.getItem("lecturerName"));
  const [lecturerError, setLecturerError] = useState<string | null>(null);
  const [isLecturerLoggingIn, setIsLecturerLoggingIn] = useState(false);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadStatus, setUploadStatus] = useState<string | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);

  // Lecturer Workspace States
  const [lecturerWorkspaceTab, setLecturerWorkspaceTab] = useState<"courses" | "grades" | "upload">("courses");
  const [lecturerCourses, setLecturerCourses] = useState<any[]>([]);
  const [selectedLecturerCourseId, setSelectedLecturerCourseId] = useState<string>("");
  const [lecturerGrades, setLecturerGrades] = useState<any[]>([]);
  const [isLecturerLoading, setIsLecturerLoading] = useState(false);

  // Lecturer Course and Student Filters/Sorters
  const [lecturerCourseSearch, setLecturerCourseSearch] = useState("");
  const [lecturerStudentSearch, setLecturerStudentSearch] = useState("");
  const [sortByStudentName, setSortByStudentName] = useState(false);

  // Lecturer CRUD Student Grades Inline States
  const [editingGradeRow, setEditingGradeRow] = useState<any | null>(null);
  const [editGradeMidterm, setEditGradeMidterm] = useState("");
  const [editGradeRegular, setEditGradeRegular] = useState("");
  const [editGradeFinal, setEditGradeFinal] = useState("");
  const [editGradePractice1, setEditGradePractice1] = useState("");
  const [editGradePractice2, setEditGradePractice2] = useState("");
  const [editGradePractice3, setEditGradePractice3] = useState("");
  const [editGradeReason, setEditGradeReason] = useState("Giảng viên cập nhật");

  // Advisor & Admin States
  const [adminEmail, setAdminEmail] = useState("admin@smartgpa.edu");
  const [adminPassword, setAdminPassword] = useState("Admin@123");
  const [adminToken, setAdminToken] = useState<string | null>(() => localStorage.getItem("adminToken"));
  const [adminName, setAdminName] = useState<string | null>(() => localStorage.getItem("adminName"));
  const [adminError, setAdminError] = useState<string | null>(null);
  const [adminStatus, setAdminStatus] = useState<string | null>(null);
  const [isAdminBusy, setIsAdminBusy] = useState(false);

  // Admin Workspace Dashboard Data
  const [adminOverview, setAdminOverview] = useState<AdminOverview | null>(null);
  const [adminTimeline, setAdminTimeline] = useState<any[]>([]);
  const [adminUsers, setAdminUsers] = useState<any[]>([]);

  const [adminWarnings, setAdminWarnings] = useState<any[]>([]);
  const [gradingRules, setGradingRules] = useState<Record<string, any> | null>(null);
  const [adminCourses, setAdminCourses] = useState<any[]>([]);
  const [adminAssignments, setAdminAssignments] = useState<any[]>([]);


  // Admin Student CRUD States
  const [editingStudent, setEditingStudent] = useState<any | null>(null);
  const [newStudentId, setNewStudentId] = useState("");
  const [newStudentEmail, setNewStudentEmail] = useState("");
  const [newStudentName, setNewStudentName] = useState("");
  const [newStudentFaculty] = useState("CNTT");
  const [newStudentMajor] = useState("KHDL");
  const [newStudentClass, setNewStudentClass] = useState("DHKHDL19A");

  // Admin Course CRUD States
  const [editingCourse, setEditingCourse] = useState<any | null>(null);
  const [newCourseId, setNewCourseId] = useState("");
  const [newCourseName, setNewCourseName] = useState("");
  const [newCourseType, setNewCourseType] = useState("ly_thuyet");
  const [newCourseCredits, setNewCourseCredits] = useState(3);

  // Admin Assignment States
  const [assignLecturerId, setAssignLecturerId] = useState("");
  const [assignCourseId, setAssignCourseId] = useState("");
  const [assignClassId, setAssignClassId] = useState("L01");


  const [timelineTitle, setTimelineTitle] = useState("Cập nhật hệ thống");
  const [timelineDetails, setTimelineDetails] = useState("Admin cập nhật cấu hình SmartGPA.");
  const [adminActiveSubTab, setAdminActiveSubTab] = useState<"warnings" | "students" | "courses" | "assignments" | "rules" | "timeline">("warnings");

  // Track scrolling to style navbar dynamically
  useEffect(() => {
    const handleScroll = () => {
      if (window.scrollY > 40) {
        setIsScrolled(true);
      } else {
        setIsScrolled(false);
      }
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  // Sync scroll animations (scroll reveal elements)
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("animate-fade-in");
          }
        });
      },
      { threshold: 0.1 }
    );

    document.querySelectorAll(".reveal").forEach((el) => observer.observe(el));
    return () => observer.disconnect();
  }, []);

  // Demo account automatic filler and API submit trigger
  async function handleDemoLogin(role: "student" | "lecturer" | "admin", u: string, p: string) {
    if (role === "student") {
      setStudentUsername(u);
      setStudentPassword(p);
      setStudentLoginError(null);
      setStudentAccountStatus(null);
      try {
        const loginResp = await fetch(`${API_BASE}/auth/login`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email: u, password: p }),
        });
        const loginData = (await loginResp.json()) as LoginResponse;
        if (!loginResp.ok) throw new Error("Đăng nhập sinh viên thất bại.");

        const meResp = await fetch(`${API_BASE}/auth/me`, {
          headers: { Authorization: `Bearer ${loginData.access_token}` },
        });
        const me = await meResp.json();
        if (!meResp.ok || me.role !== "student") throw new Error("Tài khoản này không phải sinh viên.");

        setStudentToken(loginData.access_token);
        setStudentName(me.full_name);
        setStudentId(me.student_id || me.username);
        setStudentMustChangePassword(Boolean(me.must_change_password || loginData.must_change_password));
        setStudentAccountStatus(null);
        setResults([]);
        setSelectedCourseId("");
        setHasPredicted(false);
        setShowLoginModal(false);

        // Load subjects and notifications
        if (!me.must_change_password && !loginData.must_change_password && me.student_id) {
          await loadStudentSubjects(loginData.access_token, me.student_id);
          await loadStudentNotifications(loginData.access_token);
        }
      } catch (err) {
        setStudentLoginError(err instanceof Error ? err.message : "Không đăng nhập được sinh viên.");
      }
    } else if (role === "lecturer") {
      setLecturerEmail(u);
      setLecturerPassword(p);
      setIsLecturerLoggingIn(true);
      setLecturerError(null);
      try {
        const loginResp = await fetch(`${API_BASE}/auth/login`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email: u, password: p }),
        });
        const loginData = (await loginResp.json()) as LoginResponse;
        if (!loginResp.ok) throw new Error("Đăng nhập giảng viên thất bại.");

        const meResp = await fetch(`${API_BASE}/auth/me`, {
          headers: { Authorization: `Bearer ${loginData.access_token}` },
        });
        const me = await meResp.json();
        if (!meResp.ok || me.role !== "lecturer") throw new Error("Tài khoản này không phải giảng viên.");

        setLecturerToken(loginData.access_token);
        setLecturerName(me.full_name);
        setShowLoginModal(false);
      } catch (err) {
        setLecturerError(err instanceof Error ? err.message : "Không đăng nhập được giảng viên.");
      } finally {
        setIsLecturerLoggingIn(false);
      }
    } else if (role === "admin") {
      setAdminEmail(u);
      setAdminPassword(p);
      setIsAdminBusy(true);
      setAdminError(null);
      setAdminStatus(null);
      try {
        const loginResp = await fetch(`${API_BASE}/auth/login`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email: u, password: p }),
        });
        const loginData = (await loginResp.json()) as LoginResponse;
        if (!loginResp.ok) throw new Error("Đăng nhập Admin thất bại.");

        const meResp = await fetch(`${API_BASE}/auth/me`, {
          headers: { Authorization: `Bearer ${loginData.access_token}` },
        });
        const me = await meResp.json();
        if (!meResp.ok || me.role !== "admin") throw new Error("Tài khoản này không phải admin.");

        setAdminToken(loginData.access_token);
        setAdminName(me.full_name);
        setAdminStatus("Đã đăng nhập Admin.");
        await loadAdminDashboard(loginData.access_token);
        setShowLoginModal(false);
      } catch (err) {
        setAdminError(err instanceof Error ? err.message : "Không đăng nhập được admin.");
      } finally {
        setIsAdminBusy(false);
      }
    }
  }

  // Load student data helpers
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
        throw new Error(data.detail || "Không tải được danh sách môn học.");
      }
      const subjects = data as StudentLookupResult[];
      setResults(subjects);
      if (subjects.length > 0) {
        const firstHk = subjects[0]?.hoc_ky || 1;
        setPredictSemester(firstHk);
        setSelectedCourseId(subjects[0]?.ma_mon || "");
      } else {
        setSelectedCourseId("");
      }
    } catch (err) {
      setLookupError(err instanceof Error ? err.message : "Không tải được danh sách môn học.");
    } finally {
      setIsLookingUp(false);
    }
  }

  // Load Notifications
  async function loadStudentNotifications(token: string) {
    try {
      const resp = await fetch(`${API_BASE}/simulation/student-notifications`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (resp.ok) {
        const notis = await resp.json();
        setStudentNotifications(notis);
      }
    } catch (e) {
      console.error("Lỗi lấy thông báo sinh viên:", e);
    }
  }

  // Read all notifications
  async function readAllNotifications() {
    if (!studentToken) return;
    try {
      const resp = await fetch(`${API_BASE}/simulation/student-notifications/read-all`, {
        method: "POST",
        headers: { Authorization: `Bearer ${studentToken}` },
      });
      if (resp.ok) {
        await loadStudentNotifications(studentToken);
        setStudentAccountStatus("Đã đánh dấu đọc toàn bộ thông báo.");
      }
    } catch (e) {
      console.error(e);
    }
  }

  // Student Normal Login
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
      if (!loginResp.ok) throw new Error("Đăng nhập sinh viên thất bại. Kiểm tra lại thông tin.");

      const meResp = await fetch(`${API_BASE}/auth/me`, {
        headers: { Authorization: `Bearer ${loginData.access_token}` },
      });
      const me = await meResp.json();
      if (!meResp.ok || me.role !== "student") throw new Error("Tài khoản này không phải vai trò sinh viên.");

      setStudentToken(loginData.access_token);
      setStudentName(me.full_name);
      setStudentId(me.student_id || studentId);
      setStudentMustChangePassword(Boolean(me.must_change_password || loginData.must_change_password));
      setStudentAccountStatus(null);
      setResults([]);
      setSelectedCourseId("");
      setHasPredicted(false);
      setShowLoginModal(false);
      
      if (!me.must_change_password && !loginData.must_change_password && me.student_id) {
        await loadStudentSubjects(loginData.access_token, me.student_id);
        await loadStudentNotifications(loginData.access_token);
      }
    } catch (err) {
      setStudentLoginError(err instanceof Error ? err.message : "Đăng nhập sinh viên thất bại.");
    }
  }

  // OTP triggers
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
      if (!resp.ok) throw new Error(data.detail || "Không lấy được mã OTP.");
      setStudentOtp("");
      setStudentAccountStatus(`Đã gửi thành công OTP đến ${data.email}. Hãy kiểm tra hòm thư.`);
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
      setStudentAccountStatus("Đã xác thực email & đổi mật khẩu thành công!");
      if (studentToken && studentId) {
        await loadStudentSubjects(studentToken, studentId);
        await loadStudentNotifications(studentToken);
      }
    } catch (err) {
      setStudentLoginError(err instanceof Error ? err.message : "Không đổi được mật khẩu.");
    }
  }

  // Calculate target grade
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

  // Lecturer Login & Upload
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
      if (!loginResp.ok) throw new Error("Đăng nhập giảng viên thất bại.");

      const meResp = await fetch(`${API_BASE}/auth/me`, {
        headers: { Authorization: `Bearer ${loginData.access_token}` },
      });
      const me = await meResp.json();
      if (!meResp.ok || me.role !== "lecturer") throw new Error("Tài khoản này không có quyền giảng viên.");

      setLecturerToken(loginData.access_token);
      setLecturerName(me.full_name);
      setShowLoginModal(false);
    } catch (err) {
      setLecturerError(err instanceof Error ? err.message : "Đăng nhập giảng viên thất bại.");
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
        throw new Error(detail || "Định dạng tệp tin hoặc dữ liệu không hợp lệ.");
      }
      
      const runId = data.databricks_run_id;
      const recordsProcessed = data.records_processed ?? 0;
      const syncedRows = data.db_synced ?? recordsProcessed;
      
      if (data.pipeline_status === "RUNNING" && runId) {
        setUploadStatus(`Đã gửi tệp thành công. Đang khởi chạy Databricks Pipeline (Run ID: ${runId})... Vui lòng chờ...`);
        
        // Polling loop
        const pollInterval = setInterval(async () => {
          try {
            const statusResp = await fetch(`${API_BASE}/upload/status/${runId}`, {
              headers: { Authorization: `Bearer ${lecturerToken}` }
            });
            if (!statusResp.ok) return;
            const statusData = await statusResp.json();
            
            if (statusData.status === "SUCCESS") {
              clearInterval(pollInterval);
              setUploadStatus(
                `Đồng bộ Delta Lake thành công! Đã xử lý ${recordsProcessed} dòng. Đồng bộ: ${syncedRows} dòng.`
              );
              setIsUploading(false);
              loadLecturerDashboard();
              if (selectedLecturerCourseId) {
                loadLecturerGrades(selectedLecturerCourseId);
              }
            } else if (statusData.status === "FAILED") {
              clearInterval(pollInterval);
              setUploadError(`Databricks Pipeline thất bại: ${statusData.message || "Lỗi không xác định."}`);
              setIsUploading(false);
            } else {
              setUploadStatus(`Đang chạy Databricks Pipeline (Trạng thái: ${statusData.life_cycle_state || "RUNNING"})...`);
            }
          } catch (e) {
            console.error("Lỗi khi kiểm tra trạng thái Databricks:", e);
          }
        }, 3000);
      } else {
        setUploadStatus(
          `Đã nạp thành công: Xử lý ${recordsProcessed} dòng. Đồng bộ: ${syncedRows} dòng.`
        );
        setIsUploading(false);
        loadLecturerDashboard();
        if (selectedLecturerCourseId) {
          loadLecturerGrades(selectedLecturerCourseId);
        }
      }
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : "Đã có lỗi xảy ra khi tải điểm.");
      setIsUploading(false);
    }
  }


  async function loadLecturerDashboard(tokenOverride?: string) {
    const token = tokenOverride || lecturerToken;
    if (!token) return;
    setIsLecturerLoading(true);
    setLecturerError(null);
    try {
      const headers = { Authorization: `Bearer ${token}` };
      const resp = await fetch(`${API_BASE}/lecturer/courses`, { headers });
      const data = await resp.json();
      if (!resp.ok) throw new Error(data.detail || "Không tải được danh sách môn học.");
      const courses = data.courses || [];
      setLecturerCourses(courses);
      if (courses.length > 0) {
        setSelectedLecturerCourseId(courses[0].ma_mon);
      }
    } catch (err) {
      setLecturerError(err instanceof Error ? err.message : "Lỗi tải dữ liệu giảng viên.");
    } finally {
      setIsLecturerLoading(false);
    }
  }

  async function loadLecturerGrades(courseId: string) {
    if (!lecturerToken || !courseId) return;
    setIsLecturerLoading(true);
    try {
      const headers = { Authorization: `Bearer ${lecturerToken}` };
      const resp = await fetch(`${API_BASE}/lecturer/grades/${courseId}`, { headers });
      const data = await resp.json();
      if (!resp.ok) throw new Error(data.detail || "Không tải được bảng điểm môn học.");
      setLecturerGrades(data.grades || []);
    } catch (err) {
      setLecturerError(err instanceof Error ? err.message : "Lỗi tải bảng điểm.");
    } finally {
      setIsLecturerLoading(false);
    }
  }

  // Effect to load lecturer grades when course changes
  useEffect(() => {
    if (lecturerToken && selectedLecturerCourseId) {
      loadLecturerGrades(selectedLecturerCourseId);
    }
  }, [lecturerToken, selectedLecturerCourseId]);

  async function lecturerUpdateGrade(studentId: string, maMon: string) {
    if (!lecturerToken) return;
    setIsLecturerLoading(true);
    try {
      const diem_thong_thuong = editGradeRegular.split(/[;,]/).map(x => x.trim()).filter(Boolean).map(Number);
      const diem_giua_ky = editGradeMidterm !== "" ? Number(editGradeMidterm) : null;
      const diem_cuoi_ky = editGradeFinal !== "" ? Number(editGradeFinal) : null;

      const currentStudent = lecturerGrades.find(g => g.student_id === studentId);
      const loaiHp = currentStudent?.loai_hoc_phan || "ly_thuyet";

      let diem_thuc_hanh_hien_tai: number[] = [];
      let diem_thuc_hanh_tich_hop: number | null = null;

      if (loaiHp === "tich_hop") {
        if (editGradePractice1 !== "") {
          diem_thuc_hanh_tich_hop = Number(editGradePractice1);
          diem_thuc_hanh_hien_tai = [diem_thuc_hanh_tich_hop];
        }
      } else if (loaiHp === "thuc_hanh") {
        const scores = [editGradePractice1, editGradePractice2, editGradePractice3]
          .map(x => x.trim())
          .filter(Boolean)
          .map(Number);
        diem_thuc_hanh_hien_tai = scores;
      }

      const body: any = {
        reason: editGradeReason
      };
      if (diem_thong_thuong.length > 0) body.diem_thong_thuong = diem_thong_thuong;
      if (diem_giua_ky !== null) body.diem_giua_ky = diem_giua_ky;
      if (diem_cuoi_ky !== null) body.diem_cuoi_ky = diem_cuoi_ky;
      if (loaiHp === "tich_hop") {
        if (diem_thuc_hanh_tich_hop !== null) body.diem_thuc_hanh_tich_hop = diem_thuc_hanh_tich_hop;
        if (diem_thuc_hanh_hien_tai.length > 0) body.diem_thuc_hanh_hien_tai = diem_thuc_hanh_hien_tai;
      } else if (loaiHp === "thuc_hanh") {
        if (diem_thuc_hanh_hien_tai.length > 0) body.diem_thuc_hanh_hien_tai = diem_thuc_hanh_hien_tai;
      }

      const resp = await fetch(`${API_BASE}/lecturer/grades/${studentId}/${maMon}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${lecturerToken}`
        },
        body: JSON.stringify(body)
      });
      const data = await resp.json();
      if (!resp.ok) throw new Error(data.detail || "Không thể cập nhật điểm sinh viên.");
      setUploadStatus(`Cập nhật điểm thành công cho SV ${studentId}.`);
      setEditingGradeRow(null);
      if (selectedLecturerCourseId) {
        await loadLecturerGrades(selectedLecturerCourseId);
      }
    } catch (err) {
      setLecturerError(err instanceof Error ? err.message : "Không sửa được điểm.");
    } finally {
      setIsLecturerLoading(false);
    }
  }

  async function lecturerDeleteGrade(studentId: string, maMon: string) {
    if (!lecturerToken) return;
    if (!window.confirm(`Bạn có chắc muốn xóa điểm môn này của sinh viên ${studentId}?`)) return;
    setIsLecturerLoading(true);
    try {
      const resp = await fetch(`${API_BASE}/lecturer/grades/${studentId}/${maMon}`, {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${lecturerToken}`
        }
      });
      const data = await resp.json();
      if (!resp.ok) throw new Error(data.detail || "Không thể xóa điểm sinh viên.");
      setUploadStatus(`Xóa điểm thành công cho SV ${studentId}.`);
      if (selectedLecturerCourseId) {
        await loadLecturerGrades(selectedLecturerCourseId);
      }
    } catch (err) {
      setLecturerError(err instanceof Error ? err.message : "Không xóa được điểm.");
    } finally {
      setIsLecturerLoading(false);
    }
  }

  // Student calculator local algorithm (individual inputs)
  function runLocalCalculation() {
    let finalScore = 0;
    let message = "";
    let isPass = true;

    try {
      const parseVal = (val: string) => {
        if (!val || !val.trim()) return null;
        const n = Number(val.trim());
        if (isNaN(n) || n < 0 || n > 10) throw new Error("Điểm số phải nằm trong khoảng 0.0 - 10.0");
        return n;
      };

      if (calcType === "ly_thuyet") {
        // Collect TX scores
        const txs = [tx1Input, tx2Input, tx3Input, tx4Input].map(parseVal).filter((x): x is number => x !== null);
        const gk = parseVal(gkInput);
        const ck = parseVal(ckInput);

        if (gk === null || ck === null) {
          throw new Error("Vui lòng nhập đầy đủ điểm Giữa kỳ và Cuối kỳ.");
        }
        if (txs.length === 0) {
          throw new Error("Vui lòng nhập ít nhất một đầu điểm Thường kỳ (TX).");
        }

        const txAvg = txs.reduce((a, b) => a + b, 0) / txs.length;
        finalScore = txAvg * 0.2 + gk * 0.3 + ck * 0.5;
        isPass = finalScore >= 4.0 && ck >= 3.0;
        if (ck < 3.0) {
          message = "Rất tiếc! Bạn bị điểm liệt thi cuối kỳ (< 3.0). Kết quả: KHÔNG ĐẠT (F).";
        } else {
          message = isPass ? "Chúc mừng! Bạn đã đạt học phần này." : "Rất tiếc! Điểm tổng kết dưới 4.0, bạn phải học lại học phần này.";
        }
      } else if (calcType === "thuc_hanh") {
        const ths = [th1Input, th2Input, th3Input, th4Input].map(parseVal).filter((x): x is number => x !== null);
        if (ths.length === 0) {
          throw new Error("Vui lòng nhập ít nhất một đầu điểm Thực hành (TH).");
        }
        finalScore = ths.reduce((a, b) => a + b, 0) / ths.length;
        const hasLieth = ths.some(s => s < 3.0);
        isPass = finalScore >= 4.0 && !hasLieth;
        if (hasLieth) {
          isPass = false;
          message = "Bạn bị điểm liệt thực hành (có buổi < 3.0). Kết quả: KHÔNG ĐẠT (F).";
        } else {
          message = isPass ? "Chúc mừng! Bạn đã đạt học phần thực hành." : "Rất tiếc! Điểm trung bình thực hành dưới 4.0.";
        }
      } else { // tich_hop
        const txs = [tx1Input, tx2Input, tx3Input, tx4Input].map(parseVal).filter((x): x is number => x !== null);
        const gk = parseVal(gkInput);
        const ck = parseVal(ckInput);
        const ths = [th1Input, th2Input, th3Input, th4Input].map(parseVal).filter((x): x is number => x !== null);

        if (gk === null || ck === null || ths.length === 0) {
          throw new Error("Vui lòng nhập đầy đủ điểm Giữa kỳ LT, Cuối kỳ LT và ít nhất một điểm Thực hành.");
        }
        if (txs.length === 0) {
          throw new Error("Vui lòng nhập ít nhất một đầu điểm Thường kỳ LT.");
        }

        const txAvg = txs.reduce((a, b) => a + b, 0) / txs.length;
        const lt_score = txAvg * 0.2 + gk * 0.3 + ck * 0.5;
        const thAvg = ths.reduce((a, b) => a + b, 0) / ths.length;
        
        finalScore = (lt_score * 2 + thAvg * 1) / 3;
        isPass = finalScore >= 4.0 && thAvg >= 3.0 && ck >= 3.0;
        
        if (thAvg < 3.0) {
          isPass = false;
          message = "CẢNH BÁO: Bạn bị điểm liệt phần thực hành (< 3.0). Kết quả: KHÔNG ĐẠT (F).";
        } else if (ck < 3.0) {
          isPass = false;
          message = "CẢNH BÁO: Bạn bị điểm liệt thi cuối kỳ lý thuyết (< 3.0). Kết quả: KHÔNG ĐẠT (F).";
        } else {
          message = isPass ? "Chúc mừng! Bạn đã đạt học phần tích hợp." : "Rất tiếc! Điểm tổng kết tích hợp dưới 4.0.";
        }
      }

      finalScore = Math.round(finalScore * 100) / 100;

      let letterGrade = "F";
      let system4Grade = 0.0;

      if (finalScore >= 9.0) {
        letterGrade = "A+";
        system4Grade = 4.0;
      } else if (finalScore >= 8.5) {
        letterGrade = "A";
        system4Grade = 3.8;
      } else if (finalScore >= 8.0) {
        letterGrade = "B+";
        system4Grade = 3.5;
      } else if (finalScore >= 7.0) {
        letterGrade = "B";
        system4Grade = 3.0;
      } else if (finalScore >= 6.0) {
        letterGrade = "C+";
        system4Grade = 2.5;
      } else if (finalScore >= 5.5) {
        letterGrade = "C";
        system4Grade = 2.0;
      } else if (finalScore >= 5.0) {
        letterGrade = "D+";
        system4Grade = 1.5;
      } else if (finalScore >= 4.0) {
        letterGrade = "D";
        system4Grade = 1.0;
      } else {
        letterGrade = "F";
        system4Grade = 0.0;
      }

      if (!isPass) {
        letterGrade = "F";
        system4Grade = 0.0;
      }

      setCalcResult({
        finalScore,
        letterGrade,
        system4Grade,
        isPass,
        message
      });
    } catch (err) {
      alert(err instanceof Error ? err.message : "Đã xảy ra lỗi khi tính toán.");
    }
  }

  // Add/Delete/Update dynamic rows for GPA (TBHK/TBTL)
  function addGpaRow() {
    setGpaRows([
      ...gpaRows,
      { id: Date.now(), name: `Môn ${gpaRows.length + 1}`, credits: 3, grade: "" },
    ]);
  }

  function deleteGpaRow(id: number) {
    if (gpaRows.length <= 1) return;
    setGpaRows(gpaRows.filter((r) => r.id !== id));
  }

  function updateGpaRow(id: number, field: "name" | "credits" | "grade", value: any) {
    setGpaRows(
      gpaRows.map((r) => {
        if (r.id === id) {
          return { ...r, [field]: value };
        }
        return r;
      })
    );
  }

  function calculateGpa() {
    try {
      const validRows = gpaRows.filter(
        (r) => r.credits > 0 && r.grade.trim() !== ""
      );

      if (validRows.length === 0) {
        throw new Error("Vui lòng nhập đầy đủ thông tin số tín chỉ và điểm số của ít nhất một môn học.");
      }

      let totalCredits = 0;
      let sumGpa10 = 0;
      let sumGpa4 = 0;

      validRows.forEach((r) => {
        const gradeVal = Number(r.grade);
        const creditsVal = Number(r.credits);

        if (isNaN(gradeVal) || gradeVal < 0 || gradeVal > 10) {
          throw new Error(`Môn '${r.name}': Điểm số phải nằm trong khoảng 0.0 - 10.0`);
        }
        if (isNaN(creditsVal) || creditsVal <= 0) {
          throw new Error(`Môn '${r.name}': Số tín chỉ phải lớn hơn 0`);
        }

        // Convert course score to System 4 (enforcing overall GPA > 1.50)
        let sys4 = 0;
        if (gradeVal >= 9.0) sys4 = 4.0;
        else if (gradeVal >= 8.5) sys4 = 3.8;
        else if (gradeVal >= 8.0) sys4 = 3.5;
        else if (gradeVal >= 7.0) sys4 = 3.0;
        else if (gradeVal >= 6.0) sys4 = 2.5;
        else if (gradeVal >= 5.5) sys4 = 2.0;
        else if (gradeVal >= 5.0) sys4 = 1.5;
        else if (gradeVal >= 4.0) sys4 = 1.0;
        else sys4 = 0.0;

        totalCredits += creditsVal;
        sumGpa10 += gradeVal * creditsVal;
        sumGpa4 += sys4 * creditsVal;
      });

      const gpa10 = Math.round((sumGpa10 / totalCredits) * 100) / 100;
      const gpa4 = Math.round((sumGpa4 / totalCredits) * 100) / 100;

      let letterGrade = "F";
      let classification = "Yếu";

      if (gpa4 >= 3.6) {
        letterGrade = "A";
        classification = "Xuất sắc";
      } else if (gpa4 >= 3.2) {
        letterGrade = "B+";
        classification = "Giỏi";
      } else if (gpa4 >= 2.5) {
        letterGrade = "B";
        classification = "Khá";
      } else if (gpa4 >= 2.0) {
        letterGrade = "C";
        classification = "Trung bình";
      } else if (gpa4 >= 1.0) {
        letterGrade = "D";
        classification = "Trung bình yếu";
      } else {
        letterGrade = "F";
        classification = "Kém";
      }

      setGpaResult({
        totalCredits,
        gpa10,
        gpa4,
        letterGrade,
        classification,
      });
    } catch (err) {
      alert(err instanceof Error ? err.message : "Lỗi tính toán GPA.");
    }
  }

  // Admin Student CRUD
  async function createStudent() {
    try {
      await adminFetch("/admin/students", {
        method: "POST",
        body: JSON.stringify({
          student_id: newStudentId,
          email: newStudentEmail,
          password: "Sv@123",
          full_name: newStudentName,
          faculty_id: newStudentFaculty,
          major_id: newStudentMajor,
          lop_hoc: newStudentClass,
        }),
      });
      setAdminStatus(`Đã tạo thành công sinh viên ${newStudentName} (Mã: ${newStudentId}).`);
      setNewStudentId("");
      setNewStudentEmail("");
      setNewStudentName("");
      await loadAdminDashboard();
    } catch (err) {
      setAdminError(err instanceof Error ? err.message : "Không tạo được sinh viên.");
    }
  }

  async function handleUpdateStudent(id: string, email: string, name: string) {
    try {
      await adminFetch(`/admin/students/${id}`, {
        method: "PUT",
        body: JSON.stringify({
          email,
          full_name: name,
        }),
      });
      setAdminStatus(`Đã cập nhật sinh viên ${name}.`);
      setEditingStudent(null);
      await loadAdminDashboard();
    } catch (err) {
      setAdminError(err instanceof Error ? err.message : "Không cập nhật được sinh viên.");
    }
  }

  async function handleDeleteStudent(id: string) {
    if (!id) return;
    if (!window.confirm(`Bạn có chắc muốn xóa sinh viên ${id}?`)) return;
    try {
      await adminFetch(`/admin/students/${id}`, { method: "DELETE" });
      setAdminStatus(`Đã xóa sinh viên mã ${id}.`);
      await loadAdminDashboard();
    } catch (err) {
      setAdminError(err instanceof Error ? err.message : "Không xóa được sinh viên.");
    }
  }

  // Admin Course CRUD
  async function createCourse() {
    try {
      await adminFetch("/admin/courses", {
        method: "POST",
        body: JSON.stringify({
          id: newCourseId,
          name: newCourseName,
          type: newCourseType,
          credits: Number(newCourseCredits),
          chi_lt: newCourseType === "ly_thuyet" ? Number(newCourseCredits) : 0,
          chi_th: newCourseType === "thuc_hanh" ? Number(newCourseCredits) : 0,
        }),
      });
      setAdminStatus(`Đã tạo môn học ${newCourseName} (${newCourseId}) thành công.`);
      setNewCourseId("");
      setNewCourseName("");
      await loadAdminDashboard();
    } catch (err) {
      setAdminError(err instanceof Error ? err.message : "Không tạo được môn học.");
    }
  }

  async function handleUpdateCourse(id: string, name: string, type: string, credits: number) {
    try {
      await adminFetch(`/admin/courses/${id}`, {
        method: "PUT",
        body: JSON.stringify({
          id,
          name,
          type,
          credits: Number(credits),
          chi_lt: type === "ly_thuyet" ? Number(credits) : 0,
          chi_th: type === "thuc_hanh" ? Number(credits) : 0,
        }),
      });
      setAdminStatus(`Đã cập nhật môn học ${name}.`);
      setEditingCourse(null);
      await loadAdminDashboard();
    } catch (err) {
      setAdminError(err instanceof Error ? err.message : "Không cập nhật được môn học.");
    }
  }

  async function handleDeleteCourse(id: string) {
    if (!id) return;
    if (!window.confirm(`Bạn có chắc muốn xóa môn học ${id}?`)) return;
    try {
      await adminFetch(`/admin/courses/${id}`, { method: "DELETE" });
      setAdminStatus(`Đã xóa môn học ${id}.`);
      await loadAdminDashboard();
    } catch (err) {
      setAdminError(err instanceof Error ? err.message : "Không xóa được môn học.");
    }
  }

  // Admin Assignment CRUD
  async function createAssignment() {
    try {
      await adminFetch("/admin/assignments", {
        method: "POST",
        body: JSON.stringify({
          lecturer_id: assignLecturerId,
          ma_mon: assignCourseId,
          ma_lop: assignClassId,
        }),
      });
      setAdminStatus(`Đã phân công giảng viên ${assignLecturerId} cho môn ${assignCourseId}.`);
      await loadAdminDashboard();
    } catch (err) {
      setAdminError(err instanceof Error ? err.message : "Không phân công được giảng viên.");
    }
  }

  async function handleDeleteAssignment(id: string) {
    if (!id) return;
    if (!window.confirm(`Bạn có chắc muốn xóa phân công này?`)) return;
    try {
      await adminFetch(`/admin/assignments/${id}`, { method: "DELETE" });
      setAdminStatus(`Đã xóa phân công.`);
      await loadAdminDashboard();
    } catch (err) {
      setAdminError(err instanceof Error ? err.message : "Không xóa được phân công.");
    }
  }

  // Helper for admin fetch requests
  async function adminFetch(path: string, options: RequestInit = {}) {
    if (!adminToken) throw new Error("Chưa đăng nhập vai trò Quản trị viên.");
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
      throw new Error(detail || "Hành động thất bại.");
    }
    return data;
  }

  // Load Admin Dashboard
  async function loadAdminDashboard(tokenOverride?: string) {
    const token = tokenOverride || adminToken;
    if (!token) return;
    setIsAdminBusy(true);
    setAdminError(null);
    try {
      const headers = { Authorization: `Bearer ${token}` };
      const [overview, timeline, users, warnings, rules, courses, assignments] = await Promise.all([
        fetch(`${API_BASE}/admin/overview`, { headers }).then((r) => r.json()),
        fetch(`${API_BASE}/admin/timeline`, { headers }).then((r) => r.json()),
        fetch(`${API_BASE}/admin/users`, { headers }).then((r) => r.json()),
        fetch(`${API_BASE}/admin/warnings`, { headers }).then((r) => r.json()),
        fetch(`${API_BASE}/admin/grading-rules`, { headers }).then((r) => r.json()),
        fetch(`${API_BASE}/admin/courses`, { headers }).then((r) => r.json()),
        fetch(`${API_BASE}/admin/assignments`, { headers }).then((r) => r.json()),
      ]);
      setAdminOverview(overview);
      setAdminTimeline(Array.isArray(timeline) ? timeline : []);
      setAdminUsers(Array.isArray(users) ? users : []);

      setAdminWarnings(Array.isArray(warnings) ? warnings : []);
      setGradingRules(rules);
      setAdminCourses(Array.isArray(courses) ? courses : []);
      setAdminAssignments(Array.isArray(assignments) ? assignments : []);
    } catch (err) {
      setAdminError(err instanceof Error ? err.message : "Không tải được dữ liệu quản trị.");
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
      if (!loginResp.ok) throw new Error("Đăng nhập admin thất bại.");

      const meResp = await fetch(`${API_BASE}/auth/me`, {
        headers: { Authorization: `Bearer ${loginData.access_token}` },
      });
      const me = await meResp.json();
      if (!meResp.ok || me.role !== "admin") throw new Error("Tài khoản này không phải quản trị viên.");

      setAdminToken(loginData.access_token);
      setAdminName(me.full_name);
      setAdminStatus("Đăng nhập quản trị viên thành công.");
      await loadAdminDashboard(loginData.access_token);
      setShowLoginModal(false);
    } catch (err) {
      setAdminError(err instanceof Error ? err.message : "Đăng nhập quản trị viên thất bại.");
    } finally {
      setIsAdminBusy(false);
    }
  }


  // Admin add timeline updates
  async function addTimeline() {
    try {
      await adminFetch("/admin/timeline", {
        method: "POST",
        body: JSON.stringify({ title: timelineTitle, category: "admin", details: timelineDetails }),
      });
      setAdminStatus("Lưu tin tức timeline thành công.");
      await loadAdminDashboard();
    } catch (err) {
      setAdminError(err instanceof Error ? err.message : "Không lưu được timeline.");
    }
  }

  // Admin update rules
  async function updateGradingRules() {
    try {
      await adminFetch("/admin/grading-rules", {
        method: "PUT",
        body: JSON.stringify({ version: "v2026.06", practice_min_pass: 3.0 }),
      });
      setAdminStatus("Cập nhật quy chế tính điểm (Điểm liệt Thực hành: 3.0) thành công.");
      await loadAdminDashboard();
    } catch (err) {
      setAdminError(err instanceof Error ? err.message : "Không cập nhật được quy chế.");
    }
  }

  const selectedResult = useMemo(
    () => results.find((item) => item.ma_mon === selectedCourseId) ?? null,
    [results, selectedCourseId],
  );

  const summary = useMemo(() => {
    const total = results.length;
    const warning = results.filter((item) => item.status_canh_bao !== "An toan").length;
    const best = results
      .filter((item) => item.prediction?.is_kha_thi)
      .sort((a, b) => (a.prediction?.diem_can_dat || 10) - (b.prediction?.diem_can_dat || 10))[0];
    return { total, warning, best };
  }, [results]);

  const activeNotificationCount = useMemo(
    () => studentNotifications.filter((n) => !n.is_read).length,
    [studentNotifications]
  );

  // Group subjects by semester
  const coursesBySemester = useMemo(() => {
    const grouped: Record<number, StudentLookupResult[]> = {};
    results.forEach((r) => {
      const hk = r.hoc_ky || 1;
      if (!grouped[hk]) grouped[hk] = [];
      grouped[hk].push(r);
    });
    return grouped;
  }, [results]);

  const allSemesters = useMemo(() => Object.keys(coursesBySemester).map(Number).sort((a, b) => a - b), [coursesBySemester]);

  // GPA calculations: only courses with diem_tong_ket != null and ket qua != "Hoc lai"
  const gpaStats = useMemo(() => {
    const passed = results.filter((r) => r.diem_tong_ket != null && r.diem_tong_ket >= 4.0);
    const totalCredits = passed.reduce((acc, r) => acc + (r.tong_so_chi || 0), 0);
    const sumGpa10 = passed.reduce((acc, r) => acc + (r.diem_tong_ket || 0) * (r.tong_so_chi || 0), 0);
    const sumGpa4 = passed.reduce((acc, r) => acc + (r.diem_he_4 || 0) * (r.tong_so_chi || 0), 0);
    const gpa10 = totalCredits > 0 ? Math.round((sumGpa10 / totalCredits) * 100) / 100 : 0;
    const gpa4 = totalCredits > 0 ? Math.round((sumGpa4 / totalCredits) * 100) / 100 : 0;
    const totalRegistered = results.reduce((acc, r) => acc + (r.tong_so_chi || 0), 0);
    return { totalCredits, totalRegistered, gpa10, gpa4 };
  }, [results]);

  // Courses in selected semester for simulation
  const coursesInSemester = useMemo(
    () => (coursesBySemester[predictSemester] || []),
    [coursesBySemester, predictSemester]
  );

  // Lecturer: filter courses
  const filteredLecturerCourses = useMemo(() => {
    if (!lecturerCourseSearch.trim()) return lecturerCourses;
    const query = lecturerCourseSearch.toLowerCase().trim();
    return lecturerCourses.filter(
      (c) =>
        c.ten_mon?.toLowerCase().includes(query) ||
        c.ma_mon?.toLowerCase().includes(query) ||
        c.ma_lop?.toLowerCase().includes(query)
    );
  }, [lecturerCourses, lecturerCourseSearch]);

  // Lecturer: Vietnamese sorting helpers for grade list
  const getLastNameForSorting = (fullName: string): string => {
    if (!fullName) return "";
    const parts = fullName.trim().split(/\s+/);
    return parts[parts.length - 1] || "";
  };

  const compareVietnameseNames = (nameA: string, nameB: string): number => {
    const a = nameA || "";
    const b = nameB || "";
    const lastA = getLastNameForSorting(a);
    const lastB = getLastNameForSorting(b);
    const cmp = lastA.localeCompare(lastB, "vi", { sensitivity: "accent" });
    if (cmp !== 0) return cmp;
    return a.localeCompare(b, "vi", { sensitivity: "accent" });
  };

  // Lecturer: filter and sort grades list
  const filteredAndSortedGrades = useMemo(() => {
    let result = [...lecturerGrades];

    // Filter by student search query (student_id or ten_sv)
    if (lecturerStudentSearch.trim()) {
      const q = lecturerStudentSearch.toLowerCase().trim();
      result = result.filter(
        (g) =>
          g.student_id?.toLowerCase().includes(q) ||
          g.ten_sv?.toLowerCase().includes(q)
      );
    }

    // Sort by name if toggle is active
    if (sortByStudentName) {
      result.sort((a, b) => compareVietnameseNames(a.ten_sv, b.ten_sv));
    }

    return result;
  }, [lecturerGrades, lecturerStudentSearch, sortByStudentName]);

  const maxPracticeScores = useMemo(() => {
    const firstGrade = filteredAndSortedGrades[0];
    if (!firstGrade || firstGrade.loai_hoc_phan !== "thuc_hanh") return 0;
    let maxLen = 0;
    for (const g of filteredAndSortedGrades) {
      if (g.diem_thuc_hanh_hien_tai && g.diem_thuc_hanh_hien_tai.length > maxLen) {
        maxLen = g.diem_thuc_hanh_hien_tai.length;
      }
    }
    return maxLen || 3;
  }, [filteredAndSortedGrades]);

  const isLoggedIn = !!(studentToken || lecturerToken || adminToken);

  function handleLogout() {
    setStudentToken(null);
    setLecturerToken(null);
    setAdminToken(null);
    setResults([]);
    setLecturerCourses([]);
    setLecturerGrades([]);
    setAdminOverview(null);
    setAdminUsers([]);
    setAdminCourses([]);
    setAdminAssignments([]);
    setStudentName(null);
    setLecturerName(null);
    setAdminName(null);
    localStorage.clear();
  }

  // Save sessions to localStorage to persist across refreshes (F5)
  useEffect(() => {
    localStorage.setItem("activeTab", activeTab);
  }, [activeTab]);

  useEffect(() => {
    if (studentToken) {
      localStorage.setItem("studentToken", studentToken);
    } else {
      localStorage.removeItem("studentToken");
    }
  }, [studentToken]);

  useEffect(() => {
    if (studentName) {
      localStorage.setItem("studentName", studentName);
    } else {
      localStorage.removeItem("studentName");
    }
  }, [studentName]);

  useEffect(() => {
    if (studentId) {
      localStorage.setItem("studentId", studentId);
    } else {
      localStorage.removeItem("studentId");
    }
  }, [studentId]);

  useEffect(() => {
    localStorage.setItem("studentMustChangePassword", String(studentMustChangePassword));
  }, [studentMustChangePassword]);

  useEffect(() => {
    if (lecturerToken) {
      localStorage.setItem("lecturerToken", lecturerToken);
    } else {
      localStorage.removeItem("lecturerToken");
    }
  }, [lecturerToken]);

  useEffect(() => {
    if (lecturerName) {
      localStorage.setItem("lecturerName", lecturerName);
    } else {
      localStorage.removeItem("lecturerName");
    }
  }, [lecturerName]);

  useEffect(() => {
    if (adminToken) {
      localStorage.setItem("adminToken", adminToken);
    } else {
      localStorage.removeItem("adminToken");
    }
  }, [adminToken]);

  useEffect(() => {
    if (adminName) {
      localStorage.setItem("adminName", adminName);
    } else {
      localStorage.removeItem("adminName");
    }
  }, [adminName]);

  // Auto load student subjects & notifications when logged in
  useEffect(() => {
    if (studentToken && studentId) {
      loadStudentSubjects(studentToken, studentId);
      loadStudentNotifications(studentToken);
    }
  }, [studentToken, studentId]);

  // Auto load admin dashboard when logged in
  useEffect(() => {
    if (adminToken) {
      loadAdminDashboard(adminToken);
    }
  }, [adminToken]);

  // Auto load lecturer courses when lecturer logged in
  useEffect(() => {
    if (lecturerToken) {
      loadLecturerDashboard();
    }
  }, [lecturerToken]);

  // Auto pre-fill admin assignment dropdown options
  useEffect(() => {
    if (adminToken && adminUsers.length > 0 && adminCourses.length > 0) {
      const firstLec = adminUsers.find(u => u.role === "lecturer")?.lecturer_id || "";
      const firstCourse = adminCourses[0]?.id || "";
      setAssignLecturerId(firstLec);
      setAssignCourseId(firstCourse);
    }
  }, [adminToken, adminUsers, adminCourses]);

  return (
    <main style={{ minHeight: "100vh", position: "relative" }}>
      {/* Dynamic Floating Navbar */}
      <nav className={`navbar ${isScrolled || isLoggedIn ? "scrolled" : ""}`}>
        <div className={isLoggedIn ? "nav-container-fluid" : "nav-container"}>
          <a href="#" className="logo">
            <i className="pi pi-graduation-cap"></i>
            <span>SmartGPA</span>
          </a>
          {!isLoggedIn ? (
            <div className="nav-links">
              <a href="#architecture">Kiến trúc</a>
              <a href="#features">Tính năng</a>
              <a href="#subject-data">Dữ liệu mẫu</a>
              <button onClick={() => setShowLoginModal(true)} className="btn btn-primary btn-sm" style={{ color: "#ffffff", border: "none", cursor: "pointer" }}>
                Vào Workspace
              </button>
            </div>
          ) : (
            <div className="nav-links" style={{ display: "flex", alignItems: "center", gap: "16px" }}>
              {activeTab === "student" && (
                <>
                  {/* Notifications bell */}
                  <div style={{ position: "relative" }}>
                    <button className="btn btn-ghost" onClick={() => setShowNotificationsDropdown(!showNotificationsDropdown)} style={{ position: "relative", padding: 8, borderRadius: "50%", background: "transparent", border: "none", cursor: "pointer", color: "var(--text-secondary)", display: "flex", alignItems: "center" }}>
                      <i className={`pi pi-bell ${activeNotificationCount > 0 ? "animate-swing" : ""}`} style={{ fontSize: 18 }}></i>
                      {activeNotificationCount > 0 && (
                        <span style={{ position: "absolute", top: 2, right: 2, background: "var(--color-primary)", color: "#fff", fontSize: 10, padding: "2px 5px", borderRadius: "50%", fontWeight: 700, lineHeight: 1 }}>
                          {activeNotificationCount}
                        </span>
                      )}
                    </button>
                    {showNotificationsDropdown && (
                      <div className="glass-card" style={{ position: "absolute", top: 40, right: 0, width: 320, zIndex: 1000, padding: 16, border: "1px solid var(--border-glass-glow)", background: "rgba(255, 255, 255, 0.95)", boxShadow: "0 10px 30px rgba(0,0,0,0.1)", borderRadius: "12px" }}>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12, borderBottom: "1px solid var(--border-glass)", paddingBottom: 8 }}>
                          <strong style={{ fontSize: 14 }}>Thông báo</strong>
                          {activeNotificationCount > 0 && (
                            <button className="btn btn-ghost btn-sm" onClick={readAllNotifications} style={{ padding: "2px 6px", fontSize: 11, cursor: "pointer" }}>Đánh dấu đã đọc tất cả</button>
                          )}
                        </div>
                        <div style={{ maxHeight: 250, overflowY: "auto", display: "flex", flexDirection: "column", gap: 8 }}>
                          {studentNotifications.length === 0 ? (
                            <p className="text-gray text-sm text-center" style={{ padding: 12 }}>Không có thông báo nào.</p>
                          ) : (
                            studentNotifications.map((noti) => (
                              <div key={noti.id} style={{ background: noti.is_read ? "transparent" : "rgba(232,93,117,0.04)", padding: 8, borderRadius: 8, borderLeft: noti.is_read ? "none" : "3px solid var(--color-primary)", textAlign: "left" }}>
                                <strong style={{ fontSize: 12, display: "block" }}>{noti.title}</strong>
                                <span style={{ fontSize: 11, color: "var(--text-secondary)", display: "block", marginTop: 2 }}>{noti.message}</span>
                                <span style={{ fontSize: 10, color: "var(--text-muted)", display: "block", marginTop: 4 }}>{noti.timestamp}</span>
                              </div>
                            ))
                          )}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Student Details */}
                  {studentName && (
                    <div className="nav-user-details" style={{ display: "flex", flexDirection: "column", alignItems: "flex-end" }}>
                      <span style={{ fontWeight: 600, fontSize: "14px", color: "var(--text-primary)", lineHeight: "1.2" }}>{studentName}</span>
                      <span style={{ fontSize: "11px", color: "var(--text-muted)", lineHeight: "1.2", marginTop: "2px" }}>
                        MSSV: <strong style={{ color: "var(--color-primary)" }}>{studentUsername}</strong> · Khoa học Dữ liệu
                      </span>
                    </div>
                  )}
                </>
              )}

              {activeTab === "lecturer" && lecturerName && (
                <div className="nav-user-details" style={{ display: "flex", flexDirection: "column", alignItems: "flex-end" }}>
                  <span style={{ fontWeight: 600, fontSize: "14px", color: "var(--text-primary)", lineHeight: "1.2" }}>{lecturerName}</span>
                  <span style={{ fontSize: "11px", color: "var(--text-muted)", lineHeight: "1.2", marginTop: "2px" }}>
                    Giảng viên · Khoa CNTT
                  </span>
                </div>
              )}

              {activeTab === "admin" && adminName && (
                <div className="nav-user-details" style={{ display: "flex", flexDirection: "column", alignItems: "flex-end" }}>
                  <span style={{ fontWeight: 600, fontSize: "14px", color: "var(--text-primary)", lineHeight: "1.2" }}>{adminName}</span>
                  <span style={{ fontSize: "11px", color: "var(--text-muted)", lineHeight: "1.2", marginTop: "2px" }}>
                    Quản trị viên
                  </span>
                </div>
              )}

              <span className="badge badge-info" style={{ textTransform: "uppercase", display: "inline-flex", alignItems: "center", background: "rgba(232, 93, 117, 0.1)", color: "var(--color-primary)", padding: "4px 10px", borderRadius: 20, fontSize: "11px", fontWeight: 600 }}>
                {activeTab === "student" ? "Sinh viên" : activeTab === "lecturer" ? "Giảng viên" : "Quản trị viên"}
              </span>
              <button className="btn btn-outline btn-sm" onClick={handleLogout} style={{ padding: "6px 12px", display: "flex", alignItems: "center", gap: "6px", fontSize: "12px", cursor: "pointer" }}>
                <i className="pi pi-sign-out" style={{ fontSize: "12px" }}></i>
                Đăng xuất
              </button>
            </div>
          )}
        </div>
      </nav>

      {!isLoggedIn && (
        <>
          {/* Hero Section */}
          <header className="hero container reveal">
            <div className="blob blob-1"></div>
            <div className="blob blob-2"></div>
            <div className="hero-perspective">
              <div className="hero-card-3d floating-slow">
                <h1 className="hero-title">
                  Hệ thống Phân tích & Giả lập<br />
                  <span className="gradient-text">Điểm số GPA Thông minh</span>
                </h1>
                <p className="hero-subtitle">
                  Sử dụng ngôn ngữ FastAPI, thuật toán tính ngược GPA và mô hình Học máy trên 
                  đám mây Databricks Delta Lake giúp theo dõi lộ trình học tập, cảnh báo điểm liệt 
                  và tối ưu hóa mục tiêu học thuật.
                </p>
                <div style={{ display: "flex", justifyContent: "center", gap: 14 }}>
                  <button onClick={() => setShowLoginModal(true)} className="btn-cta" style={{ border: "none", cursor: "pointer" }}>
                    Bắt đầu ngay
                    <i className="pi pi-arrow-right"></i>
                  </button>
                  <a href="#architecture" className="btn btn-outline" style={{ borderRadius: "50px", padding: "14px 28px" }}>
                    Tìm hiểu thêm
                  </a>
                </div>

                {/* Micro Connection Flows */}
                <div className="flow-line-container" style={{ marginTop: 40 }}>
                  <div className="flow-line"></div>
                </div>

                {/* Transparent Floating Mockup Dashboard */}
                <div className="glass-card mt-4 mx-auto" style={{ maxWidth: "600px", padding: "16px", borderRadius: "16px", opacity: 0.9 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: "12px", borderBottom: "1px solid var(--border-glass)", paddingBottom: "10px", marginBottom: "10px" }}>
                    <span className="text-gray"><i className="pi pi-server" style={{ marginRight: 6 }}></i>FastAPI Core Gateway</span>
                    <span className="badge badge-success"><i className="pi pi-check-circle" style={{ marginRight: 4 }}></i>Databricks Active</span>
                  </div>
                  <div style={{ display: "flex", gap: "12px", textAlign: "left" }}>
                    <div style={{ flex: 1, padding: "10px", background: "#ffffff", borderRadius: "8px" }}>
                      <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>Học phần chọn</span>
                      <p style={{ fontSize: "13px", fontWeight: 700, marginTop: "4px" }}>Cấu trúc dữ liệu & Giải thuật</p>
                    </div>
                    <div style={{ flex: 1, padding: "10px", background: "#ffffff", borderRadius: "8px" }}>
                      <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>Mục tiêu tối thiểu</span>
                      <p style={{ fontSize: "13px", fontWeight: 700, color: "var(--color-primary)", marginTop: "4px" }}>Mức điểm chữ A (CK ≥ 8.5)</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </header>

          {/* Architecture Section */}
          <section id="architecture" className="section container reveal">
            <div className="text-center mb-12">
              <div className="badge badge-info mb-4">Sơ đồ Công nghệ</div>
              <h2 style={{ fontSize: 32, fontFamily: "var(--font-heading)" }}>Kiến trúc SOA 3 Tầng hiện đại</h2>
              <p style={{ color: "var(--text-secondary)", maxWidth: "550px", margin: "8px auto 0 auto" }}>
                Trực quan hóa luồng dữ liệu xử lý điểm số khép kín của nền tảng qua 3 lớp xử lý chuyên biệt.
              </p>
            </div>
            <div className="grid grid-3">
              <div className="glass-card hover-float">
                <div className="icon-box">
                  <i className="pi pi-desktop"></i>
                </div>
                <h3 className="font-bold mb-4">1. Giao diện Presentation (React/Vite)</h3>
                <p className="text-gray text-sm">
                  Trang giao diện thiết kế Soft Pastel mộng mơ, bo góc mềm mại, glassmorphism sang trọng, bảo vệ mắt người dùng khi làm việc lâu.
                </p>
              </div>
              <div className="glass-card hover-float">
                <div className="icon-box">
                  <i className="pi pi-server"></i>
                </div>
                <h3 className="font-bold mb-4">2. API Gateway & Business Logic (FastAPI)</h3>
                <p className="text-gray text-sm">
                  Xử lý xác thực người dùng, giải mã phân quyền, thực thi thuật toán Simulation Engine tính điểm thi cần đạt thời gian thực.
                </p>
              </div>
              <div className="glass-card hover-float">
                <div className="icon-box">
                  <i className="pi pi-database"></i>
                </div>
                <h3 className="font-bold mb-4">3. Data & ML Platform (Databricks)</h3>
                <p className="text-gray text-sm">
                  Tổ chức kho dữ liệu Delta Lake (Bronze - Silver - Gold), thực hiện chuẩn hóa ETL và lưu vết lịch sử điểm số bảo mật.
                </p>
              </div>
            </div>
          </section>

          {/* Core Features Section */}
          <section id="features" className="section container reveal" style={{ background: "rgba(250, 246, 240, 0.5)", borderRadius: "24px", padding: "50px 24px" }}>
            <div className="text-center mb-12">
              <div className="badge badge-info mb-4">Tính năng cốt lõi</div>
              <h2 style={{ fontSize: 32, fontFamily: "var(--font-heading)" }}>Trải nghiệm Phân tích Học vụ thông minh</h2>
            </div>
            <div className="grid grid-3">
              <div className="glass-card hover-float">
                <div className="icon-box">
                  <i className="pi pi-calculator"></i>
                </div>
                <h3 className="font-bold mb-4">Inverse Calculation</h3>
                <p className="text-gray text-sm">
                  Tính ngược điểm thi cuối kỳ dựa trên các đầu điểm quá trình hiện tại. Hệ thống chỉ ra số điểm tối thiểu và tính khả thi mục tiêu học tập.
                </p>
              </div>
              <div className="glass-card hover-float">
                <div className="icon-box">
                  <i className="pi pi-list"></i>
                </div>
                <h3 className="font-bold mb-4">Quy chế 3 loại học phần</h3>
                <p className="text-gray text-sm">
                  Hệ thống xử lý tối ưu 3 quy chế tính điểm: Lý thuyết (LT 50%, CK 50%), Thực hành (trung bình các buổi), và Tích hợp LT & TH (LT điểm thi, TH điểm liệt &lt; 3.0).
                </p>
              </div>
              <div className="glass-card hover-float" style={{ border: "1.5px solid rgba(232, 93, 117, 0.25)", background: "rgba(255, 255, 255, 0.85)" }}>
                <div className="icon-box" style={{ background: "rgba(240, 167, 142, 0.12)", color: "var(--color-secondary)" }}>
                  <i className="pi pi-chart-line"></i>
                </div>
                <h3 className="font-bold mb-4" style={{ color: "var(--color-primary)" }}>ML Prediction</h3>
                <p className="text-gray text-sm">
                  Phát hiện sớm các sinh viên có nguy cơ rớt môn nhờ mô hình dự báo ngắt quãng. Tỷ lệ rớt môn trên 70% sẽ được cảnh báo đỏ đào/san hô nổi bật nhưng dịu mắt.
                </p>
              </div>
            </div>
          </section>

          {/* Subjects Data Section */}
          <section id="subject-data" className="section container reveal">
            <div className="text-center mb-8">
              <div className="badge badge-info mb-4">Bảng dữ liệu môn học</div>
              <h2 style={{ fontSize: 32, fontFamily: "var(--font-heading)" }}>Khung chương trình đào tạo mẫu</h2>
            </div>
            <div className="data-table-container">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Mã học phần</th>
                    <th>Tên môn học</th>
                    <th>Số tín chỉ</th>
                    <th>Loại hình</th>
                    <th>Trọng số lý thuyết / Quy chế</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td><strong>INT1306</strong></td>
                    <td>Cấu trúc dữ liệu & Giải thuật</td>
                    <td>3 TC</td>
                    <td>Lý thuyết</td>
                    <td>TK 20%, GK 30%, CK 50%</td>
                  </tr>
                  <tr>
                    <td><strong>INT1340</strong></td>
                    <td>Thực hành Hệ điều hành</td>
                    <td>2 TC</td>
                    <td>Thực hành</td>
                    <td>Trung bình các bài báo cáo thực hành (Liệt &lt; 3.0)</td>
                  </tr>
                  <tr>
                    <td><strong>INT1410</strong></td>
                    <td>Mạng máy tính</td>
                    <td>3 TC</td>
                    <td>Tích hợp (LT+TH)</td>
                    <td>Quy chế tính điểm tích hợp (TH hệ số tách biệt)</td>
                  </tr>
                  <tr>
                    <td><strong>GDQP102</strong></td>
                    <td>Giáo dục quốc phòng</td>
                    <td>3 TC</td>
                    <td>Lý thuyết</td>
                    <td>Môn học đặc thù tính điểm riêng biệt</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </section>
        </>
      )}

      {/* ─── LOGIN MODAL OVERLAY ─── */}
      {showLoginModal && !isLoggedIn && (
        <div
          style={{
            position: "fixed", inset: 0, zIndex: 9999,
            background: "rgba(30,20,40,0.55)", backdropFilter: "blur(8px)",
            display: "flex", alignItems: "center", justifyContent: "center", padding: 20,
          }}
          onClick={(e) => { if (e.target === e.currentTarget) setShowLoginModal(false); }}
        >
          <div className="glass-card glow-card" style={{
            width: "100%", maxWidth: 500, borderRadius: 24, padding: 36, position: "relative",
            border: "1.5px solid var(--border-glass-glow)", boxShadow: "0 24px 80px rgba(232,93,117,0.18)",
            animation: "fadeInUp 0.35s cubic-bezier(.4,0,.2,1)",
          }}>
            {/* Close */}
            <button onClick={() => setShowLoginModal(false)} style={{
              position: "absolute", top: 14, right: 14, background: "transparent", border: "none",
              cursor: "pointer", fontSize: 22, color: "var(--text-muted)", lineHeight: 1,
            }}><i className="pi pi-times" /></button>

            <div className="text-center mb-6">
              <div style={{ fontSize: 36, marginBottom: 8, color: "var(--primary)" }}>
                <i className="pi pi-graduation-cap" />
              </div>
              <h2 style={{ fontSize: 22, fontFamily: "var(--font-heading)", marginBottom: 4 }}>Đăng nhập SmartGPA</h2>
              <p className="text-gray text-sm">Chọn loại tài khoản để tiếp tục</p>
            </div>

            {/* Role Selector */}
            <div style={{ display: "flex", gap: 10, marginBottom: 24, justifyContent: "center" }}>
              <button
                className={`btn ${activeTab === "student" ? "btn-primary" : "btn-ghost"}`}
                onClick={() => setActiveTab("student")}
                style={{ borderRadius: 30, flex: 1 }}
              >
                <i className="pi pi-graduation-cap" style={{ marginRight: 6 }}></i>Sinh viên
              </button>
              <button
                className={`btn ${activeTab === "lecturer" ? "btn-primary" : "btn-ghost"}`}
                onClick={() => setActiveTab("lecturer")}
                style={{ borderRadius: 30, flex: 1 }}
              >
                <i className="pi pi-user-edit" style={{ marginRight: 6 }}></i>Giảng viên
              </button>
              <button
                className={`btn ${activeTab === "admin" ? "btn-primary" : "btn-ghost"}`}
                onClick={() => setActiveTab("admin")}
                style={{ borderRadius: 30, flex: 1 }}
              >
                <i className="pi pi-cog" style={{ marginRight: 6 }}></i>Admin
              </button>
            </div>

            {/* STUDENT login form */}
            {activeTab === "student" && (
              <div>
                <div className="form-group">
                  <label className="form-label">Mã số sinh viên (MSSV)</label>
                  <input className="form-control" type="text" value={studentUsername}
                    onChange={(e) => setStudentUsername(e.target.value.toUpperCase())}
                    placeholder="Ví dụ: 23695481" onKeyDown={(e) => e.key === "Enter" && loginStudent()} />
                </div>
                <div className="form-group">
                  <label className="form-label">Mật khẩu</label>
                  <input className="form-control" type="password" value={studentPassword}
                    onChange={(e) => setStudentPassword(e.target.value)}
                    placeholder="Mật khẩu mặc định: Sv@123" onKeyDown={(e) => e.key === "Enter" && loginStudent()} />
                </div>
                <button className="btn btn-primary" onClick={loginStudent} style={{ width: "100%", height: 46, marginTop: 4 }}>
                  <i className="pi pi-sign-in" style={{ marginRight: 8 }}></i>Đăng nhập Sinh viên
                </button>
                {studentLoginError && <div className="badge badge-danger mt-3" style={{ width: "100%", justifyContent: "center" }}>{studentLoginError}</div>}
                <div style={{ borderTop: "1px dashed var(--border-glass)", marginTop: 18, paddingTop: 14 }}>
                  <span className="text-gray text-sm font-bold" style={{ display: "block", marginBottom: 8 }}>Tài khoản demo:</span>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                    <button className="btn btn-ghost btn-sm" onClick={() => handleDemoLogin("student", "23723801", "Sv@123")} style={{ background: "#F2ECE4", fontSize: 12 }}>
                      La Thiên Bảo · 23723801
                    </button>
                    <button className="btn btn-ghost btn-sm" onClick={() => handleDemoLogin("student", "23695481", "Sv@123")} style={{ background: "#F2ECE4", fontSize: 12 }}>
                      Muhammad Arifil · 23695481
                    </button>
                    <button className="btn btn-ghost btn-sm" onClick={() => handleDemoLogin("student", "23703521", "Sv@123")} style={{ background: "#F2ECE4", fontSize: 12 }}>
                      Mai Văn Quân · 23703521
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* LECTURER login form */}
            {activeTab === "lecturer" && (
              <div>
                <div className="form-group">
                  <label className="form-label">Email Giảng viên</label>
                  <input className="form-control" type="text" value={lecturerEmail}
                    onChange={(e) => setLecturerEmail(e.target.value)}
                    placeholder="email@smartgpa.edu" onKeyDown={(e) => e.key === "Enter" && loginLecturer()} />
                </div>
                <div className="form-group">
                  <label className="form-label">Mật khẩu</label>
                  <input className="form-control" type="password" value={lecturerPassword}
                    onChange={(e) => setLecturerPassword(e.target.value)}
                    placeholder="Mật khẩu mặc định: Gv@123" onKeyDown={(e) => e.key === "Enter" && loginLecturer()} />
                </div>
                <button className="btn btn-primary" onClick={loginLecturer} disabled={isLecturerLoggingIn} style={{ width: "100%", height: 46, marginTop: 4 }}>
                  {isLecturerLoggingIn ? <span><i className="pi pi-spin pi-spinner" style={{ marginRight: 6 }}></i>Đang xử lý...</span> : <span><i className="pi pi-sign-in" style={{ marginRight: 8 }}></i>Đăng nhập Giảng viên</span>}
                </button>
                {lecturerError && <div className="badge badge-danger mt-3" style={{ width: "100%", justifyContent: "center" }}>{lecturerError}</div>}
                <div style={{ borderTop: "1px dashed var(--border-glass)", marginTop: 18, paddingTop: 14 }}>
                  <span className="text-gray text-sm font-bold" style={{ display: "block", marginBottom: 8 }}>Tài khoản demo:</span>
                  <button className="btn btn-ghost btn-sm" onClick={() => handleDemoLogin("lecturer", "thibinh.gv1001@smartgpa.edu", "Gv@123")} style={{ background: "#F2ECE4", fontSize: 12 }}>
                    TS. Trần Thị Bình · Gv@123
                  </button>
                </div>
              </div>
            )}

            {/* ADMIN login form */}
            {activeTab === "admin" && (
              <div>
                <div className="form-group">
                  <label className="form-label">Email Admin</label>
                  <input className="form-control" type="text" value={adminEmail}
                    onChange={(e) => setAdminEmail(e.target.value)}
                    placeholder="admin@smartgpa.edu" onKeyDown={(e) => e.key === "Enter" && loginAdmin()} />
                </div>
                <div className="form-group">
                  <label className="form-label">Mật khẩu</label>
                  <input className="form-control" type="password" value={adminPassword}
                    onChange={(e) => setAdminPassword(e.target.value)}
                    placeholder="Admin@123" onKeyDown={(e) => e.key === "Enter" && loginAdmin()} />
                </div>
                <button className="btn btn-primary" onClick={loginAdmin} disabled={isAdminBusy} style={{ width: "100%", height: 46, marginTop: 4 }}>
                  <i className="pi pi-sign-in" style={{ marginRight: 8 }}></i>Đăng nhập Admin
                </button>
                {adminError && <div className="badge badge-danger mt-3" style={{ width: "100%", justifyContent: "center" }}>{adminError}</div>}
                <div style={{ borderTop: "1px dashed var(--border-glass)", marginTop: 18, paddingTop: 14 }}>
                  <span className="text-gray text-sm font-bold" style={{ display: "block", marginBottom: 8 }}>Tài khoản demo:</span>
                  <button className="btn btn-ghost btn-sm" onClick={() => handleDemoLogin("admin", "admin@smartgpa.edu", "Admin@123")} style={{ background: "#F2ECE4", fontSize: 12 }}>
                    Hệ thống Admin · Admin@123
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ─── MAIN WORKSPACE (Visible when logged in) ─── */}
      {isLoggedIn && (
        <div className="workspace-layout">
          {/* Collapsible Left Sidebar */}
          <aside className={`sidebar ${sidebarCollapsed ? "collapsed" : ""}`}>
            <div className="sidebar-toggle" onClick={() => setSidebarCollapsed(!sidebarCollapsed)}>
              <i className={`pi ${sidebarCollapsed ? "pi-angle-right" : "pi-angle-left"}`}></i>
            </div>
            
            <div className="sidebar-header">
              <div className="sidebar-avatar">
                <i className="pi pi-user"></i>
              </div>
              <div className="sidebar-user-info">
                <strong>{activeTab === "student" ? studentName : activeTab === "lecturer" ? lecturerName : adminName}</strong>
                <span>{activeTab === "student" ? "Sinh viên" : activeTab === "lecturer" ? "Giảng viên" : "Quản trị viên"}</span>
              </div>
            </div>

            <div className="sidebar-divider"></div>

            <div className="sidebar-section-title">Chức năng chính</div>

            <nav className="sidebar-nav">
              {activeTab === "student" && (
                <>
                  <button className={`sidebar-item ${studentWorkspaceTab === "dashboard" ? "active" : ""}`} onClick={() => setStudentWorkspaceTab("dashboard")} title="Trang chủ">
                    <i className="pi pi-home sidebar-icon"></i>
                    <span className="sidebar-label">Trang chủ</span>
                  </button>
                  <button className={`sidebar-item ${studentWorkspaceTab === "curriculum" ? "active" : ""}`} onClick={() => setStudentWorkspaceTab("curriculum")} title="Chương trình khung">
                    <i className="pi pi-list sidebar-icon"></i>
                    <span className="sidebar-label">Chương trình khung</span>
                  </button>
                  <button className={`sidebar-item ${studentWorkspaceTab === "simulation" ? "active" : ""}`} onClick={() => setStudentWorkspaceTab("simulation")} title="Dự báo điểm">
                    <i className="pi pi-chart-line sidebar-icon"></i>
                    <span className="sidebar-label">Dự báo điểm</span>
                  </button>
                  <button className={`sidebar-item ${studentWorkspaceTab === "calculator" ? "active" : ""}`} onClick={() => setStudentWorkspaceTab("calculator")} title="Công cụ tính điểm">
                    <i className="pi pi-calculator sidebar-icon"></i>
                    <span className="sidebar-label">Công cụ tính điểm</span>
                  </button>
                </>
              )}

              {activeTab === "lecturer" && (
                <>
                  <button className={`sidebar-item ${lecturerWorkspaceTab === "courses" ? "active" : ""}`} onClick={() => setLecturerWorkspaceTab("courses")} title="Quản lý môn">
                    <i className="pi pi-book sidebar-icon"></i>
                    <span className="sidebar-label">Quản lý môn</span>
                  </button>
                  <button className={`sidebar-item ${lecturerWorkspaceTab === "grades" ? "active" : ""}`} onClick={() => setLecturerWorkspaceTab("grades")} title="Chỉnh sửa điểm">
                    <i className="pi pi-pencil sidebar-icon"></i>
                    <span className="sidebar-label">Chỉnh sửa điểm</span>
                  </button>
                  <button className={`sidebar-item ${lecturerWorkspaceTab === "upload" ? "active" : ""}`} onClick={() => setLecturerWorkspaceTab("upload")} title="Nạp điểm CSV/XLSX">
                    <i className="pi pi-upload sidebar-icon"></i>
                    <span className="sidebar-label">Nạp điểm CSV/XLSX</span>
                  </button>
                </>
              )}

              {activeTab === "admin" && (
                <>
                  <button className={`sidebar-item ${adminActiveSubTab === "warnings" ? "active" : ""}`} onClick={() => setAdminActiveSubTab("warnings")} title="Cảnh báo học vụ">
                    <i className="pi pi-exclamation-triangle sidebar-icon"></i>
                    <span className="sidebar-label">Cảnh báo học vụ</span>
                  </button>
                  <button className={`sidebar-item ${adminActiveSubTab === "students" ? "active" : ""}`} onClick={() => setAdminActiveSubTab("students")} title="Quản lý sinh viên">
                    <i className="pi pi-users sidebar-icon"></i>
                    <span className="sidebar-label">Quản lý sinh viên</span>
                  </button>

                  <button className={`sidebar-item ${adminActiveSubTab === "courses" ? "active" : ""}`} onClick={() => setAdminActiveSubTab("courses")} title="Quản lý môn học">
                    <i className="pi pi-bookmark sidebar-icon"></i>
                    <span className="sidebar-label">Quản lý môn học</span>
                  </button>
                  <button className={`sidebar-item ${adminActiveSubTab === "assignments" ? "active" : ""}`} onClick={() => setAdminActiveSubTab("assignments")} title="Phân công GV">
                    <i className="pi pi-link sidebar-icon"></i>
                    <span className="sidebar-label">Phân công GV</span>
                  </button>

                  <button className={`sidebar-item ${adminActiveSubTab === "rules" ? "active" : ""}`} onClick={() => setAdminActiveSubTab("rules")} title="Quy chế & Thang điểm">
                    <i className="pi pi-sliders-h sidebar-icon"></i>
                    <span className="sidebar-label">Quy chế & Thang điểm</span>
                  </button>
                  <button className={`sidebar-item ${adminActiveSubTab === "timeline" ? "active" : ""}`} onClick={() => setAdminActiveSubTab("timeline")} title="Timeline hoạt động">
                    <i className="pi pi-clock sidebar-icon"></i>
                    <span className="sidebar-label">Timeline hoạt động</span>
                  </button>
                </>
              )}
            </nav>

            <div className="sidebar-footer">
              <button className="sidebar-item" onClick={handleLogout} title="Đăng xuất" style={{ color: "var(--color-danger)" }}>
                <i className="pi pi-sign-out sidebar-icon"></i>
                <span className="sidebar-label">Đăng xuất</span>
              </button>
            </div>
          </aside>

          {/* Shifting Main Content Area */}
          <div className={`workspace-main ${sidebarCollapsed ? "sidebar-collapsed" : ""}`} style={{ paddingTop: 20 }}>
            <div className="glass-card glow-card" style={{ padding: "32px", borderRadius: "24px", minHeight: 500 }}>

          {/* 1. STUDENT WORKSPACE */}
          {activeTab === "student" && (
            <div>
              {/* Student header */}
              <div style={{ borderBottom: "1px solid var(--border-glass)", paddingBottom: 16, marginBottom: 20 }}>
                <h2 style={{ fontSize: "20px", fontWeight: 700, color: "var(--text-primary)", margin: 0 }}>
                  Trang chủ Sinh viên
                </h2>
                <p className="text-gray text-sm" style={{ marginTop: "4px", margin: 0 }}>
                  Chào mừng bạn quay trở lại, {studentName}. Hãy theo dõi kết quả học tập và giả lập lộ trình điểm số bên dưới.
                </p>
              </div>

              {/* Sub-tab nav */}
              <div style={{ display: "flex", gap: 8, marginBottom: 24, borderBottom: "1px solid var(--border-glass)", paddingBottom: 12 }}>
                {([
                  { id: "dashboard", label: "Trang chủ", icon: "pi-home" },
                  { id: "curriculum", label: "Chương trình khung", icon: "pi-list" },
                  { id: "simulation", label: "Dự báo điểm", icon: "pi-chart-line" },
                  { id: "calculator", label: "Công cụ tính điểm", icon: "pi-calculator" },
                ] as const).map((t) => (
                  <button
                    key={t.id}
                    className={`btn btn-sm ${studentWorkspaceTab === t.id ? "btn-primary" : "btn-ghost"}`}
                    onClick={() => setStudentWorkspaceTab(t.id)}
                    style={{ borderRadius: 20, display: "flex", alignItems: "center", gap: 6 }}
                  >
                    <i className={`pi ${t.icon}`} style={{ fontSize: 13 }} />
                    {t.label}
                  </button>
                ))}
              </div>

              {/* ── DASHBOARD TAB ── */}
              {studentWorkspaceTab === "dashboard" && (
                <div>
                  {studentMustChangePassword ? (
                    <div className="glass-card" style={{ maxWidth: 500, margin: "20px auto", padding: 24, border: "1.5px solid var(--border-glass-glow)" }}>
                      <h3 className="font-bold mb-4 text-center"><i className="pi pi-lock-open" style={{ marginRight: 8 }}></i>Đổi mật khẩu lần đầu</h3>
                      <p className="text-gray text-sm text-center mb-6">Bạn đang đăng nhập bằng mật khẩu mặc định. Hãy đổi mật khẩu để bảo mật tài khoản.</p>
                      <div className="form-group">
                        <label className="form-label">Email liên lạc</label>
                        <div style={{ display: "flex", gap: 10 }}>
                          <input className="form-control" type="email" value={studentEmail} onChange={(e) => setStudentEmail(e.target.value)} placeholder="email@gmail.com" />
                          <button className="btn btn-outline" onClick={requestStudentOtp} disabled={!studentEmail}>Nhận OTP</button>
                        </div>
                      </div>
                      <div className="form-group">
                        <label className="form-label">Mã OTP</label>
                        <input className="form-control" type="text" value={studentOtp} onChange={(e) => setStudentOtp(e.target.value)} placeholder="Nhập OTP từ email" />
                      </div>
                      <div className="form-group">
                        <label className="form-label">Mật khẩu mới</label>
                        <input className="form-control" type="password" value={studentNewPassword} onChange={(e) => setStudentNewPassword(e.target.value)} placeholder="Mật khẩu mới" />
                      </div>
                      <button className="btn btn-primary" onClick={changeStudentPassword} disabled={!studentOtp || !studentNewPassword} style={{ width: "100%", marginTop: 12 }}>Xác nhận & Cập nhật</button>
                    </div>
                  ) : (
                    <div>
                      {/* GPA Summary cards */}
                      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: 16, marginBottom: 28 }}>
                        <div style={{ background: "linear-gradient(135deg, var(--color-primary), #f7a8b8)", color: "#fff", borderRadius: 14, padding: "18px 20px" }}>
                          <p style={{ fontSize: 11, opacity: 0.85, marginBottom: 4 }}>TÍCH LŨY ĐÃ QUA</p>
                          <strong style={{ fontSize: 28 }}>{gpaStats.totalCredits}</strong>
                          <p style={{ fontSize: 11, opacity: 0.75, marginTop: 2 }}>tín chỉ</p>
                        </div>
                        <div style={{ background: "linear-gradient(135deg, #f9c784, #f7a46a)", color: "#fff", borderRadius: 14, padding: "18px 20px" }}>
                          <p style={{ fontSize: 11, opacity: 0.85, marginBottom: 4 }}>TỔNG ĐÃ ĐĂNG KÝ</p>
                          <strong style={{ fontSize: 28 }}>{gpaStats.totalRegistered}</strong>
                          <p style={{ fontSize: 11, opacity: 0.75, marginTop: 2 }}>tín chỉ</p>
                        </div>
                        <div style={{ background: "linear-gradient(135deg, #a8d8ea, #7ac7e0)", color: "#fff", borderRadius: 14, padding: "18px 20px" }}>
                          <p style={{ fontSize: 11, opacity: 0.85, marginBottom: 4 }}>GPA HỆ 10</p>
                          <strong style={{ fontSize: 28 }}>{gpaStats.gpa10}</strong>
                          <p style={{ fontSize: 11, opacity: 0.75, marginTop: 2 }}>trung bình tích lũy</p>
                        </div>
                        <div style={{ background: "linear-gradient(135deg, #b5ead7, #7dd9b6)", color: "#fff", borderRadius: 14, padding: "18px 20px" }}>
                          <p style={{ fontSize: 11, opacity: 0.85, marginBottom: 4 }}>GPA HỆ 4</p>
                          <strong style={{ fontSize: 28 }}>{gpaStats.gpa4}</strong>
                          <p style={{ fontSize: 11, opacity: 0.75, marginTop: 2 }}>trung bình tích lũy</p>
                        </div>
                        <div style={{ background: "var(--bg-primary)", border: "1px solid var(--border-glass)", borderRadius: 14, padding: "18px 20px" }}>
                          <p style={{ fontSize: 11, color: "var(--text-muted)", marginBottom: 4 }}>MÔN CẦN LƯƠ Ý</p>
                          <strong style={{ fontSize: 28, color: summary.warning > 0 ? "var(--color-danger)" : "var(--color-success)" }}>{summary.warning}</strong>
                          <p style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 2 }}>môn nguy cơ</p>
                        </div>
                      </div>

                      {/* Recent courses mini-table */}
                      {results.length > 0 && (
                        <div>
                          <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Các môn gần nhất</h4>
                          <div style={{ overflowX: "auto" }}>
                            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
                              <thead>
                                <tr style={{ background: "var(--bg-primary)" }}>
                                  <th style={{ padding: "8px 12px", textAlign: "left", fontWeight: 600 }}>Môn học</th>
                                  <th style={{ padding: "8px 12px", textAlign: "center" }}>HK</th>
                                  <th style={{ padding: "8px 12px", textAlign: "center" }}>Tín chỉ</th>
                                  <th style={{ padding: "8px 12px", textAlign: "center" }}>Thường xuyên</th>
                                  <th style={{ padding: "8px 12px", textAlign: "center" }}>Giữa kỳ</th>
                                  <th style={{ padding: "8px 12px", textAlign: "center" }}>Thực hành</th>
                                  <th style={{ padding: "8px 12px", textAlign: "center" }}>Cuối kỳ</th>
                                  <th style={{ padding: "8px 12px", textAlign: "center" }}>Tổng kết</th>
                                  <th style={{ padding: "8px 12px", textAlign: "center" }}>Chữ</th>
                                  <th style={{ padding: "8px 12px", textAlign: "center" }}>Tình trạng</th>
                                </tr>
                              </thead>
                              <tbody>
                                {results.slice(0, 8).map((r, i) => {
                                  const txDisplay = r.thuong_xuyen && r.thuong_xuyen.length > 0 ? r.thuong_xuyen.join(", ") : "-";
                                  const gkDisplay = r.giua_ky != null ? r.giua_ky : "-";
                                  
                                  let thDisplay = "-";
                                  if (r.loai_hoc_phan === "thuc_hanh" && r.thuc_hanh && r.thuc_hanh.length > 0) {
                                    thDisplay = r.thuc_hanh.join(", ");
                                  } else if (r.loai_hoc_phan === "tich_hop" && r.thuc_hanh_tich_hop != null) {
                                    thDisplay = r.thuc_hanh_tich_hop;
                                  } else if (r.thuc_hanh && r.thuc_hanh.length > 0) {
                                    thDisplay = r.thuc_hanh.join(", ");
                                  } else if (r.thuc_hanh_tich_hop != null) {
                                    thDisplay = r.thuc_hanh_tich_hop;
                                  }

                                  const ckDisplay = r.diem_cuoi_ky != null ? r.diem_cuoi_ky : "-";

                                  return (
                                    <tr key={i} style={{ borderTop: "1px solid var(--border-glass)" }}>
                                      <td style={{ padding: "8px 12px" }}>
                                        <strong style={{ fontSize: 13, display: "block", color: "var(--text-primary)" }}>{r.ten_mon}</strong>
                                        <span style={{ fontSize: 11, color: "var(--text-muted)" }}>{r.ma_mon}</span>
                                      </td>
                                      <td style={{ padding: "8px 12px", textAlign: "center" }}>HK{r.hoc_ky}</td>
                                      <td style={{ padding: "8px 12px", textAlign: "center" }}>{r.tong_so_chi}</td>
                                      <td style={{ padding: "8px 12px", textAlign: "center" }}>{txDisplay}</td>
                                      <td style={{ padding: "8px 12px", textAlign: "center" }}>{gkDisplay}</td>
                                      <td style={{ padding: "8px 12px", textAlign: "center" }}>{thDisplay}</td>
                                      <td style={{ padding: "8px 12px", textAlign: "center" }}>{ckDisplay}</td>
                                      <td style={{ padding: "8px 12px", textAlign: "center", fontWeight: 700 }}>
                                        {r.diem_tong_ket != null ? r.diem_tong_ket : <span style={{ color: "var(--text-muted)" }}>-</span>}
                                      </td>
                                      <td style={{ padding: "8px 12px", textAlign: "center", fontWeight: 600 }}>{r.diem_chu || "-"}</td>
                                      <td style={{ padding: "8px 12px", textAlign: "center" }}>
                                        <span className={`badge ${r.status_canh_bao === "An toan" ? "badge-success" : "badge-danger"}`} style={{ fontSize: 10, padding: "2px 8px" }}>
                                          {r.status_canh_bao === "An toan" ? "An toàn" : r.status_canh_bao}
                                        </span>
                                      </td>
                                    </tr>
                                  );
                                })}
                              </tbody>
                            </table>
                          </div>
                          {results.length > 8 && (
                            <p className="text-gray text-sm text-center" style={{ marginTop: 10 }}>
                              ... và {results.length - 8} môn khác. Xem toàn bộ trong tab “Chương trình khung”.
                            </p>
                          )}
                        </div>
                      )}
                      {results.length === 0 && (
                        <div className="text-center" style={{ padding: 40, color: "var(--text-muted)" }}>
                          <i className="pi pi-spin pi-spinner" style={{ fontSize: 32 }}></i>
                          <p style={{ marginTop: 12 }}>Đang tải dữ liệu học phần...</p>
                        </div>
                      )}
                    </div>
                  )}
                  {studentAccountStatus && <div className="badge badge-success mt-4" style={{ width: "100%", justifyContent: "center" }}>{studentAccountStatus}</div>}
                </div>
              )}

              {/* ── CURRICULUM TAB ── */}
              {studentWorkspaceTab === "curriculum" && (
                <div>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
                    <h3 style={{ fontSize: 18, fontWeight: 700 }}>Chương trình đào tạo - Ngành Khoa học Dữ liệu</h3>
                    <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
                      <span style={{ fontSize: 13, color: "var(--text-secondary)" }}>
                        Tổng số tín chỉ chương trình: <strong style={{ color: "var(--color-primary)" }}>{gpaStats.totalRegistered}</strong> tín chỉ
                      </span>
                    </div>
                  </div>

                  {allSemesters.length === 0 ? (
                    <div className="text-center" style={{ padding: 40, color: "var(--text-muted)" }}>
                      <i className="pi pi-spin pi-spinner" style={{ fontSize: 32 }}></i>
                      <p style={{ marginTop: 12 }}>Đang tải chương trình...
                      </p>
                    </div>
                  ) : (
                    allSemesters.map((hk) => {
                      const courses = coursesBySemester[hk] || [];
                      const hkCredits = courses.reduce((acc, c) => acc + (c.tong_so_chi || 0), 0);
                      const hkPassed = courses.filter(c => c.diem_tong_ket != null && c.diem_tong_ket >= 4.0).reduce((acc, c) => acc + (c.tong_so_chi || 0), 0);
                      return (
                        <div key={hk} style={{ marginBottom: 28 }}>
                          <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 12 }}>
                            <div style={{ background: "var(--color-primary)", color: "#fff", borderRadius: 8, padding: "4px 14px", fontSize: 13, fontWeight: 700 }}>
                              Học kỳ {hk}
                            </div>
                            <span style={{ fontSize: 12, color: "var(--text-secondary)" }}>{hkCredits} tín chỉ</span>
                          </div>
                          <div style={{ overflowX: "auto" }}>
                            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
                              <thead>
                                <tr style={{ background: "var(--bg-primary)", borderRadius: 8 }}>
                                  <th style={{ padding: "8px 10px", textAlign: "left", fontWeight: 600 }}>Mã MH</th>
                                  <th style={{ padding: "8px 10px", textAlign: "left", fontWeight: 600 }}>Tên môn học</th>
                                  <th style={{ padding: "8px 10px", textAlign: "center" }}>Loại</th>
                                  <th style={{ padding: "8px 10px", textAlign: "center" }}>Số tín chỉ</th>
                                </tr>
                              </thead>
                              <tbody>
                                {courses.map((c, ci) => (
                                  <tr key={ci} style={{ borderTop: "1px solid var(--border-glass)" }}>
                                    <td style={{ padding: "7px 10px", color: "var(--text-secondary)", whiteSpace: "nowrap" }}>{c.ma_mon}</td>
                                    <td style={{ padding: "7px 10px", fontWeight: 600, color: "var(--text-primary)" }}>{c.ten_mon}</td>
                                    <td style={{ padding: "7px 10px", textAlign: "center" }}>
                                      <span style={{ fontSize: 11, background: c.loai_hoc_phan === "ly_thuyet" ? "#e8f4fd" : c.loai_hoc_phan === "thuc_hanh" ? "#e8fdf0" : "#fdf8e8", padding: "2px 7px", borderRadius: 10, color: "#555" }}>
                                        {c.loai_hoc_phan === "ly_thuyet" ? "LT" : c.loai_hoc_phan === "thuc_hanh" ? "TH" : "TH"}
                                      </span>
                                    </td>
                                    <td style={{ padding: "7px 10px", textAlign: "center", fontWeight: 700 }}>{c.tong_so_chi}</td>
                                  </tr>
                                ))}
                              </tbody>
                              <tfoot>
                                <tr style={{ background: "var(--bg-primary)", borderTop: "2px solid var(--border-glass)" }}>
                                  <td colSpan={3} style={{ padding: "8px 10px", fontWeight: 700, fontSize: 12 }}>TỔNG HK{hk}</td>
                                  <td style={{ padding: "8px 10px", textAlign: "center", fontWeight: 700 }}>{hkCredits} TC</td>
                                </tr>
                              </tfoot>
                            </table>
                          </div>
                        </div>
                      );
                    })
                  )}
                </div>
              )}

              {/* ── SIMULATION TAB ── */}
              {studentWorkspaceTab === "simulation" && (
                <div>
                  <h3 className="font-bold mb-4" style={{ fontSize: 18 }}>Dự báo Điểm thi cuối kỳ</h3>
                  <div style={{ display: "grid", gridTemplateColumns: "1.2fr 1fr", gap: 28, alignItems: "start" }}>
                    <div>
                      {/* Semester selector */}
                      <div className="form-group">
                        <label className="form-label">Bước 1: Chọn học kỳ</label>
                        <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                          {allSemesters.map((hk) => (
                            <button
                              key={hk}
                              className={`btn btn-sm ${predictSemester === hk ? "btn-primary" : "btn-ghost"}`}
                              onClick={() => { setPredictSemester(hk); setSelectedCourseId(""); setHasPredicted(false); }}
                              style={{ borderRadius: 20 }}
                            >
                              Học kỳ {hk}
                            </button>
                          ))}
                        </div>
                      </div>

                      {/* Course selector (filtered by semester) */}
                      <div className="form-group">
                        <label className="form-label">Bước 2: Chọn môn học cần dự báo</label>
                        <select
                          className="form-control"
                          value={selectedCourseId}
                          onChange={(e) => { setSelectedCourseId(e.target.value); setHasPredicted(false); }}
                          style={{ width: "100%" }}
                        >
                          <option value="">-- Chọn môn --</option>
                          {coursesInSemester.map((item) => (
                            <option key={`${item.student_id}-${item.ma_mon}`} value={item.ma_mon}>
                              {item.ma_mon} – {item.ten_mon} ({item.loai_hoc_phan === "ly_thuyet" ? "LT" : item.loai_hoc_phan === "thuc_hanh" ? "TH" : "TH"})
                            </option>
                          ))}
                        </select>
                        {coursesInSemester.length === 0 && allSemesters.length > 0 && (
                          <p className="text-gray text-sm" style={{ marginTop: 6 }}>Không có môn nào ở học kỳ này.</p>
                        )}
                      </div>

                      {/* Grade target */}
                      <div className="form-group">
                        <label className="form-label">Bước 3: Chọn mức điểm chữ mục tiêu</label>
                        <div className="grade-slider-container">
                          <div className="grade-slider-track">
                            <div className="grade-slider-fill" style={{ width: `${(TARGETS.indexOf(target) / (TARGETS.length - 1)) * 100}%` }}></div>
                          </div>
                          {TARGETS.map((g) => (
                            <div key={g} className={`grade-node ${target === g ? "active" : ""}`} onClick={() => { setTarget(g); setHasPredicted(false); }}>{g}</div>
                          ))}
                        </div>
                      </div>

                      <button
                        className="btn btn-primary"
                        onClick={lookupStudent}
                        disabled={isLookingUp || !selectedCourseId}
                        style={{ width: "100%", height: 46 }}
                      >
                        {isLookingUp ? (
                          <span><i className="pi pi-spin pi-spinner" style={{ marginRight: 6 }}></i>Đang xử lý...</span>
                        ) : "Chạy dự báo điểm thi cuối kỳ"}
                      </button>
                      {lookupError && (
                        <div className="badge badge-danger mt-3" style={{ width: "100%", justifyContent: "center" }}>{lookupError}</div>
                      )}
                    </div>

                    {/* Result Cards */}
                    <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
                      <div className="glass-card" style={{ background: "#ffffff", padding: 22 }}>
                        <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12, borderBottom: "1px solid var(--border-glass)", paddingBottom: 6 }}>Tóm tắt học tập</h4>
                        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                          <div style={{ background: "var(--bg-primary)", padding: 12, borderRadius: 10 }}>
                            <span style={{ fontSize: 11, color: "var(--text-muted)" }}>Tổng môn</span>
                            <strong style={{ fontSize: 22, display: "block", marginTop: 4 }}>{summary.total}</strong>
                          </div>
                          <div style={{ background: "var(--bg-primary)", padding: 12, borderRadius: 10 }}>
                            <span style={{ fontSize: 11, color: "var(--text-muted)" }}>Cần lưu ý</span>
                            <strong style={{ fontSize: 22, display: "block", marginTop: 4, color: summary.warning > 0 ? "var(--color-danger)" : "var(--color-success)" }}>{summary.warning}</strong>
                          </div>
                          <div style={{ background: "var(--bg-primary)", padding: 12, borderRadius: 10 }}>
                            <span style={{ fontSize: 11, color: "var(--text-muted)" }}>GPA HỆ 10</span>
                            <strong style={{ fontSize: 22, display: "block", marginTop: 4, color: "var(--color-primary)" }}>{gpaStats.gpa10}</strong>
                          </div>
                          <div style={{ background: "var(--bg-primary)", padding: 12, borderRadius: 10 }}>
                            <span style={{ fontSize: 11, color: "var(--text-muted)" }}>GPA HỆ 4</span>
                            <strong style={{ fontSize: 22, display: "block", marginTop: 4, color: "var(--color-secondary)" }}>{gpaStats.gpa4}</strong>
                          </div>
                        </div>
                      </div>

                      {hasPredicted && selectedResult && (
                        <div className="glass-card glow-card" style={{ padding: 22 }}>
                          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
                            <strong style={{ fontSize: 16, color: "var(--color-primary)" }}>Mục tiêu {selectedResult.ten_mon} ({selectedResult.ma_mon})</strong>
                            <span className={`badge ${selectedResult.prediction?.is_kha_thi ? "badge-success" : "badge-danger"}`}>
                              {selectedResult.prediction?.is_kha_thi ? "Khả thi" : "Bất khả thi"}
                            </span>
                          </div>
                          <div style={{ textAlign: "center", padding: "14px 0", background: "var(--bg-primary)", borderRadius: 12, marginBottom: 14 }}>
                            <span style={{ fontSize: 12, color: "var(--text-secondary)" }}>ĐIỂM THI CUỐI KỲ CẦN ĐẠT</span>
                            <h3 style={{ fontSize: 36, fontWeight: 800, color: "var(--text-primary)", marginTop: 6 }}>
                              {selectedResult.prediction?.diem_can_dat !== null ? selectedResult.prediction?.diem_can_dat : "N/A"}
                            </h3>
                            <p style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 4 }}>Ngưỡng {target}: {selectedResult.prediction?.diem_muc_tieu_nguong} / 10</p>
                          </div>
                          <p className="text-sm text-gray" style={{ lineHeight: 1.5, marginBottom: 10 }}>{selectedResult.prediction?.message}</p>
                          <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, borderTop: "1px solid var(--border-glass)", paddingTop: 10 }}>
                            <span className="text-gray">Nguồn dữ liệu:</span>
                            <span className="badge badge-info" style={{ textTransform: "uppercase", padding: "2px 8px", fontSize: 10 }}>
                              {selectedResult.source === "databricks" ? "Databricks Cloud" : "Local DB"}
                            </span>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Full score breakdown */}
                  {hasPredicted && selectedResult && selectedResult.prediction?.chi_tiet?.full_scores && (
                    <div className="glass-card mt-6" style={{ background: "#ffffff" }}>
                      <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 16 }}><i className="pi pi-table" style={{ marginRight: 8, color: "var(--color-primary)" }}></i>Chi tiết thành phần điểm hiện tại</h4>
                      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))", gap: 12 }}>
                        <div style={{ border: "1px solid var(--border-glass)", padding: 12, borderRadius: 10 }}>
                          <span style={{ fontSize: 11, color: "var(--text-muted)" }}>Thường kỳ</span>
                          <strong style={{ fontSize: 16, display: "block", marginTop: 4 }}>
                            {selectedResult.prediction.chi_tiet.full_scores.diem_thong_thuong?.length > 0
                              ? selectedResult.prediction.chi_tiet.full_scores.diem_thong_thuong.join("; ")
                              : "Chưa có"}
                          </strong>
                        </div>
                        <div style={{ border: "1px solid var(--border-glass)", padding: 12, borderRadius: 10 }}>
                          <span style={{ fontSize: 11, color: "var(--text-muted)" }}>Giữa kỳ</span>
                          <strong style={{ fontSize: 16, display: "block", marginTop: 4 }}>
                            {selectedResult.prediction.chi_tiet.full_scores.diem_giua_ky !== null
                              ? selectedResult.prediction.chi_tiet.full_scores.diem_giua_ky : "Chưa có"}
                          </strong>
                        </div>
                        {selectedResult.prediction.chi_tiet.full_scores.loai_hoc_phan !== "ly_thuyet" && (
                          <div style={{ border: "1px solid var(--border-glass)", padding: 12, borderRadius: 10 }}>
                            <span style={{ fontSize: 11, color: "var(--text-muted)" }}>Thực hành</span>
                            <strong style={{ fontSize: 16, display: "block", marginTop: 4 }}>
                              {selectedResult.prediction.chi_tiet.full_scores.diem_thuc_hanh_hien_tai?.length > 0
                                ? selectedResult.prediction.chi_tiet.full_scores.diem_thuc_hanh_hien_tai.join("; ")
                                : selectedResult.prediction.chi_tiet.full_scores.diem_thuc_hanh_tich_hop ?? "Chưa có"}
                            </strong>
                          </div>
                        )}
                        <div style={{ border: "1px solid var(--border-glass)", padding: 12, borderRadius: 10 }}>
                          <span style={{ fontSize: 11, color: "var(--text-muted)" }}>Học vụ</span>
                          <strong style={{ fontSize: 14, display: "block", marginTop: 4, color: selectedResult.status_canh_bao !== "An toan" ? "var(--color-danger)" : "var(--color-success)" }}>
                            {selectedResult.status_canh_bao === "An toan" ? "An toàn" : "Nguy cơ"}
                          </strong>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* ── CALCULATOR TAB ── */}
              {studentWorkspaceTab === "calculator" && (
                <div>
                  <h3 className="font-bold mb-4" style={{ fontSize: 18 }}>Công cụ Tính điểm Học vụ IUH</h3>
                  <p className="text-sm text-gray mb-6">
                    Hỗ trợ tính điểm trung bình học phần (TBMH), trung bình học kỳ (TBHK) và tích lũy (TBTL) bằng cách nhập điểm vào từng ô riêng biệt.
                  </p>

                  {/* Calculator Selector Tabs */}
                  <div style={{ display: "flex", gap: 10, marginBottom: 20 }}>
                    <button className={`btn btn-sm ${calcSubTab === "TBMH" ? "btn-primary" : "btn-outline"}`} onClick={() => setCalcSubTab("TBMH")} style={{ borderRadius: 12 }}>
                      <i className="pi pi-book" style={{ marginRight: 6 }}></i>Tính điểm Môn học (TBMH)
                    </button>
                    <button className={`btn btn-sm ${calcSubTab === "TBHK" ? "btn-primary" : "btn-outline"}`} onClick={() => { setCalcSubTab("TBHK"); setGpaResult(null); }} style={{ borderRadius: 12 }}>
                      <i className="pi pi-calendar" style={{ marginRight: 6 }}></i>Tính GPA Học kỳ (TBHK)
                    </button>
                    <button className={`btn btn-sm ${calcSubTab === "TBTL" ? "btn-primary" : "btn-outline"}`} onClick={() => { setCalcSubTab("TBTL"); setGpaResult(null); }} style={{ borderRadius: 12 }}>
                      <i className="pi pi-chart-line" style={{ marginRight: 6 }}></i>Tính GPA Tích lũy (TBTL)
                    </button>
                  </div>

                  {calcSubTab === "TBMH" && (
                    <div style={{ display: "grid", gridTemplateColumns: "1.2fr 1fr", gap: 28, alignItems: "start" }}>
                      <div className="glass-card" style={{ background: "#ffffff", padding: 22 }}>
                        <div className="form-group">
                          <label className="form-label">Loại hình học phần</label>
                          <select className="form-control" value={calcType} onChange={(e) => { setCalcType(e.target.value as any); setCalcResult(null); }}>
                            <option value="ly_thuyet">Lý thuyết (Quá trình 50% - Thi 50%)</option>
                            <option value="thuc_hanh">Thực hành (Liệt thực hành &lt; 3.0)</option>
                            <option value="tich_hop">Tích hợp LT & TH (Liệt thực hành &lt; 3.0)</option>
                          </select>
                        </div>

                        {/* TX inputs for LT or Tich Hop */}
                        {(calcType === "ly_thuyet" || calcType === "tich_hop") && (
                          <div className="mb-4">
                            <span className="form-label font-bold mb-2" style={{ display: "block" }}>Điểm Thường kỳ (Lý thuyết):</span>
                            <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 10 }}>
                              <div className="form-group">
                                <label className="form-label" style={{ fontSize: 11 }}>TX1</label>
                                <input className="form-control" style={{ textAlign: "center" }} value={tx1Input} onChange={(e) => setTx1Input(e.target.value)} placeholder="0.0" />
                              </div>
                              <div className="form-group">
                                <label className="form-label" style={{ fontSize: 11 }}>TX2</label>
                                <input className="form-control" style={{ textAlign: "center" }} value={tx2Input} onChange={(e) => setTx2Input(e.target.value)} placeholder="0.0" />
                              </div>
                              <div className="form-group">
                                <label className="form-label" style={{ fontSize: 11 }}>TX3</label>
                                <input className="form-control" style={{ textAlign: "center" }} value={tx3Input} onChange={(e) => setTx3Input(e.target.value)} placeholder="0.0" />
                              </div>
                              <div className="form-group">
                                <label className="form-label" style={{ fontSize: 11 }}>TX4</label>
                                <input className="form-control" style={{ textAlign: "center" }} value={tx4Input} onChange={(e) => setTx4Input(e.target.value)} placeholder="0.0" />
                              </div>
                            </div>
                          </div>
                        )}

                        {/* GK & CK Inputs for LT or Tich Hop */}
                        {(calcType === "ly_thuyet" || calcType === "tich_hop") && (
                          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }} className="mb-4">
                            <div className="form-group">
                              <label className="form-label font-bold">Điểm Giữa kỳ</label>
                              <input className="form-control" value={gkInput} onChange={(e) => setGkInput(e.target.value)} placeholder="Nhập điểm giữa kỳ" />
                            </div>
                            <div className="form-group">
                              <label className="form-label font-bold">Điểm Thi Cuối kỳ</label>
                              <input className="form-control" value={ckInput} onChange={(e) => setCkInput(e.target.value)} placeholder="Nhập điểm thi" />
                            </div>
                          </div>
                        )}

                        {/* TH inputs for TH or Tich Hop */}
                        {(calcType === "thuc_hanh" || calcType === "tich_hop") && (
                          <div className="mb-4">
                            <span className="form-label font-bold mb-2" style={{ display: "block" }}>Điểm thành phần Thực hành:</span>
                            <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 10 }}>
                              <div className="form-group">
                                <label className="form-label" style={{ fontSize: 11 }}>TH1</label>
                                <input className="form-control" style={{ textAlign: "center" }} value={th1Input} onChange={(e) => setTh1Input(e.target.value)} placeholder="0.0" />
                              </div>
                              <div className="form-group">
                                <label className="form-label" style={{ fontSize: 11 }}>TH2</label>
                                <input className="form-control" style={{ textAlign: "center" }} value={th2Input} onChange={(e) => setTh2Input(e.target.value)} placeholder="0.0" />
                              </div>
                              <div className="form-group">
                                <label className="form-label" style={{ fontSize: 11 }}>TH3</label>
                                <input className="form-control" style={{ textAlign: "center" }} value={th3Input} onChange={(e) => setTh3Input(e.target.value)} placeholder="0.0" />
                              </div>
                              <div className="form-group">
                                <label className="form-label" style={{ fontSize: 11 }}>TH4</label>
                                <input className="form-control" style={{ textAlign: "center" }} value={th4Input} onChange={(e) => setTh4Input(e.target.value)} placeholder="0.0" />
                              </div>
                            </div>
                          </div>
                        )}

                        <button className="btn btn-primary" onClick={runLocalCalculation} style={{ width: "100%", height: 46, marginTop: 12 }}>
                          Tính điểm môn học (TBMH)
                        </button>
                      </div>

                      <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
                        <div className="glass-card" style={{ background: "#ffffff", padding: 22 }}>
                          <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12, borderBottom: "1px solid var(--border-glass)", paddingBottom: 6 }}>Công thức tính môn học</h4>
                          <ul style={{ paddingLeft: 16, color: "var(--text-secondary)", fontSize: 13, display: "flex", flexDirection: "column", gap: 6 }}>
                            <li><strong>Lý thuyết:</strong> (Trung bình TX)*0.2 + GK*0.3 + CK*0.5.</li>
                            <li><strong>Thực hành:</strong> Trung bình cộng điểm thực hành. Liệt TH &lt; 3.0 → F.</li>
                            <li><strong>Tích hợp:</strong> (Điểm LT * 2 + Trung bình TH * 1) / 3. Liệt TH &lt; 3.0 → F.</li>
                          </ul>
                        </div>

                        {calcResult && (
                          <div className="glass-card glow-card" style={{ padding: 22, border: "1.5px solid var(--border-glass-glow)" }}>
                            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
                              <strong style={{ fontSize: 16, color: "var(--color-primary)" }}>Kết quả quy đổi</strong>
                              <span className={`badge ${calcResult.isPass ? "badge-success" : "badge-danger"}`}>
                                {calcResult.isPass ? "Đạt môn học" : "Học lại (F)"}
                              </span>
                            </div>
                            
                            <div style={{ textAlign: "center", padding: "14px 0", background: "var(--bg-primary)", borderRadius: 12, marginBottom: 14 }}>
                              <span style={{ fontSize: 12, color: "var(--text-secondary)" }}>ĐIỂM TỔNG KẾT MÔN</span>
                              <h3 style={{ fontSize: 36, fontWeight: 800, color: "var(--text-primary)", marginTop: 6 }}>
                                {calcResult.finalScore}
                              </h3>
                              <p style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 4 }}>
                                Hệ chữ: <strong style={{ color: "var(--color-primary)" }}>{calcResult.letterGrade}</strong> · Hệ 4: <strong>{calcResult.system4Grade}</strong>
                              </p>
                            </div>
                            <p className="text-sm text-gray" style={{ lineHeight: 1.5 }}>{calcResult.message}</p>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {(calcSubTab === "TBHK" || calcSubTab === "TBTL") && (
                    <div style={{ display: "grid", gridTemplateColumns: "1.2fr 1fr", gap: 28, alignItems: "start" }}>
                      <div className="glass-card" style={{ background: "#ffffff", padding: 22 }}>
                        <h4 className="font-bold mb-4" style={{ fontSize: 16 }}>Danh sách môn học tính GPA ({calcSubTab})</h4>
                        
                        <div style={{ display: "flex", flexDirection: "column", gap: 12, marginBottom: 16 }}>
                          {gpaRows.map((row, idx) => (
                            <div key={row.id} style={{ display: "flex", gap: 10, alignItems: "center" }}>
                              <span style={{ fontSize: 13, color: "var(--text-muted)", minWidth: 20 }}>{idx + 1}.</span>
                              <input className="form-control" style={{ flex: 2 }} value={row.name} onChange={(e) => updateGpaRow(row.id, "name", e.target.value)} placeholder="Tên môn học" />
                              <input className="form-control" style={{ width: 80, textAlign: "center" }} type="number" min="1" max="10" value={row.credits || ""} onChange={(e) => updateGpaRow(row.id, "credits", Number(e.target.value))} placeholder="Số TC" />
                              <input className="form-control" style={{ width: 100, textAlign: "center" }} value={row.grade} onChange={(e) => updateGpaRow(row.id, "grade", e.target.value)} placeholder="Điểm hệ 10" />
                              <button className="btn btn-ghost" style={{ color: "var(--color-danger)", padding: 6 }} onClick={() => deleteGpaRow(row.id)} disabled={gpaRows.length <= 1}>
                                <i className="pi pi-trash"></i>
                              </button>
                            </div>
                          ))}
                        </div>

                        <div style={{ display: "flex", gap: 10 }}>
                          <button className="btn btn-outline btn-sm" onClick={addGpaRow}>
                            <i className="pi pi-plus"></i> Thêm môn học
                          </button>
                          <button className="btn btn-primary btn-sm" onClick={calculateGpa} style={{ marginLeft: "auto" }}>
                            Tính GPA tích lũy
                          </button>
                        </div>
                      </div>

                      <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
                        <div className="glass-card" style={{ background: "#ffffff", padding: 22 }}>
                          <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12, borderBottom: "1px solid var(--border-glass)", paddingBottom: 6 }}>Phân loại học lực tích lũy</h4>
                          <ul style={{ paddingLeft: 16, color: "var(--text-secondary)", fontSize: 13, display: "flex", flexDirection: "column", gap: 4 }}>
                            <li>GPA hệ 4 ≥ 3.6: Xuất sắc</li>
                            <li>GPA hệ 4 từ 3.2 – 3.59: Giỏi</li>
                            <li>GPA hệ 4 từ 2.5 – 3.19: Khá</li>
                            <li>GPA hệ 4 từ 2.0 – 2.49: Trung bình</li>
                            <li>GPA hệ 4 &lt; 2.0: Yếu / Kém</li>
                          </ul>
                        </div>

                        {gpaResult && (
                          <div className="glass-card glow-card" style={{ padding: 22, border: "1.5px solid var(--border-glass-glow)" }}>
                            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
                              <strong style={{ fontSize: 16, color: "var(--color-primary)" }}>Kết quả GPA tích lũy</strong>
                              <span className="badge badge-success">{gpaResult.classification}</span>
                            </div>
                            
                            <div style={{ textAlign: "center", padding: "14px 0", background: "var(--bg-primary)", borderRadius: 12 }}>
                              <span style={{ fontSize: 12, color: "var(--text-secondary)" }}>ĐIỂM GPA (HỆ 4)</span>
                              <h3 style={{ fontSize: 36, fontWeight: 800, color: "var(--text-primary)", marginTop: 6 }}>
                                {gpaResult.gpa4}
                              </h3>
                              <p style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 4 }}>
                                Thang điểm 10: <strong>{gpaResult.gpa10}</strong> · Tổng số tín chỉ: <strong>{gpaResult.totalCredits} TC</strong>
                              </p>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                </div>
              )}
            </div>
          )}

          {/* 2. LECTURER WORKSPACE */}
          {activeTab === "lecturer" && (
            <div>
              {/* Lecturer header */}
              <div style={{ borderBottom: "1px solid var(--border-glass)", paddingBottom: 16, marginBottom: 20 }}>
                <h2 style={{ fontSize: "20px", fontWeight: 700, color: "var(--text-primary)", margin: 0 }}>
                  Không gian làm việc Giảng viên
                </h2>
                <p className="text-gray text-sm" style={{ marginTop: "4px", margin: 0 }}>
                  Chào mừng trở lại, {lecturerName}. Quản lý danh sách môn học, cập nhật điểm số và nhập điểm nhanh từ tệp tin.
                </p>
              </div>

              {/* Lecturer Sub-tab Nav */}
              <div style={{ display: "flex", gap: 8, marginBottom: 24, borderBottom: "1px solid var(--border-glass)", paddingBottom: 12 }}>
                {([
                  { id: "courses", label: "Quản lý môn phụ trách", icon: "pi-book" },
                  { id: "grades", label: "Nhập và sửa điểm SV", icon: "pi-pencil" },
                  { id: "upload", label: "Nạp tệp điểm CSV/XLSX", icon: "pi-upload" },
                ] as const).map((t) => (
                  <button
                    key={t.id}
                    className={`btn btn-sm ${lecturerWorkspaceTab === t.id ? "btn-primary" : "btn-ghost"}`}
                    onClick={() => setLecturerWorkspaceTab(t.id)}
                    style={{ borderRadius: 20, display: "flex", alignItems: "center", gap: 6 }}
                  >
                    <i className={`pi ${t.icon}`} style={{ fontSize: 13 }} />
                    {t.label}
                  </button>
                ))}
              </div>

              {/* Tab: COURSES */}
              {lecturerWorkspaceTab === "courses" && (
                <div>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20, flexWrap: "wrap", gap: 16 }}>
                    <h4 className="font-bold" style={{ fontSize: 16, margin: 0 }}><i className="pi pi-book" style={{ marginRight: 8, color: "var(--color-primary)" }}></i>Các môn học đang giảng dạy</h4>
                    {/* Course Search Bar */}
                    <div className="search-box-container" style={{ position: "relative", minWidth: 260 }}>
                      <i className="pi pi-search" style={{ position: "absolute", left: 12, top: "50%", transform: "translateY(-50%)", color: "var(--text-gray)", pointerEvents: "none" }}></i>
                      <input
                        type="text"
                        placeholder="Tìm tên môn, mã môn..."
                        value={lecturerCourseSearch}
                        onChange={(e) => setLecturerCourseSearch(e.target.value)}
                        className="form-control"
                        style={{ paddingLeft: 36, width: "100%", borderRadius: 20, border: "1px solid var(--border-glass)", background: "rgba(255, 255, 255, 0.8)", height: "38px" }}
                      />
                      {lecturerCourseSearch && (
                        <i className="pi pi-times" onClick={() => setLecturerCourseSearch("")} style={{ position: "absolute", right: 12, top: "50%", transform: "translateY(-50%)", cursor: "pointer", color: "var(--text-gray)" }}></i>
                      )}
                    </div>
                  </div>
                  {isLecturerLoading ? (
                    <div className="text-center" style={{ padding: 40 }}><i className="pi pi-spin pi-spinner" style={{ fontSize: 32 }}></i></div>
                  ) : lecturerCourses.length === 0 ? (
                    <p className="text-gray text-center">Bạn chưa được phân công môn học nào trong học kỳ này.</p>
                  ) : filteredLecturerCourses.length === 0 ? (
                    <p className="text-gray text-center">Không tìm thấy môn học nào phù hợp với tìm kiếm của bạn.</p>
                  ) : (
                    <div className="grid grid-3">
                      {filteredLecturerCourses.map((c) => (
                        <div key={c.ma_mon} className="glass-card hover-float" style={{ background: "#ffffff", cursor: "pointer" }} onClick={() => { setSelectedLecturerCourseId(c.ma_mon); setLecturerWorkspaceTab("grades"); }}>
                          <div className="icon-box" style={{ background: "rgba(240, 167, 142, 0.1)" }}><i className="pi pi-book"></i></div>
                          <h4 className="font-bold mb-1">{c.ten_mon}</h4>
                          <p className="text-gray text-sm mb-4">Mã môn: {c.ma_mon} · Lớp: {c.ma_lop}</p>
                          <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, borderTop: "1px solid var(--border-glass)", paddingTop: 10 }}>
                            <span>Sĩ số: <strong>{c.so_sinh_vien} SV</strong></span>
                            <span>Tín chỉ: <strong>{c.tin_chi} TC</strong></span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Tab: GRADES */}
              {lecturerWorkspaceTab === "grades" && (
                <div>
                  <h4 className="font-bold mb-4" style={{ fontSize: 16 }}><i className="pi pi-pencil" style={{ marginRight: 8, color: "var(--color-primary)" }}></i>Nhập và chỉnh sửa điểm số sinh viên</h4>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20, flexWrap: "wrap", gap: 16 }}>
                    {/* Left controls: Select class & Refresh */}
                    <div style={{ display: "flex", gap: 16, alignItems: "center", flexWrap: "wrap" }}>
                      <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                        <label className="form-label" style={{ whiteSpace: "nowrap", margin: 0 }}>Chọn lớp học phần:</label>
                        <select className="form-control" value={selectedLecturerCourseId} onChange={(e) => { setSelectedLecturerCourseId(e.target.value); setLecturerStudentSearch(""); }} style={{ maxWidth: 260 }}>
                          <option value="">-- Chọn môn học --</option>
                          {lecturerCourses.map((c) => (
                            <option key={c.ma_mon} value={c.ma_mon}>{c.ten_mon} ({c.ma_mon})</option>
                          ))}
                        </select>
                      </div>
                      <button className="btn btn-outline btn-sm" onClick={() => selectedLecturerCourseId && loadLecturerGrades(selectedLecturerCourseId)} style={{ height: "38px", display: "flex", alignItems: "center", gap: 6 }}><i className="pi pi-refresh"></i> Làm mới</button>
                    </div>

                    {/* Right controls: Sort button & Search student */}
                    {selectedLecturerCourseId && lecturerGrades.length > 0 && (
                      <div style={{ display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
                        {/* Sort button */}
                        <button
                          className={`btn btn-sm ${sortByStudentName ? "btn-primary" : "btn-outline"}`}
                          onClick={() => setSortByStudentName(!sortByStudentName)}
                          style={{ height: "38px", display: "flex", alignItems: "center", gap: 6, borderRadius: 20, whiteSpace: "nowrap" }}
                          title="Sắp xếp danh sách sinh viên theo chữ cái đầu của Tên"
                        >
                          <i className="pi pi-sort-alpha-down"></i>
                          Xếp theo tên: {sortByStudentName ? "Bật" : "Tắt"}
                        </button>

                        {/* Search input */}
                        <div className="search-box-container" style={{ position: "relative", minWidth: 260 }}>
                          <i className="pi pi-search" style={{ position: "absolute", left: 12, top: "50%", transform: "translateY(-50%)", color: "var(--text-gray)", pointerEvents: "none" }}></i>
                          <input
                            type="text"
                            placeholder="Tìm MSSV, tên sinh viên..."
                            value={lecturerStudentSearch}
                            onChange={(e) => setLecturerStudentSearch(e.target.value)}
                            className="form-control"
                            style={{ paddingLeft: 36, width: "100%", borderRadius: 20, border: "1px solid var(--border-glass)", background: "rgba(255, 255, 255, 0.8)", height: "38px" }}
                          />
                          {lecturerStudentSearch && (
                            <i className="pi pi-times" onClick={() => setLecturerStudentSearch("")} style={{ position: "absolute", right: 12, top: "50%", transform: "translateY(-50%)", cursor: "pointer", color: "var(--text-gray)" }}></i>
                          )}
                        </div>
                      </div>
                    )}
                  </div>

                  {isLecturerLoading ? (
                    <div className="text-center" style={{ padding: 40 }}><i className="pi pi-spin pi-spinner" style={{ fontSize: 32 }}></i></div>
                  ) : !selectedLecturerCourseId ? (
                    <p className="text-gray text-center">Vui lòng chọn môn học cần chỉnh sửa điểm.</p>
                  ) : lecturerGrades.length === 0 ? (
                    <p className="text-gray text-center">Lớp này chưa có dữ liệu điểm sinh viên. Vui lòng chuyển sang tab "Nạp tệp điểm" để tải lên file CSV/XLSX.</p>
                  ) : filteredAndSortedGrades.length === 0 ? (
                    <p className="text-gray text-center" style={{ padding: 20 }}>Không tìm thấy sinh viên nào phù hợp với từ khóa tìm kiếm.</p>
                  ) : (
                    <div className="data-table-container" style={{ overflowX: "auto" }}>
                      <table className="data-table">
                        <thead>
                          <tr>
                            <th>MSSV</th>
                            <th>Họ & Tên</th>
                            <th>Thường kỳ (LT)</th>
                            <th>Giữa kỳ (LT)</th>
                            {filteredAndSortedGrades[0]?.loai_hoc_phan === "tich_hop" && <th>Điểm TH</th>}
                            {filteredAndSortedGrades[0]?.loai_hoc_phan === "thuc_hanh" && Array.from({ length: maxPracticeScores }).map((_, i) => (
                              <th key={`th-practice-${i}`}>TH {i + 1}</th>
                            ))}
                            <th>Cuối kỳ</th>
                            <th>Tổng kết</th>
                            <th>Hệ chữ</th>
                            <th>Hệ 4</th>
                            <th>Cảnh báo</th>
                            <th>Thao tác</th>
                          </tr>
                        </thead>
                        <tbody>
                          {filteredAndSortedGrades.map((g) => {
                            const isEditing = editingGradeRow === g.student_id;
                            return (
                              <tr key={g.student_id}>
                                <td><strong>{g.student_id}</strong></td>
                                <td>{g.ten_sv || <span className="text-gray">Chưa đồng bộ</span>}</td>
                                <td>
                                  {isEditing ? (
                                    <input className="form-control" style={{ width: 100, padding: "4px 8px" }} value={editGradeRegular} onChange={(e) => setEditGradeRegular(e.target.value)} placeholder="VD: 8.0, 7.5" />
                                  ) : (
                                    g.diem_thong_thuong?.join(", ") || "-"
                                  )}
                                </td>
                                <td>
                                  {isEditing ? (
                                    <input className="form-control" style={{ width: 80, padding: "4px 8px" }} type="number" min="0" max="10" step="0.1" value={editGradeMidterm} onChange={(e) => setEditGradeMidterm(e.target.value)} />
                                  ) : (
                                    g.diem_giua_ky ?? "-"
                                  )}
                                </td>
                                {g.loai_hoc_phan === "tich_hop" && (
                                  <td>
                                    {isEditing ? (
                                      <input className="form-control" style={{ width: 80, padding: "4px 8px" }} type="number" min="0" max="10" step="0.1" value={editGradePractice1} onChange={(e) => setEditGradePractice1(e.target.value)} />
                                    ) : (
                                      g.diem_thuc_hanh_tich_hop ?? "-"
                                    )}
                                  </td>
                                )}
                                {g.loai_hoc_phan === "thuc_hanh" && Array.from({ length: maxPracticeScores }).map((_, i) => {
                                  const val = i === 0 ? editGradePractice1 : i === 1 ? editGradePractice2 : editGradePractice3;
                                  const setVal = i === 0 ? setEditGradePractice1 : i === 1 ? setEditGradePractice2 : setEditGradePractice3;
                                  return (
                                    <td key={`edit-practice-${i}`}>
                                      {isEditing ? (
                                        <input className="form-control" style={{ width: 80, padding: "4px 8px" }} type="number" min="0" max="10" step="0.1" value={val} onChange={(e) => setVal(e.target.value)} />
                                      ) : (
                                        g.diem_thuc_hanh_hien_tai?.[i] ?? "-"
                                      )}
                                    </td>
                                  );
                                })}
                                <td>
                                  {isEditing ? (
                                    <input className="form-control" style={{ width: 80, padding: "4px 8px" }} type="number" min="0" max="10" step="0.1" value={editGradeFinal} onChange={(e) => setEditGradeFinal(e.target.value)} />
                                  ) : (
                                    g.diem_cuoi_ky ?? "-"
                                  )}
                                </td>
                                <td><strong>{g.diem_tong_ket ?? "-"}</strong></td>
                                <td><span className={`badge ${g.diem_chu === "F" ? "badge-danger" : g.diem_chu ? "badge-success" : ""}`}>{g.diem_chu || "-"}</span></td>
                                <td>{g.diem_he_4 ?? "-"}</td>
                                <td>
                                  <span className={`badge ${g.status_canh_bao === "An toan" ? "badge-success" : "badge-danger"}`}>
                                    {g.status_canh_bao === "An toan" ? "An toàn" : g.status_canh_bao}
                                  </span>
                                </td>
                                <td>
                                  {isEditing ? (
                                    <div style={{ display: "flex", gap: 6 }}>
                                      <button className="btn btn-primary btn-sm" onClick={() => lecturerUpdateGrade(g.student_id, g.ma_mon)}>Lưu</button>
                                      <button className="btn btn-outline btn-sm" onClick={() => setEditingGradeRow(null)}>Hủy</button>
                                    </div>
                                  ) : (
                                    <div style={{ display: "flex", gap: 6 }}>
                                      <button className="btn btn-outline btn-sm" onClick={() => {
                                        setEditingGradeRow(g.student_id);
                                        setEditGradeRegular(g.diem_thong_thuong?.join(", ") || "");
                                        setEditGradeMidterm(g.diem_giua_ky !== undefined && g.diem_giua_ky !== null ? g.diem_giua_ky.toString() : "");
                                        setEditGradeFinal(g.diem_cuoi_ky !== undefined && g.diem_cuoi_ky !== null ? g.diem_cuoi_ky.toString() : "");
                                        setEditGradePractice1(
                                          g.loai_hoc_phan === "tich_hop"
                                            ? (g.diem_thuc_hanh_tich_hop !== undefined && g.diem_thuc_hanh_tich_hop !== null ? g.diem_thuc_hanh_tich_hop.toString() : "")
                                            : (g.diem_thuc_hanh_hien_tai?.[0] !== undefined && g.diem_thuc_hanh_hien_tai?.[0] !== null ? g.diem_thuc_hanh_hien_tai[0].toString() : "")
                                        );
                                        setEditGradePractice2(
                                          g.diem_thuc_hanh_hien_tai?.[1] !== undefined && g.diem_thuc_hanh_hien_tai?.[1] !== null ? g.diem_thuc_hanh_hien_tai[1].toString() : ""
                                        );
                                        setEditGradePractice3(
                                          g.diem_thuc_hanh_hien_tai?.[2] !== undefined && g.diem_thuc_hanh_hien_tai?.[2] !== null ? g.diem_thuc_hanh_hien_tai[2].toString() : ""
                                        );
                                        setEditGradeReason("Giảng viên sửa điểm trực tiếp");
                                      }}><i className="pi pi-pencil"></i></button>
                                      <button className="btn btn-outline btn-sm" style={{ color: "var(--color-danger)", borderColor: "var(--color-danger)" }} onClick={() => lecturerDeleteGrade(g.student_id, g.ma_mon)}><i className="pi pi-trash"></i></button>
                                    </div>
                                  )}
                                </td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              )}

              {/* Tab: UPLOAD */}
              {lecturerWorkspaceTab === "upload" && (
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 28 }}>
                  <div className="glass-card" style={{ background: "#ffffff" }}>
                    <h4 className="font-bold mb-4" style={{ fontSize: 16 }}><i className="pi pi-cloud-upload" style={{ marginRight: 8, color: "var(--color-primary)" }}></i>Nạp tệp điểm CSV/XLSX học phần</h4>
                    <p className="text-sm text-gray mb-3">Chọn tệp CSV hoặc XLSX chứa điểm số sinh viên. Hỗ trợ file IUH chuẩn (Bảng điểm lớp học phần) và CSV thông thường.</p>

                    <div style={{ background: "rgba(93, 156, 236, 0.08)", border: "1px solid rgba(93, 156, 236, 0.3)", borderRadius: 10, padding: "10px 14px", marginBottom: 14, fontSize: 12.5 }}>
                      <span style={{ fontWeight: 600, color: "#3a7ec8" }}><i className="pi pi-star-fill" style={{ marginRight: 5 }}></i>File IUH: </span>
                      <span style={{ color: "var(--text-secondary)" }}>Dòng <em>"Lớp học phần: [MÃ_MÔN] - TÊN (LỚP)"</em> được nhận dạng tự động. Mã môn 2101409 → INT1306, 2101539 → INT1001...</span>
                    </div>
                    
                    <div className="form-group mb-4">
                      <label className="form-label">Tải lên file điểm (.csv, .xlsx)</label>
                      <input className="form-control" type="file" accept=".csv, .xlsx" onChange={(e) => setUploadFile(e.target.files?.[0] ?? null)} style={{ border: "1px dashed var(--color-primary)", padding: 20, background: "rgba(232, 93, 117, 0.02)" }} />
                      {uploadFile && (
                        <div style={{ marginTop: 8, fontSize: 12, color: "var(--text-secondary)", display: "flex", alignItems: "center", gap: 6 }}>
                          <i className="pi pi-file-excel" style={{ color: "#1d7044" }}></i>
                          <strong>{uploadFile.name}</strong>&nbsp;({(uploadFile.size / 1024).toFixed(1)} KB)
                        </div>
                      )}
                    </div>

                    <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
                      <button className="btn btn-primary" onClick={uploadScores} disabled={!uploadFile || isUploading}>
                        {isUploading ? (
                          <span><i className="pi pi-spin pi-spinner" style={{ marginRight: 6 }}></i>Đang đẩy lên Databricks...</span>
                        ) : <span><i className="pi pi-cloud-upload" style={{ marginRight: 6 }}></i>Nạp điểm lên Cloud</span>}
                      </button>
                      <button className="btn btn-outline" onClick={downloadXlsxTemplate} style={{ borderColor: "#1d7044", color: "#1d7044" }}>
                        <i className="pi pi-file-excel" style={{ marginRight: 6 }}></i>XLSX IUH mẫu
                      </button>
                      <button className="btn btn-outline" onClick={downloadTemplate}>
                        <i className="pi pi-download" style={{ marginRight: 6 }}></i>CSV mẫu
                      </button>
                    </div>
                  </div>

                  <div>
                    <div className="glass-card" style={{ background: "#ffffff", height: "100%" }}>
                      <h4 className="font-bold mb-4" style={{ fontSize: 16 }}><i className="pi pi-info-circle" style={{ marginRight: 8, color: "var(--color-secondary)" }}></i>Quy chế nạp tệp điểm số</h4>
                      <ul style={{ paddingLeft: 18, color: "var(--text-secondary)", display: "flex", flexDirection: "column", gap: 8, fontSize: 13.5 }}>
                        <li>Hỗ trợ <strong>CSV</strong> và <strong>Excel (.xlsx)</strong> gồm cả file IUH chuẩn (xuất từ phần mềm trường).</li>
                        <li>Điểm thành phần phải nằm trong thang điểm <strong>0.0 – 10.0</strong>.</li>
                        <li>File IUH: dòng <em>Lớp học phần</em> phải có định dạng <code style={{ background: "#f0f0f0", padding: "0 3px", borderRadius: 3, fontSize: 12 }}>[MÃ] - TÊN (LỚP)</code>.</li>
                        <li>Sau khi nạp, hệ thống chạy Databricks pipeline → cập nhật điểm và thông báo cho sinh viên.</li>
                      </ul>
                      <div style={{ marginTop: 18, borderTop: "1px dashed var(--border-glass)", paddingTop: 14 }}>
                        <div style={{ fontSize: 11, fontWeight: 600, color: "var(--text-muted)", marginBottom: 8, textTransform: "uppercase", letterSpacing: 0.8 }}>Ánh xạ Mã môn IUH → Nội bộ</div>
                        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 4, fontSize: 12 }}>
                          {[["2101409","INT1306"],["2101539","INT1001"],["2101680","INT1001"],["2101436","INT1100"],["2101864","INT1200"],["2101831","INT2001"]].map(([c,n]) => (
                            <div key={c} style={{ background: "#f8f9fa", borderRadius: 6, padding: "3px 8px", color: "var(--text-secondary)" }}><code style={{ fontSize: 11, color: "#333" }}>{c}</code> → {n}</div>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {uploadStatus && <div className="badge badge-success mt-4" style={{ width: "100%", justifyContent: "center" }}>{uploadStatus}</div>}
              {uploadError && <div className="badge badge-danger mt-4" style={{ width: "100%", justifyContent: "center" }}>{uploadError}</div>}
            </div>
          )}



          {/* 4. ADMIN WORKSPACE */}
          {activeTab === "admin" && (
            <div>
                  {/* Admin header */}
                  <div style={{ display: "flex", justifyContent: "space-between", gap: 16, borderBottom: "1px solid var(--border-glass)", paddingBottom: 16, marginBottom: 24, alignItems: "center" }}>
                    <div>
                      <h2 style={{ fontSize: "20px", fontWeight: 700, color: "var(--text-primary)", margin: 0 }}>
                        Hệ thống Quản trị Đào tạo
                      </h2>
                      <p className="text-gray text-sm" style={{ marginTop: "4px", margin: 0 }}>
                        Chào mừng trở lại, {adminName}. Quản lý cảnh báo học vụ, danh sách sinh viên, giảng viên, môn học và phân công giảng dạy.
                      </p>
                    </div>
                    <div>
                      <button className="btn btn-outline btn-sm" onClick={() => loadAdminDashboard()} style={{ padding: "6px 12px", display: "flex", alignItems: "center", gap: "6px", fontSize: "12px", cursor: "pointer" }}>
                        <i className="pi pi-refresh" style={{ fontSize: "11px" }}></i>
                        Làm mới dữ liệu
                      </button>
                    </div>
                  </div>

                  {/* Summary counts */}
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 16, marginBottom: 26 }}>
                    {Object.entries(adminOverview?.counts || {}).map(([key, value]) => (
                      <div key={key} style={{ background: "#ffffff", border: "1px solid var(--border-glass)", borderRadius: 12, padding: "16px 20px" }}>
                        <p style={{ color: "var(--text-muted)", fontSize: 12, textTransform: "uppercase" }}>{key.replaceAll("_", " ")}</p>
                        <strong style={{ fontSize: 24, marginTop: 4, display: "block" }}>{value}</strong>
                      </div>
                    ))}
                  </div>

                  {/* Admin sub menu tabs */}
                  <div style={{ display: "flex", gap: 8, borderBottom: "1px solid var(--border-glass)", marginBottom: 24, paddingBottom: 10, flexWrap: "wrap" }}>
                    <button className={`btn btn-sm ${adminActiveSubTab === "warnings" ? "btn-primary" : "btn-ghost"}`} onClick={() => setAdminActiveSubTab("warnings")}>
                      Cảnh báo học vụ
                    </button>
                    <button className={`btn btn-sm ${adminActiveSubTab === "students" ? "btn-primary" : "btn-ghost"}`} onClick={() => setAdminActiveSubTab("students")}>
                      Quản lý sinh viên
                    </button>

                    <button className={`btn btn-sm ${adminActiveSubTab === "courses" ? "btn-primary" : "btn-ghost"}`} onClick={() => setAdminActiveSubTab("courses")}>
                      Quản lý môn học
                    </button>
                    <button className={`btn btn-sm ${adminActiveSubTab === "assignments" ? "btn-primary" : "btn-ghost"}`} onClick={() => setAdminActiveSubTab("assignments")}>
                      Phân công GV
                    </button>

                    <button className={`btn btn-sm ${adminActiveSubTab === "rules" ? "btn-primary" : "btn-ghost"}`} onClick={() => setAdminActiveSubTab("rules")}>
                      Quy chế & Thang điểm
                    </button>
                    <button className={`btn btn-sm ${adminActiveSubTab === "timeline" ? "btn-primary" : "btn-ghost"}`} onClick={() => setAdminActiveSubTab("timeline")}>
                      Timeline hoạt động
                    </button>
                  </div>

                  {/* Sub tab contents */}
                  <div style={{ background: "#ffffff", padding: 24, borderRadius: 16, border: "1px solid var(--border-glass)" }}>
                    
                    {/* A. Warnings tab */}
                    {adminActiveSubTab === "warnings" && (
                      <div>
                        <h4 className="font-bold mb-4" style={{ fontSize: 16 }}>Báo cáo cảnh báo học vụ tổng hợp</h4>
                        <div className="data-table-container">
                          <table className="data-table">
                            <thead>
                              <tr>
                                <th>Mã SV</th>
                                <th>Môn học</th>
                                <th>Nguyên nhân</th>
                                <th>Nguy cơ (ML)</th>
                                <th>Dữ liệu</th>
                              </tr>
                            </thead>
                            <tbody>
                              {adminWarnings.slice(0, 8).map((w, idx) => (
                                <tr key={`${w.student_id}-${w.ma_mon}-${idx}`}>
                                  <td><strong>{w.student_id}</strong></td>
                                  <td>{w.ma_mon} - {w.ten_mon}</td>
                                  <td><span className="badge badge-warning" style={{ fontSize: 11.5 }}>{w.reason}</span></td>
                                  <td><strong>{w.fail_risk}%</strong></td>
                                  <td><span className="badge badge-info" style={{ fontSize: 11 }}>{w.status}</span></td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    )}

                    {/* B. Students tab */}
                    {adminActiveSubTab === "students" && (
                      <div style={{ display: "grid", gridTemplateColumns: "1fr 1.2fr", gap: 28 }}>
                        <div>
                          <h4 className="font-bold mb-4" style={{ fontSize: 16 }}>{editingStudent ? "Cập nhật thông tin Sinh viên" : "Thêm tài khoản Sinh viên"}</h4>
                          <div className="form-group">
                            <label className="form-label">Mã số sinh viên (MSSV)</label>
                            <input className="form-control" value={newStudentId} onChange={(e) => setNewStudentId(e.target.value.toUpperCase())} disabled={!!editingStudent} placeholder="VD: 23723801" />
                          </div>
                          <div className="form-group">
                            <label className="form-label">Email liên hệ</label>
                            <input className="form-control" type="email" value={newStudentEmail} onChange={(e) => setNewStudentEmail(e.target.value)} placeholder="email@smartgpa.edu" />
                          </div>
                          <div className="form-group">
                            <label className="form-label">Họ tên sinh viên</label>
                            <input className="form-control" value={newStudentName} onChange={(e) => setNewStudentName(e.target.value)} placeholder="Họ tên đầy đủ" />
                          </div>
                          <div className="form-group">
                            <label className="form-label">Lớp học</label>
                            <input className="form-control" value={newStudentClass} onChange={(e) => setNewStudentClass(e.target.value)} placeholder="DHKHDL19A" />
                          </div>
                          <div style={{ display: "flex", gap: 10, marginTop: 12 }}>
                            {editingStudent ? (
                              <>
                                <button className="btn btn-primary" onClick={() => handleUpdateStudent(newStudentId, newStudentEmail, newStudentName)} style={{ flex: 1 }}>Cập nhật</button>
                                <button className="btn btn-outline" onClick={() => {
                                  setEditingStudent(null);
                                  setNewStudentId("");
                                  setNewStudentEmail("");
                                  setNewStudentName("");
                                  setNewStudentClass("DHKHDL19A");
                                }}>Hủy</button>
                              </>
                            ) : (
                              <button className="btn btn-primary" onClick={createStudent} style={{ width: "100%" }}>Thêm mới sinh viên</button>
                            )}
                          </div>
                        </div>
                        <div>
                          <h4 className="font-bold mb-4" style={{ fontSize: 16 }}>Danh sách sinh viên ({adminUsers.filter(u => u.role === "student").length})</h4>
                          <div style={{ display: "flex", flexDirection: "column", gap: 10, maxHeight: 400, overflowY: "auto" }}>
                            {adminUsers.filter(u => u.role === "student").map((u) => (
                              <div key={u.student_id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: "1px solid var(--border-glass)", paddingBottom: 8 }}>
                                <div>
                                  <strong>{u.full_name}</strong>
                                  <p style={{ fontSize: 12, color: "var(--text-secondary)" }}>MSSV: {u.student_id} · Lớp: {u.lop_hoc || "Chưa xếp"} · Email: {u.email}</p>
                                </div>
                                <div style={{ display: "flex", gap: 6 }}>
                                  <button className="btn btn-outline btn-sm" onClick={() => {
                                    setEditingStudent(u);
                                    setNewStudentId(u.student_id);
                                    setNewStudentEmail(u.email);
                                    setNewStudentName(u.full_name);
                                    setNewStudentClass(u.lop_hoc || "DHKHDL19A");
                                  }}><i className="pi pi-pencil"></i></button>
                                  <button className="btn btn-outline btn-sm" style={{ color: "var(--color-danger)", borderColor: "var(--color-danger)" }} onClick={() => handleDeleteStudent(u.student_id)}><i className="pi pi-trash"></i></button>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      </div>
                    )}



                    {/* D. Courses tab */}
                    {adminActiveSubTab === "courses" && (
                      <div style={{ display: "grid", gridTemplateColumns: "1fr 1.2fr", gap: 28 }}>
                        <div>
                          <h4 className="font-bold mb-4" style={{ fontSize: 16 }}>{editingCourse ? "Cập nhật thông tin Môn học" : "Thêm môn học mới"}</h4>
                          <div className="form-group">
                            <label className="form-label">Mã học phần</label>
                            <input className="form-control" value={newCourseId} onChange={(e) => setNewCourseId(e.target.value.toUpperCase())} disabled={!!editingCourse} placeholder="VD: INT1306" />
                          </div>
                          <div className="form-group">
                            <label className="form-label">Tên môn học</label>
                            <input className="form-control" value={newCourseName} onChange={(e) => setNewCourseName(e.target.value)} placeholder="Tên môn học" />
                          </div>
                          <div className="form-group">
                            <label className="form-label">Loại học phần</label>
                            <select className="form-control" value={newCourseType} onChange={(e) => setNewCourseType(e.target.value)}>
                              <option value="ly_thuyet">Lý thuyết</option>
                              <option value="thuc_hanh">Thực hành</option>
                              <option value="tich_hop">Tích hợp</option>
                            </select>
                          </div>
                          <div className="form-group">
                            <label className="form-label">Số tín chỉ</label>
                            <input className="form-control" type="number" min="1" max="10" value={newCourseCredits} onChange={(e) => setNewCourseCredits(Number(e.target.value))} />
                          </div>
                          <div style={{ display: "flex", gap: 10, marginTop: 12 }}>
                            {editingCourse ? (
                              <>
                                <button className="btn btn-primary" onClick={() => handleUpdateCourse(newCourseId, newCourseName, newCourseType, newCourseCredits)} style={{ flex: 1 }}>Cập nhật</button>
                                <button className="btn btn-outline" onClick={() => {
                                  setEditingCourse(null);
                                  setNewCourseId("");
                                  setNewCourseName("");
                                  setNewCourseType("ly_thuyet");
                                  setNewCourseCredits(3);
                                }}>Hủy</button>
                              </>
                            ) : (
                              <button className="btn btn-primary" onClick={createCourse} style={{ width: "100%" }}>Thêm mới môn học</button>
                            )}
                          </div>
                        </div>
                        <div>
                          <h4 className="font-bold mb-4" style={{ fontSize: 16 }}>Danh sách môn học ({adminCourses.length})</h4>
                          <div style={{ display: "flex", flexDirection: "column", gap: 10, maxHeight: 400, overflowY: "auto" }}>
                            {adminCourses.map((c) => (
                              <div key={c.id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: "1px solid var(--border-glass)", paddingBottom: 8 }}>
                                <div>
                                  <strong>{c.name}</strong>
                                  <p style={{ fontSize: 12, color: "var(--text-secondary)" }}>Mã môn: {c.id} · Loại: {c.type === "ly_thuyet" ? "LT" : c.type === "thuc_hanh" ? "TH" : "Tích hợp"} · Tín chỉ: {c.credits} TC</p>
                                </div>
                                <div style={{ display: "flex", gap: 6 }}>
                                  <button className="btn btn-outline btn-sm" onClick={() => {
                                    setEditingCourse(c);
                                    setNewCourseId(c.id);
                                    setNewCourseName(c.name);
                                    setNewCourseType(c.type);
                                    setNewCourseCredits(c.credits);
                                  }}><i className="pi pi-pencil"></i></button>
                                  <button className="btn btn-outline btn-sm" style={{ color: "var(--color-danger)", borderColor: "var(--color-danger)" }} onClick={() => handleDeleteCourse(c.id)}><i className="pi pi-trash"></i></button>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      </div>
                    )}

                    {/* E. Assignments tab */}
                    {adminActiveSubTab === "assignments" && (
                      <div style={{ display: "grid", gridTemplateColumns: "1fr 1.2fr", gap: 28 }}>
                        <div>
                          <h4 className="font-bold mb-4" style={{ fontSize: 16 }}>Phân công Giảng viên vào môn học</h4>
                          <div className="form-group">
                            <label className="form-label">Chọn Giảng viên</label>
                            <select className="form-control" value={assignLecturerId} onChange={(e) => setAssignLecturerId(e.target.value)}>
                              <option value="">-- Chọn giảng viên --</option>
                              {adminUsers.filter(u => u.role === "lecturer").map((u) => (
                                <option key={u.lecturer_id} value={u.lecturer_id}>{u.full_name} ({u.lecturer_id})</option>
                              ))}
                            </select>
                          </div>
                          <div className="form-group">
                            <label className="form-label">Chọn Môn học</label>
                            <select className="form-control" value={assignCourseId} onChange={(e) => setAssignCourseId(e.target.value)}>
                              <option value="">-- Chọn môn học --</option>
                              {adminCourses.map((c) => (
                                <option key={c.id} value={c.id}>{c.name} ({c.id})</option>
                              ))}
                            </select>
                          </div>
                          <div className="form-group">
                            <label className="form-label">Mã lớp học phần</label>
                            <input className="form-control" value={assignClassId} onChange={(e) => setAssignClassId(e.target.value)} placeholder="L01" />
                          </div>
                          <button className="btn btn-primary" onClick={createAssignment} disabled={!assignLecturerId || !assignCourseId} style={{ width: "100%", marginTop: 8 }}>Tạo phân công</button>
                        </div>
                        <div>
                          <h4 className="font-bold mb-4" style={{ fontSize: 16 }}>Danh sách phân công hiện hành ({adminAssignments.length})</h4>
                          <div style={{ display: "flex", flexDirection: "column", gap: 10, maxHeight: 400, overflowY: "auto" }}>
                            {adminAssignments.map((a) => {
                              const lecturerName = adminUsers.find(u => u.lecturer_id === a.lecturer_id)?.full_name || a.lecturer_id;
                              const courseName = adminCourses.find(c => c.id === a.ma_mon)?.name || a.ma_mon;
                              return (
                                <div key={a.id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: "1px solid var(--border-glass)", paddingBottom: 8 }}>
                                  <div>
                                    <strong>{courseName}</strong>
                                    <p style={{ fontSize: 12, color: "var(--text-secondary)" }}>Lớp: {a.ma_lop} · GV: {lecturerName} · Học kỳ: {a.hoc_ky}</p>
                                  </div>
                                  <button className="btn btn-outline btn-sm" style={{ color: "var(--color-danger)", borderColor: "var(--color-danger)" }} onClick={() => handleDeleteAssignment(a.id)}><i className="pi pi-trash"></i></button>
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      </div>
                    )}

                    {/* F. Grades Tab */}


                    {/* G. Rules tab */}
                    {adminActiveSubTab === "rules" && (
                      <div style={{ display: "grid", gridTemplateColumns: "1.2fr 1fr", gap: 28 }}>
                        <div>
                          <h4 className="font-bold mb-4" style={{ fontSize: 16 }}>Quy chế cấu hình thang điểm hiện hành</h4>
                          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                            <div style={{ borderBottom: "1px solid var(--border-glass)", paddingBottom: 6 }}>
                              <span style={{ fontSize: 12, color: "var(--text-muted)" }}>Phiên bản quy chế:</span>
                              <p><strong>{gradingRules?.version || "2026.06"}</strong></p>
                            </div>
                            <div style={{ borderBottom: "1px solid var(--border-glass)", paddingBottom: 6 }}>
                              <span style={{ fontSize: 12, color: "var(--text-muted)" }}>Hệ số Lý thuyết:</span>
                              <p>Thường kỳ: 20%, Giữa kỳ: 30%, Cuối kỳ: 50%</p>
                            </div>
                            <div style={{ borderBottom: "1px solid var(--border-glass)", paddingBottom: 6 }}>
                              <span style={{ fontSize: 12, color: "var(--text-muted)" }}>Điểm liệt Thực hành:</span>
                              <p><strong>{gradingRules?.practice_min_pass || "3.0"} điểm</strong></p>
                            </div>
                          </div>
                        </div>
                        <div>
                          <h4 className="font-bold mb-4" style={{ fontSize: 16 }}>Thao tác quy chế</h4>
                          <p className="text-sm text-gray mb-6">Đồng bộ cấu hình quy chế mới lên FastAPI Server và Databricks warehouse.</p>
                          <button className="btn btn-outline" onClick={updateGradingRules} style={{ width: "100%" }}>Cập nhật quy chế mẫu mới</button>
                        </div>
                      </div>
                    )}

                    {/* H. Timeline tab */}
                    {adminActiveSubTab === "timeline" && (
                      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 28 }}>
                        <div>
                          <h4 className="font-bold mb-4" style={{ fontSize: 16 }}>Tạo thông báo timeline mới</h4>
                          <div className="form-group">
                            <label className="form-label">Tiêu đề</label>
                            <input className="form-control" value={timelineTitle} onChange={(e) => setTimelineTitle(e.target.value)} />
                          </div>
                          <div className="form-group">
                            <label className="form-label">Nội dung chi tiết</label>
                            <textarea className="form-control" value={timelineDetails} onChange={(e) => setTimelineDetails(e.target.value)} rows={3}></textarea>
                          </div>
                          <button className="btn btn-primary" onClick={addTimeline} style={{ width: "100%", marginTop: 8 }}>Gửi Timeline</button>
                        </div>
                        <div>
                          <h4 className="font-bold mb-4" style={{ fontSize: 16 }}>Lịch sử timeline gần đây</h4>
                          <div style={{ display: "flex", flexDirection: "column", gap: 10, maxHeight: 300, overflowY: "auto" }}>
                            {adminTimeline.slice(0, 5).map((item, idx) => (
                              <div key={idx} style={{ borderBottom: "1px solid var(--border-glass)", paddingBottom: 8 }}>
                                <strong style={{ fontSize: 13.5 }}>{item.title}</strong>
                                <p style={{ fontSize: 12, color: "var(--text-secondary)" }}>{item.details}</p>
                                <span style={{ fontSize: 10, color: "var(--text-muted)" }}>{item.timestamp}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      </div>
                    )}

                  </div>

                  {(adminStatus || adminError) && (
                    <div className={`badge ${adminError ? "badge-danger" : "badge-success"} mt-4`} style={{ width: "100%", justifyContent: "center" }}>
                      {adminError || adminStatus}
                    </div>
                  )}
            </div>
          )}

            </div>
          </div>
        </div>
      )}

      {/* Footer */}
      {!isLoggedIn && (
        <footer className="footer">
          <div className="container" style={{ display: "grid", gridTemplateColumns: "1.5fr 1fr 1fr", gap: 40 }}>
            <div>
              <strong style={{ fontSize: 20, fontFamily: "var(--font-heading)" }}>SmartGPA Platform</strong>
              <p className="text-sm text-gray mt-4" style={{ lineHeight: 1.6, maxWidth: 300 }}>
                Hệ thống giả lập lộ trình điểm học tập, phân tích và dự báo cảnh báo học vụ sớm theo kiến trúc SOA.
              </p>
            </div>
            <div>
              <h5 className="footer-link-title">Thành viên Nhóm</h5>
              <ul style={{ fontSize: 13.5, color: "var(--text-secondary)", display: "flex", flexDirection: "column", gap: 8 }}>
                <li>Nguyễn Thị Quỳnh Trang (Leader) - 23676071</li>
                <li>Vũ Ngọc Thu Phương - 23696981</li>
                <li>Phan Trần Thảo Vy - 23670631</li>
                <li>Ngô Phước Thiên - 23670311</li>
                <li>Trương Thế Hải Thịnh - 23725051</li>
              </ul>
            </div>
            <div>
              <h5 className="footer-link-title">Công nghệ</h5>
              <ul>
                <li><a href="https://databricks.com" target="_blank" rel="noreferrer">Databricks SQL & Spark</a></li>
                <li><a href="https://fastapi.tiangolo.com" target="_blank" rel="noreferrer">FastAPI Gateway</a></li>
                <li><a href="https://react.dev" target="_blank" rel="noreferrer">ReactJS & Vite</a></li>
              </ul>
            </div>
          </div>
          <div className="footer-bottom container">
            <p>© 2026 SmartGPA Project Team. Developed under SOA & Cloud Intelligence guidelines.</p>
          </div>
        </footer>
      )}
    </main>
  );
}

function downloadTemplate() {
  const blob = new Blob([SAMPLE_CSV], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "smartgpa_scores_template.csv";
  a.click();
  URL.revokeObjectURL(url);
}

function downloadXlsxTemplate() {
  // Generate IUH-format XLSX template using a data URI approach
  // We embed a pre-built CSV that demonstrates the correct format,
  // and instruct the user to use the Python generator script for actual XLSX
  const iuhCsvContent = [
    ",,,,Lớp học phần: [2101409] - Cấu trúc Dữ liệu & Giải thuật (DHKHDL19A_B)",
    ",Mã sinh viên,Họ đệm,Tên,Lớp học,Giữa kỳ,Thường xuyên 1,Thường xuyên 2,Cuối kỳ",
    "1,23001005,Nguyễn Hữu,Thuận,DHKHDL19A,6.4,7.0,6.6,7.5",
    "2,23001015,Vũ Hoàng,Phúc,DHKHDL19A,8.4,8.3,8.1,7.8",
    "3,23001025,Bùi Đức,Mạnh,DHKHDL19A,6.3,6.2,5.8,6.5",
    "4,23695481,Muhammad,Arifil,DHKHDL19B,7.5,7.0,7.2,6.8",
    "5,23723801,La Thiên,Bảo,DHKHDL19B,8.0,8.5,8.2,8.0",
  ].join("\n");
  const blob = new Blob(["\uFEFF" + iuhCsvContent], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "[2101409]_[Cau_truc_DL_Giai_thuat]_BangDiem_MAU.csv";
  a.click();
  URL.revokeObjectURL(url);
  alert(
    "ℹ️ File mẫu đã tải xuống (định dạng CSV preview).\n\n" +
    "Để có file .xlsx đúng chuẩn IUH, hãy sử dụng file bảng điểm xuất từ phần mềm trường IUH " +
    "(có dòng 'Lớp học phần: [MÃ_MÔN] - TÊN (LỚP)') – hệ thống sẽ tự nhận dạng."
  );
}
