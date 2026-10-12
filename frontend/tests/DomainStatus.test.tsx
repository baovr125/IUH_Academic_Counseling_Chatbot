import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { DomainStatus, formatSeconds } from "../src/components/translation/DomainStatus";
import type { TranslationWarning } from "../src/types";

function renderStatus(props: Partial<React.ComponentProps<typeof DomainStatus>> = {}) {
  render(<DomainStatus warnings={[]} waiting={false} {...props} />);
}

describe("DomainStatus", () => {
  it("không còn huy hiệu lĩnh vực: kết quả nhận diện hiện trong ô chọn lĩnh vực", () => {
    renderStatus();
    expect(screen.queryByTestId("domain-badge")).not.toBeInTheDocument();
    expect(screen.queryByTestId("domain-pin")).not.toBeInTheDocument();
  });

  it("hiện banner cảnh báo về bản dịch với mức độ tương ứng", () => {
    const warnings: TranslationWarning[] = [
      { code: "FALLBACK_NLLB", severity: "warning", message: "Chế độ chuyên ngành tạm gián đoạn, đã dịch thông thường." },
      { code: "BOOM", severity: "error", message: "Lỗi." },
    ];
    renderStatus({ warnings });
    expect(screen.getByTestId("domain-warning-FALLBACK_NLLB")).toHaveAttribute("role", "alert");
    expect(screen.getByTestId("domain-warning-FALLBACK_NLLB")).toHaveTextContent("đã dịch thông thường");
    expect(screen.getByTestId("domain-warning-BOOM")).toBeInTheDocument();
  });

  it("không hiện DOMAIN_AMBIGUOUS thành banner (đã có khung chọn lĩnh vực)", () => {
    renderStatus({ warnings: [{ code: "DOMAIN_AMBIGUOUS", severity: "warning", message: "Chọn lĩnh vực" }] });
    expect(screen.queryByTestId("domain-warning-DOMAIN_AMBIGUOUS")).not.toBeInTheDocument();
  });

  it("chỉ báo chờ ngắn gọn, số giây viết theo kiểu Việt", () => {
    renderStatus({ waiting: true });
    expect(screen.getByTestId("domain-waiting")).toHaveTextContent("Sẽ dịch sau 1,5 giây ngừng gõ (Ctrl+Enter để dịch ngay).");
    expect(formatSeconds(1500)).toBe("1,5");
    expect(formatSeconds(2000)).toBe("2");
  });

  it("không hiện gì khi không chờ và không có cảnh báo", () => {
    renderStatus();
    expect(screen.queryByTestId("domain-waiting")).not.toBeInTheDocument();
    expect(screen.getByTestId("domain-status")).toBeEmptyDOMElement();
  });
});
