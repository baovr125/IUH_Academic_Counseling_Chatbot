import React from "react";

interface FcSkeletonProps {
  /** Kích thước và hình dạng, ví dụ "h-4 w-24" hoặc "h-40 rounded-3xl". */
  className?: string;
}

/** Khối giữ chỗ khi đang tải, thay cho vòng xoay để giao diện không nhảy khi dữ liệu về. */
export const FcSkeleton: React.FC<FcSkeletonProps> = ({ className = "h-4 w-24" }) => (
  <span aria-hidden="true" className={`block animate-pulse rounded-xl bg-slate-200 motion-reduce:animate-none dark:bg-slate-700 ${className}`} />
);

/** Vùng tải có thông báo cho trình đọc màn hình (role=status), chứa các FcSkeleton bên trong. */
export const FcLoading: React.FC<{ label?: string; className?: string; children: React.ReactNode }> = ({
  label = "Đang tải…",
  className = "",
  children
}) => (
  <div role="status" aria-live="polite" className={className}>
    <span className="sr-only">{label}</span>
    {children}
  </div>
);
