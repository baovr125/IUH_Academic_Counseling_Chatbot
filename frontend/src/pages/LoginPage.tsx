import { useEffect, useId, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Globe, GraduationCap } from "lucide-react";
import { useAuth } from "../hooks/useAuth";
import { useSettings } from "../context/SettingsContext";
import { FormField } from "../components/auth/FormField";
import { Combobox } from "../components/ui/Combobox";
import { IUH_UNITS, OTHER } from "../data/iuhCatalog";
import { useCatalogSelection } from "../hooks/useCatalogSelection";
import logoMark from "../assets/brand/iuh-mark-256.png";
import { Alert } from "../components/ui/Alert";
import { validatePassword } from "../services/passwordPolicy";

type UserType = "student" | "public";
type FieldErrors = Record<string, string>;

const EMAIL_REGEX = /^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)+$/;
const NAME_REGEX = /^[\p{L}\s.'-]+$/u;
const departmentOptions = IUH_UNITS.map((u) => u.name);
const IUH_DOMAINS = ["@student.iuh.edu.vn", "@iuh.edu.vn"];

// Tên trường server (snake_case) → tên trường trên form.
const SERVER_FIELD_MAP: Record<string, string> = {
  email: "identifier",
  identifier: "identifier",
  student_code: "identifier", // MSSV được suy ra từ email nên lỗi trùng MSSV hiển thị ở ô email
  studentCode: "identifier",
  full_name: "fullName",
  fullName: "fullName",
  department: "department",
  major: "major",
  password: "password",
  confirm_password: "confirmPassword",
};

export default function LoginPage() {
  const { isAuthenticated, login, register, isLoading, error } = useAuth();
  const { t, language, setLanguage } = useSettings();
  const navigate = useNavigate();
  const formRef = useRef<HTMLFormElement>(null);
  const rememberId = useId();

  const [isRegistering, setIsRegistering] = useState(false);
  const [userType, setUserType] = useState<UserType>("student");
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  // Khoa/Viện và Ngành: chọn từ danh mục IUH (tìm kiếm được) hoặc "Khác…" rồi nhập tay.
  const catalog = useCatalogSelection();
  const { departmentSel, majorSel, department, major } = catalog;
  const [rememberMe, setRememberMe] = useState(false);

  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Đã đăng nhập thì chuyển vào ứng dụng.
  useEffect(() => {
    if (isAuthenticated) navigate("/dashboard", { replace: true });
  }, [isAuthenticated, navigate]);

  // Sau khi có lỗi trên form, đưa focus tới ô lỗi đầu tiên (người dùng bàn phím/trình đọc màn hình).
  useEffect(() => {
    if (Object.keys(fieldErrors).length > 0) {
      formRef.current?.querySelector<HTMLElement>('[aria-invalid="true"]')?.focus();
    }
  }, [fieldErrors]);

  const clearError = (field: string) => {
    setFieldErrors((prev) => {
      if (!prev[field]) return prev;
      const next = { ...prev };
      delete next[field];
      return next;
    });
    setFormError(null);
  };

  const bind = (field: string, setter: (v: string) => void) => (value: string) => {
    setter(value);
    clearError(field);
  };

  const switchMode = (registering: boolean) => {
    setIsRegistering(registering);
    setFieldErrors({});
    setFormError(null);
  };

  const validateRegistration = (): FieldErrors => {
    const errors: FieldErrors = {};
    const name = fullName.trim();
    const email = identifier.trim().toLowerCase();

    if (!name) errors.fullName = t("auth.err.nameRequired");
    else if (name.length < 2 || name.length > 100) errors.fullName = t("auth.err.nameLength");
    else if (!NAME_REGEX.test(name)) errors.fullName = t("auth.err.nameChars");

    if (!email) errors.identifier = t("auth.err.emailRequired");
    else if (!EMAIL_REGEX.test(email)) errors.identifier = t("auth.err.emailFormat");
    else if (userType === "student" && !IUH_DOMAINS.some((d) => email.endsWith(d))) {
      errors.identifier = t("auth.err.emailDomain");
    }

    if (userType === "student") {
      if (!departmentSel) errors.department = t("auth.err.departmentRequired");
      else if (departmentSel === OTHER && (department.length < 2 || department.length > 150)) errors.department = t("auth.err.otherLength");
      if (!majorSel) errors.major = t("auth.err.majorRequired");
      else if (majorSel === OTHER && (major.length < 2 || major.length > 150)) errors.major = t("auth.err.otherLength");
    }

    const passwordProblem = validatePassword(password, email);
    if (passwordProblem) errors.password = t(passwordProblem);

    if (!confirmPassword) errors.confirmPassword = t("auth.err.confirmRequired");
    else if (password !== confirmPassword) errors.confirmPassword = t("auth.err.confirmMismatch");
    return errors;
  };

  const handleRegister = async () => {
    const errors = validateRegistration();
    if (Object.keys(errors).length > 0) {
      setFieldErrors(errors);
      setFormError(t("auth.err.fixFields"));
      return;
    }
    const email = identifier.trim();
    const result = await register({
      fullName: fullName.trim(),
      identifier: email,
      password,
      confirmPassword,
      userType,
      department: userType === "student" ? department : undefined,
      major: userType === "student" ? major : undefined,
    });

    if (result.ok) {
      setIsRegistering(false);
      setIdentifier(email);
      setPassword("");
      setConfirmPassword("");
      setFieldErrors({});
      setSuccessMsg(t("auth.registerSuccess"));
      return;
    }

    const serverErrors: FieldErrors = {};
    if (result.field) {
      serverErrors[SERVER_FIELD_MAP[result.field] ?? result.field] = result.message || t("auth.err.invalid");
    }
    result.details?.forEach((item) => {
      const key = SERVER_FIELD_MAP[item.field];
      if (key && !serverErrors[key]) serverErrors[key] = item.message;
    });
    setFieldErrors(serverErrors);
    setFormError(result.message || t("auth.err.registerFailed"));
  };

  const handleLogin = async () => {
    const errors: FieldErrors = {};
    if (!identifier.trim()) errors.identifier = t("auth.err.identifierRequired");
    if (!password) errors.password = t("auth.err.passwordRequired");
    if (Object.keys(errors).length > 0) {
      setFieldErrors(errors);
      setFormError(t("auth.err.loginRequired"));
      return;
    }
    setFieldErrors({});
    const ok = await login({ identifier: identifier.trim(), password, rememberMe });
    if (ok) navigate("/dashboard");
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);
    setSuccessMsg(null);
    if (isRegistering) await handleRegister();
    else await handleLogin();
  };

  // Lỗi tầng đăng nhập (sai mật khẩu, bị khóa tạm, máy chủ lỗi...) lấy từ useAuth.
  const bannerError = formError || (!isRegistering ? error : null);

  const tabClass = (active: boolean) =>
    `flex-1 rounded-lg py-2 text-sm font-semibold transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 ${
      active
        ? "bg-white text-blue-700 shadow-sm dark:bg-slate-700 dark:text-blue-300"
        : "text-slate-700 hover:text-slate-900 dark:text-slate-300 dark:hover:text-white"
    }`;

  const typeClass = (active: boolean) =>
    `flex items-center justify-center gap-2 rounded-xl border p-2.5 text-sm font-semibold transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 ${
      active
        ? "border-blue-600 bg-blue-50 text-blue-700 dark:border-blue-400 dark:bg-blue-950/40 dark:text-blue-200"
        : "border-slate-300 bg-white text-slate-700 hover:bg-slate-50 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
    }`;

  return (
    <div className="flex min-h-screen">
      {/* Banner bên trái (ẩn trên màn hình nhỏ) */}
      <div className="relative hidden flex-col justify-between overflow-hidden bg-gradient-to-br from-blue-900 via-blue-800 to-indigo-950 p-12 text-white lg:flex lg:w-1/2">
        <div className="pointer-events-none absolute -left-24 -top-24 h-96 w-96 rounded-full bg-blue-500/20 blur-3xl" />
        <div className="pointer-events-none absolute -bottom-24 -right-24 h-96 w-96 rounded-full bg-indigo-500/20 blur-3xl" />

        <div className="relative z-10 flex items-center gap-4">
          {/* relative z-10: các vệt sáng trang trí (absolute) nếu không sẽ phủ lên và làm ngả màu thẻ logo */}
          {/* Logo nền xanh đậm nên đặt trên thẻ trắng để giữ đúng màu nhận diện của trường */}
          <div className="rounded-2xl bg-white p-2.5 shadow-lg shadow-blue-950/30">
            <img src={logoMark} alt={t("auth.logoAlt")} className="h-12 w-auto" />
          </div>
          <span className="text-3xl font-extrabold tracking-tight text-white">IUH Portal AI</span>
        </div>

        <div className="relative z-10 my-auto space-y-4 py-12">
          <div className="inline-flex items-center gap-2 rounded-full border border-blue-300/30 bg-blue-500/20 px-3 py-1 text-xs font-medium text-blue-100">
            <GraduationCap size={14} aria-hidden="true" />
            <span>{t("auth.tagline")}</span>
          </div>
          <h1 className="text-3xl font-extrabold leading-tight text-white lg:text-4xl">
            {t("auth.heroLine1")} <br />
            <span className="bg-gradient-to-r from-blue-200 via-indigo-100 to-white bg-clip-text text-transparent">
              {t("auth.heroLine2")}
            </span>
          </h1>
          <p className="max-w-md text-sm leading-relaxed text-blue-100">{t("auth.heroDesc")}</p>
        </div>
      </div>

      {/* Form bên phải */}
      <main className="flex w-full items-center justify-center overflow-y-auto bg-slate-50 p-4 dark:bg-slate-900 sm:p-6 lg:w-1/2">
        <div className="my-auto w-full max-w-md">
          {/* Màn hình nhỏ không có banner: hiển thị logo trường phía trên form */}
          <div className="mb-3 flex items-center justify-between">
            <div className="flex items-center gap-3 lg:invisible">
              <div className="rounded-xl bg-white p-1.5 shadow-sm ring-1 ring-slate-200 dark:ring-slate-700">
                <img src={logoMark} alt={t("auth.logoAlt")} className="h-10 w-10 object-contain" />
              </div>
              <span className="text-xl font-extrabold tracking-tight text-slate-800 dark:text-slate-100">IUH Portal AI</span>
            </div>
            <div role="group" aria-label={t("auth.languageLabel")} className="flex gap-1 text-xs">
              {(["vi", "en"] as const).map((code) => (
                <button
                  key={code}
                  type="button"
                  onClick={() => setLanguage(code)}
                  aria-pressed={language === code}
                  className={`rounded-md px-2 py-1 font-semibold focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 ${
                    language === code
                      ? "bg-blue-700 text-white"
                      : "text-slate-700 hover:bg-slate-200 dark:text-slate-300 dark:hover:bg-slate-700"
                  }`}
                >
                  {code === "vi" ? "Tiếng Việt" : "English"}
                </button>
              ))}
            </div>
          </div>

          <form
            ref={formRef}
            onSubmit={handleSubmit}
            noValidate
            aria-busy={isLoading}
            className="rounded-2xl bg-white p-6 shadow-sm dark:bg-slate-800 sm:p-8"
          >
            <div role="tablist" aria-label={t("auth.modeLabel")} className="mb-6 flex rounded-xl bg-slate-100 p-1 dark:bg-slate-900">
              <button type="button" role="tab" aria-selected={!isRegistering} onClick={() => switchMode(false)} className={tabClass(!isRegistering)}>
                {t("auth.tabLogin")}
              </button>
              <button type="button" role="tab" aria-selected={isRegistering} onClick={() => switchMode(true)} className={tabClass(isRegistering)}>
                {t("auth.tabRegister")}
              </button>
            </div>

            <h2 className="mb-1 text-xl font-bold text-slate-800 dark:text-slate-100">
              {isRegistering ? t("auth.titleRegister") : t("auth.titleLogin")}
            </h2>
            <p className="mb-5 text-sm text-slate-600 dark:text-slate-300">
              {isRegistering ? t("auth.subtitleRegister") : t("auth.subtitleLogin")}
            </p>

            <div className="space-y-4">
              {successMsg && <Alert variant="success">{successMsg}</Alert>}

              {isRegistering && (
                <fieldset className="space-y-2">
                  <legend className="mb-1 text-sm font-semibold text-slate-700 dark:text-slate-200">{t("auth.audience")}</legend>
                  <div className="grid grid-cols-2 gap-2">
                    <button
                      type="button"
                      aria-pressed={userType === "student"}
                      onClick={() => {
                        setUserType("student");
                        setFieldErrors({});
                      }}
                      className={typeClass(userType === "student")}
                    >
                      <GraduationCap size={16} aria-hidden="true" />
                      <span>{t("auth.audienceStudent")}</span>
                    </button>
                    <button
                      type="button"
                      aria-pressed={userType === "public"}
                      onClick={() => {
                        setUserType("public");
                        setFieldErrors({});
                      }}
                      className={typeClass(userType === "public")}
                    >
                      <Globe size={16} aria-hidden="true" />
                      <span>{t("auth.audiencePublic")}</span>
                    </button>
                  </div>
                </fieldset>
              )}

              {isRegistering && (
                <FormField
                  label={t("auth.fullName")}
                  value={fullName}
                  onChange={bind("fullName", setFullName)}
                  error={fieldErrors.fullName}
                  placeholder={t("auth.fullNamePlaceholder")}
                  autoComplete="name"
                  required
                />
              )}

              <FormField
                label={
                  isRegistering
                    ? userType === "student"
                      ? t("auth.emailStudent")
                      : t("auth.emailPublic")
                    : t("auth.identifier")
                }
                value={identifier}
                onChange={bind("identifier", setIdentifier)}
                error={fieldErrors.identifier}
                placeholder={
                  isRegistering
                    ? userType === "student"
                      ? "mssv@student.iuh.edu.vn"
                      : "ten@gmail.com"
                    : t("auth.identifierPlaceholder")
                }
                hint={isRegistering && userType === "student" ? t("auth.emailStudentHint") : undefined}
                autoComplete={isRegistering ? "email" : "username"}
                inputMode={isRegistering ? "email" : "text"}
                required
                autoFocus={!isRegistering}
              />

              {isRegistering && userType === "student" && (
                <>
                  <Combobox
                    label={t("auth.department")}
                    value={departmentSel}
                    onChange={(v) => {
                      catalog.chooseDepartment(v);
                      clearError("department");
                      clearError("major");
                    }}
                    options={departmentOptions}
                    otherLabel={t("auth.other")}
                    placeholder={t("auth.departmentPlaceholder")}
                    error={departmentSel === OTHER ? undefined : fieldErrors.department}
                    required
                  />
                  {departmentSel === OTHER && (
                    <FormField
                      label={t("auth.departmentOther")}
                      value={catalog.departmentOther}
                      onChange={bind("department", catalog.setDepartmentOther)}
                      error={fieldErrors.department}
                      autoComplete="organization"
                      required
                    />
                  )}
                  <Combobox
                    label={t("auth.major")}
                    value={majorSel}
                    onChange={(v) => {
                      catalog.chooseMajor(v);
                      clearError("major");
                    }}
                    options={catalog.majorOptions}
                    otherLabel={t("auth.other")}
                    placeholder={departmentSel ? t("auth.majorPlaceholder") : t("auth.majorChooseDepartmentFirst")}
                    disabled={!departmentSel}
                    error={majorSel === OTHER ? undefined : fieldErrors.major}
                    required
                  />
                  {majorSel === OTHER && (
                    <FormField
                      label={t("auth.majorOther")}
                      value={catalog.majorOther}
                      onChange={bind("major", catalog.setMajorOther)}
                      error={fieldErrors.major}
                      autoComplete="off"
                      required
                    />
                  )}
                </>
              )}

              <FormField
                type="password"
                label={t("auth.password")}
                value={password}
                onChange={bind("password", setPassword)}
                error={fieldErrors.password}
                hint={isRegistering ? t("auth.passwordHint") : undefined}
                autoComplete={isRegistering ? "new-password" : "current-password"}
                required
              />

              {isRegistering && (
                <FormField
                  type="password"
                  label={t("auth.confirmPassword")}
                  value={confirmPassword}
                  onChange={bind("confirmPassword", setConfirmPassword)}
                  error={fieldErrors.confirmPassword}
                  autoComplete="new-password"
                  required
                />
              )}

              {!isRegistering && (
                <div className="flex items-center gap-2">
                  <input
                    id={rememberId}
                    type="checkbox"
                    checked={rememberMe}
                    onChange={(e) => setRememberMe(e.target.checked)}
                    className="h-4 w-4 rounded border-slate-400 text-blue-700 focus:ring-2 focus:ring-blue-500"
                  />
                  <label htmlFor={rememberId} className="text-sm text-slate-700 dark:text-slate-200">
                    {t("auth.rememberMe")}
                  </label>
                </div>
              )}

              {bannerError && <Alert variant="error">{bannerError}</Alert>}

              <button
                type="submit"
                disabled={isLoading}
                className="w-full rounded-lg bg-blue-700 py-2.5 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-blue-800 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 disabled:opacity-60"
              >
                {isLoading
                  ? isRegistering
                    ? t("auth.submittingRegister")
                    : t("auth.submittingLogin")
                  : isRegistering
                  ? t("auth.submitRegister")
                  : t("auth.submitLogin")}
              </button>

              {!isRegistering && <p className="text-center text-xs text-slate-600 dark:text-slate-400">{t("auth.forgotNotice")}</p>}
            </div>

            <p className="mt-6 text-center text-sm text-slate-600 dark:text-slate-300">
              {isRegistering ? t("auth.haveAccount") : t("auth.noAccount")}{" "}
              <button
                type="button"
                onClick={() => switchMode(!isRegistering)}
                className="font-semibold text-blue-700 underline-offset-2 hover:underline focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 dark:text-blue-300"
              >
                {isRegistering ? t("auth.tabLogin") : t("auth.tabRegister")}
              </button>
            </p>
          </form>
        </div>
      </main>
    </div>
  );
}
