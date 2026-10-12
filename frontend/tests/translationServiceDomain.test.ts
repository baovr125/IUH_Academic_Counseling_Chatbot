import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { streamTranslation, translateText } from "../src/services/translationService";

const fetchMock = vi.fn();

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}

function sseResponse(events: unknown[]): Response {
  const encoder = new TextEncoder();
  const stream = new ReadableStream({
    start(controller) {
      for (const event of events) {
        controller.enqueue(encoder.encode(`data: ${JSON.stringify(event)}\r\n\r\n`));
      }
      controller.close();
    },
  });
  return new Response(stream, { status: 200, headers: { "Content-Type": "text/event-stream" } });
}

beforeEach(() => {
  fetchMock.mockReset();
  vi.stubGlobal("fetch", fetchMock);
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("streamTranslation - chuyên ngành", () => {
  it("chuyển event domain và warnings có cấu trúc cho UI", async () => {
    const domain = { status: "detected", domain: "Marketing", confidence: 0.95, method: "llm", matched_terms: [], applied_terms: [] };
    const warnings = [{ code: "FALLBACK_NLLB", severity: "warning", message: "Chế độ chuyên ngành tạm gián đoạn, đã dịch thông thường." }];
    fetchMock.mockResolvedValue(
      sseResponse([
        { event: "detection", detection: { status: "detected", resolved_source_lang: "en", confidence: 0.99, margin: 0.9, engine: "fasttext" } },
        { resolved_source_lang: "en" },
        { event: "domain", domain },
        { text: "Xin chào" },
        { warnings },
      ])
    );
    const onChunk = vi.fn();
    const onDomain = vi.fn();
    const onWarnings = vi.fn();
    const onWarning = vi.fn();

    await streamTranslation(
      { sourceLang: "auto", targetLang: "vi", sourceText: "Hello", domain: "auto" },
      onChunk, vi.fn(), onWarning, vi.fn(), undefined, undefined, undefined, onDomain, onWarnings
    );

    expect(JSON.parse(fetchMock.mock.calls[0][1].body).domain).toBe("auto");
    expect(onDomain).toHaveBeenCalledWith(expect.objectContaining({ status: "detected", domain: "Marketing" }));
    expect(onChunk).toHaveBeenCalledWith("Xin chào");
    expect(onWarnings).toHaveBeenCalledWith(warnings);
    expect(onWarning).not.toHaveBeenCalled();
  });

  it("vẫn hỗ trợ cảnh báo chuỗi cũ", async () => {
    fetchMock.mockResolvedValue(sseResponse([{ warning: "Cảnh báo cũ" }, { text: "x" }]));
    const onWarning = vi.fn();
    await streamTranslation({ sourceLang: "en", targetLang: "vi", sourceText: "x" }, vi.fn(), vi.fn(), onWarning, vi.fn());
    expect(onWarning).toHaveBeenCalledWith("Cảnh báo cũ");
  });

  it("không gọi onWarnings với mảng rỗng", async () => {
    fetchMock.mockResolvedValue(sseResponse([{ warnings: [] }, { text: "x" }]));
    const onWarnings = vi.fn();
    await streamTranslation(
      { sourceLang: "en", targetLang: "vi", sourceText: "x" },
      vi.fn(), vi.fn(), vi.fn(), vi.fn(), undefined, undefined, undefined, undefined, onWarnings
    );
    expect(onWarnings).not.toHaveBeenCalled();
  });

  it("event reset xóa phần đã stream trước đó", async () => {
    fetchMock.mockResolvedValue(sseResponse([{ text: "bản sao chép" }, { event: "reset" }, { text: "Bản dịch NLLB" }]));
    const order: string[] = [];
    await streamTranslation(
      { sourceLang: "en", targetLang: "vi", sourceText: "x", domain: "auto" },
      (t) => order.push(`chunk:${t}`), vi.fn(), vi.fn(), vi.fn(), undefined, undefined, undefined, undefined, undefined,
      () => order.push("reset")
    );
    expect(order).toEqual(["chunk:bản sao chép", "reset", "chunk:Bản dịch NLLB"]);
  });

  it("báo lỗi dịch (không có bản dịch nào) qua onError", async () => {
    fetchMock.mockResolvedValue(
      sseResponse([{ error: "Dịch vụ dịch thuật tạm thời gián đoạn. Không thể dịch.", code: "TRANSLATION_UNAVAILABLE" }])
    );
    const onError = vi.fn();
    await streamTranslation({ sourceLang: "en", targetLang: "vi", sourceText: "x", domain: "auto" }, vi.fn(), onError, vi.fn(), vi.fn());
    expect(onError).toHaveBeenCalledWith("Dịch vụ dịch thuật tạm thời gián đoạn. Không thể dịch.", "TRANSLATION_UNAVAILABLE");
  });
});

describe("translateText - chuyên ngành", () => {
  it("trả domain và warnings của /text", async () => {
    const domain = { status: "selected", domain: "Luật / Pháp lý", confidence: 1, method: "manual" };
    const warnings = [{ code: "FALLBACK_NLLB", severity: "warning", message: "Đã dịch bằng NLLB." }];
    fetchMock.mockResolvedValue(
      jsonResponse(200, { ok: true, data: { translated_text: "Xin chào", resolved_source_lang: "en", domain, warnings } })
    );
    const res = await translateText({ sourceLang: "en", targetLang: "vi", sourceText: "Hello", domain: "Luật / Pháp lý" });
    expect(res.ok).toBe(true);
    if (res.ok) {
      expect(res.data.domainDetails).toEqual(domain);
      expect(res.data.warnings).toEqual(warnings);
    }
  });

  it("chế độ thông thường không có domain/warnings thì trả mảng rỗng", async () => {
    fetchMock.mockResolvedValue(jsonResponse(200, { ok: true, data: { translated_text: "Xin chào", resolved_source_lang: "en" } }));
    const res = await translateText({ sourceLang: "en", targetLang: "vi", sourceText: "Hello" });
    expect(res.ok).toBe(true);
    if (res.ok) {
      expect(res.data.domainDetails).toBeUndefined();
      expect(res.data.warnings).toEqual([]);
    }
  });
});
