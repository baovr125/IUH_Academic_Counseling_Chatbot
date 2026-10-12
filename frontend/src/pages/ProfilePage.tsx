import { useEffect, useRef, useState } from "react";
import { Camera, Check, KeyRound, Lock, Save, ShieldCheck, Trash2, Upload, User as UserIcon } from "lucide-react";
import { useAuth } from "../hooks/useAuth";
import { useSettings } from "../context/SettingsContext";
import { FormField } from "../components/auth/FormField";
import { Alert } from "../components/ui/Alert";
import { Modal } from "../components/ui/Modal";
import { Combobox } from "../components/ui/Combobox";
import { IUH_UNITS, OTHER } from "../data/iuhCatalog";
import { useCatalogSelection } from "../hooks/useCatalogSelection";
import { checkPassword, estimateStrength, validatePassword } from "../services/passwordPolicy";
import { fileToAvatarDataUrl } from "../services/avatar";

type Tab = "info" | "security";

// Tên trường server → tên trường form.
const PROFILE_FIELD_MAP: Record<string, string> = {
  full_name: "fullName",
  phone_number: "phoneNumber",
  department: "department",
  major: "major",
  avatar_url: "avatar",
};
const departmentOptions = IUH_UNITS.map((u) => u.name);
const PASSWORD_FIELD_MAP: Record<string, string> = {
  current_password: "current",
  new_password: "next",
  confirm_password: "confirm",
};

