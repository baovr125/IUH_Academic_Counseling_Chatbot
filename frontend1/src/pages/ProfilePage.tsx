import { useState, useEffect } from "react";
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
  Link as LinkIcon,
  X,
  Key,
  Check,
  Camera,
} from "lucide-react";

export default function ProfilePage() {
  const { user, updateProfile, linkGoogleAccount, setAccountPassword } = useAuth();
  const [activeTab, setActiveTab] = useState<"info" | "security" | "password">("info");

  // Determine user identity mode
  const isStudent = user?.role === "student" || Boolean(user?.studentCode);

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

  // Avatar Modal state
  const [showAvatarModal, setShowAvatarModal] = useState(false);
  const [inputAvatarUrl, setInputAvatarUrl] = useState(user?.avatarUrl || "");
  const [isUpdatingAvatar, setIsUpdatingAvatar] = useState(false);

  // Sync state if user changes
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

  // Password Form state (Tab Đổi mật khẩu)
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showCurrent, setShowCurrent] = useState(false);
  const [showNew, setShowNew] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [passwordError, setPasswordError] = useState<string | null>(null);
  const [passwordSuccess, setPasswordSuccess] = useState(false);

  // Account Security & Linking state (Tab Liên kết & Bảo mật)
  const [setupPassword, setSetupPassword] = useState("");
  const [setupConfirmPassword, setSetupConfirmPassword] = useState("");
  const [showSetup, setShowSetup] = useState(false);
  const [showSetupConfirm, setShowSetupConfirm] = useState(false);
  const [securitySuccess, setSecuritySuccess] = useState<string | null>(null);
  const [securityError, setSecurityError] = useState<string | null>(null);
  const [isSubmittingPassword, setIsSubmittingPassword] = useState(false);

  // Google Modal state
  const [showGoogleModal, setShowGoogleModal] = useState(false);
  const [selectedGoogleAccount, setSelectedGoogleAccount] = useState(
    user?.email || "nguyenvana.iuh@gmail.com"
  );
  const [isLinkingGoogle, setIsLinkingGoogle] = useState(false);

  // Kiểm tra cờ trạng thái tài khoản
  const hasGoogleLinked = Boolean(user?.google_id || user?.googleId);
  const hasPasswordSet = Boolean(user?.password_hash || user?.passwordHash);

  // Xử lý gửi Form Cập nhật thông tin cá nhân
  const handleProfileSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setProfileError(null);
    setProfileSuccess(false);
    setIsUpdatingProfile(true);

    const result = await updateProfile({
      fullName,
      phoneNumber: phone,
      studentCode: studentCode ? studentCode.trim() : undefined,
      department,
      major,
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

  // Xử lý Đổi mật khẩu
  const handlePasswordSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPasswordError(null);
    setPasswordSuccess(false);

    if (!currentPassword || !newPassword || !confirmPassword) {
      setPasswordError("Vui lòng nhập đầy đủ các trường thông tin mật khẩu.");
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

    setPasswordSuccess(true);
    setCurrentPassword("");
    setNewPassword("");
    setConfirmPassword("");
    setTimeout(() => setPasswordSuccess(false), 5000);
  };

  // Xử lý thiết lập mật khẩu lần đầu cho tài khoản tạo qua Google (!user.password_hash)
  const handleSetupPasswordSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSecuritySuccess(null);
    setSecurityError(null);

    if (!setupPassword || !setupConfirmPassword) {
      setSecurityError("Vui lòng nhập đầy đủ mật khẩu mới và xác nhận mật khẩu.");
      return;
    }

    if (setupPassword.length < 6) {
      setSecurityError("Mật khẩu mới phải có ít nhất 6 ký tự.");
      return;
    }

    if (setupPassword !== setupConfirmPassword) {
      setSecurityError("Mật khẩu xác nhận không khớp.");
      return;
    }

    setIsSubmittingPassword(true);
    const result = await setAccountPassword(setupPassword, setupConfirmPassword);
    setIsSubmittingPassword(false);

    if (!result.ok) {
      setSecurityError(result.message || "Thiết lập mật khẩu thất bại.");
    } else {
      setSecuritySuccess("Thiết lập mật khẩu đăng nhập thành công!");
      setSetupPassword("");
      setSetupConfirmPassword("");
      setTimeout(() => setSecuritySuccess(null), 5000);
    }
  };

  // Xử lý liên kết tài khoản Google
  const handleLinkGoogle = async () => {
    setSecuritySuccess(null);
    setSecurityError(null);
    setIsLinkingGoogle(true);

    const mockIdToken = `google_id_token_${selectedGoogleAccount}`;
    const result = await linkGoogleAccount(mockIdToken);
    setIsLinkingGoogle(false);
    setShowGoogleModal(false);

    if (!result.ok) {
      setSecurityError(result.message || "Liên kết Google thất bại.");
    } else {
      setSecuritySuccess(`Đã liên kết thành công với tài khoản Google (${selectedGoogleAccount})!`);
      setTimeout(() => setSecuritySuccess(null), 5000);
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
                  className="absolute inset-0 flex flex-col items-center justify-center rounded-2xl bg-black/50 text-white opacity-0 transition-opacity group-hover:opacity-100 border-4 border-white"
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

              {user?.studentCode && (
                <span className="rounded-full bg-slate-100 px-3.5 py-1 text-xs font-semibold text-slate-700 border border-slate-200">
                  MSSV: {user.studentCode}
                </span>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="mb-6 flex gap-2 border-b border-slate-200 pb-px">
        <button
          type="button"
          onClick={() => setActiveTab("info")}
          className={`flex items-center gap-2 border-b-2 px-4 py-2.5 text-xs font-semibold transition-colors ${
            activeTab === "info"
              ? "border-blue-600 text-blue-600"
              : "border-transparent text-slate-600 hover:text-slate-800"
          }`}
        >
          <UserIcon size={15} />
          <span>Thông tin chung</span>
        </button>
        <button
          type="button"
          onClick={() => setActiveTab("security")}
          className={`flex items-center gap-2 border-b-2 px-4 py-2.5 text-xs font-semibold transition-colors ${
            activeTab === "security"
              ? "border-blue-600 text-blue-600"
              : "border-transparent text-slate-600 hover:text-slate-800"
          }`}
        >
          <ShieldCheck size={15} />
          <span>Liên kết & Bảo mật</span>
        </button>
        <button
          type="button"
          onClick={() => setActiveTab("password")}
          className={`flex items-center gap-2 border-b-2 px-4 py-2.5 text-xs font-semibold transition-colors ${
            activeTab === "password"
              ? "border-blue-600 text-blue-600"
              : "border-transparent text-slate-600 hover:text-slate-800"
          }`}
        >
          <Lock size={15} />
          <span>Đổi mật khẩu</span>
        </button>
      </div>

      {/* Content */}
      {activeTab === "info" && (
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="mb-1 text-base font-bold text-slate-800">Cập nhật thông tin cá nhân</h2>
          <p className="mb-6 text-xs text-slate-500">
            Quản lý thông tin học vụ và liên hệ cá nhân trên hệ thống Trợ lý IUH
          </p>

          {profileSuccess && (
            <div className="mb-6 flex items-center gap-3 rounded-xl border border-green-200 bg-green-50 p-4 text-xs font-medium text-green-800">
              <CheckCircle2 size={18} className="text-green-600 flex-shrink-0" />
              <span>Thông tin tài khoản đã được lưu thành công!</span>
            </div>
          )}

          {profileError && (
            <div className="mb-6 flex items-center gap-3 rounded-xl border border-red-200 bg-red-50 p-4 text-xs font-medium text-red-800">
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
                  className="w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-xs text-slate-800 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100"
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
                <label className="mb-1.5 block text-xs font-semibold text-slate-700">Mã số sinh viên (MSSV)</label>
                <input
                  type="text"
                  value={studentCode}
                  onChange={(e) => setStudentCode(e.target.value)}
                  placeholder="Nhập MSSV nếu là Sinh viên IUH..."
                  className="w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-xs text-slate-800 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100"
                />
              </div>

              <div>
                <label className="mb-1.5 block text-xs font-semibold text-slate-700">Số điện thoại liên hệ</label>
                <input
                  type="text"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  placeholder="Nhập số điện thoại..."
                  className="w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-xs text-slate-800 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100"
                />
              </div>

              <div>
                <label className="mb-1.5 block text-xs font-semibold text-slate-700">Khoa / Viện</label>
                <input
                  type="text"
                  value={department}
                  onChange={(e) => setDepartment(e.target.value)}
                  placeholder="Ví dụ: Khoa Công nghệ Thông tin..."
                  className="w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-xs text-slate-800 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100"
                />
              </div>

              <div>
                <label className="mb-1.5 block text-xs font-semibold text-slate-700">Ngành học</label>
                <input
                  type="text"
                  value={major}
                  onChange={(e) => setMajor(e.target.value)}
                  placeholder="Ví dụ: Kỹ thuật Phần mềm..."
                  className="w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-xs text-slate-800 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100"
                />
              </div>
            </div>

            <div className="flex justify-end pt-2">
              <button
                type="submit"
                disabled={isUpdatingProfile}
                className="flex items-center gap-2 rounded-xl bg-blue-600 px-5 py-2.5 text-xs font-semibold text-white shadow-sm hover:bg-blue-700 disabled:opacity-60 transition-colors"
              >
                <Save size={15} />
                <span>{isUpdatingProfile ? "Đang lưu..." : "Lưu thay đổi"}</span>
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Account Security & Linking Tab */}
      {activeTab === "security" && (
        <div className="space-y-6">
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <h2 className="mb-1 text-base font-bold text-slate-800">
              Liên kết & Bảo mật tài khoản (Account Security & Linking)
            </h2>
            <p className="mb-6 text-xs text-slate-500">
              Quản lý trạng thái liên kết với Google và thiết lập mật khẩu đăng nhập cho hệ thống IUH Portal AI.
            </p>

            {securitySuccess && (
              <div className="mb-6 flex items-center gap-3 rounded-xl border border-green-200 bg-green-50 p-4 text-xs font-medium text-green-800">
                <CheckCircle2 size={18} className="text-green-600 flex-shrink-0" />
                <span>{securitySuccess}</span>
              </div>
            )}

            {securityError && (
              <div className="mb-6 flex items-center gap-3 rounded-xl border border-red-200 bg-red-50 p-4 text-xs font-medium text-red-800">
                <AlertCircle size={18} className="text-red-600 flex-shrink-0" />
                <span>{securityError}</span>
              </div>
            )}

            {/* Grid Trạng thái */}
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 mb-6">
              {/* Thẻ trạng thái Mật khẩu */}
              <div className="flex flex-col justify-between rounded-xl border border-slate-200 bg-slate-50/70 p-4">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-semibold text-slate-700 flex items-center gap-2">
                      <Key size={16} className="text-slate-500" />
                      Mật khẩu đăng nhập
                    </span>
                    {hasPasswordSet ? (
                      <span className="flex items-center gap-1 rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-semibold text-green-700">
                        <Check size={13} />
                        Đã thiết lập
                      </span>
                    ) : (
                      <span className="flex items-center gap-1 rounded-full bg-amber-100 px-2.5 py-0.5 text-xs font-semibold text-amber-700">
                        <AlertCircle size={13} />
                        Chưa thiết lập
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-slate-500">
                    {hasPasswordSet
                      ? "Tài khoản của bạn đã được bảo vệ bằng mật khẩu. Bạn có thể cập nhật mật khẩu tại tab Đổi mật khẩu."
                      : "Tài khoản được đăng ký qua Google chưa có mật khẩu độc lập. Hãy thiết lập bên dưới để đăng nhập bằng Email/MSSV."}
                  </p>
                </div>
              </div>

              {/* Thẻ trạng thái Google */}
              <div className="flex flex-col justify-between rounded-xl border border-slate-200 bg-slate-50/70 p-4">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-semibold text-slate-700 flex items-center gap-2">
                      <LinkIcon size={16} className="text-slate-500" />
                      Tài khoản Google
                    </span>
                    {hasGoogleLinked ? (
                      <span className="flex items-center gap-1 rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-semibold text-green-700">
                        <Check size={13} />
                        Đã liên kết
                      </span>
                    ) : (
                      <span className="flex items-center gap-1 rounded-full bg-slate-200 px-2.5 py-0.5 text-xs font-semibold text-slate-700">
                        Chưa liên kết
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-slate-500">
                    {hasGoogleLinked
                      ? `Đã liên kết với Google ID: ${user?.google_id || user?.googleId}. Bạn có thể đăng nhập nhanh bằng Google Sign-In.`
                      : "Liên kết với tài khoản Google để đăng nhập nhanh chỉ với một lần nhấp chuột mà không cần mật khẩu."}
                  </p>
                </div>
                {!hasGoogleLinked && (
                  <div className="mt-3">
                    <button
                      type="button"
                      onClick={() => setShowGoogleModal(true)}
                      className="flex items-center justify-center gap-2 w-full rounded-lg bg-white border border-slate-300 px-3.5 py-2 text-xs font-semibold text-slate-700 shadow-sm hover:bg-slate-50 transition-colors"
                    >
                      <img
                        src="https://www.gstatic.com/images/branding/product/1x/gsa_512dp.png"
                        alt="Google"
                        className="w-4 h-4"
                      />
                      <span>Liên kết với tài khoản Google</span>
                    </button>
                  </div>
                )}
              </div>
            </div>

            {/* Form Thiết lập mật khẩu khi user.password_hash === null */}
            {!hasPasswordSet && (
              <div className="mt-6 border-t border-slate-200 pt-6">
                <h3 className="text-sm font-bold text-slate-800 mb-1">
                  Thiết lập mật khẩu đăng nhập
                </h3>
                <p className="text-xs text-slate-500 mb-4">
                  Thiết lập mật khẩu để bạn có thể đăng nhập vào hệ thống bằng Email hoặc Mã số sinh viên bên cạnh Google Sign-In.
                </p>

                <form onSubmit={handleSetupPasswordSubmit} className="max-w-md space-y-4">
                  <div>
                    <label className="mb-1.5 block text-xs font-semibold text-slate-700">
                      Mật khẩu mới
                    </label>
                    <div className="relative">
                      <input
                        type={showSetup ? "text" : "password"}
                        value={setupPassword}
                        onChange={(e) => setSetupPassword(e.target.value)}
                        placeholder="Ít nhất 6 ký tự..."
                        className="w-full rounded-xl border border-slate-200 px-3.5 py-2.5 pr-10 text-xs text-slate-800 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100"
                      />
                      <button
                        type="button"
                        onClick={() => setShowSetup((p) => !p)}
                        className="absolute right-3 top-2.5 text-slate-400 hover:text-slate-600"
                      >
                        {showSetup ? <EyeOff size={16} /> : <Eye size={16} />}
                      </button>
                    </div>
                  </div>

                  <div>
                    <label className="mb-1.5 block text-xs font-semibold text-slate-700">
                      Xác nhận mật khẩu mới
                    </label>
                    <div className="relative">
                      <input
                        type={showSetupConfirm ? "text" : "password"}
                        value={setupConfirmPassword}
                        onChange={(e) => setSetupConfirmPassword(e.target.value)}
                        placeholder="Nhập lại mật khẩu mới..."
                        className="w-full rounded-xl border border-slate-200 px-3.5 py-2.5 pr-10 text-xs text-slate-800 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100"
                      />
                      <button
                        type="button"
                        onClick={() => setShowSetupConfirm((p) => !p)}
                        className="absolute right-3 top-2.5 text-slate-400 hover:text-slate-600"
                      >
                        {showSetupConfirm ? <EyeOff size={16} /> : <Eye size={16} />}
                      </button>
                    </div>
                  </div>

                  <div className="pt-2">
                    <button
                      type="submit"
                      disabled={isSubmittingPassword}
                      className="flex items-center gap-2 rounded-xl bg-blue-600 px-5 py-2.5 text-xs font-semibold text-white shadow-sm hover:bg-blue-700 disabled:opacity-60 transition-colors"
                    >
                      <Lock size={15} />
                      <span>{isSubmittingPassword ? "Đang lưu..." : "Thiết lập mật khẩu"}</span>
                    </button>
                  </div>
                </form>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab Đổi mật khẩu */}
      {activeTab === "password" && (
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="mb-1 text-base font-bold text-slate-800">Đổi mật khẩu tài khoản</h2>
          <p className="mb-6 text-xs text-slate-500">
            Nên sử dụng mật khẩu mạnh có ít nhất 8 ký tự, bao gồm chữ hoa, chữ thường và số.
          </p>

          {passwordSuccess && (
            <div className="mb-6 flex items-center gap-3 rounded-xl border border-green-200 bg-green-50 p-4 text-xs font-medium text-green-800">
              <CheckCircle2 size={18} className="text-green-600 flex-shrink-0" />
              <span>
                Mật khẩu đã được cập nhật thành công! Vui lòng sử dụng mật khẩu mới trong các lần đăng
                nhập tiếp theo.
              </span>
            </div>
          )}

          {passwordError && (
            <div className="mb-6 flex items-center gap-3 rounded-xl border border-red-200 bg-red-50 p-4 text-xs font-medium text-red-800">
              <AlertCircle size={18} className="text-red-600 flex-shrink-0" />
              <span>{passwordError}</span>
            </div>
          )}

          <form onSubmit={handlePasswordSubmit} className="max-w-md space-y-4">
            <div>
              <label className="mb-1.5 block text-xs font-semibold text-slate-700">Mật khẩu hiện tại</label>
              <div className="relative">
                <input
                  type={showCurrent ? "text" : "password"}
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full rounded-xl border border-slate-200 px-3.5 py-2.5 pr-10 text-xs text-slate-800 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100"
                />
                <button
                  type="button"
                  onClick={() => setShowCurrent((p) => !p)}
                  className="absolute right-3 top-2.5 text-slate-400 hover:text-slate-600"
                >
                  {showCurrent ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            <div>
              <label className="mb-1.5 block text-xs font-semibold text-slate-700">Mật khẩu mới</label>
              <div className="relative">
                <input
                  type={showNew ? "text" : "password"}
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full rounded-xl border border-slate-200 px-3.5 py-2.5 pr-10 text-xs text-slate-800 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100"
                />
                <button
                  type="button"
                  onClick={() => setShowNew((p) => !p)}
                  className="absolute right-3 top-2.5 text-slate-400 hover:text-slate-600"
                >
                  {showNew ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            <div>
              <label className="mb-1.5 block text-xs font-semibold text-slate-700">Xác nhận mật khẩu mới</label>
              <div className="relative">
                <input
                  type={showConfirm ? "text" : "password"}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full rounded-xl border border-slate-200 px-3.5 py-2.5 pr-10 text-xs text-slate-800 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100"
                />
                <button
                  type="button"
                  onClick={() => setShowConfirm((p) => !p)}
                  className="absolute right-3 top-2.5 text-slate-400 hover:text-slate-600"
                >
                  {showConfirm ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            <div className="pt-2">
              <button
                type="submit"
                className="flex items-center gap-2 rounded-xl bg-blue-600 px-5 py-2.5 text-xs font-semibold text-white shadow-sm hover:bg-blue-700 transition-colors"
              >
                <Lock size={15} />
                <span>Cập nhật mật khẩu</span>
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
                className="text-slate-400 hover:text-slate-600"
              >
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleAvatarSubmit} className="space-y-4">
              <p className="text-xs text-slate-500">
                Nhập đường dẫn URL ảnh đại diện của bạn (hỗ trợ ảnh Google, Unsplash, Gravatar...):
              </p>

              <div>
                <label className="mb-1 block text-xs font-semibold text-slate-700">URL ảnh đại diện</label>
                <input
                  type="url"
                  value={inputAvatarUrl}
                  onChange={(e) => setInputAvatarUrl(e.target.value)}
                  placeholder="https://images.unsplash.com/..."
                  required
                  className="w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-xs text-slate-800 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100"
                />
              </div>

              {inputAvatarUrl && (
                <div className="flex items-center gap-3 rounded-xl border border-slate-200 bg-slate-50 p-3">
                  <span className="text-xs text-slate-500 font-medium">Xem trước:</span>
                  <img
                    src={inputAvatarUrl}
                    alt="Preview"
                    className="w-10 h-10 rounded-full object-cover border border-slate-300"
                    onError={(e) => {
                      (e.target as HTMLElement).style.display = "none";
                    }}
                  />
                </div>
              )}

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowAvatarModal(false)}
                  className="px-4 py-2 rounded-xl border border-slate-200 text-xs font-semibold text-slate-600 hover:bg-slate-50"
                >
                  Hủy
                </button>
                <button
                  type="submit"
                  disabled={isUpdatingAvatar}
                  className="px-4 py-2 rounded-xl bg-blue-600 text-xs font-semibold text-white shadow-sm hover:bg-blue-700 disabled:opacity-60"
                >
                  {isUpdatingAvatar ? "Đang lưu..." : "Cập nhật ảnh"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Popup Modal Chọn tài khoản Google để liên kết */}
      {showGoogleModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm p-4">
          <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl border border-slate-100">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <img
                  src="https://www.gstatic.com/images/branding/product/1x/gsa_512dp.png"
                  alt="Google"
                  className="w-5 h-5"
                />
                <h3 className="text-base font-bold text-slate-800">Liên kết tài khoản Google</h3>
              </div>
              <button
                type="button"
                onClick={() => setShowGoogleModal(false)}
                className="text-slate-400 hover:text-slate-600"
              >
                <X size={18} />
              </button>
            </div>

            <p className="text-xs text-slate-500 mb-4">
              Chọn tài khoản Google (Google Sign-In) để liên kết với hệ thống Trợ lý học vụ IUH:
            </p>

            <div className="space-y-2 mb-6">
              {[
                {
                  email: user?.email || "nguyenvana.iuh@gmail.com",
                  name: user?.fullName || "Nguyễn Văn A",
                  recommended: true,
                },
                {
                  email: "student.iuh.2026@gmail.com",
                  name: "IUH Student Google",
                  recommended: false,
                },
              ].map((item) => (
                <div
                  key={item.email}
                  onClick={() => setSelectedGoogleAccount(item.email)}
                  className={`flex items-center justify-between p-3 rounded-xl border cursor-pointer transition-all ${
                    selectedGoogleAccount === item.email
                      ? "border-blue-600 bg-blue-50/70"
                      : "border-slate-200 hover:bg-slate-50"
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-blue-600 text-white font-bold flex items-center justify-center text-xs">
                      {item.name.charAt(0)}
                    </div>
                    <div>
                      <p className="text-xs font-semibold text-slate-800">{item.name}</p>
                      <p className="text-[11px] text-slate-500">{item.email}</p>
                    </div>
                  </div>
                  {item.recommended && (
                    <span className="text-[10px] bg-blue-100 text-blue-700 font-semibold px-2 py-0.5 rounded-full">
                      Khuyên dùng
                    </span>
                  )}
                </div>
              ))}
            </div>

            <div className="flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setShowGoogleModal(false)}
                className="px-4 py-2 rounded-xl border border-slate-200 text-xs font-semibold text-slate-600 hover:bg-slate-50"
              >
                Hủy
              </button>
              <button
                type="button"
                onClick={handleLinkGoogle}
                disabled={isLinkingGoogle}
                className="px-4 py-2 rounded-xl bg-blue-600 text-xs font-semibold text-white shadow-sm hover:bg-blue-700 disabled:opacity-60"
              >
                {isLinkingGoogle ? "Đang liên kết..." : "Xác nhận liên kết"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
