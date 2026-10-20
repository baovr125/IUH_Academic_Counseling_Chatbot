import React from "react";
import { act, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import indexHtml from "../index.html?raw";
import { applyAppTheme, SettingsProvider, useSettings } from "../src/context/SettingsContext";

/** Lấy nguyên văn script chống nháy sáng trong index.html để chạy thử. */
function bootstrapScript(): string {
  const m = indexHtml.match(/<script>([\s\S]*?)<\/script>/);
  if (!m) throw new Error("index.html không còn script chống nháy sáng");
  return m[1];
}

type MqlListener = (e: { matches: boolean }) => void;
let prefersDark = false;
let listeners: MqlListener[] = [];

function stubMatchMedia() {
  window.matchMedia = ((query: string) => ({
    get matches() {
      return query.includes("dark") ? prefersDark : false;
    },
    media: query,
    addEventListener: (_: string, cb: MqlListener) => listeners.push(cb),
    removeEventListener: (_: string, cb: MqlListener) => {
      listeners = listeners.filter((l) => l !== cb);
    },
    addListener: () => {},
    removeListener: () => {},
    dispatchEvent: () => false,
    onchange: null
  })) as unknown as typeof window.matchMedia;
}

beforeEach(() => {
  prefersDark = false;
  listeners = [];
  stubMatchMedia();
  localStorage.clear();
  document.documentElement.className = "";
});
afterEach(() => {
  localStorage.clear();
  document.documentElement.className = "";
});

describe("script chống nháy sáng (index.html)", () => {
  const stored: Array<string | null> = [null, "light", "dark", "system", "rác"];

  it("cho kết quả giống applyAppTheme với mọi giá trị đã lưu × ưu tiên hệ thống", () => {
    const script = bootstrapScript();
    for (const value of stored) {
      for (const dark of [false, true]) {
        prefersDark = dark;
        localStorage.clear();
        if (value !== null) localStorage.setItem("app_theme", value);

        document.documentElement.className = "";
        new Function(script)();
        const fromScript = document.documentElement.classList.contains("dark");

        // SettingsProvider dùng "light" khi chưa lưu gì; giá trị lạ không bật dark.
        document.documentElement.className = "";
        applyAppTheme(((value ?? "light") as "light" | "dark" | "system"));
        const fromApp = document.documentElement.classList.contains("dark");

        expect(fromScript, `lưu=${value} hệ thống tối=${dark}`).toBe(fromApp);
      }
    }
  });

  it("không ném lỗi khi localStorage không dùng được", () => {
    const script = bootstrapScript();
    const spy = vi.spyOn(Storage.prototype, "getItem").mockImplementation(() => {
      throw new Error("blocked");
    });
    expect(() => new Function(script)()).not.toThrow();
    spy.mockRestore();
  });
});

function Probe() {
  const { theme, setTheme } = useSettings();
  return (
    <div>
      <span data-testid="theme">{theme}</span>
      <button onClick={() => setTheme("dark")}>dark</button>
      <button onClick={() => setTheme("light")}>light</button>
      <button onClick={() => setTheme("system")}>system</button>
    </div>
  );
}

const isDark = () => document.documentElement.classList.contains("dark");
const click = (name: string) => act(async () => { screen.getByRole("button", { name }).click(); });

describe("chuyển theme không cần tải lại", () => {
  it("Sáng → Tối → Sáng bật/gỡ class dark và lưu app_theme", async () => {
    render(<SettingsProvider><Probe /></SettingsProvider>);
    expect(isDark()).toBe(false);
    await click("dark");
    expect(isDark()).toBe(true);
    expect(localStorage.getItem("app_theme")).toBe("dark");
    await click("light");
    expect(isDark()).toBe(false);
    expect(localStorage.getItem("app_theme")).toBe("light");
  });

  it("Hệ thống: theo prefers-color-scheme lúc chọn và khi hệ điều hành đổi giữa chừng", async () => {
    prefersDark = true;
    render(<SettingsProvider><Probe /></SettingsProvider>);
    await click("system");
    expect(isDark()).toBe(true);

    prefersDark = false;
    await act(async () => { listeners.forEach((l) => l({ matches: false })); });
    expect(isDark()).toBe(false);

    prefersDark = true;
    await act(async () => { listeners.forEach((l) => l({ matches: true })); });
    expect(isDark()).toBe(true);
  });

  it("rời chế độ Hệ thống thì không còn bị hệ điều hành kéo đi", async () => {
    render(<SettingsProvider><Probe /></SettingsProvider>);
    await click("system");
    await click("light");
    prefersDark = true;
    await act(async () => { listeners.forEach((l) => l({ matches: true })); });
    expect(isDark()).toBe(false);
  });
});
