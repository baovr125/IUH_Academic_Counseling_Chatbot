import React from "react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { act, renderHook } from "@testing-library/react";
import { useMediaQuery } from "../src/hooks/useMediaQuery";

describe("useMediaQuery", () => {
  const original = window.matchMedia;
  afterEach(() => {
    window.matchMedia = original;
  });

  it("môi trường không có matchMedia (jsdom) trả về giá trị dự phòng", () => {
    // @ts-expect-error mô phỏng trình duyệt/jsdom không có matchMedia
    window.matchMedia = undefined;
    expect(renderHook(() => useMediaQuery("(min-width: 1024px)")).result.current).toBe(true);
    expect(renderHook(() => useMediaQuery("(min-width: 1024px)", false)).result.current).toBe(false);
  });

  it("theo dõi thay đổi của media query", () => {
    let listener: () => void = () => {};
    const mql = {
      matches: false,
      addEventListener: (_: string, cb: () => void) => (listener = cb),
      removeEventListener: vi.fn(),
    };
    window.matchMedia = vi.fn(() => mql) as unknown as typeof window.matchMedia;
    const { result } = renderHook(() => useMediaQuery("(min-width: 1024px)"));
    expect(result.current).toBe(false);
    mql.matches = true;
    act(() => listener());
    expect(result.current).toBe(true);
  });
});
