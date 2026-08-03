import { useState, useEffect } from "react";
import { Sun, Moon, Laptop, Globe, Bell, CheckCircle2, Save, Loader2, AlertCircle } from "lucide-react";
import { fetchUserSettings, updateUserSettings } from "../services/settingsService";

export default function SettingsPage() {
  const [theme, setTheme] = useState<"light" | "dark" | "system">("light");
  const [language, setLanguage] = useState<"vi" | "en">("vi");

  // Notification toggles
  const [soundEnabled, setSoundEnabled] = useState(true);
  const [academicAlerts, setAcademicAlerts] = useState(true);

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    async function loadSettings() {
      setLoading(true);
      setErrorMessage(null);
      const res = await fetchUserSettings();
      if (res.ok && res.data) {
        if (res.data.theme) setTheme(res.data.theme as "light" | "dark" | "system");
        if (res.data.language) setLanguage(res.data.language as "vi" | "en");
        if (typeof res.data.soundEnabled === "boolean") setSoundEnabled(res.data.soundEnabled);
        if (typeof res.data.academicAlerts === "boolean") setAcademicAlerts(res.data.academicAlerts);
      } else if (!res.ok) {
        // Fallback gracefully if not logged in or server unreachable
      }
      setLoading(false);
    }
    loadSettings();
  }, []);

  const handleSaveSettings = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setSavedSuccess(false);
    setErrorMessage(null);

    const res = await updateUserSettings({
      theme,
      language,
      soundEnabled,
      academicAlerts,
    });

    setSaving(false);
    if (res.ok) {
      setSavedSuccess(true);
      setTimeout(() => setSavedSuccess(false), 3500);
    } else {
      setErrorMessage(res.error?.message || "Không thể lưu cài đặt hệ thống.");
    }
  };

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
        <span className="ml-3 text-xs font-medium text-slate-500">Đang tải cài đặt hệ thống...</span>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl p-6">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-slate-800">Cài đặt hệ thống</h1>
          <p className="text-xs text-slate-500">
            Tùy chỉnh giao diện, ngôn ngữ và nhận thông báo học vụ IUH
          </p>
        </div>

        <button
          onClick={handleSaveSettings}
          disabled={saving}
          type="button"
          className="flex items-center gap-2 rounded-xl bg-blue-600 px-5 py-2.5 text-xs font-semibold text-white shadow-sm hover:bg-blue-700 disabled:opacity-50 transition-colors"
        >
          {saving ? <Loader2 size={15} className="animate-spin" /> : <Save size={15} />}
          <span>{saving ? "Đang lưu..." : "Lưu cài đặt"}</span>
        </button>
      </div>

      {savedSuccess && (
        <div className="mb-6 flex items-center gap-3 rounded-xl border border-green-200 bg-green-50 p-4 text-xs font-medium text-green-800">
          <CheckCircle2 size={18} className="text-green-600 flex-shrink-0" />
          <span>Toàn bộ cài đặt hệ thống đã được lưu thành công!</span>
        </div>
      )}

      {errorMessage && (
        <div className="mb-6 flex items-center gap-3 rounded-xl border border-red-200 bg-red-50 p-4 text-xs font-medium text-red-800">
          <AlertCircle size={18} className="text-red-600 flex-shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      <div className="space-y-6">
        {/* Appearance Section */}
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="mb-1 text-sm font-bold text-slate-800">Giao diện & Hiển thị</h2>
          <p className="mb-4 text-xs text-slate-500">
            Chọn chủ đề giao diện phù hợp với sở thích của bạn
          </p>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            {[
              { id: "light", label: "Giao diện Sáng", desc: "Chuẩn sáng dễ nhìn", icon: Sun },
              { id: "dark", label: "Giao diện Tối", desc: "Tiết kiệm mắt ban đêm", icon: Moon },
              { id: "system", label: "Theo hệ thống", desc: "Đồng bộ thiết bị", icon: Laptop },
            ].map(({ id, label, desc, icon: Icon }) => (
              <button
                type="button"
                key={id}
                onClick={() => setTheme(id as "light" | "dark" | "system")}
                className={`flex flex-col items-start rounded-xl border p-4 text-left transition-all ${
                  theme === id
                    ? "border-blue-600 bg-blue-50/60 ring-2 ring-blue-500/20"
                    : "border-slate-200 bg-white hover:bg-slate-50"
                }`}
              >
                <div
                  className={`mb-3 flex h-10 w-10 items-center justify-center rounded-lg ${
                    theme === id ? "bg-blue-600 text-white" : "bg-slate-100 text-slate-600"
                  }`}
                >
                  <Icon size={20} />
                </div>
                <div className="text-xs font-bold text-slate-800">{label}</div>
                <div className="mt-0.5 text-[11px] text-slate-500">{desc}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Language Section */}
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex items-center gap-2 mb-1">
            <Globe size={16} className="text-blue-600" />
            <h2 className="text-sm font-bold text-slate-800">Ngôn ngữ hiển thị</h2>
          </div>
          <p className="mb-4 text-xs text-slate-500">
            Ngôn ngữ chính sử dụng trong giao diện hệ thống
          </p>

          <div className="flex flex-wrap gap-3">
            {[
              { id: "vi", label: "Tiếng Việt (Mặc định)" },
              { id: "en", label: "English (United States)" },
            ].map(({ id, label }) => (
              <button
                type="button"
                key={id}
                onClick={() => setLanguage(id as "vi" | "en")}
                className={`rounded-xl border px-4 py-2.5 text-xs font-semibold transition-colors ${
                  language === id
                    ? "border-blue-600 bg-blue-50 text-blue-700"
                    : "border-slate-200 bg-white text-slate-700 hover:bg-slate-50"
                }`}
              >
                {label}
              </button>
            ))}
          </div>
        </div>

        {/* Notification Settings */}
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex items-center gap-2 mb-1">
            <Bell size={16} className="text-blue-600" />
            <h2 className="text-sm font-bold text-slate-800">Thông báo hệ thống</h2>
          </div>
          <p className="mb-4 text-xs text-slate-500">
            Quản lý nhận thông báo học vụ từ trường và âm thanh thông báo
          </p>

          <div className="divide-y divide-slate-100">
            <div className="flex items-center justify-between py-3">
              <div>
                <div className="text-xs font-semibold text-slate-800">Âm thanh thông báo</div>
                <div className="text-[11px] text-slate-500">
                  Phát âm báo nhẹ khi hoàn thành dịch thuật hoặc thao tác xong
                </div>
              </div>
              <button
                type="button"
                onClick={() => setSoundEnabled(!soundEnabled)}
                className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full transition-colors ${
                  soundEnabled ? "bg-blue-600" : "bg-slate-200"
                }`}
              >
                <span
                  className={`inline-block h-5 w-5 transform rounded-full bg-white shadow transition-transform ${
                    soundEnabled ? "translate-x-5" : "translate-x-0.5"
                  } mt-0.5`}
                />
              </button>
            </div>

            <div className="flex items-center justify-between py-3">
              <div>
                <div className="text-xs font-semibold text-slate-800">Thông báo học vụ mới từ IUH</div>
                <div className="text-[11px] text-slate-500">
                  Nhận thông báo tự động khi có quy chế mới hoặc thông báo học vụ
                </div>
              </div>
              <button
                type="button"
                onClick={() => setAcademicAlerts(!academicAlerts)}
                className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full transition-colors ${
                  academicAlerts ? "bg-blue-600" : "bg-slate-200"
                }`}
              >
                <span
                  className={`inline-block h-5 w-5 transform rounded-full bg-white shadow transition-transform ${
                    academicAlerts ? "translate-x-5" : "translate-x-0.5"
                  } mt-0.5`}
                />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
