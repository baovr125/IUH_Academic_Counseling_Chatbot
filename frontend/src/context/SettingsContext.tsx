import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import { fetchUserSettings, updateUserSettings } from "../services/settingsService";
import { getToken } from "../services/authService";
import { translations, Language, TranslationKey } from "../translations";
import type { UserSettings } from "../types";

export type ThemeMode = "light" | "dark" | "system";

export function applyAppTheme(selectedTheme: ThemeMode) {
  const root = document.documentElement;
  if (selectedTheme === "dark") {
    root.classList.add("dark");
  } else if (selectedTheme === "light") {
    root.classList.remove("dark");
  } else {
    const isDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    if (isDark) root.classList.add("dark");
    else root.classList.remove("dark");
  }
}

interface SettingsContextType {
  theme: ThemeMode;
  language: Language;
  soundEnabled: boolean;
  academicAlerts: boolean;
  loading: boolean;
  setTheme: (newTheme: ThemeMode) => void;
  setLanguage: (newLang: Language) => void;
  setSoundEnabled: (enabled: boolean) => void;
  setAcademicAlerts: (enabled: boolean) => void;
  t: (key: TranslationKey | string) => string;
}

const SettingsContext = createContext<SettingsContextType | undefined>(undefined);

export const SettingsProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [theme, setThemeState] = useState<ThemeMode>(() => {
    const saved = localStorage.getItem("app_theme");
    return (saved as ThemeMode) || "light";
  });

  const [language, setLanguageState] = useState<Language>(() => {
    const saved = localStorage.getItem("app_language");
    return (saved as Language) || "vi";
  });

  const [soundEnabled, setSoundEnabledState] = useState<boolean>(() => {
    const saved = localStorage.getItem("app_sound");
    return saved !== null ? saved === "true" : true;
  });

  const [academicAlerts, setAcademicAlertsState] = useState<boolean>(() => {
    const saved = localStorage.getItem("app_academic_alerts");
    return saved !== null ? saved === "true" : true;
  });

  const [loading, setLoading] = useState<boolean>(true);

  // Apply theme immediately on change or system preference change
  useEffect(() => {
    applyAppTheme(theme);
    localStorage.setItem("app_theme", theme);

    if (theme === "system") {
      const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
      const handleChange = () => applyAppTheme("system");
      mediaQuery.addEventListener("change", handleChange);
      return () => mediaQuery.removeEventListener("change", handleChange);
    }
  }, [theme]);

  // Load initial settings from backend silently only if user is logged in
  useEffect(() => {
    let isMounted = true;
    async function loadBackendSettings() {
      if (!getToken()) {
        if (isMounted) setLoading(false);
        return;
      }

      try {
        const res = await fetchUserSettings();
        if (isMounted && res.ok && res.data) {
          if (res.data.theme) {
            const loadedTheme = res.data.theme as ThemeMode;
            setThemeState(loadedTheme);
            localStorage.setItem("app_theme", loadedTheme);
            applyAppTheme(loadedTheme);
          }
          if (res.data.language) {
            const loadedLang = res.data.language as Language;
            setLanguageState(loadedLang);
            localStorage.setItem("app_language", loadedLang);
          }
          if (typeof res.data.soundEnabled === "boolean") {
            setSoundEnabledState(res.data.soundEnabled);
            localStorage.setItem("app_sound", String(res.data.soundEnabled));
          }
          if (typeof res.data.academicAlerts === "boolean") {
            setAcademicAlertsState(res.data.academicAlerts);
            localStorage.setItem("app_academic_alerts", String(res.data.academicAlerts));
          }
        }
      } catch (err) {
        // Silent fallback to local state
      } finally {
        if (isMounted) setLoading(false);
      }
    }
    loadBackendSettings();
    return () => {
      isMounted = false;
    };
  }, []);

  // Silent background sync with backend
  const syncToBackend = useCallback(async (updated: Partial<UserSettings>) => {
    if (!getToken()) return;
    const payload: UserSettings = {
      theme: updated.theme ?? theme,
      language: updated.language ?? language,
      soundEnabled: updated.soundEnabled ?? soundEnabled,
      academicAlerts: updated.academicAlerts ?? academicAlerts,
    };
    try {
      await updateUserSettings(payload);
    } catch (err) {
      // Silent error logging
    }
  }, [theme, language, soundEnabled, academicAlerts]);

  const setTheme = (newTheme: ThemeMode) => {
    setThemeState(newTheme);
    applyAppTheme(newTheme);
    localStorage.setItem("app_theme", newTheme);
    syncToBackend({ theme: newTheme });
  };

  const setLanguage = (newLang: Language) => {
    setLanguageState(newLang);
    localStorage.setItem("app_language", newLang);
    syncToBackend({ language: newLang });
  };

  const setSoundEnabled = (enabled: boolean) => {
    setSoundEnabledState(enabled);
    localStorage.setItem("app_sound", String(enabled));
    syncToBackend({ soundEnabled: enabled });
  };

  const setAcademicAlerts = (enabled: boolean) => {
    setAcademicAlertsState(enabled);
    localStorage.setItem("app_academic_alerts", String(enabled));
    syncToBackend({ academicAlerts: enabled });
  };

  const t = useCallback(
    (key: TranslationKey | string): string => {
      const dict = translations[language] || translations.vi;
      return (dict as any)[key] || (translations.vi as any)[key] || key;
    },
    [language]
  );

  return (
    <SettingsContext.Provider
      value={{
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
      }}
    >
      {children}
    </SettingsContext.Provider>
  );
};

export function useSettings(): SettingsContextType {
  const context = useContext(SettingsContext);
  if (!context) {
    throw new Error("useSettings must be used within a SettingsProvider");
  }
  return context;
}
