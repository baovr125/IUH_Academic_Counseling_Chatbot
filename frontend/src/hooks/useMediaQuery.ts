import { useEffect, useState } from "react";

/**
 * Theo dõi một media query. Môi trường không có `matchMedia` (jsdom trong test, SSR) trả về `fallback`
 * để giao diện vẫn render ở bố cục máy tính.
 */
export function useMediaQuery(query: string, fallback = true): boolean {
  const supported = typeof window !== "undefined" && typeof window.matchMedia === "function";
  const [matches, setMatches] = useState<boolean>(() => (supported ? window.matchMedia(query).matches : fallback));

  useEffect(() => {
    if (!supported) return;
    const mql = window.matchMedia(query);
    const onChange = () => setMatches(mql.matches);
    onChange();
    mql.addEventListener("change", onChange);
    return () => mql.removeEventListener("change", onChange);
  }, [query, supported]);

  return matches;
}
