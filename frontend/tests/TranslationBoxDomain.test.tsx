import React, { useState } from "react";
import { act, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const streamMock = vi.fn();

vi.mock("../src/services/translationService", () => ({
  streamTranslation: (...args: unknown[]) => streamMock(...args),
  extractFlashcard: vi.fn(),
}));
vi.mock("../src/components/translation/FloatingMenu", () => ({ FloatingMenu: () => null }));
vi.mock("../src/components/translation/SaveFlashcardModal", () => ({ SaveFlashcardModal: () => null }));
vi.mock("../src/components/translation/WordAnalysisPopup", () => ({ WordAnalysisPopup: () => null }));
vi.mock("../src/hooks/useWordAnalysis", () => ({
  useWordAnalysis: () => ({ analyze: vi.fn(), state: null, close: vi.fn() }),
}));

import { TranslationBox } from "../src/components/translation/TranslationBox";

const IT = "Công nghệ Thông tin (IT)";

function Harness({ initial = "" }: { initial?: string }) {
  const [text, setText] = useState(initial);
  return (
    <TranslationBox
      sourceLang="en"
      targetLang="vi"
      sourceText={text}
      setSourceLang={() => {}}
      setTargetLang={() => {}}
      setSourceText={setText}
      swapLanguages={() => {}}
      targetLangMeta={{ flag: "🇻🇳", label: "Tiếng Việt", defaultTitle: "Bản dịch" }}
    />
  );
}

async function chooseDomain(label: RegExp | string) {
  fireEvent.click(screen.getByText(/Chọn lĩnh vực dịch thuật/));
  fireEvent.click(screen.getByText(label));
}

/** Gọi các callback của lần streamTranslation gần nhất (thứ tự tham số khớp translationService). */
function lastCallbacks() {
  const args = streamMock.mock.calls[streamMock.mock.calls.length - 1];
  return {
    req: args[0],
    onChunk: args[1] as (t: string) => void,
    onComplete: args[4] as () => void,
    onDomain: args[8] as (d: unknown) => void,
    onWarnings: args[9] as (w: unknown[]) => void,
  };
}

beforeEach(() => {
  vi.useFakeTimers();
  streamMock.mockReset();
  streamMock.mockResolvedValue(undefined);
});

afterEach(() => {
  vi.useRealTimers();
});

describe("TranslationBox - chế độ chuyên ngành", () => {
  it("dịch thông thường vẫn gửi sau 300 ms", () => {
    render(<Harness />);
    fireEvent.change(screen.getByPlaceholderText(/Nhập văn bản/), { target: { value: "Hello" } });
    act(() => { vi.advanceTimersByTime(299); });
    expect(streamMock).not.toHaveBeenCalled();
    act(() => { vi.advanceTimersByTime(2); });
    expect(streamMock).toHaveBeenCalledTimes(1);
  });

  it("chế độ auto chỉ gửi sau 1,5 s ngừng gõ và hiện chỉ báo đang chờ", async () => {
    render(<Harness />);
    await chooseDomain(/Tự động nhận diện/);
    fireEvent.change(screen.getByPlaceholderText(/Nhập văn bản/), { target: { value: "A memory leak" } });

    expect(screen.getByTestId("domain-waiting")).toBeInTheDocument();
    act(() => { vi.advanceTimersByTime(1499); });
    expect(streamMock).not.toHaveBeenCalled();
    act(() => { vi.advanceTimersByTime(2); });
    expect(streamMock).toHaveBeenCalledTimes(1);
    expect(streamMock.mock.calls[0][0]).toMatchObject({ domain: "auto", sourceText: "A memory leak" });
    expect(screen.queryByTestId("domain-waiting")).not.toBeInTheDocument();
  });

  it("gõ tiếp trong lúc chờ thì làm lại bộ đếm và chỉ gửi một request", async () => {
    render(<Harness />);
    await chooseDomain(IT);
    const box = screen.getByPlaceholderText(/Nhập văn bản/);
    fireEvent.change(box, { target: { value: "A" } });
    act(() => { vi.advanceTimersByTime(1000); });
    fireEvent.change(box, { target: { value: "A memory" } });
    act(() => { vi.advanceTimersByTime(1000); });
    fireEvent.change(box, { target: { value: "A memory leak" } });
    act(() => { vi.advanceTimersByTime(1000); });
    expect(streamMock).not.toHaveBeenCalled();
    act(() => { vi.advanceTimersByTime(600); });
    expect(streamMock).toHaveBeenCalledTimes(1);
    expect(streamMock.mock.calls[0][0]).toMatchObject({ domain: IT, sourceText: "A memory leak" });
  });

  it("Ctrl+Enter dịch ngay, không chờ debounce", async () => {
    render(<Harness />);
    await chooseDomain(/Tự động nhận diện/);
    const box = screen.getByPlaceholderText(/Nhập văn bản/);
    fireEvent.change(box, { target: { value: "A memory leak" } });
    fireEvent.keyDown(box, { key: "Enter", ctrlKey: true });
    expect(streamMock).toHaveBeenCalledTimes(1);
    expect(screen.queryByTestId("domain-waiting")).not.toBeInTheDocument();
    // Bộ đếm cũ đã bị hủy: hết 1,5 s cũng không gửi lần hai.
    act(() => { vi.advanceTimersByTime(2000); });
    expect(streamMock).toHaveBeenCalledTimes(1);
  });

  it("lĩnh vực tự nhận diện hiện trong ô chọn như nhãn ngôn ngữ, không có banner", async () => {
    render(<Harness initial="A memory leak causes crashes" />);
    await chooseDomain(/Tự động nhận diện/);
    act(() => { vi.advanceTimersByTime(1500); });
    expect(streamMock).toHaveBeenCalledTimes(1);

    const { onDomain, onChunk } = lastCallbacks();
    act(() => {
      onDomain({ status: "detected", domain: IT, confidence: 0.97, method: "lexical_llm", matched_terms: ["memory leak"], applied_terms: ["memory leak"], translator: "llm:groq:m" });
      onChunk("Rò rỉ bộ nhớ");
    });
    expect(screen.getByText(`✨ Tự động nhận diện (${IT})`)).toBeInTheDocument();
    expect(screen.queryByTestId("domain-badge")).not.toBeInTheDocument();
    expect(screen.getByTestId("domain-status")).toBeEmptyDOMElement();
  });

  it("nhãn không nhấp nháy khi gõ tiếp; kết quả unknown thì bỏ tên lĩnh vực", async () => {
    render(<Harness initial="A memory leak causes crashes" />);
    await chooseDomain(/Tự động nhận diện/);
    act(() => { vi.advanceTimersByTime(1500); });
    act(() => {
      lastCallbacks().onDomain({ status: "detected", domain: IT, confidence: 0.97, method: "llm" });
    });

    // Gõ tiếp: request mới bắt đầu nhưng nhãn cũ vẫn giữ cho tới khi có kết quả mới.
    fireEvent.change(screen.getByPlaceholderText(/Nhập văn bản/), { target: { value: "We walked along the beach" } });
    act(() => { vi.advanceTimersByTime(1500); });
    expect(streamMock).toHaveBeenCalledTimes(2);
    expect(screen.getByText(`✨ Tự động nhận diện (${IT})`)).toBeInTheDocument();

    act(() => {
      lastCallbacks().onDomain({ status: "unknown", confidence: 0.9, method: "llm", reason: "llm_unknown" });
    });
    expect(screen.getByText("✨ Tự động nhận diện")).toBeInTheDocument();
    expect(screen.getByTestId("domain-status")).toBeEmptyDOMElement();
  });

  it("chỉ hiện banner khi bản dịch bị ảnh hưởng (fallback)", async () => {
    render(<Harness initial="A memory leak causes crashes" />);
    await chooseDomain(/Tự động nhận diện/);
    act(() => { vi.advanceTimersByTime(1500); });
    act(() => {
      lastCallbacks().onWarnings([{ code: "FALLBACK_NLLB", severity: "warning", message: "Chế độ chuyên ngành tạm gián đoạn, đã dịch thông thường." }]);
    });
    expect(screen.getByTestId("domain-warning-FALLBACK_NLLB")).toHaveTextContent("đã dịch thông thường");
  });

  it("đổi lĩnh vực thủ công thì xóa nhãn đã nhận diện", async () => {
    render(<Harness initial="A memory leak causes crashes" />);
    await chooseDomain(/Tự động nhận diện/);
    act(() => { vi.advanceTimersByTime(1500); });
    act(() => { lastCallbacks().onDomain({ status: "detected", domain: IT, confidence: 0.97, method: "llm" }); });
    fireEvent.click(screen.getByText(`✨ Tự động nhận diện (${IT})`));
    fireEvent.click(screen.getByText("Marketing"));
    expect(screen.queryByText(/Tự động nhận diện \(/)).not.toBeInTheDocument();
  });

  it("từ nhiều lĩnh vực: chọn một ứng viên sẽ dịch lại với lĩnh vực đó", async () => {
    render(<Harness initial="stock" />);
    await chooseDomain(/Tự động nhận diện/);
    act(() => { vi.advanceTimersByTime(1500); });
    const { onDomain } = lastCallbacks();
    act(() => {
      onDomain({
        status: "ambiguous", confidence: 0, method: "exact",
        candidates: [
          { domain: "Kinh tế / Tài chính", term: "stock", translation: "cổ phiếu" },
          { domain: "Y khoa / Sức khỏe", term: "stock", translation: "kho thuốc" },
        ],
      });
    });
    // Khung chọn nằm trong vùng bản dịch, cùng kiểu với khung dừng ngôn ngữ.
    expect(screen.getByTestId("domain-candidates")).toHaveTextContent("Từ này có nghĩa ở nhiều lĩnh vực. Hãy chọn một lĩnh vực.");
    expect(screen.queryByText(/Bản dịch sẽ xuất hiện/)).not.toBeInTheDocument();
    fireEvent.click(screen.getAllByTestId("domain-candidate")[1]);
    act(() => { vi.advanceTimersByTime(1); });
    expect(streamMock).toHaveBeenCalledTimes(2);
    expect(streamMock.mock.calls[1][0]).toMatchObject({ domain: "Y khoa / Sức khỏe" });
  });

  it("xóa hết văn bản thì xóa cảnh báo, huy hiệu và chỉ báo chờ", async () => {
    render(<Harness initial="A memory leak" />);
    await chooseDomain(/Tự động nhận diện/);
    expect(screen.getByTestId("domain-waiting")).toBeInTheDocument();
    fireEvent.change(screen.getByPlaceholderText(/Nhập văn bản/), { target: { value: "" } });
    expect(screen.queryByTestId("domain-waiting")).not.toBeInTheDocument();
    act(() => { vi.advanceTimersByTime(3000); });
    expect(streamMock).not.toHaveBeenCalled();
  });
});

/**
 * Mô phỏng một phiên gõ trên component thật: 60 ký tự, mỗi ký tự cách nhau 150 ms,
 * dừng 900 ms sau ký tự thứ 20 và dừng 2 s sau ký tự thứ 40, rồi gõ xong.
 * Đếm số request thật sự được gửi để so debounce 300 ms (dịch thông thường) với 1,5 s (chế độ domain).
 */
async function typingSession(domainLabel: RegExp | string | null): Promise<number> {
  const { unmount } = render(<Harness />);
  if (domainLabel) await chooseDomain(domainLabel);
  const box = screen.getByPlaceholderText(/Nhập văn bản/);
  let value = "";
  for (let i = 1; i <= 60; i++) {
    value += "a";
    fireEvent.change(box, { target: { value } });
    act(() => { vi.advanceTimersByTime(150); });
    if (i === 20) act(() => { vi.advanceTimersByTime(900); });
    if (i === 40) act(() => { vi.advanceTimersByTime(2000); });
  }
  act(() => { vi.advanceTimersByTime(3000); });
  const calls = streamMock.mock.calls.length;
  unmount();
  return calls;
}

describe("Số request mỗi phiên gõ (mô phỏng trên component thật)", () => {
  it("chế độ domain gửi ít request hơn dịch thông thường trong cùng một phiên gõ", async () => {
    const normal = await typingSession(null);
    streamMock.mockClear();
    const auto = await typingSession(/Tự động nhận diện/);
    // Thông thường: dừng 1050 ms và 2150 ms đều > 300 ms, cộng lần cuối => 3 request.
    expect(normal).toBe(3);
    // Domain: dừng 1050 ms < 1,5 s nên không gửi; chỉ còn lần dừng 2150 ms và lần cuối => 2 request.
    expect(auto).toBe(2);
    expect(auto).toBeLessThan(normal);
  });
});
