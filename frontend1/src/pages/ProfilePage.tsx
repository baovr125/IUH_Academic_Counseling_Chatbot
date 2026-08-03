import { useState, useEffect, useRef } from "react";
import { useAuth } from "../hooks/useAuth";
import {
  User as UserIcon,
  Lock,
  Eye,
  EyeOff,
  CheckCircle2,
  AlertCircle,
  Save,
  ShieldCheck,
  Key,
  Camera,
  Upload,
  Trash2,
  X,
  Check,
} from "lucide-react";

export default function ProfilePage() {
  const { user, updateProfile, setAccountPassword } = useAuth();
  const [activeTab, setActiveTab] = useState<"info" | "security">("info");

  // Kiểm tra vai trò Sinh viên / Người dùng công cộng
  const isStudent = user?.role === "student";

  // Profile Form state
  const [fullName, setFullName] = useState(user?.fullName || "");
  const [studentCode, setStudentCode] = useState(user?.studentCode || "");
  const [department, setDepartment] = useState(user?.department || "");
  const [major, setMajor] = useState(user?.major || "");
  const [phone, setPhone] = useState(user?.phoneNumber || "");
  const [avatarUrl, setAvatarUrl] = useState(user?.avatarUrl || "");
  const [profileSuccess, setProfileSuccess] = useState(false);
  const [profileError, setProfileError] = useState<string | null>(null);
  const [isUpdatingProfile, setIsUpdatingProfile] = useState(false);

  // Avatar Modal & Local File Upload state
  const [showAvatarModal, setShowAvatarModal] = useState(false);
  const [inputAvatarUrl, setInputAvatarUrl] = useState(user?.avatarUrl || "");
  const [isUpdatingAvatar, setIsUpdatingAvatar] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Tự động nhận diện trạng thái mật khẩu tài khoản
  const hasPasswordSet = Boolean(user?.password_hash || user?.passwordHash);

  // Password Form state (Tab Bảo mật & Mật khẩu)
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showCurrent, setShowCurrent] = useState(false);
  const [showNew, setShowNew] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [passwordError, setPasswordError] = useState<string | null>(null);
  const [passwordSuccess, setPasswordSuccess] = useState<string | null>(null);
  const [isSubmittingPassword, setIsSubmittingPassword] = useState(false);

  // Đồng bộ thông tin khi user object thay đổi
  useEffect(() => {
    if (user) {
      setFullName(user.fullName || "");
      setStudentCode(user.studentCode || "");
      setDepartment(user.department || "");
      setMajor(user.major || "");
      setPhone(user.phoneNumber || "");
      setAvatarUrl(user.avatarUrl || "");
      setInputAvatarUrl(user.avatarUrl || "");
    }
  }, [user]);

  // Xử lý chọn tệp ảnh đại diện từ máy tính
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (file.size > 5 * 1024 * 1024) {
      setProfileError("Kích thước tệp ảnh quá lớn (tối đa 5MB). Vui lòng chọn ảnh nhỏ hơn.");
      return;
    }

    const reader = new FileReader();
    reader.onload = () => {
      if (typeof reader.result === "string") {
        setInputAvatarUrl(reader.result);
      }
    };
    reader.readAsDataURL(file);
  };

  // Xử lý gửi Form Cập nhật thông tin cá nhân
  const handleProfileSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setProfileError(null);
    setProfileSuccess(false);
    setIsUpdatingProfile(true);

    const result = await updateProfile({
      fullName,
      phoneNumber: phone,
      studentCode: isStudent ? (studentCode ? studentCode.trim() : undefined) : undefined,
      department: isStudent ? (department ? department.trim() : undefined) : undefined,
      major: isStudent ? (major ? major.trim() : undefined) : undefined,
      avatarUrl,
    });

    setIsUpdatingProfile(false);

    if (!result.ok) {
      setProfileError(result.message || "Cập nhật thông tin thất bại.");
    } else {
      setProfileSuccess(true);
      setTimeout(() => setProfileSuccess(false), 5000);
    }
  };

  // Xử lý Cập nhật Avatar
  const handleAvatarSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputAvatarUrl) {
      setProfileError("Vui lòng chọn tệp ảnh hoặc nhập URL.");
      return;
    }
    setIsUpdatingAvatar(true);
    const result = await updateProfile({ avatarUrl: inputAvatarUrl.trim() });
    setIsUpdatingAvatar(false);

    if (result.ok) {
      setAvatarUrl(inputAvatarUrl.trim());
      setShowAvatarModal(false);
      setProfileSuccess(true);
      setTimeout(() => setProfileSuccess(false), 5000);
    } else {
      setProfileError(result.message || "Cập nhật ảnh đại diện thất bại.");
    }
  };

  // Tính toán Thước đo Độ mạnh Mật khẩu (Password Strength Indicator)
  const getPasswordStrength = (pass: string) => {
    if (!pass) return { score: 0, label: "", color: "bg-slate-200", textColor: "text-slate-400", width: "0%", details: { length: false, uppercase: false, number: false, special: false } };

    const details = {
      length: pass.length >= 8,
      uppercase: /[A-Z]/.test(pass),
      number: /[0-9]/.test(pass),
      special: /[!@#$%^&*]/.test(pass),
    };

    let points = 0;
    if (details.length) points += 1;
    if (details.uppercase) points += 1;
    if (details.number) points += 1;
    if (details.special) points += 1;

    if (pass.length < 6 || points <= 1) {
      return { score: 1, label: "Yếu", color: "bg-red-500", textColor: "text-red-600", width: "33%", details };
    }
    if (points <= 3) {
      return { score: 2, label: "Trung bình", color: "bg-amber-500", textColor: "text-amber-600", width: "66%", details };
    }
    return { score: 3, label: "Mạnh", color: "bg-emerald-500", textColor: "text-emerald-600", width: "100%", details };
  };

  const passwordStrength = getPasswordStrength(newPassword);

  // Xử lý Thiết lập / Đổi mật khẩu
  const handlePasswordSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setPasswordError(null);
    setPasswordSuccess(null);

    if (hasPasswordSet && !currentPassword) {
      setPasswordError("Vui lòng nhập mật khẩu hiện tại.");
      return;
    }

    if (!newPassword || !confirmPassword) {
      setPasswordError("Vui lòng nhập đầy đủ mật khẩu mới và xác nhận mật khẩu.");
      return;
    }

    if (newPassword.length < 6) {
      setPasswordError("Mật khẩu mới phải có ít nhất 6 ký tự.");
      return;
    }

    if (newPassword !== confirmPassword) {
      setPasswordError("Mật khẩu xác nhận không trùng khớp.");
      return;
    }

    setIsSubmittingPassword(true);
    const result = await setAccountPassword(newPassword, confirmPassword);
    setIsSubmittingPassword(false);

    if (!result.ok) {
      setPasswordError(result.message || "Cập nhật mật khẩu thất bại.");
    } else {
      setPasswordSuccess(
        hasPasswordSet
          ? "Cập nhật mật khẩu thành công! Vui lòng sử dụng mật khẩu mới trong lần đăng nhập tới."
          : "Thiết lập mật khẩu thành công! Tài khoản của bạn hiện đã được bảo mật."
      );
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
      setTimeout(() => setPasswordSuccess(null), 5000);
    }
  };

  return (
    <div className="mx-auto max-w-4xl p-6">
      {/* Header section */}
      <div className="mb-6 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
        <div className="h-28 bg-gradient-to-r from-blue-700 via-indigo-700 to-blue-800" />
        <div className="relative px-6 pb-6 pt-0">
          <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between">
            <div className="-mt-12 flex items-end gap-4">
              {/* Avatar với nút thay ảnh */}
              <div className="relative group">
                <div className="flex h-24 w-24 items-center justify-center overflow-hidden rounded-2xl border-4 border-white bg-blue-600 text-3xl font-bold text-white shadow-md">
                  {user?.avatarUrl ? (
                    <img src={user.avatarUrl} alt={user.fullName} className="h-full w-full object-cover" />
                  ) : (
                    <span>{user?.fullName?.charAt(0) ?? "U"}</span>
                  )}
                </div>
                <button
                  type="button"
                  onClick={() => setShowAvatarModal(true)}
                  className="absolute inset-0 flex flex-col items-center justify-center rounded-2xl bg-black/50 text-white opacity-0 transition-opacity group-hover:opacity-100 border-4 border-white cursor-pointer"
                  title="Thay đổi ảnh đại diện"
                >
                  <Camera size={20} />
                  <span className="text-[10px] font-semibold mt-0.5">Thay ảnh</span>
                </button>
              </div>

              <div className="mb-2">
                <h1 className="text-xl font-bold text-slate-800">{user?.fullName || fullName}</h1>
                <p className="text-xs text-slate-500">{user?.email || "student@iuh.edu.vn"}</p>
              </div>
            </div>

            {/* Huy hiệu thông minh (Badge) */}
            <div className="mt-4 flex gap-2 sm:mt-0">
              {isStudent ? (
                <span className="rounded-full bg-blue-50 px-3.5 py-1 text-xs font-semibold text-blue-700 border border-blue-200 shadow-sm flex items-center gap-1.5">
                  🎓 Sinh viên IUH
                </span>
              ) : (
                <span className="rounded-full bg-slate-100 px-3.5 py-1 text-xs font-semibold text-slate-700 border border-slate-200 shadow-sm flex items-center gap-1.5">
                  🌐 Người dùng công cộng
                </span>
              )}

              {isStudent && user?.studentCode && (
                <span className="rounded-full bg-slate-100 px-3.5 py-1 text-xs font-semibold text-slate-700 border border-slate-200">
                  MSSV: {user.studentCode}
                </span>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Tabs - 2 Tabs: Thông tin cá nhân & Bảo mật & Mật khẩu */}
      <div className="mb-6 flex gap-2 border-b border-slate-200 pb-px">
        <button
          type="button"
          onClick={() => setActiveTab("info")}
          className={`flex items-center gap-2 border-b-2 px-4 py-2.5 text-xs font-semibold transition-colors cursor-pointer ${
            activeTab === "info"
              ? "border-blue-600 text-blue-600"
              : "border-transparent text-slate-600 hover:text-slate-800"
          }`}
        >
          <UserIcon size={15} />
          <span>Thông tin cá nhân</span>
        </button>
        <button
          type="button"
          onClick={() => setActiveTab("security")}
          className={`flex items-center gap-2 border-b-2 px-4 py-2.5 text-xs font-semibold transition-colors cursor-pointer ${
            activeTab === "security"
              ? "border-blue-600 text-blue-600"
              : "border-transparent text-slate-600 hover:text-slate-800"
          }`}
        >
          <ShieldCheck size={15} />
          <span>Bảo mật & Mật khẩu</span>
        </button>
      </div>

      {/* Tab 1: Thông tin cá nhân */}
      {activeTab === "info" && (
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="mb-1 text-base font-bold text-slate-800">Cập nhật thông tin cá nhân</h2>
          <p className="mb-6 text-xs text-slate-500">
            {isStudent
              ? "Quản lý thông tin học vụ và liên hệ cá nhân trên hệ thống Trợ lý IUH"
              : "Quản lý thông tin hồ sơ và liên hệ cá nhân trên hệ thống Trợ lý IUH"}
          </p>

          {profileSuccess && (
            <div className="mb-6 flex items-center gap-3 rounded-xl border border-green-200 bg-green-50 p-4 text-xs font-medium text-green-800 transition-all">
              <CheckCircle2 size={18} className="text-green-600 flex-shrink-0" />
              <span>Thông tin tài khoản đã được lưu thành công!</span>
            </div>
          )}

          {profileError && (
            <div className="mb-6 flex items-center gap-3 rounded-xl border border-red-200 bg-red-50 p-4 text-xs font-medium text-red-800 transition-all">
              <AlertCircle size={18} className="text-red-600 flex-shrink-0" />
              <span>{profileError}</span>
            </div>
          )}

          <form onSubmit={handleProfileSubmit} className="space-y-5">
            <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
              <div>
                <label className="mb-1.5 block text-xs font-semibold text-slate-700">Họ và tên</label>
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-xs text-slate-800 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100 transition-all"
                />
              </div>

              <div>
                <label className="mb-1.5 block text-xs font-semibold text-slate-700">Email hệ thống</label>
                <input
                  type="email"
                  value={user?.email || ""}
                  disabled
                  className="w-full cursor-not-allowed rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-xs text-slate-500"
                />
              </div>

              <div>
                <label className="mb-1.5 block text-xs font-semibold text-slate-700">Số điện thoại liên hệ</label>
                <input
                  type="text"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  placeholder="Nhập số điện thoại..."
                  className="w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-xs text-slate-800 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100 transition-all"
                />
              </div>

              {/* Các trường Học vụ: CHỈ HIỂN THỊ DÀNH CHO TÀI KHOẢN SINH VIÊN IUH */}
              {isStudent && (
                <>
                  <div>
                    <label className="mb-1.5 block text-xs font-semibold text-slate-700">Mã số sinh viên (MSSV)</label>
                    <input
                      type="text"
                      value={studentCode}
                      onChange={(e) => setStudentCode(e.target.value)}
                      placeholder="Nhập MSSV nếu là Sinh viên IUH..."
                      className="w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-xs text-slate-800 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100 transition-all"
                    />
                  </div>

                  <div>
                    <label className="mb-1.5 block text-xs font-semibold text-slate-700">Khoa / Viện</label>
                    <input
                      type="text"
                      value={department}
                      onChange={(e) => setDepartment(e.target.value)}
                      placeholder="Ví dụ: Khoa Công nghệ Thông tin..."
                      className="w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-xs text-slate-800 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100 transition-all"
                    />
                  </div>

                  <div>
                    <label className="mb-1.5 block text-xs font-semibold text-slate-700">Ngành học</label>
                    <input
                      type="text"
                      value={major}
                      onChange={(e) => setMajor(e.target.value)}
                      placeholder="Ví dụ: Kỹ thuật Phần mềm..."
                      className="w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-xs text-slate-800 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100 transition-all"
                    />
                  </div>
                </>
              )}
            </div>

            <div className="flex justify-end pt-2">
              <button
                type="submit"
                disabled={isUpdatingProfile}
                className="flex items-center gap-2 rounded-xl bg-blue-600 px-5 py-2.5 text-xs font-semibold text-white shadow-sm hover:bg-blue-700 disabled:opacity-60 transition-all cursor-pointer"
              >
                <Save size={15} />
                <span>{isUpdatingProfile ? "Đang lưu..." : "Lưu thay đổi"}</span>
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Tab 2: Bảo mật & Mật khẩu */}
      {activeTab === "security" && (
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          {/* Card Header & Status */}
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between pb-5 mb-6 border-b border-slate-100 gap-3">
            <div>
              <h2 className="text-base font-bold text-slate-800 flex items-center gap-2">
                <ShieldCheck className="text-blue-600" size={20} />
                {hasPasswordSet ? "Quản lý & Đổi mật khẩu" : "Thiết lập mật khẩu tài khoản"}
              </h2>
              <p className="mt-0.5 text-xs text-slate-500">
                {hasPasswordSet
                  ? "Cập nhật mật khẩu thường xuyên để tăng cường tính bảo mật cho tài khoản của bạn."
                  : "Tài khoản của bạn hiện chưa được thiết lập mật khẩu đăng nhập trực tiếp."}
              </p>
            </div>

            {/* Trạng thái nhận diện tài khoản */}
            <div className="flex-shrink-0">
              {hasPasswordSet ? (
                <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700 border border-emerald-200">
                  <Check size={14} className="text-emerald-600" />
                  Đã có mật khẩu
                </span>
              ) : (
                <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-50 px-3 py-1 text-xs font-semibold text-amber-700 border border-amber-200">
                  <Key size={14} className="text-amber-600" />
                  Chưa thiết lập mật khẩu
                </span>
              )}
            </div>
          </div>

          {/* Thông báo hướng dẫn khi chưa có mật khẩu */}
          {!hasPasswordSet && (
            <div className="mb-6 flex items-start gap-3 rounded-xl border border-amber-200 bg-amber-50/70 p-4 text-xs text-amber-900">
              <AlertCircle size={18} className="text-amber-600 flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold text-amber-900 mb-0.5">Hướng dẫn bảo mật</p>
                <p className="text-amber-800 leading-relaxed">
                  Thiết lập mật khẩu để bảo vệ tài khoản và giúp bạn đăng nhập dễ dàng hơn.
                </p>
              </div>
            </div>
          )}

          {/* Alerts Thông báo Thành công / Thất bại */}
          {passwordSuccess && (
            <div className="mb-6 flex items-center gap-3 rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-xs font-medium text-emerald-800 transition-all">
              <CheckCircle2 size={18} className="text-emerald-600 flex-shrink-0" />
              <span>{passwordSuccess}</span>
            </div>
          )}

          {passwordError && (
            <div className="mb-6 flex items-center gap-3 rounded-xl border border-red-200 bg-red-50 p-4 text-xs font-medium text-red-800 transition-all">
              <AlertCircle size={18} className="text-red-600 flex-shrink-0" />
              <span>{passwordError}</span>
            </div>
          )}

          {/* Password Form */}
          <form onSubmit={handlePasswordSubmit} className="max-w-md space-y-4">
            {/* 1. Mật khẩu hiện tại (Chỉ render khi ĐÃ CÓ mật khẩu) */}
            {hasPasswordSet && (
              <div>
                <label className="mb-1.5 block text-xs font-semibold text-slate-700">
                  Mật khẩu hiện tại <span className="text-red-500">*</span>
                </label>
                <div className="relative">
                  <input
                    type={showCurrent ? "text" : "password"}
                    value={currentPassword}
                    onChange={(e) => setCurrentPassword(e.target.value)}
                    placeholder="Nhập mật khẩu hiện tại..."
                    className="w-full rounded-xl border border-slate-200 px-3.5 py-2.5 pr-10 text-xs text-slate-800 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100 transition-all"
                  />
                  <button
                    type="button"
                    onClick={() => setShowCurrent((prev) => !prev)}
                    className="absolute right-3 top-2.5 text-slate-400 hover:text-slate-600 transition-colors cursor-pointer"
                    title={showCurrent ? "Ẩn mật khẩu" : "Hiện mật khẩu"}
                  >
                    {showCurrent ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
                </div>
              </div>
            )}

            {/* 2. Mật khẩu mới */}
            <div>
              <label className="mb-1.5 block text-xs font-semibold text-slate-700">
                Mật khẩu mới <span className="text-red-500">*</span>
              </label>
              <div className="relative">
                <input
                  type={showNew ? "text" : "password"}
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="Ít nhất 6 ký tự..."
                  className="w-full rounded-xl border border-slate-200 px-3.5 py-2.5 pr-10 text-xs text-slate-800 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100 transition-all"
                />
                <button
                  type="button"
                  onClick={() => setShowNew((prev) => !prev)}
                  className="absolute right-3 top-2.5 text-slate-400 hover:text-slate-600 transition-colors cursor-pointer"
                  title={showNew ? "Ẩn mật khẩu" : "Hiện mật khẩu"}
                >
                  {showNew ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>

              {/* Thước đo Độ mạnh Mật khẩu (Password Strength Indicator) */}
              {newPassword && (
                <div className="mt-2.5 space-y-2 rounded-xl border border-slate-100 bg-slate-50/80 p-3 transition-all">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-medium text-slate-600">Độ mạnh mật khẩu:</span>
                    <span className={`font-bold ${passwordStrength.textColor}`}>
                      {passwordStrength.label}
                    </span>
                  </div>

                  {/* Thanh Progress Bar */}
                  <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-200">
                    <div
                      className={`h-full transition-all duration-300 ${passwordStrength.color}`}
                      style={{ width: passwordStrength.width }}
                    />
                  </div>

                  {/* Chi tiết tiêu chí */}
                  <div className="grid grid-cols-2 gap-1.5 pt-1 text-[11px]">
                    <div
                      className={`flex items-center gap-1 ${
                        passwordStrength.details.length ? "text-emerald-600 font-medium" : "text-slate-400"
                      }`}
                    >
                      <Check
                        size={12}
                        className={passwordStrength.details.length ? "opacity-100" : "opacity-30"}
                      />
                      <span>Ít nhất 8 ký tự</span>
                    </div>
                    <div
                      className={`flex items-center gap-1 ${
                        passwordStrength.details.uppercase ? "text-emerald-600 font-medium" : "text-slate-400"
                      }`}
                    >
                      <Check
                        size={12}
                        className={passwordStrength.details.uppercase ? "opacity-100" : "opacity-30"}
                      />
                      <span>Chữ cái viết hoa</span>
                    </div>
                    <div
                      className={`flex items-center gap-1 ${
                        passwordStrength.details.number ? "text-emerald-600 font-medium" : "text-slate-400"
                      }`}
                    >
                      <Check
                        size={12}
                        className={passwordStrength.details.number ? "opacity-100" : "opacity-30"}
                      />
                      <span>Chữ số (0-9)</span>
                    </div>
                    <div
                      className={`flex items-center gap-1 ${
                        passwordStrength.details.special ? "text-emerald-600 font-medium" : "text-slate-400"
                      }`}
                    >
                      <Check
                        size={12}
                        className={passwordStrength.details.special ? "opacity-100" : "opacity-30"}
                      />
                      <span>Ký tự đặc biệt (!@#$%^&*)</span>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* 3. Xác nhận mật khẩu mới */}
            <div>
              <label className="mb-1.5 block text-xs font-semibold text-slate-700">
                Xác nhận mật khẩu mới <span className="text-red-500">*</span>
              </label>
              <div className="relative">
                <input
                  type={showConfirm ? "text" : "password"}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Nhập lại mật khẩu mới..."
                  className="w-full rounded-xl border border-slate-200 px-3.5 py-2.5 pr-10 text-xs text-slate-800 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100 transition-all"
                />
                <button
                  type="button"
                  onClick={() => setShowConfirm((prev) => !prev)}
                  className="absolute right-3 top-2.5 text-slate-400 hover:text-slate-600 transition-colors cursor-pointer"
                  title={showConfirm ? "Ẩn mật khẩu" : "Hiện mật khẩu"}
                >
                  {showConfirm ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            {/* Nút hành động */}
            <div className="pt-3">
              <button
                type="submit"
                disabled={isSubmittingPassword}
                className="flex items-center justify-center gap-2 rounded-xl bg-blue-600 px-5 py-2.5 text-xs font-semibold text-white shadow-sm hover:bg-blue-700 disabled:opacity-60 transition-all w-full sm:w-auto cursor-pointer"
              >
                <Lock size={15} />
                <span>
                  {isSubmittingPassword
                    ? "Đang lưu..."
                    : hasPasswordSet
                    ? "Đổi mật khẩu"
                    : "Thiết lập mật khẩu"}
                </span>
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Popup Modal Thay đổi Ảnh đại diện Avatar */}
      {showAvatarModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm p-4">
          <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl border border-slate-100">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Camera className="w-5 h-5 text-blue-600" />
                <h3 className="text-base font-bold text-slate-800">Cập nhật ảnh đại diện</h3>
              </div>
              <button
                type="button"
                onClick={() => setShowAvatarModal(false)}
                className="text-slate-400 hover:text-slate-600 cursor-pointer"
              >
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleAvatarSubmit} className="space-y-4">
              {/* Tải ảnh trực tiếp từ thư mục máy tính */}
              <div>
                <label className="mb-1.5 block text-xs font-semibold text-slate-700">
                  Tải ảnh lên từ máy tính
                </label>
                <input
                  type="file"
                  ref={fileInputRef}
                  accept="image/*"
                  onChange={handleFileChange}
                  className="hidden"
                />
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  className="flex flex-col items-center justify-center gap-2 w-full rounded-2xl border-2 border-dashed border-blue-300 bg-blue-50/60 p-6 text-center hover:bg-blue-50 hover:border-blue-400 transition-all cursor-pointer group"
                >
                  <div className="p-3 rounded-full bg-blue-100 text-blue-600 group-hover:scale-110 transition-transform">
                    <Upload size={24} />
                  </div>
                  <div>
                    <p className="text-xs font-bold text-slate-800">Bấm vào đây để chọn tệp ảnh từ thiết bị</p>
                    <p className="text-[11px] text-slate-500 mt-0.5">Hỗ trợ PNG, JPG, JPEG, WEBP, GIF, SVG (tối đa 5MB)</p>
                  </div>
                </button>
              </div>

              {inputAvatarUrl && (
                <div className="flex items-center justify-between gap-3 rounded-xl border border-slate-200 bg-slate-50 p-3">
                  <div className="flex items-center gap-3">
                    <img
                      src={inputAvatarUrl}
                      alt="Preview"
                      className="w-12 h-12 rounded-2xl object-cover border border-slate-300 shadow-sm"
                      onError={(e) => {
                        (e.target as HTMLElement).style.display = "none";
                      }}
                    />
                    <div>
                      <p className="text-xs font-semibold text-slate-800">Xem trước ảnh đại diện</p>
                      <p className="text-[10px] text-slate-500 truncate max-w-[200px]">
                        {inputAvatarUrl.startsWith("data:") ? "Ảnh tải từ máy tính" : inputAvatarUrl}
                      </p>
                    </div>
                  </div>

                  <button
                    type="button"
                    onClick={() => setInputAvatarUrl("")}
                    className="text-xs text-red-600 hover:text-red-800 p-1.5 rounded-lg hover:bg-red-50 cursor-pointer"
                    title="Xóa ảnh"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              )}

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowAvatarModal(false)}
                  className="px-4 py-2 rounded-xl border border-slate-200 text-xs font-semibold text-slate-600 hover:bg-slate-50 cursor-pointer"
                >
                  Hủy
                </button>
                <button
                  type="submit"
                  disabled={isUpdatingAvatar || !inputAvatarUrl}
                  className="px-4 py-2 rounded-xl bg-blue-600 text-xs font-semibold text-white shadow-sm hover:bg-blue-700 disabled:opacity-60 cursor-pointer"
                >
                  {isUpdatingAvatar ? "Đang lưu..." : "Cập nhật ảnh đại diện"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
