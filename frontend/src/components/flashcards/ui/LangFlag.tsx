import React from "react";
import { Globe } from "lucide-react";

/**
 * Cờ vẽ bằng SVG cho 10 ngôn ngữ của Flashcard.
 * Lý do không dùng emoji cờ: Windows không có font cờ nên Chrome/Edge hiển thị thành chữ ("GB", "DE"...).
 * Hình vẽ đơn giản hóa (không có quốc huy) nhưng đủ nhận diện ở cỡ 20–64 px.
 */

export type LangFlagSize = "xs" | "sm" | "md" | "lg" | "xl";

const SIZE_CLASS: Record<LangFlagSize, string> = {
  xs: "h-3.5 w-[18px]",
  sm: "h-[18px] w-6",
  md: "h-6 w-8",
  lg: "h-9 w-12",
  xl: "h-12 w-16"
};

/** Đa giác ngôi sao 5 cánh (đỉnh hướng lên khi rotate = 0). */
function starPoints(cx: number, cy: number, outer: number, rotateDeg = 0): string {
  const inner = outer * 0.382;
  const pts: string[] = [];
  for (let i = 0; i < 10; i++) {
    const r = i % 2 === 0 ? outer : inner;
    const a = ((-90 + rotateDeg + i * 36) * Math.PI) / 180;
    pts.push(`${(cx + r * Math.cos(a)).toFixed(1)},${(cy + r * Math.sin(a)).toFixed(1)}`);
  }
  return pts.join(" ");
}

/** Ba vạch quẻ của quốc kỳ Hàn Quốc, xoay quanh tâm của chính nó. */
const Trigram: React.FC<{ cx: number; cy: number; angle: number }> = ({ cx, cy, angle }) => (
  <g transform={`rotate(${angle} ${cx} ${cy})`} fill="#000">
    {[-26, 0, 26].map((dy) => (
      <rect key={dy} x={cx - 56} y={cy + dy - 8} width={112} height={16} />
    ))}
  </g>
);

const FLAGS: Record<string, React.ReactNode> = {
  en: (
    <>
      <rect width="640" height="480" fill="#012169" />
      <path d="M0 0 640 480M640 0 0 480" stroke="#fff" strokeWidth="96" />
      <path d="M0 0 640 480M640 0 0 480" stroke="#C8102E" strokeWidth="32" />
      <path d="M320 0V480M0 240H640" stroke="#fff" strokeWidth="160" />
      <path d="M320 0V480M0 240H640" stroke="#C8102E" strokeWidth="96" />
    </>
  ),
  de: (
    <>
      <rect width="640" height="160" fill="#000" />
      <rect y="160" width="640" height="160" fill="#DD0000" />
      <rect y="320" width="640" height="160" fill="#FFCE00" />
    </>
  ),
  zh: (
    <>
      <rect width="640" height="480" fill="#DE2910" />
      <polygon points={starPoints(160, 160, 96)} fill="#FFDE00" />
      <polygon points={starPoints(320, 64, 32, 20)} fill="#FFDE00" />
      <polygon points={starPoints(384, 128, 32, 45)} fill="#FFDE00" />
      <polygon points={starPoints(384, 224, 32, 0)} fill="#FFDE00" />
      <polygon points={starPoints(320, 288, 32, 20)} fill="#FFDE00" />
    </>
  ),
  ja: (
    <>
      <rect width="640" height="480" fill="#fff" />
      <circle cx="320" cy="240" r="144" fill="#BC002D" />
    </>
  ),
  ko: (
    <>
      <rect width="640" height="480" fill="#fff" />
      <path d="M200 240a120 120 0 0 1 240 0z" fill="#CD2E3A" />
      <path d="M440 240a120 120 0 0 1-240 0z" fill="#0047A0" />
      <circle cx="260" cy="240" r="60" fill="#CD2E3A" />
      <circle cx="380" cy="240" r="60" fill="#0047A0" />
      <Trigram cx={130} cy={104} angle={-52.6} />
      <Trigram cx={510} cy={104} angle={52.6} />
      <Trigram cx={130} cy={376} angle={52.6} />
      <Trigram cx={510} cy={376} angle={-52.6} />
    </>
  ),
  fr: (
    <>
      <rect width="214" height="480" fill="#002395" />
      <rect x="213" width="214" height="480" fill="#fff" />
      <rect x="426" width="214" height="480" fill="#ED2939" />
    </>
  ),
  es: (
    <>
      <rect width="640" height="480" fill="#AA151B" />
      <rect y="120" width="640" height="240" fill="#F1BF00" />
    </>
  ),
  ru: (
    <>
      <rect width="640" height="160" fill="#fff" />
      <rect y="160" width="640" height="160" fill="#0039A6" />
      <rect y="320" width="640" height="160" fill="#D52B1E" />
    </>
  ),
  th: (
    <>
      <rect width="640" height="480" fill="#A51931" />
      <rect y="80" width="640" height="320" fill="#F4F5F8" />
      <rect y="160" width="640" height="160" fill="#2D2A4A" />
    </>
  ),
  vi: (
    <>
      <rect width="640" height="480" fill="#DA251D" />
      <polygon points={starPoints(320, 252, 150)} fill="#FFFF00" />
    </>
  )
};

interface LangFlagProps {
  /** Mã ngôn ngữ (en, de, ...). Mã lạ hiện biểu tượng quả địa cầu. */
  lang?: string | null;
  size?: LangFlagSize;
  /** Có tên thì cờ là hình có nhãn; mặc định cờ chỉ trang trí vì tên ngôn ngữ luôn ghi bên cạnh. */
  title?: string;
  className?: string;
}

export const LangFlag: React.FC<LangFlagProps> = ({ lang, size = "md", title, className = "" }) => {
  const art = lang ? FLAGS[lang] : undefined;
  const a11y = title ? { role: "img", "aria-label": title } : { "aria-hidden": true };
  const frame = `inline-block shrink-0 overflow-hidden rounded-[5px] shadow-sm ring-1 ring-slate-900/10 dark:ring-white/20 ${SIZE_CLASS[size]} ${className}`;

  if (!art) {
    return (
      <span
        data-testid="lang-flag-fallback"
        className={`${frame} flex items-center justify-center bg-slate-100 text-slate-600 dark:bg-slate-700 dark:text-slate-300`}
        {...a11y}
      >
        <Globe className="h-3/4 w-3/4" />
      </span>
    );
  }

  return (
    <svg
      data-testid={`lang-flag-${lang}`}
      viewBox="0 0 640 480"
      preserveAspectRatio="xMidYMid slice"
      className={frame}
      {...a11y}
    >
      {art}
    </svg>
  );
};
