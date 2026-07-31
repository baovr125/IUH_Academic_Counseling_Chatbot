import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { Eye, EyeOff } from "lucide-react";

const GoogleIcon = () => (
  <svg className="h-4 w-4" viewBox="0 0 24 24">
    <path
      fill="#4285F4"
      d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
    />
    <path
      fill="#34A853"
      d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
    />
    <path
      fill="#FBBC05"
      d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
    />
    <path
      fill="#EA4335"
      d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
    />
  </svg>
);

export default function LoginPage() {
  const { login, register, isLoading, error } = useAuth();
  const navigate = useNavigate();

  const [isRegistering, setIsRegistering] = useState(false);
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isGoogleLoading, setIsGoogleLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isRegistering) {
      const ok = await register({
        fullName,
        identifier,
        password,
        confirmPassword,
      });
      if (ok) navigate("/dashboard");
    } else {
      const ok = await login({ identifier, password });
      if (ok) navigate("/dashboard");
    }
  };

  const handleGoogleLogin = async () => {
    setIsGoogleLoading(true);
    const ok = await login({
      identifier: "nguyenvana.google@iuh.edu.vn",
      password: "google_oauth_token",
    });
    setIsGoogleLoading(false);
    if (ok) navigate("/dashboard");
  };

  return (
    <div className="flex h-screen w-full">
      <div className="hidden w-1/2 flex-col justify-between bg-[#152a6e] p-10 text-white lg:flex">
        <span className="font-semibold">IUH Portal AI</span>
        <div>
          <h1 className="mb-3 text-3xl font-bold leading-tight">
            Hệ thống Trợ lý Học vụ Thông minh IUH
          </h1>
          <p className="text-blue-200">
            Tra cứu quy chế, dịch thuật tài liệu học thuật trong vài giây. Một giải pháp AI đột phá
            dành cho cộng đồng IUH.
          </p>
        </div>
        <span className="w-fit rounded-full bg-white/10 px-3 py-1 text-xs">
          Hệ thống sẵn sàng cho HK2 · 2024
        </span>
      </div>

      <div className="flex w-full items-center justify-center bg-slate-50 p-6 lg:w-1/2">
        <form onSubmit={handleSubmit} className="w-full max-w-sm rounded-2xl bg-white p-8 shadow-sm">
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
          <p className="mb-6 text-sm text-slate-500">
            {isRegistering
              ? "Đăng ký tài khoản để trải nghiệm trợ lý AI học vụ"
              : "Đăng nhập bằng tài khoản được cấp để tiếp tục"}
          </p>

          {isRegistering && (
            <div className="mb-4">
              <label className="mb-1 block text-xs font-medium text-slate-600">Họ và tên</label>
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Nhập họ và tên của bạn..."
                required={isRegistering}
                className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm focus:border-blue-400 focus:outline-none"
              />
            </div>
          )}

          <div className="mb-4">
            <label className="mb-1 block text-xs font-medium text-slate-600">
              Mã số sinh viên hoặc Email
            </label>
            <input
              type="text"
              value={identifier}
              onChange={(e) => setIdentifier(e.target.value)}
              placeholder="Nhập mã số hoặc email..."
              required
              className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm focus:border-blue-400 focus:outline-none"
            />
          </div>

          <div className="mb-4">
            <label className="mb-1 block text-xs font-medium text-slate-600">Mật khẩu</label>
            <div className="relative">
              <input
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
                className="w-full rounded-lg border border-slate-200 px-3 py-2 pr-9 text-sm focus:border-blue-400 focus:outline-none"
              />
              <button
                type="button"
                onClick={() => setShowPassword((prev) => !prev)}
                className="absolute right-2.5 top-2.5 text-slate-400 hover:text-slate-600"
              >
                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>

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
                  className="w-full rounded-lg border border-slate-200 px-3 py-2 pr-9 text-sm focus:border-blue-400 focus:outline-none"
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword((prev) => !prev)}
                  className="absolute right-2.5 top-2.5 text-slate-400 hover:text-slate-600"
                >
                  {showConfirmPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>
          )}

          {error && <p className="mb-3 text-xs text-red-600">{error}</p>}

          <button
            type="submit"
            disabled={isLoading || isGoogleLoading}
            className="mb-4 w-full rounded-lg bg-blue-700 py-2.5 text-sm font-medium text-white hover:bg-blue-800 disabled:opacity-60 transition-colors shadow-sm"
          >
            {isLoading
              ? isRegistering
                ? "Đang đăng ký..."
                : "Đang đăng nhập..."
              : isRegistering
              ? "Đăng ký tài khoản"
              : "Đăng nhập"}
          </button>

          <div className="my-4 flex items-center gap-2 text-[11px] uppercase text-slate-400">
            <div className="h-px flex-1 bg-slate-200" /> Hoặc <div className="h-px flex-1 bg-slate-200" />
          </div>

          <button
            type="button"
            onClick={handleGoogleLogin}
            disabled={isLoading || isGoogleLoading}
            className="flex w-full items-center justify-center gap-2.5 rounded-lg border border-slate-200 bg-white px-4 py-2.5 text-xs font-medium text-slate-700 shadow-sm hover:bg-slate-50 disabled:opacity-60 transition-colors"
          >
            <GoogleIcon />
            <span>
              {isGoogleLoading
                ? "Đang kết nối Google..."
                : "Đăng nhập bằng tài khoản Google"}
            </span>
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
    </div>
  );
}

