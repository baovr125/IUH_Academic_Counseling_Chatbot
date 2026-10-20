import React from "react";

export type FcPageWidth = "md" | "lg" | "xl";

const WIDTH: Record<FcPageWidth, string> = {
  md: "max-w-4xl",
  lg: "max-w-5xl",
  xl: "max-w-6xl"
};

interface FcPageProps extends React.HTMLAttributes<HTMLDivElement> {
  /** md = màn học tập trung (4xl), lg = mặc định (5xl), xl = màn nhiều cột (6xl). */
  width?: FcPageWidth;
}

/**
 * Khung trang chung của Flashcard: nền và khoảng đệm giống DashboardPage
 * (slate-50/60, tối là slate-950), nội dung căn giữa trong một độ rộng cố định.
 */
export const FcPage: React.FC<FcPageProps> = ({ width = "lg", className = "", children, ...rest }) => (
  <div className="min-h-full w-full bg-slate-50/60 transition-colors dark:bg-slate-950" {...rest}>
    <div className={`mx-auto flex w-full flex-col p-4 sm:p-6 lg:p-8 ${WIDTH[width]} ${className}`}>{children}</div>
  </div>
);
