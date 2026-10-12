import type { ReactNode } from "react";
import { AlertCircle, CheckCircle2, Info } from "lucide-react";

type Variant = "error" | "success" | "info";

const styles: Record<Variant, string> = {
  error: "border-red-200 bg-red-50 text-red-900 dark:border-red-900 dark:bg-red-950/50 dark:text-red-100",
  success: "border-green-200 bg-green-50 text-green-900 dark:border-green-900 dark:bg-green-950/50 dark:text-green-100",
  info: "border-blue-200 bg-blue-50 text-blue-900 dark:border-blue-900 dark:bg-blue-950/50 dark:text-blue-100",
};

/** Thông báo trạng thái: lỗi dùng role="alert" (đọc ngay), còn lại dùng role="status". */
export function Alert({ variant, children }: { variant: Variant; children: ReactNode }) {
  const Icon = variant === "error" ? AlertCircle : variant === "success" ? CheckCircle2 : Info;
  return (
    <div
      role={variant === "error" ? "alert" : "status"}
      className={`flex items-start gap-2 rounded-xl border p-3 text-sm font-medium ${styles[variant]}`}
    >
      <Icon size={16} className="mt-0.5 flex-shrink-0" aria-hidden="true" />
      <div>{children}</div>
    </div>
  );
}
