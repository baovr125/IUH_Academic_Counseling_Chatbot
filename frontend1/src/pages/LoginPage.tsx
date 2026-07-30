import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { Eye, GraduationCap, User, Users } from "lucide-react";

export default function LoginPage() {
  const { login, isLoading, error } = useAuth();
  const navigate = useNavigate();
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const ok = await login({ identifier, password });
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
          <h2 className="mb-1 text-xl font-bold text-slate-800">Chào mừng đến với IUH Portal AI</h2>
          <p className="mb-6 text-sm text-slate-500">Đăng nhập bằng tài khoản được cấp để tiếp tục</p>

          <label className="mb-1 block text-xs font-medium text-slate-600">Mã số sinh viên</label>
          <input
            value={identifier}
            onChange={(e) => setIdentifier(e.target.value)}
            placeholder="Nhập mã số hoặc email..."
            className="mb-4 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm focus:border-blue-400 focus:outline-none"
          />

          <label className="mb-1 block text-xs font-medium text-slate-600">Mật khẩu</label>
          <div className="relative mb-4">
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm focus:border-blue-400 focus:outline-none"
            />
            <Eye size={16} className="absolute right-3 top-2.5 text-slate-400" />
          </div>

          {error && <p className="mb-3 text-xs text-red-600">{error}</p>}

          <button
            type="submit"
            disabled={isLoading}
            className="mb-4 w-full rounded-lg bg-blue-700 py-2.5 text-sm font-medium text-white hover:bg-blue-800 disabled:opacity-60"
          >
            {isLoading ? "Đang đăng nhập..." : "Đăng nhập"}
          </button>

          <div className="mb-4 flex items-center gap-2 text-[11px] uppercase text-slate-400">
            <div className="h-px flex-1 bg-slate-200" /> Hoặc truy cập nhanh với vai trò
            <div className="h-px flex-1 bg-slate-200" />
          </div>

          <div className="space-y-2">
            {[
              { label: "Phụ huynh", icon: Users },
              { label: "Học sinh Cấp 3 (Tuyển sinh)", icon: GraduationCap },
              { label: "Khách vãng lai", icon: User },
            ].map(({ label, icon: Icon }) => (
              <button
                type="button"
                key={label}
                className="flex w-full items-center gap-2 rounded-lg border border-slate-200 px-3 py-2 text-xs text-slate-600 hover:bg-slate-50"
              >
                <Icon size={14} /> {label}
              </button>
            ))}
          </div>
        </form>
      </div>
    </div>
  );
}
