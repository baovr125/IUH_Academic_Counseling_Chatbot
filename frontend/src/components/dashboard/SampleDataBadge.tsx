import React from "react";
import { FlaskConical } from "lucide-react";
import { FcBadge } from "../flashcards/ui";

/** Nhãn báo ô này đang hiện dữ liệu mẫu (chưa có nguồn dữ liệu thật), để không bị nhầm là số liệu của người dùng. */
export const SampleDataBadge: React.FC<{ className?: string }> = ({ className = "" }) => (
  <FcBadge tone="amber" icon={<FlaskConical size={12} aria-hidden="true" />} className={`shrink-0 !px-2 !py-0 text-xs ${className}`} data-testid="sample-badge">
    Dữ liệu mẫu
  </FcBadge>
);
