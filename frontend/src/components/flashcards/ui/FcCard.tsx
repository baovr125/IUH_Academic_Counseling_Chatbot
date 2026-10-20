import React from "react";

type CardTag = "div" | "section" | "article" | "li";
type CardPadding = "none" | "sm" | "md" | "lg";

const PADDING: Record<CardPadding, string> = {
  none: "",
  sm: "p-4",
  md: "p-5 sm:p-6",
  lg: "p-6 sm:p-8"
};

interface FcCardProps extends React.HTMLAttributes<HTMLElement> {
  as?: CardTag;
  padding?: CardPadding;
  /** Thẻ bấm được: nhấc nhẹ khi rê chuột, viền xanh khi hover. */
  interactive?: boolean;
}

/** Thẻ nội dung chuẩn, cùng kiểu với thẻ ở Dashboard: rounded-3xl, viền mảnh, nền trắng / slate-800 khi tối. */
export const FcCard = React.forwardRef<HTMLElement, FcCardProps>(function FcCard(
  { as = "div", padding = "md", interactive = false, className = "", children, ...rest },
  ref
) {
  const Tag = as as React.ElementType;
  return (
    <Tag
      ref={ref}
      className={
        "rounded-3xl border border-slate-200/80 bg-white shadow-sm transition-all duration-200 dark:border-slate-800 dark:bg-slate-800 " +
        (interactive
          ? "hover:-translate-y-0.5 hover:border-blue-300 hover:shadow-md dark:hover:border-blue-500/60 "
          : "") +
        `${PADDING[padding]} ${className}`
      }
      {...rest}
    >
      {children}
    </Tag>
  );
});
