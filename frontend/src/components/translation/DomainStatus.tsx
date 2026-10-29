import React from "react";
import { AlertTriangle, Clock, Info, XCircle } from "lucide-react";
import type { TranslationWarning, WarningSeverity } from "../../types";
import { DOMAIN_DEBOUNCE_MS } from "./domainMode";

export interface DomainStatusProps {
  warnings: TranslationWarning[];
  /** Đang chờ người dùng ngừng gõ trước khi gửi request (chế độ chuyên ngành). */
  waiting: boolean;
}

/**
 * Chỉ báo chờ + banner cảnh báo về chất lượng/tính đầy đủ của bản dịch.
 * Kết quả nhận diện lĩnh vực hiện trong ô chọn lĩnh vực (giống nhãn ngôn ngữ), không ở đây;
 * trường hợp từ thuộc nhiều lĩnh vực hiện thành khung chọn trong vùng bản dịch.
 */
const SEVERITY_STYLE: Record<WarningSeverity, { box: string; icon: string }> = {
  info: { box: "bg-brand-50 text-brand-700 border-brand-100 dark:bg-brand-950/40 dark:text-brand-300 dark:border-brand-900/50", icon: "text-brand-500 dark:text-brand-400" },
  warning: { box: "bg-amber-50 text-amber-800 border-amber-200 dark:bg-amber-950/40 dark:text-amber-300 dark:border-amber-800", icon: "text-amber-500 dark:text-amber-400" },
  error: { box: "bg-red-50 text-red-700 border-red-200 dark:bg-red-950/40 dark:text-red-300 dark:border-red-800", icon: "text-red-500 dark:text-red-400" },
};

/** Cảnh báo đã có giao diện riêng (khung chọn lĩnh vực) nên không hiện thành banner. */
const HANDLED_ELSEWHERE = new Set(["DOMAIN_AMBIGUOUS"]);

function SeverityIcon({ severity }: { severity: WarningSeverity }) {
  const cls = `${SEVERITY_STYLE[severity].icon} shrink-0`;
  if (severity === "error") return <XCircle className={cls} size={16} />;
  if (severity === "warning") return <AlertTriangle className={cls} size={16} />;
  return <Info className={cls} size={16} />;
}

export function formatSeconds(ms: number): string {
  return (ms / 1000).toLocaleString("vi-VN", { maximumFractionDigits: 1 });
}

export const DomainStatus: React.FC<DomainStatusProps> = ({ warnings, waiting }) => (
  <div data-testid="domain-status">
    {waiting && (
      <div
        data-testid="domain-waiting"
        role="status"
        className="bg-slate-50 text-slate-500 px-6 py-2 text-xs border-b border-slate-100 flex items-center gap-2 dark:bg-slate-900/50 dark:text-slate-400 dark:border-slate-700"
      >
        <Clock size={14} className="shrink-0" />
        <span>Sẽ dịch sau {formatSeconds(DOMAIN_DEBOUNCE_MS)} giây ngừng gõ (Ctrl+Enter để dịch ngay).</span>
      </div>
    )}

    {warnings
      .filter((w) => !HANDLED_ELSEWHERE.has(w.code))
      .map((w) => {
        const style = SEVERITY_STYLE[w.severity] ?? SEVERITY_STYLE.info;
        return (
          <div
            key={w.code}
            data-testid={`domain-warning-${w.code}`}
            role={w.severity === "info" ? "status" : "alert"}
            className={`${style.box} px-6 py-3 text-sm border-b flex items-center gap-2 animate-in slide-in-from-top-2 fade-in`}
          >
            <SeverityIcon severity={w.severity} />
            <span>{w.message}</span>
          </div>
        );
      })}
  </div>
);
