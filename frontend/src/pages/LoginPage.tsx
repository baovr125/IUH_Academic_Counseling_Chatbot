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
  Sparkles,
  GraduationCap,
  Globe,
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

    if (isRegistering) {
      if (!fullName || fullName.trim().length < 2) {
        setClientError("Họ và tên phải chứa ít nhất 2 ký tự.");
        return;
      }
      if (userType === "student" && (!studentCode || !studentCode.trim())) {
        setClientError("Mã số sinh viên (MSSV) là bắt buộc đối với tài khoản Sinh viên.");
        return;
      }
      if (!identifier || !identifier.includes("@")) {
        setClientError("Vui lòng nhập Email hợp lệ (chứa ký tự '@').");
        return;
      }
      if (!password || password.length < 6) {
        setClientError("Mật khẩu phải có ít nhất 6 ký tự.");
        return;
      }
      if (password !== confirmPassword) {
        setClientError("Mật khẩu xác nhận không trùng khớp.");
        return;
      }

      const ok = await register({
        fullName: fullName.trim(),
        identifier: identifier.trim(),
        password,
        confirmPassword,
        userType,
        studentCode: userType === "student" ? studentCode.trim() : undefined,
        department: userType === "student" ? department.trim() : undefined,
        major: userType === "student" ? major.trim() : undefined,
      });
      if (ok) navigate("/dashboard");
    } else {
      if (!identifier || !identifier.trim()) {
        setClientError("Vui lòng nhập Email hoặc Mã số sinh viên.");
        return;
      }
      if (!password) {
        setClientError("Vui lòng nhập mật khẩu.");
        return;
      }

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
      setForgotErr("Vui lòng nhập mã OTP 6 số.");
      return;
    }

    if (!forgotNewPassword || forgotNewPassword.length < 6) {
      setForgotErr("Mật khẩu mới phải có ít nhất 6 ký tự.");
      return;
    }

    if (forgotNewPassword !== forgotConfirmPassword) {
      setForgotErr("Mật khẩu xác nhận không khớp.");
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
      setForgotErr(result.message || "Xác nhận mã OTP hoặc đổi mật khẩu thất bại.");
    } else {
      setShowForgotModal(false);
      setIdentifier(forgotEmail);
      setPassword("");
      setResetSuccessMsg("Đặt lại mật khẩu thành công! Vui lòng đăng nhập bằng mật khẩu mới.");
      setTimeout(() => setResetSuccessMsg(null), 6000);
    }
  };

  return (
    <div className="flex h-screen w-full">
      {/* Left side banner */}
      <div className="hidden w-1/2 flex-col justify-between bg-[#152a6e] p-10 text-white lg:flex">
        <span className="font-semibold text-lg flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-amber-300" />
          IUH Portal AI
        </span>
        <div>
          <h1 className="mb-3 text-3xl font-bold leading-tight">
            Hệ thống Trợ lý Học vụ Thông minh IUH
          </h1>
          <p className="text-blue-200 text-sm leading-relaxed">
            Tra cứu quy chế, dịch thuật tài liệu học thuật trong vài giây. Một giải pháp AI đột phá
            dành cho cộng đồng Trường Đại học Công nghiệp TP.HCM.
          </p>
        </div>
        <span className="w-fit rounded-full bg-white/10 px-3.5 py-1.5 text-xs font-medium">
          Hệ thống sẵn sàng cho HK2 · 2026
        </span>
      </div>

      {/* Right side form */}
      <div className="flex w-full items-center justify-center bg-slate-50 p-6 lg:w-1/2 overflow-y-auto">
        <form onSubmit={handleSubmit} className="w-full max-w-md rounded-2xl bg-white p-8 shadow-sm my-auto">
          {/* Tab chuyển đổi Đăng nhập / Đăng ký */}
          <div className="mb-6 flex rounded-xl bg-slate-100 p-1">
            <button
              type="button"
              onClick={() => setIsRegistering(false)}
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
              onClick={() => setIsRegistering(true)}
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
                  onClick={() => setUserType("student")}
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
                  onClick={() => setUserType("public")}
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

              {/* Các ô thông tin theo chế độ */}
              <div>
                <label className="mb-1 block text-xs font-medium text-slate-600">Họ và tên</label>
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="Nhập họ và tên của bạn..."
                  required={isRegistering}
                  className="w-full rounded-lg border border-slate-200 px-3 py-2 text-xs focus:border-blue-400 focus:outline-none"
                />
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
                      onChange={(e) => setStudentCode(e.target.value)}
                      placeholder="Ví dụ: 20045211..."
                      required={userType === "student"}
                      className="w-full rounded-lg border border-slate-200 px-3 py-2 text-xs focus:border-blue-400 focus:outline-none"
                    />
                  </div>

                  <div>
                    <label className="mb-1 block text-xs font-medium text-slate-600">Khoa / Viện</label>
                    <input
                      type="text"
                      value={department}
                      onChange={(e) => setDepartment(e.target.value)}
                      placeholder="Ví dụ: Khoa Công nghệ Thông tin..."
                      className="w-full rounded-lg border border-slate-200 px-3 py-2 text-xs focus:border-blue-400 focus:outline-none"
                    />
                  </div>

                  <div>
                    <label className="mb-1 block text-xs font-medium text-slate-600">Ngành học</label>
                    <input
                      type="text"
                      value={major}
                      onChange={(e) => setMajor(e.target.value)}
                      placeholder="Ví dụ: Kỹ thuật Phần mềm..."
                      className="w-full rounded-lg border border-slate-200 px-3 py-2 text-xs focus:border-blue-400 focus:outline-none"
                    />
                  </div>
                </>
              )}
            </div>
          )}

          {/* Ô nhập Email hoặc Mã số */}
          <div className="mb-4">
            <label className="mb-1 block text-xs font-medium text-slate-600">
              {isRegistering
                ? "Email đăng ký"
                : "Mã số sinh viên hoặc Email đăng nhập"}
            </label>
            <input
              type="text"
              value={identifier}
              onChange={(e) => setIdentifier(e.target.value)}
              placeholder={isRegistering ? "nhapemail@iuh.edu.vn..." : "Nhập mã số hoặc email..."}
              required
              className="w-full rounded-lg border border-slate-200 px-3 py-2 text-xs focus:border-blue-400 focus:outline-none"
            />
          </div>

          {/* Ô nhập Mật khẩu */}
          <div className="mb-3">
            <label className="mb-1 block text-xs font-medium text-slate-600">Mật khẩu</label>
            <div className="relative">
              <input
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
                className="w-full rounded-lg border border-slate-200 px-3 py-2 pr-9 text-xs focus:border-blue-400 focus:outline-none"
              />
              <button
                type="button"
                onClick={() => setShowPassword((prev) => !prev)}
                className="absolute right-2.5 top-2 text-slate-400 hover:text-slate-600"
              >
                {showPassword ? <EyeOff size={15} /> : <Eye size={15} />}
              </button>
            </div>

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
                Xác nhận mật khẩu
              </label>
              <div className="relative">
                <input
                  type={showConfirmPassword ? "text" : "password"}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="••••••••"
                  required={isRegistering}
                  className="w-full rounded-lg border border-slate-200 px-3 py-2 pr-9 text-xs focus:border-blue-400 focus:outline-none"
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword((prev) => !prev)}
                  className="absolute right-2.5 top-2 text-slate-400 hover:text-slate-600"
                >
                  {showConfirmPassword ? <EyeOff size={15} /> : <Eye size={15} />}
                </button>
              </div>
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

          {/* Quick Bypass Test Mode Button */}
          <div className="relative my-4">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-slate-200" />
            </div>
            <div className="relative flex justify-center text-[10px] uppercase">
              <span className="bg-white px-2 text-slate-400 font-semibold">Chế độ kiểm thử nhanh</span>
            </div>
          </div>

          <button
            type="button"
            onClick={async () => {
              const ok = await login({ identifier: "dev@iuh.edu.vn", password: "password123" });
              if (ok) {
                navigate("/dashboard", { replace: true });
                // We don't necessarily need window.location.reload() here since useAuth should update the context
              } else {
                setClientError("Lỗi đăng nhập nhanh: Tài khoản dev@iuh.edu.vn chưa được tạo.");
              }
            }}
            className="w-full flex items-center justify-center gap-2 rounded-lg border-2 border-dashed border-amber-400 bg-amber-50/70 py-2 text-xs font-bold text-amber-800 hover:bg-amber-100/80 active:scale-[0.99] transition-all shadow-sm"
          >
            <Sparkles className="w-4 h-4 text-amber-600 animate-pulse" />
            <span>⚡ Đăng nhập Nhanh bằng Dev Account</span>
          </button>

          <div className="mt-6 text-center text-xs text-slate-500">
            {isRegistering ? (
              <span>
                Đã có tài khoản?{" "}
                <button
                  type="button"
                  onClick={() => setIsRegistering(false)}
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
