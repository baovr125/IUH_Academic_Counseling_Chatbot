import { Sun, Moon, Laptop, Globe, Bell, Loader2 } from "lucide-react";
import { useSettings, applyAppTheme } from "../context/SettingsContext";

export { applyAppTheme };

export default function SettingsPage() {
  const {
    theme,
    language,
    soundEnabled,
    academicAlerts,
    loading,
    setTheme,
    setLanguage,
    setSoundEnabled,
    setAcademicAlerts,
    t,
  } = useSettings();

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600 dark:text-blue-400" />
        <span className="ml-3 text-xs font-medium text-slate-500 dark:text-slate-400">
          {t("settings.loadingSettings")}
        </span>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl p-6">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-slate-800 dark:text-slate-100">{t("settings.title")}</h1>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            {t("settings.subtitle")}
          </p>
        </div>
      </div>

      <div className="space-y-6">
        {/* Appearance Section */}
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-800 transition-colors">
          <h2 className="mb-1 text-sm font-bold text-slate-800 dark:text-slate-100">{t("settings.appearance")}</h2>
          <p className="mb-4 text-xs text-slate-500 dark:text-slate-400">
            {t("settings.appearanceDesc")}
          </p>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            {[
              { id: "light", label: t("settings.themeLight"), desc: t("settings.themeLightDesc"), icon: Sun },
              { id: "dark", label: t("settings.themeDark"), desc: t("settings.themeDarkDesc"), icon: Moon },
              { id: "system", label: t("settings.themeSystem"), desc: t("settings.themeSystemDesc"), icon: Laptop },
            ].map(({ id, label, desc, icon: Icon }) => (
              <button
                type="button"
                key={id}
                onClick={() => setTheme(id as "light" | "dark" | "system")}
                className={`flex flex-col items-start rounded-xl border p-4 text-left transition-all ${
                  theme === id
                    ? "border-blue-600 bg-blue-50/60 ring-2 ring-blue-500/20 dark:border-blue-500 dark:bg-blue-950/40 dark:ring-blue-400/20"
                    : "border-slate-200 bg-white hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800/80 dark:hover:bg-slate-700/60"
                }`}
              >
                <div
                  className={`mb-3 flex h-10 w-10 items-center justify-center rounded-lg ${
                    theme === id
                      ? "bg-blue-600 text-white dark:bg-blue-500"
                      : "bg-slate-100 text-slate-600 dark:bg-slate-700 dark:text-slate-300"
                  }`}
                >
                  <Icon size={20} />
                </div>
                <div className="text-xs font-bold text-slate-800 dark:text-slate-100">{label}</div>
                <div className="mt-0.5 text-[11px] text-slate-500 dark:text-slate-400">{desc}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Language Section */}
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-800 transition-colors">
          <div className="flex items-center gap-2 mb-1">
            <Globe size={16} className="text-blue-600 dark:text-blue-400" />
            <h2 className="text-sm font-bold text-slate-800 dark:text-slate-100">{t("settings.language")}</h2>
          </div>
          <p className="mb-4 text-xs text-slate-500 dark:text-slate-400">
            {t("settings.languageDesc")}
          </p>

          <div className="flex flex-wrap gap-3">
            {[
              { id: "vi", label: t("settings.langVi") },
              { id: "en", label: t("settings.langEn") },
            ].map(({ id, label }) => (
              <button
                type="button"
                key={id}
                onClick={() => setLanguage(id as "vi" | "en")}
                className={`rounded-xl border px-4 py-2.5 text-xs font-semibold transition-colors ${
                  language === id
                    ? "border-blue-600 bg-blue-50 text-blue-700 dark:border-blue-500 dark:bg-blue-950/60 dark:text-blue-400"
                    : "border-slate-200 bg-white text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
                }`}
              >
                {label}
              </button>
            ))}
          </div>
        </div>

        {/* Notification Settings */}
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-800 transition-colors">
          <div className="flex items-center gap-2 mb-1">
            <Bell size={16} className="text-blue-600 dark:text-blue-400" />
            <h2 className="text-sm font-bold text-slate-800 dark:text-slate-100">{t("settings.notifications")}</h2>
          </div>
          <p className="mb-4 text-xs text-slate-500 dark:text-slate-400">
            {t("settings.notificationsDesc")}
          </p>

          <div className="divide-y divide-slate-100 dark:divide-slate-700/50">
            <div className="flex items-center justify-between py-3">
              <div>
                <div className="text-xs font-semibold text-slate-800 dark:text-slate-100">{t("settings.soundTitle")}</div>
                <div className="text-[11px] text-slate-500 dark:text-slate-400">
                  {t("settings.soundDesc")}
                </div>
              </div>
              <button
                type="button"
                onClick={() => setSoundEnabled(!soundEnabled)}
                className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full transition-colors ${
                  soundEnabled ? "bg-blue-600 dark:bg-blue-500" : "bg-slate-200 dark:bg-slate-700"
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
                <div className="text-xs font-semibold text-slate-800 dark:text-slate-100">{t("settings.academicAlertsTitle")}</div>
                <div className="text-[11px] text-slate-500 dark:text-slate-400">
                  {t("settings.academicAlertsDesc")}
                </div>
              </div>
              <button
                type="button"
                onClick={() => setAcademicAlerts(!academicAlerts)}
                className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full transition-colors ${
                  academicAlerts ? "bg-blue-600 dark:bg-blue-500" : "bg-slate-200 dark:bg-slate-700"
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