export default function ProfilePage() {
  const { user, updateProfile, changePassword } = useAuth();
  const { t } = useSettings();
  const [activeTab, setActiveTab] = useState<Tab>("info");
  const isStudent = user?.role === "student";

  // ---- Thông tin cá nhân ----
  const [fullName, setFullName] = useState(user?.fullName || "");
  const [phoneNumber, setPhoneNumber] = useState(user?.phoneNumber || "");
  // Khoa/Ngành dùng cùng danh mục với form đăng ký; giá trị cũ ngoài danh mục tự rơi vào "Khác…".
  const catalog = useCatalogSelection(user?.department || "", user?.major || "");
  const { reset: resetCatalog } = catalog;
  const [profileErrors, setProfileErrors] = useState<Record<string, string>>({});
  const [profileMsg, setProfileMsg] = useState<{ kind: "success" | "error"; text: string } | null>(null);
  const [savingProfile, setSavingProfile] = useState(false);

  // ---- Ảnh đại diện ----
  const [showAvatarModal, setShowAvatarModal] = useState(false);
  const [avatarPreview, setAvatarPreview] = useState<string>("");
  const [avatarError, setAvatarError] = useState<string | null>(null);
  const [savingAvatar, setSavingAvatar] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // ---- Mật khẩu ----
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [passwordErrors, setPasswordErrors] = useState<Record<string, string>>({});
  const [passwordMsg, setPasswordMsg] = useState<{ kind: "success" | "error"; text: string } | null>(null);
  const [savingPassword, setSavingPassword] = useState(false);

  useEffect(() => {
    if (user) {
      setFullName(user.fullName || "");
      setPhoneNumber(user.phoneNumber || "");
      resetCatalog(user.department, user.major);
    }
  }, [user, resetCatalog]);

  const roleLabel =
    user?.role === "admin" ? t("profile.roleAdmin") : isStudent ? t("profile.roleStudent") : t("profile.rolePublic");

  const handleProfileSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setProfileMsg(null);
    const errors: Record<string, string> = {};
    const name = fullName.trim();
    if (name.length < 2 || name.length > 100) errors.fullName = t("auth.err.nameLength");
    if (phoneNumber.trim() && !/^\+?[0-9][0-9 .\-]{7,18}$/.test(phoneNumber.trim())) errors.phoneNumber = t("profile.err.phone");
    if (isStudent) {
      if (!catalog.departmentSel) errors.department = t("auth.err.departmentRequired");
      else if (catalog.department.length < 2 || catalog.department.length > 150) errors.department = t("auth.err.otherLength");
      if (!catalog.majorSel) errors.major = t("auth.err.majorRequired");
      else if (catalog.major.length < 2 || catalog.major.length > 150) errors.major = t("auth.err.otherLength");
    }
    setProfileErrors(errors);
    if (Object.keys(errors).length) return;

    setSavingProfile(true);
    const result = await updateProfile({
      fullName: name,
      phoneNumber: phoneNumber.trim(),
      ...(isStudent ? { department: catalog.department, major: catalog.major } : {}),
    });
    setSavingProfile(false);

    if (result.ok) {
      setProfileMsg({ kind: "success", text: t("profile.saved") });
    } else {
      if (result.field) setProfileErrors({ [PROFILE_FIELD_MAP[result.field] ?? result.field]: result.message ?? "" });
      setProfileMsg({ kind: "error", text: result.message || t("profile.saveFailed") });
    }
  };

  const openAvatarModal = () => {
    setAvatarPreview(user?.avatarUrl || "");
    setAvatarError(null);
    setShowAvatarModal(true);
  };

  const handleFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    e.target.value = ""; // cho phép chọn lại cùng một tệp
    if (!file) return;
    setAvatarError(null);
    try {
      setAvatarPreview(await fileToAvatarDataUrl(file));
    } catch (err) {
      const reason = err instanceof Error ? err.message : "";
      setAvatarError(reason === "too-large" ? t("profile.avatar.tooLarge") : t("profile.avatar.invalid"));
    }
  };

  const saveAvatar = async () => {
    setSavingAvatar(true);
    setAvatarError(null);
    const result = await updateProfile({ avatarUrl: avatarPreview });
    setSavingAvatar(false);
    if (result.ok) {
      setShowAvatarModal(false);
      setProfileMsg({ kind: "success", text: t("profile.saved") });
    } else {
      setAvatarError(result.message || t("profile.saveFailed"));
    }
  };

  const handlePasswordSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setPasswordMsg(null);
    const errors: Record<string, string> = {};
    if (!currentPassword) errors.current = t("profile.err.currentRequired");
    const problem = validatePassword(newPassword);
    if (problem) errors.next = t(problem);
    else if (newPassword === currentPassword) errors.next = t("profile.err.sameAsCurrent");
    if (!confirmPassword) errors.confirm = t("auth.err.confirmRequired");
    else if (confirmPassword !== newPassword) errors.confirm = t("auth.err.confirmMismatch");
    setPasswordErrors(errors);
    if (Object.keys(errors).length) return;

    setSavingPassword(true);
    const result = await changePassword({ currentPassword, newPassword, confirmPassword });
    setSavingPassword(false);

    if (result.ok) {
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
      setPasswordMsg({ kind: "success", text: t("profile.passwordChanged") });
    } else {
      if (result.field) setPasswordErrors({ [PASSWORD_FIELD_MAP[result.field] ?? result.field]: result.message ?? "" });
      setPasswordMsg({ kind: "error", text: result.message || t("profile.passwordFailed") });
    }
  };

  const checks = checkPassword(newPassword);
  const strength = newPassword ? estimateStrength(newPassword) : null;
  const strengthStyle = {
    weak: { bar: "bg-red-500", width: "33%", text: "text-red-700 dark:text-red-300" },
    medium: { bar: "bg-amber-500", width: "66%", text: "text-amber-700 dark:text-amber-300" },
    strong: { bar: "bg-emerald-500", width: "100%", text: "text-emerald-700 dark:text-emerald-300" },
  };

  const card = "rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-700 dark:bg-slate-800";
  const primaryBtn =
    "flex items-center gap-2 rounded-xl bg-blue-700 px-5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-blue-800 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 disabled:opacity-60";
  const tabBtn = (active: boolean) =>
    `flex items-center gap-2 border-b-2 px-4 py-2.5 text-sm font-semibold transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 ${
      active
        ? "border-blue-600 text-blue-700 dark:border-blue-400 dark:text-blue-300"
        : "border-transparent text-slate-700 hover:text-slate-900 dark:text-slate-300 dark:hover:text-white"
    }`;

  return (
    <div className="mx-auto max-w-4xl p-4 sm:p-6">
      {/* Đầu trang: ảnh đại diện + thông tin chính */}
      <div className={`${card} mb-6 overflow-hidden !p-0`}>
        <div className="h-28 bg-gradient-to-r from-blue-700 via-indigo-700 to-blue-800" />
        <div className="relative px-4 pb-6 sm:px-6">
          <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between">
            <div className="-mt-12 flex items-end gap-4">
              <button
                type="button"
                onClick={openAvatarModal}
                aria-label={t("profile.avatar.change")}
                className="group relative flex h-24 w-24 items-center justify-center overflow-hidden rounded-2xl border-4 border-white bg-blue-600 text-3xl font-bold text-white shadow-md focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-400 dark:border-slate-800"
              >
                {user?.avatarUrl ? (
                  <img src={user.avatarUrl} alt="" className="h-full w-full object-cover" />
                ) : (
                  <span aria-hidden="true">{user?.fullName?.charAt(0) ?? "U"}</span>
                )}
                <span className="absolute inset-0 flex flex-col items-center justify-center bg-black/50 text-white opacity-0 transition-opacity group-hover:opacity-100 group-focus-visible:opacity-100">
                  <Camera size={20} aria-hidden="true" />
                  <span className="mt-0.5 text-xs font-semibold">{t("profile.avatar.short")}</span>
                </span>
              </button>
              <div className="mb-1 min-w-0">
                <h1 className="truncate text-lg font-bold leading-6 text-slate-800 dark:text-slate-100">{user?.fullName}</h1>
                <p className="truncate text-sm leading-5 text-slate-600 dark:text-slate-300">{user?.email}</p>
              </div>
            </div>
            <div className="mt-4 flex flex-wrap gap-2 sm:mt-0">
              <span className="rounded-full border border-blue-200 bg-blue-50 px-3.5 py-1 text-xs font-semibold text-blue-800 dark:border-blue-800 dark:bg-blue-950/50 dark:text-blue-200">
                {roleLabel}
              </span>
              {isStudent && user?.studentCode && (
                <span className="rounded-full border border-slate-200 bg-slate-100 px-3.5 py-1 text-xs font-semibold text-slate-800 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100">
                  {t("profile.studentCodeBadge")}: {user.studentCode}
                </span>
              )}
            </div>
          </div>
        </div>
      </div>

      <div role="tablist" aria-label={t("profile.tabsLabel")} className="mb-6 flex gap-2 overflow-x-auto border-b border-slate-200 dark:border-slate-700">
        <button type="button" role="tab" id="tab-info" aria-selected={activeTab === "info"} aria-controls="panel-info" onClick={() => setActiveTab("info")} className={tabBtn(activeTab === "info")}>
          <UserIcon size={15} aria-hidden="true" />
          {t("profile.tabInfo")}
        </button>
        <button type="button" role="tab" id="tab-security" aria-selected={activeTab === "security"} aria-controls="panel-security" onClick={() => setActiveTab("security")} className={tabBtn(activeTab === "security")}>
          <ShieldCheck size={15} aria-hidden="true" />
          {t("profile.tabSecurity")}
        </button>
      </div>

      {activeTab === "info" && (
        <section id="panel-info" role="tabpanel" aria-labelledby="tab-info" className={card}>
          <h2 className="mb-1 text-base font-bold text-slate-800 dark:text-slate-100">{t("profile.infoTitle")}</h2>
          <p className="mb-6 text-sm text-slate-600 dark:text-slate-300">{t("profile.infoDesc")}</p>

          <div className="mb-4 space-y-3">
            {profileMsg && <Alert variant={profileMsg.kind}>{profileMsg.text}</Alert>}
          </div>

          <form onSubmit={handleProfileSubmit} noValidate className="space-y-5">
            <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
              <FormField label={t("auth.fullName")} value={fullName} onChange={setFullName} error={profileErrors.fullName} autoComplete="name" required />
              <FormField label={t("profile.email")} value={user?.email || ""} onChange={() => undefined} type="email" disabled hint={t("profile.emailReadonly")} />
              <FormField label={t("profile.phone")} value={phoneNumber} onChange={setPhoneNumber} error={profileErrors.phoneNumber} type="tel" inputMode="tel" autoComplete="tel" placeholder="0901234567" />
              {isStudent && (
                <>
                  <FormField label={t("auth.studentCode")} value={user?.studentCode || ""} onChange={() => undefined} disabled hint={t("profile.codeReadonly")} />
                  <Combobox
                    label={t("auth.department")}
                    value={catalog.departmentSel}
                    onChange={catalog.chooseDepartment}
                    options={departmentOptions}
                    otherLabel={t("auth.other")}
                    placeholder={t("auth.departmentPlaceholder")}
                    error={catalog.departmentSel === OTHER ? undefined : profileErrors.department}
                    required
                  />
                  {catalog.departmentSel === OTHER && (
                    <FormField label={t("auth.departmentOther")} value={catalog.departmentOther} onChange={catalog.setDepartmentOther} error={profileErrors.department} required />
                  )}
                  <Combobox
                    label={t("auth.major")}
                    value={catalog.majorSel}
                    onChange={catalog.chooseMajor}
                    options={catalog.majorOptions}
                    otherLabel={t("auth.other")}
                    placeholder={catalog.departmentSel ? t("auth.majorPlaceholder") : t("auth.majorChooseDepartmentFirst")}
                    disabled={!catalog.departmentSel}
                    error={catalog.majorSel === OTHER ? undefined : profileErrors.major}
                    required
                  />
                  {catalog.majorSel === OTHER && (
                    <FormField label={t("auth.majorOther")} value={catalog.majorOther} onChange={catalog.setMajorOther} error={profileErrors.major} required />
                  )}
                </>
              )}
            </div>
            <div className="flex justify-end pt-2">
              <button type="submit" disabled={savingProfile} className={primaryBtn}>
                <Save size={15} aria-hidden="true" />
                {savingProfile ? t("profile.saving") : t("profile.save")}
              </button>
            </div>
          </form>
        </section>
      )}

      {activeTab === "security" && (
        <section id="panel-security" role="tabpanel" aria-labelledby="tab-security" className={card}>
          <div className="mb-6 flex flex-col gap-3 border-b border-slate-100 pb-5 dark:border-slate-700 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 className="flex items-center gap-2 text-base font-bold text-slate-800 dark:text-slate-100">
                <KeyRound className="text-blue-600" size={20} aria-hidden="true" />
                {t("profile.securityTitle")}
              </h2>
              <p className="mt-0.5 text-sm text-slate-600 dark:text-slate-300">{t("profile.securityDesc")}</p>
            </div>
          </div>

          <div className="mb-4">{passwordMsg && <Alert variant={passwordMsg.kind}>{passwordMsg.text}</Alert>}</div>

          <form onSubmit={handlePasswordSubmit} noValidate className="max-w-md space-y-4">
            <FormField type="password" label={t("profile.currentPassword")} value={currentPassword} onChange={setCurrentPassword} error={passwordErrors.current} autoComplete="current-password" required />
            <div>
              <FormField type="password" label={t("profile.newPassword")} value={newPassword} onChange={setNewPassword} error={passwordErrors.next} autoComplete="new-password" required />
              {newPassword && strength && (
                <div className="mt-2.5 space-y-2 rounded-xl border border-slate-100 bg-slate-50 p-3 dark:border-slate-700 dark:bg-slate-900/50">
                  <div className="flex items-center justify-between text-xs" aria-live="polite">
                    <span className="font-medium text-slate-700 dark:text-slate-300">{t("profile.strength")}</span>
                    <span className={`font-bold ${strengthStyle[strength].text}`}>{t(`profile.strength.${strength}`)}</span>
                  </div>
                  <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-200 dark:bg-slate-700" aria-hidden="true">
                    <div className={`h-full transition-all duration-300 ${strengthStyle[strength].bar}`} style={{ width: strengthStyle[strength].width }} />
                  </div>
                  <ul className="grid grid-cols-1 gap-1 pt-1 text-xs sm:grid-cols-2">
                    {([
                      [checks.length, "auth.rule.length"],
                      [checks.letter, "auth.rule.letter"],
                      [checks.digit, "auth.rule.digit"],
                      [checks.bytes, "auth.rule.bytes"],
                    ] as const).map(([ok, key]) => (
                      <li key={key} className={`flex items-center gap-1 ${ok ? "font-medium text-emerald-700 dark:text-emerald-300" : "text-slate-600 dark:text-slate-400"}`}>
                        <Check size={12} aria-hidden="true" className={ok ? "opacity-100" : "opacity-30"} />
                        <span>{t(key)}</span>
                        <span className="sr-only">{ok ? t("profile.rule.met") : t("profile.rule.unmet")}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
            <FormField type="password" label={t("profile.confirmNew")} value={confirmPassword} onChange={setConfirmPassword} error={passwordErrors.confirm} autoComplete="new-password" required />
            <div className="pt-2">
              <button type="submit" disabled={savingPassword} className={`${primaryBtn} w-full justify-center sm:w-auto`}>
                <Lock size={15} aria-hidden="true" />
                {savingPassword ? t("profile.saving") : t("profile.changePassword")}
              </button>
            </div>
          </form>
        </section>
      )}

      {showAvatarModal && (
        <Modal title={t("profile.avatar.title")} onClose={() => setShowAvatarModal(false)}>
          <div className="space-y-4">
            {avatarError && <Alert variant="error">{avatarError}</Alert>}
            <input ref={fileInputRef} type="file" accept="image/*" onChange={handleFile} className="hidden" aria-label={t("profile.avatar.choose")} />
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="group flex w-full flex-col items-center justify-center gap-2 rounded-2xl border-2 border-dashed border-blue-300 bg-blue-50 p-6 text-center hover:border-blue-400 hover:bg-blue-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 dark:border-blue-700 dark:bg-blue-950/30 dark:hover:bg-blue-950/50"
            >
              <span className="rounded-full bg-blue-100 p-3 text-blue-700 dark:bg-blue-900 dark:text-blue-200">
                <Upload size={24} aria-hidden="true" />
              </span>
              <span className="text-sm font-bold text-slate-800 dark:text-slate-100">{t("profile.avatar.choose")}</span>
              <span className="text-xs text-slate-600 dark:text-slate-300">{t("profile.avatar.hint")}</span>
            </button>

            {avatarPreview && (
              <div className="flex items-center justify-between gap-3 rounded-xl border border-slate-200 bg-slate-50 p-3 dark:border-slate-600 dark:bg-slate-900/50">
                <div className="flex items-center gap-3">
                  <img src={avatarPreview} alt={t("profile.avatar.preview")} className="h-12 w-12 rounded-2xl border border-slate-300 object-cover" />
                  <p className="text-sm font-semibold text-slate-800 dark:text-slate-100">{t("profile.avatar.preview")}</p>
                </div>
                <button
                  type="button"
                  onClick={() => setAvatarPreview("")}
                  aria-label={t("profile.avatar.remove")}
                  className="rounded-lg p-1.5 text-red-700 hover:bg-red-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-red-500 dark:text-red-300 dark:hover:bg-red-950/40"
                >
                  <Trash2 size={16} aria-hidden="true" />
                </button>
              </div>
            )}

            <div className="flex justify-end gap-2 pt-2">
              <button type="button" onClick={() => setShowAvatarModal(false)} className="rounded-xl border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 dark:border-slate-600 dark:text-slate-200 dark:hover:bg-slate-700">
                {t("common.cancel")}
              </button>
              <button type="button" onClick={saveAvatar} disabled={savingAvatar || avatarPreview === (user?.avatarUrl || "")} className="rounded-xl bg-blue-700 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-800 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 disabled:opacity-60">
                {savingAvatar ? t("profile.saving") : t("profile.avatar.save")}
              </button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}
