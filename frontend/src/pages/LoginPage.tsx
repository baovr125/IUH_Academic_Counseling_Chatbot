import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import {
  Eye,
  EyeOff,
  X,
  KeyRound,
  CheckCircle2,
  AlertCircle,
  GraduationCap,
  Globe,
  Sparkles,
} from "lucide-react";


export default function LoginPage() {
  const { isAuthenticated, login, register, forgotPassword, resetPassword, isLoading, error } = useAuth();
  const navigate = useNavigate();

  // Tự động điều hướng sang /dashboard nếu đã đăng nhập
  useEffect(() => {
    if (isAuthenticated) {
      navigate("/dashboard", { replace: true });
    }
  }, [isAuthenticated, navigate]);

  // Auth mode & form state
  const [isRegistering, setIsRegistering] = useState(false);
  const [userType, setUserType] = useState<"student" | "public">("student");
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [studentCode, setStudentCode] = useState("");
  const [department, setDepartment] = useState("");
  const [major, setMajor] = useState("");

  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [clientError, setClientError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  // Helper cập nhật giá trị và xóa lỗi của field đó
  const handleFieldChange = (field: string, value: string, setter: (val: string) => void) => {
    setter(value);
    if (fieldErrors[field]) {
      setFieldErrors((prev) => {
        const next = { ...prev };
        delete next[field];
        return next;
      });
    }
    if (clientError) setClientError(null);
  };

  const switchMode = (registering: boolean) => {
    setIsRegistering(registering);
    setFieldErrors({});
    setClientError(null);
  };

  const switchUserType = (type: "student" | "public") => {
    setUserType(type);
    setFieldErrors({});
    setClientError(null);
  };

  // Forgot Password Modal state
  const [showForgotModal, setShowForgotModal] = useState(false);
  const [forgotStep, setForgotStep] = useState<1 | 2>(1);
  const [forgotEmail, setForgotEmail] = useState("");
  const [forgotOtp, setForgotOtp] = useState("");
  const [devOtpHint, setDevOtpHint] = useState<string | null>(null);
  const [forgotNewPassword, setForgotNewPassword] = useState("");
  const [forgotConfirmPassword, setForgotConfirmPassword] = useState("");
  const [showForgotNewPw, setShowForgotNewPw] = useState(false);
  const [showForgotConfirmPw, setShowForgotConfirmPw] = useState(false);
  const [forgotMsg, setForgotMsg] = useState<string | null>(null);
  const [forgotErr, setForgotErr] = useState<string | null>(null);
  const [isForgotLoading, setIsForgotLoading] = useState(false);
  const [resetSuccessMsg, setResetSuccessMsg] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setClientError(null);
    const newFieldErrors: Record<string, string> = {};

    if (isRegistering) {
      // 1. Kiểm tra Họ và tên
      if (!fullName.trim()) {
        newFieldErrors.fullName = "Họ và tên không được để trống.";
      } else if (fullName.trim().length < 2 || fullName.trim().length > 100) {
        newFieldErrors.fullName = "Họ và tên bắt buộc từ 2 đến 100 ký tự.";
      }

      // 2. Kiểm tra Email
      if (!identifier.trim()) {
        newFieldErrors.identifier = "Email đăng ký không được để trống.";
      } else if (!/^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)+$/.test(identifier.trim())) {
        newFieldErrors.identifier = "Email không đúng định dạng tiêu chuẩn (VD: ten@gmail.com).";
      } else if (userType === "student") {
        const emLower = identifier.trim().toLowerCase();
        if (!emLower.endsWith("@student.iuh.edu.vn") && !emLower.endsWith("@iuh.edu.vn")) {
          newFieldErrors.identifier = "Email sinh viên / GV IUH phải có đuôi @student.iuh.edu.vn hoặc @iuh.edu.vn.";
        }
      }

      // 3. Kiểm tra thông tin Sinh viên IUH
      if (userType === "student") {
        if (!studentCode.trim()) {
          newFieldErrors.studentCode = "Mã số sinh viên (MSSV) không được để trống.";
        } else if (!/^\d{8}$/.test(studentCode.trim())) {
          newFieldErrors.studentCode = "Mã số sinh viên phải chứa đúng 8 chữ số (VD: 20045211).";
        }

        if (!department.trim()) {
          newFieldErrors.department = "Khoa / Viện không được để trống.";
        }

        if (!major.trim()) {
          newFieldErrors.major = "Ngành học không được để trống.";
        }
      }

      // 4. Kiểm tra Mật khẩu
      if (!password) {
        newFieldErrors.password = "Mật khẩu không được để trống.";
      } else if (password.length < 8) {
        newFieldErrors.password = "Mật khẩu phải có tối thiểu 8 ký tự.";
      } else if (!/[A-Za-z]/.test(password)) {
        newFieldErrors.password = "Mật khẩu phải bao gồm ít nhất một chữ cái.";
      } else if (!/\d/.test(password)) {
        newFieldErrors.password = "Mật khẩu phải bao gồm ít nhất một chữ số.";
      }

      // 5. Kiểm tra Xác nhận mật khẩu
      if (!confirmPassword) {
        newFieldErrors.confirmPassword = "Vui lòng xác nhận lại mật khẩu.";
      } else if (password !== confirmPassword) {
        newFieldErrors.confirmPassword = "Mật khẩu xác nhận không trùng khớp.";
      }

      // Nếu có lỗi Client-side validation, chặn submit ngay lập tức
      if (Object.keys(newFieldErrors).length > 0) {
        setFieldErrors(newFieldErrors);
        setClientError("Vui lòng kiểm tra và điền đầy đủ các thông tin bị lỗi bên dưới.");
        return;
      }

      setFieldErrors({});
      const regIdentifier = identifier.trim();
      const result = await register({
        fullName: fullName.trim(),
        identifier: regIdentifier,
        password,
        confirmPassword,
        userType,
        studentCode: userType === "student" ? studentCode.trim() : undefined,
        department: userType === "student" ? department.trim() : undefined,
        major: userType === "student" ? major.trim() : undefined,
      });

      if (result.ok) {
        setIsRegistering(false);
        setIdentifier(regIdentifier);
        setPassword("");
        setConfirmPassword("");
        setFieldErrors({});
        setResetSuccessMsg("Đăng ký tài khoản thành công! Vui lòng đăng nhập.");
        setTimeout(() => setResetSuccessMsg(null), 8000);
      } else {
        const serverFieldErrors: Record<string, string> = {};
        const mapField: Record<string, string> = {
          email: "identifier",
          identifier: "identifier",
          student_code: "studentCode",
          studentCode: "studentCode",
          full_name: "fullName",
          fullName: "fullName",
          department: "department",
          major: "major",
          password: "password",
          confirm_password: "confirmPassword",
        };

        if (result.field) {
          const uiField = mapField[result.field] || result.field;
          serverFieldErrors[uiField] = result.message || "Thông tin không hợp lệ.";
        }

        if (result.details && Array.isArray(result.details)) {
          result.details.forEach((item) => {
            const uiField = mapField[item.field] || item.field;
            serverFieldErrors[uiField] = item.message;
          });
        }

        // Tự động phân tích message nếu chưa có mapping
        if (Object.keys(serverFieldErrors).length === 0 && result.message) {
          const msgLower = result.message.toLowerCase();
          if (msgLower.includes("email")) {
            serverFieldErrors.identifier = result.message;
          } else if (msgLower.includes("sinh viên") || msgLower.includes("mssv")) {
            serverFieldErrors.studentCode = result.message;
          } else if (msgLower.includes("mật khẩu")) {
            serverFieldErrors.password = result.message;
          } else if (msgLower.includes("khoa") || msgLower.includes("viện")) {
            serverFieldErrors.department = result.message;
          } else if (msgLower.includes("ngành")) {
            serverFieldErrors.major = result.message;
          } else if (msgLower.includes("họ và tên")) {
            serverFieldErrors.fullName = result.message;
          }
        }

        if (Object.keys(serverFieldErrors).length > 0) {
          setFieldErrors(serverFieldErrors);
        }
        setClientError(result.message || "Đăng ký không thành công. Vui lòng thử lại.");
      }
    } else {
      // Đăng nhập
      if (!identifier.trim()) {
        newFieldErrors.identifier = "Vui lòng nhập Email hoặc Mã số sinh viên.";
      }
      if (!password) {
        newFieldErrors.password = "Vui lòng nhập mật khẩu.";
      }

      if (Object.keys(newFieldErrors).length > 0) {
        setFieldErrors(newFieldErrors);
        setClientError("Vui lòng nhập đầy đủ tài khoản và mật khẩu.");
        return;
      }

      setFieldErrors({});
      const ok = await login({ identifier: identifier.trim(), password });
      if (ok) navigate("/dashboard");
    }
  };

  // Xử lý gửi OTP Quên mật khẩu (Bước 1)
  const handleForgotStep1 = async (e: React.FormEvent) => {
    e.preventDefault();
    setForgotMsg(null);
    setForgotErr(null);

    if (!forgotEmail || !forgotEmail.includes("@")) {
      setForgotErr("Vui lòng nhập Email hợp lệ.");
      return;
    }

    setIsForgotLoading(true);
    const result = await forgotPassword(forgotEmail);
    setIsForgotLoading(false);

    if (!result.ok) {
      setForgotErr(result.message || "Không thể gửi yêu cầu mã OTP.");
    } else {
      setForgotMsg(result.message || "Đã tạo mã OTP khôi phục mật khẩu.");
      if (result.devOtp) {
        setDevOtpHint(result.devOtp);
      }
      setForgotStep(2);
    }
  };

  // Xử lý xác nhận OTP & Đặt lại mật khẩu (Bước 2)
  const handleForgotStep2 = async (e: React.FormEvent) => {
    e.preventDefault();
    setForgotMsg(null);
    setForgotErr(null);

    if (!forgotOtp) {
      setForgotErr("Vui lòng nhập mã OTP.");
      return;
    }
    if (!forgotNewPassword || forgotNewPassword.length < 6) {
      setForgotErr("Mật khẩu mới phải có ít nhất 6 ký tự.");
      return;
    }
    if (forgotNewPassword !== forgotConfirmPassword) {
      setForgotErr("Mật khẩu xác nhận không trùng khớp.");
      return;
    }

    setIsForgotLoading(true);
    const result = await resetPassword({
      email: forgotEmail,
      otp: forgotOtp,
      newPassword: forgotNewPassword,
      confirmPassword: forgotConfirmPassword,
    });
    setIsForgotLoading(false);

    if (!result.ok) {
      setForgotErr(result.message || "Đặt lại mật khẩu thất bại.");
    } else {
      setShowForgotModal(false);
      setForgotStep(1);
      setForgotEmail("");
      setForgotOtp("");
      setForgotNewPassword("");
      setForgotConfirmPassword("");
      setDevOtpHint(null);
      setResetSuccessMsg("Mật khẩu đã được đặt lại thành công! Bạn có thể đăng nhập ngay.");
      setTimeout(() => setResetSuccessMsg(null), 8000);
    }
  };

  return (
    <div className="flex min-h-screen">
      {/* Left side banner */}
      <div className="hidden lg:flex lg:w-1/2 flex-col justify-between bg-gradient-to-br from-blue-900 via-blue-800 to-indigo-950 p-12 text-white relative overflow-hidden">
        {/* Background glow effects */}
        <div className="absolute -top-24 -left-24 w-96 h-96 bg-blue-500/20 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -bottom-24 -right-24 w-96 h-96 bg-indigo-500/20 rounded-full blur-3xl pointer-events-none" />

        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white/10 backdrop-blur-sm border border-white/20">
            <Sparkles className="h-5 w-5 text-blue-300" />
          </div>
          <div>
            <span className="font-bold text-lg tracking-tight">IUH Portal AI</span>
            <p className="text-[10px] text-blue-300">Đại học Công nghiệp TP. Hồ Chí Minh</p>
          </div>
        </div>

        <div className="space-y-4 my-auto py-12">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/20 border border-blue-400/30 text-blue-300 text-xs font-medium">
            <GraduationCap size={14} />
            <span>Trợ lý Học vụ & Học tập Đa tác vụ</span>
          </div>
          <h1 className="text-3xl font-extrabold leading-tight text-white lg:text-4xl">
            Tối ưu hóa học tập <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-300 via-indigo-200 to-white">
              và tư vấn học vụ thông minh
            </span>
          </h1>
          <p className="text-sm text-blue-100/80 max-w-md leading-relaxed">
            Hỏi đáp quy chế đào tạo, dịch thuật tài liệu chuyên ngành, ghi nhớ kiến thức với Flashcard FSRS thông minh và theo dõi tiến độ học tập toàn diện.
          </p>
        </div>
        <span className="w-fit rounded-full bg-white/10 px-3.5 py-1.5 text-xs font-medium">
          Hệ thống sẵn sàng cho HK2 · 2026
        </span>
      </div>

      {/* Right side form */}
      <div className="flex w-full items-center justify-center bg-slate-50 p-6 lg:w-1/2 overflow-y-auto">
        <form onSubmit={handleSubmit} noValidate className="w-full max-w-md rounded-2xl bg-white p-8 shadow-sm my-auto">
          {/* Tab chuyển đổi Đăng nhập / Đăng ký */}
          <div className="mb-6 flex rounded-xl bg-slate-100 p-1">
            <button
              type="button"
              onClick={() => switchMode(false)}
              className={`flex-1 rounded-lg py-2 text-xs font-semibold transition-all ${
                !isRegistering
                  ? "bg-white text-blue-700 shadow-sm"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              Đăng nhập
            </button>
            <button
              type="button"
              onClick={() => switchMode(true)}
              className={`flex-1 rounded-lg py-2 text-xs font-semibold transition-all ${
                isRegistering
                  ? "bg-white text-blue-700 shadow-sm"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              Đăng ký tài khoản
            </button>
          </div>

          <h2 className="mb-1 text-xl font-bold text-slate-800">
            {isRegistering ? "Tạo tài khoản mới" : "Chào mừng đến với IUH Portal AI"}
          </h2>
          <p className="mb-5 text-xs text-slate-500">
            {isRegistering
              ? "Chọn đối tượng sử dụng và điền đầy đủ thông tin bên dưới"
              : "Đăng nhập bằng Email hoặc Mã số sinh viên để tiếp tục"}
          </p>

          {resetSuccessMsg && (
            <div className="mb-4 flex items-center gap-2 rounded-xl bg-green-50 border border-green-200 p-3 text-xs text-green-800 font-medium">
              <CheckCircle2 size={16} className="text-green-600 flex-shrink-0" />
              <span>{resetSuccessMsg}</span>
            </div>
          )}

          {/* Form Đăng ký 2 chế độ: Student vs Public */}
          {isRegistering && (
            <div className="mb-5 space-y-3">
              <label className="block text-xs font-semibold text-slate-700">
                Đối tượng sử dụng hệ thống
              </label>
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => switchUserType("student")}
                  className={`flex items-center justify-center gap-2 rounded-xl border p-2.5 text-xs font-semibold transition-all ${
                    userType === "student"
                      ? "border-blue-600 bg-blue-50/80 text-blue-700 shadow-sm"
                      : "border-slate-200 bg-white text-slate-600 hover:bg-slate-50"
                  }`}
                >
                  <GraduationCap size={16} />
                  <span>Sinh viên / GV IUH</span>
                </button>

                <button
                  type="button"
                  onClick={() => switchUserType("public")}
                  className={`flex items-center justify-center gap-2 rounded-xl border p-2.5 text-xs font-semibold transition-all ${
                    userType === "public"
                      ? "border-blue-600 bg-blue-50/80 text-blue-700 shadow-sm"
                      : "border-slate-200 bg-white text-slate-600 hover:bg-slate-50"
                  }`}
                >
                  <Globe size={16} />
                  <span>Người dùng công cộng</span>
                </button>
              </div>

              {/* Ô Họ và tên */}
              <div>
                <label className="mb-1 block text-xs font-medium text-slate-600">
                  Họ và tên <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => handleFieldChange("fullName", e.target.value, setFullName)}
                  placeholder="Ví dụ: Nguyễn Văn Bảo..."
                  className={`w-full rounded-lg border px-3 py-2 text-xs transition-colors focus:outline-none ${
                    fieldErrors.fullName
                      ? "border-red-500 bg-red-50/20 text-slate-800 focus:border-red-500 focus:ring-1 focus:ring-red-500"
                      : "border-slate-200 text-slate-800 focus:border-blue-400"
                  }`}
                />
                {fieldErrors.fullName && (
                  <p className="mt-1 text-[11px] font-medium text-red-600 flex items-center gap-1">
                    <AlertCircle size={13} className="flex-shrink-0" />
                    <span>{fieldErrors.fullName}</span>
                  </p>
                )}
              </div>

              {/* Nếu là sinh viên: Hiện 3 ô học vụ */}
              {userType === "student" && (
                <>
                  <div>
                    <label className="mb-1 block text-xs font-medium text-slate-600">
                      Mã số sinh viên (MSSV) <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="text"
                      value={studentCode}
                      onChange={(e) => handleFieldChange("studentCode", e.target.value, setStudentCode)}
                      placeholder="Ví dụ: 20045211 (8 chữ số)..."
                      className={`w-full rounded-lg border px-3 py-2 text-xs transition-colors focus:outline-none ${
                        fieldErrors.studentCode
                          ? "border-red-500 bg-red-50/20 text-slate-800 focus:border-red-500 focus:ring-1 focus:ring-red-500"
                          : "border-slate-200 text-slate-800 focus:border-blue-400"
                      }`}
                    />
                    {fieldErrors.studentCode && (
                      <p className="mt-1 text-[11px] font-medium text-red-600 flex items-center gap-1">
                        <AlertCircle size={13} className="flex-shrink-0" />
                        <span>{fieldErrors.studentCode}</span>
                      </p>
                    )}
                  </div>

                  <div>
                    <label className="mb-1 block text-xs font-medium text-slate-600">
                      Khoa / Viện <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="text"
                      value={department}
                      onChange={(e) => handleFieldChange("department", e.target.value, setDepartment)}
                      placeholder="Ví dụ: Khoa Công nghệ Thông tin..."
                      className={`w-full rounded-lg border px-3 py-2 text-xs transition-colors focus:outline-none ${
                        fieldErrors.department
                          ? "border-red-500 bg-red-50/20 text-slate-800 focus:border-red-500 focus:ring-1 focus:ring-red-500"
                          : "border-slate-200 text-slate-800 focus:border-blue-400"
                      }`}
                    />
                    {fieldErrors.department && (
                      <p className="mt-1 text-[11px] font-medium text-red-600 flex items-center gap-1">
                        <AlertCircle size={13} className="flex-shrink-0" />
                        <span>{fieldErrors.department}</span>
                      </p>
                    )}
                  </div>

                  <div>
                    <label className="mb-1 block text-xs font-medium text-slate-600">
                      Ngành học <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="text"
                      value={major}
                      onChange={(e) => handleFieldChange("major", e.target.value, setMajor)}
                      placeholder="Ví dụ: Kỹ thuật Phần mềm..."
                      className={`w-full rounded-lg border px-3 py-2 text-xs transition-colors focus:outline-none ${
                        fieldErrors.major
                          ? "border-red-500 bg-red-50/20 text-slate-800 focus:border-red-500 focus:ring-1 focus:ring-red-500"
                          : "border-slate-200 text-slate-800 focus:border-blue-400"
                      }`}
                    />
                    {fieldErrors.major && (
                      <p className="mt-1 text-[11px] font-medium text-red-600 flex items-center gap-1">
                        <AlertCircle size={13} className="flex-shrink-0" />
                        <span>{fieldErrors.major}</span>
                      </p>
                    )}
                  </div>
                </>
              )}
            </div>
          )}

          {/* Ô nhập Email hoặc Mã số */}
          <div className="mb-4">
            <label className="mb-1 block text-xs font-medium text-slate-600">
              {isRegistering
                ? userType === "student"
                  ? "Email sinh viên / GV IUH"
                  : "Email đăng ký"
                : "Mã số sinh viên hoặc Email đăng nhập"} <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={identifier}
              onChange={(e) => handleFieldChange("identifier", e.target.value, setIdentifier)}
              placeholder={
                isRegistering
                  ? userType === "student"
                    ? "nhapemail@student.iuh.edu.vn..."
                    : "nhapemail@gmail.com..."
                  : "Nhập mã số hoặc email..."
              }
              className={`w-full rounded-lg border px-3 py-2 text-xs transition-colors focus:outline-none ${
                fieldErrors.identifier
                  ? "border-red-500 bg-red-50/20 text-slate-800 focus:border-red-500 focus:ring-1 focus:ring-red-500"
                  : "border-slate-200 text-slate-800 focus:border-blue-400"
              }`}
            />
            {fieldErrors.identifier && (
              <p className="mt-1 text-[11px] font-medium text-red-600 flex items-center gap-1">
                <AlertCircle size={13} className="flex-shrink-0" />
                <span>{fieldErrors.identifier}</span>
              </p>
            )}
          </div>

          {/* Ô nhập Mật khẩu */}
          <div className="mb-3">
            <label className="mb-1 block text-xs font-medium text-slate-600">
              Mật khẩu <span className="text-red-500">*</span>
            </label>
            <div className="relative">
              <input
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(e) => handleFieldChange("password", e.target.value, setPassword)}
                placeholder="Tối thiểu 8 ký tự (chứa chữ và số)..."
                className={`w-full rounded-lg border px-3 py-2 pr-9 text-xs transition-colors focus:outline-none ${
                  fieldErrors.password
                    ? "border-red-500 bg-red-50/20 text-slate-800 focus:border-red-500 focus:ring-1 focus:ring-red-500"
                    : "border-slate-200 text-slate-800 focus:border-blue-400"
                }`}
              />
              <button
                type="button"
                onClick={() => setShowPassword((prev) => !prev)}
                className="absolute right-2.5 top-2 text-slate-400 hover:text-slate-600"
              >
                {showPassword ? <EyeOff size={15} /> : <Eye size={15} />}
              </button>
            </div>
            {fieldErrors.password && (
              <p className="mt-1 text-[11px] font-medium text-red-600 flex items-center gap-1">
                <AlertCircle size={13} className="flex-shrink-0" />
                <span>{fieldErrors.password}</span>
              </p>
            )}

            {/* Nút Quên mật khẩu? (chỉ hiện khi Đăng nhập) */}
            {!isRegistering && (
              <div className="mt-1 text-right">
                <button
                  type="button"
                  onClick={() => {
                    setShowForgotModal(true);
                    setForgotStep(1);
                    setForgotEmail(identifier.includes("@") ? identifier : "");
                    setForgotMsg(null);
                    setForgotErr(null);
                    setDevOtpHint(null);
                  }}
                  className="text-[11px] font-semibold text-blue-600 hover:underline"
                >
                  Quên mật khẩu?
                </button>
              </div>
            )}
          </div>

          {/* Ô nhập Xác nhận mật khẩu (khi Đăng ký) */}
          {isRegistering && (
            <div className="mb-4">
              <label className="mb-1 block text-xs font-medium text-slate-600">
                Xác nhận mật khẩu <span className="text-red-500">*</span>
              </label>
              <div className="relative">
                <input
                  type={showConfirmPassword ? "text" : "password"}
                  value={confirmPassword}
                  onChange={(e) => handleFieldChange("confirmPassword", e.target.value, setConfirmPassword)}
                  placeholder="Nhập lại mật khẩu..."
                  className={`w-full rounded-lg border px-3 py-2 pr-9 text-xs transition-colors focus:outline-none ${
                    fieldErrors.confirmPassword
                      ? "border-red-500 bg-red-50/20 text-slate-800 focus:border-red-500 focus:ring-1 focus:ring-red-500"
                      : "border-slate-200 text-slate-800 focus:border-blue-400"
                  }`}
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword((prev) => !prev)}
                  className="absolute right-2.5 top-2 text-slate-400 hover:text-slate-600"
                >
                  {showConfirmPassword ? <EyeOff size={15} /> : <Eye size={15} />}
                </button>
              </div>
              {fieldErrors.confirmPassword && (
                <p className="mt-1 text-[11px] font-medium text-red-600 flex items-center gap-1">
                  <AlertCircle size={13} className="flex-shrink-0" />
                  <span>{fieldErrors.confirmPassword}</span>
                </p>
              )}
            </div>
          )}

          {(clientError || error) && (
            <div className="mb-4 flex items-center gap-2 rounded-xl bg-red-50 border border-red-200 p-3 text-xs text-red-800 font-medium">
              <AlertCircle size={16} className="text-red-600 flex-shrink-0" />
              <span>
                {typeof (clientError || error) === "string"
                  ? (clientError || error)
                  : JSON.stringify(clientError || error)}
              </span>
            </div>
          )}

          <button
            type="submit"
            disabled={isLoading}
            className="mb-3 w-full rounded-lg bg-blue-700 py-2.5 text-xs font-semibold text-white hover:bg-blue-800 disabled:opacity-60 transition-colors shadow-sm"
          >
            {isLoading
              ? isRegistering
                ? "Đang đăng ký..."
                : "Đang đăng nhập..."
              : isRegistering
              ? "Đăng ký tài khoản"
              : "Đăng nhập"}
          </button>

          <div className="mt-6 text-center text-xs text-slate-500">
            {isRegistering ? (
              <span>
                Đã có tài khoản?{" "}
                <button
                  type="button"
                  onClick={() => switchMode(false)}
                  className="font-semibold text-blue-600 hover:underline"
                >
                  Đăng nhập ngay
                </button>
              </span>
            ) : (
              <span>
                Chưa có tài khoản?{" "}
                <button
                  type="button"
                  onClick={() => setIsRegistering(true)}
                  className="font-semibold text-blue-600 hover:underline"
                >
                  Đăng ký tài khoản
                </button>
              </span>
            )}
          </div>
        </form>
      </div>

      {/* Modal Quên Mật Khẩu (2 bước) */}
      {showForgotModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm p-4">
          <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl border border-slate-100 relative">
            <button
              type="button"
              onClick={() => setShowForgotModal(false)}
              className="absolute right-4 top-4 text-slate-400 hover:text-slate-600"
            >
              <X size={18} />
            </button>

            <div className="flex items-center gap-2 mb-2">
              <KeyRound className="w-5 h-5 text-blue-600" />
              <h3 className="text-base font-bold text-slate-800">
                {forgotStep === 1 ? "Khôi phục mật khẩu (Bước 1/2)" : "Nhập mã OTP & Đặt lại mật khẩu (Bước 2/2)"}
              </h3>
            </div>

            {forgotErr && (
              <div className="mb-4 flex items-center gap-2 rounded-xl bg-red-50 border border-red-200 p-3 text-xs text-red-800 font-medium">
                <AlertCircle size={16} className="text-red-600 flex-shrink-0" />
                <span>{forgotErr}</span>
              </div>
            )}

            {forgotMsg && (
              <div className="mb-4 flex items-center gap-2 rounded-xl bg-green-50 border border-green-200 p-3 text-xs text-green-800 font-medium">
                <CheckCircle2 size={16} className="text-green-600 flex-shrink-0" />
                <span>{forgotMsg}</span>
              </div>
            )}

            {/* Bước 1: Nhập Email */}
            {forgotStep === 1 ? (
              <form onSubmit={handleForgotStep1} className="space-y-4">
                <p className="text-xs text-slate-500">
                  Nhập địa chỉ Email đăng ký tài khoản của bạn. Hệ thống sẽ tạo mã OTP xác minh khôi phục mật khẩu.
                </p>

                <div>
                  <label className="mb-1 block text-xs font-semibold text-slate-700">Email khôi phục</label>
                  <input
                    type="email"
                    value={forgotEmail}
                    onChange={(e) => setForgotEmail(e.target.value)}
                    placeholder="ví dụ: student@iuh.edu.vn..."
                    required
                    className="w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-xs text-slate-800 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100"
                  />
                </div>

                <div className="flex justify-end gap-2 pt-2">
                  <button
                    type="button"
                    onClick={() => setShowForgotModal(false)}
                    className="px-4 py-2 rounded-xl border border-slate-200 text-xs font-semibold text-slate-600 hover:bg-slate-50"
                  >
                    Hủy
                  </button>
                  <button
                    type="submit"
                    disabled={isForgotLoading}
                    className="px-4 py-2 rounded-xl bg-blue-600 text-xs font-semibold text-white shadow-sm hover:bg-blue-700 disabled:opacity-60"
                  >
                    {isForgotLoading ? "Đang tạo mã OTP..." : "Tiếp tục nhận OTP"}
                  </button>
                </div>
              </form>
            ) : (
              /* Bước 2: Nhập OTP + Mật khẩu mới */
              <form onSubmit={handleForgotStep2} className="space-y-4">
                <p className="text-xs text-slate-500">
                  Mã OTP đã được tạo cho email <strong className="text-slate-800">{forgotEmail}</strong>.
                </p>

                {devOtpHint && (
                  <div className="rounded-xl border border-blue-200 bg-blue-50 p-3 text-xs font-semibold text-blue-800">
                    💡 Mã OTP Demo phát triển: <span className="font-mono text-sm tracking-widest bg-white px-2 py-0.5 rounded border border-blue-300 text-blue-900">{devOtpHint}</span>
                  </div>
                )}

                <div>
                  <label className="mb-1 block text-xs font-semibold text-slate-700">
                    Mã OTP 6 số <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={forgotOtp}
                    onChange={(e) => setForgotOtp(e.target.value)}
                    placeholder="Nhập 6 chữ số OTP..."
                    maxLength={6}
                    required
                    className="w-full rounded-xl border border-slate-200 px-3.5 py-2.5 font-mono text-center text-sm font-bold tracking-widest text-slate-800 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100"
                  />
                </div>

                <div>
                  <label className="mb-1 block text-xs font-semibold text-slate-700">Mật khẩu mới</label>
                  <div className="relative">
                    <input
                      type={showForgotNewPw ? "text" : "password"}
                      value={forgotNewPassword}
                      onChange={(e) => setForgotNewPassword(e.target.value)}
                      placeholder="Ít nhất 6 ký tự..."
                      required
                      className="w-full rounded-xl border border-slate-200 px-3.5 py-2.5 pr-9 text-xs text-slate-800 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100"
                    />
                    <button
                      type="button"
                      onClick={() => setShowForgotNewPw((p) => !p)}
                      className="absolute right-3 top-2.5 text-slate-400 hover:text-slate-600"
                    >
                      {showForgotNewPw ? <EyeOff size={15} /> : <Eye size={15} />}
                    </button>
                  </div>
                </div>

                <div>
                  <label className="mb-1 block text-xs font-semibold text-slate-700">Xác nhận mật khẩu mới</label>
                  <div className="relative">
                    <input
                      type={showForgotConfirmPw ? "text" : "password"}
                      value={forgotConfirmPassword}
                      onChange={(e) => setForgotConfirmPassword(e.target.value)}
                      placeholder="Nhập lại mật khẩu..."
                      required
                      className="w-full rounded-xl border border-slate-200 px-3.5 py-2.5 pr-9 text-xs text-slate-800 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100"
                    />
                    <button
                      type="button"
                      onClick={() => setShowForgotConfirmPw((p) => !p)}
                      className="absolute right-3 top-2.5 text-slate-400 hover:text-slate-600"
                    >
                      {showForgotConfirmPw ? <EyeOff size={15} /> : <Eye size={15} />}
                    </button>
                  </div>
                </div>

                <div className="flex justify-between items-center pt-2">
                  <button
                    type="button"
                    onClick={() => setForgotStep(1)}
                    className="text-xs font-semibold text-blue-600 hover:underline"
                  >
                    ← Quay lại nhập Email
                  </button>

                  <div className="flex gap-2">
                    <button
                      type="button"
                      onClick={() => setShowForgotModal(false)}
                      className="px-4 py-2 rounded-xl border border-slate-200 text-xs font-semibold text-slate-600 hover:bg-slate-50"
                    >
                      Hủy
                    </button>
                    <button
                      type="submit"
                      disabled={isForgotLoading}
                      className="px-4 py-2 rounded-xl bg-blue-600 text-xs font-semibold text-white shadow-sm hover:bg-blue-700 disabled:opacity-60"
                    >
                      {isForgotLoading ? "Đang xử lý..." : "Đặt lại mật khẩu"}
                    </button>
                  </div>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
