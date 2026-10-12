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

describe("translateText", () => {
  it("surfaces structured language errors instead of a fake translation", async () => {
    const detection = { status: "unsupported", detected_language: "it", confidence: 0.95, margin: 0.7, engine: "fusion" };
    fetchMock.mockResolvedValue(
      jsonResponse(400, {
        ok: false,
        detail: "Ngôn ngữ nhận diện được (tiếng Ý) chưa được hỗ trợ.",
        error: { code: "LANG_UNSUPPORTED", message: "Ngôn ngữ nhận diện được (tiếng Ý) chưa được hỗ trợ.", detection },
      })
    );

    const result = await translateText({ sourceLang: "auto", targetLang: "vi", sourceText: "La intelligenza artificiale" });

    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.error.code).toBe("LANG_UNSUPPORTED");
      expect(result.error.detection?.detected_language).toBe("it");
      expect(result.error.message).toContain("chưa được hỗ trợ");
    }
  });

  it("does not fall back to a mock translation when the network fails", async () => {
    fetchMock.mockRejectedValue(new TypeError("Failed to fetch"));

    const result = await translateText({ sourceLang: "en", targetLang: "vi", sourceText: "Hello world" });

    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.error.message).toMatch(/kết nối/i);
  });

  it("does not turn an HTTP 500 into a successful result", async () => {
    fetchMock.mockResolvedValue(jsonResponse(500, { detail: "boom" }));
    const result = await translateText({ sourceLang: "en", targetLang: "vi", sourceText: "Hello world" });
    expect(result.ok).toBe(false);
  });

  it("returns the resolved language reported by the server", async () => {
    fetchMock.mockResolvedValue(
      jsonResponse(200, {
        ok: true,
        data: { translated_text: "Xin chào", resolved_source_lang: "en", detection: { status: "detected", engine: "fusion" } },
      })
    );
    const result = await translateText({ sourceLang: "auto", targetLang: "vi", sourceText: "Hello world" });
    expect(result.ok).toBe(true);
    if (result.ok) expect(result.data.detectedSourceLang).toBe("en");
  });

  it("sends source_lang_hint only in auto mode", async () => {
    fetchMock.mockResolvedValue(jsonResponse(200, { ok: true, data: { translated_text: "x", resolved_source_lang: "en" } }));

    await translateText({ sourceLang: "auto", targetLang: "vi", sourceText: "Hello", sourceLangHint: "en" });
    expect(JSON.parse(fetchMock.mock.calls[0][1].body).source_lang_hint).toBe("en");

    await translateText({ sourceLang: "en", targetLang: "vi", sourceText: "Hello", sourceLangHint: "en" });
    expect(JSON.parse(fetchMock.mock.calls[1][1].body)).not.toHaveProperty("source_lang_hint");
  });
});

describe("streamTranslation", () => {
  it("forwards the language error code and detection details", async () => {
    const detection = { status: "uncertain", confidence: 0.4, margin: 0.05, engine: "fusion", candidates: [{ language: "en", confidence: 0.4 }] };
    fetchMock.mockResolvedValue(
      sseResponse([
        { event: "detection", detection },
        { error: "Chưa đủ thông tin để xác định chắc chắn ngôn ngữ.", code: "LANG_UNCERTAIN" },
      ])
    );
    const onChunk = vi.fn();
    const onError = vi.fn();
    const onDetection = vi.fn();
    const onDetectedLanguage = vi.fn();

    await streamTranslation(
      { sourceLang: "auto", targetLang: "vi", sourceText: "ok" },
      onChunk, onError, vi.fn(), vi.fn(), undefined, onDetectedLanguage, onDetection
    );

    expect(onDetection).toHaveBeenCalledWith(expect.objectContaining({ status: "uncertain" }));
    expect(onDetectedLanguage).not.toHaveBeenCalled();
    expect(onError).toHaveBeenCalledWith("Chưa đủ thông tin để xác định chắc chắn ngôn ngữ.", "LANG_UNCERTAIN");
    expect(onChunk).not.toHaveBeenCalled();
  });

  it("reports the detected language and streams text on success", async () => {
    fetchMock.mockResolvedValue(
      sseResponse([
        { event: "detection", detection: { status: "detected", resolved_source_lang: "vi", confidence: 0.99, margin: 0.9, engine: "fasttext" } },
        { resolved_source_lang: "vi" },
        { text: "Hello" },
      ])
    );
    const onChunk = vi.fn();
    const onDetectedLanguage = vi.fn();

    await streamTranslation(
      { sourceLang: "auto", targetLang: "en", sourceText: "Xin chào" },
      onChunk, vi.fn(), vi.fn(), vi.fn(), undefined, onDetectedLanguage
    );

    expect(onDetectedLanguage).toHaveBeenCalledWith("vi", expect.anything());
    expect(onChunk).toHaveBeenCalledWith("Hello");
  });

  it("includes the hint in the request body only for auto mode", async () => {
    fetchMock.mockImplementation(() => Promise.resolve(sseResponse([{ text: "x" }])));

    await streamTranslation({ sourceLang: "auto", targetLang: "vi", sourceText: "Hello", sourceLangHint: "en" },
      vi.fn(), vi.fn(), vi.fn(), vi.fn());
    expect(JSON.parse(fetchMock.mock.calls[0][1].body).source_lang_hint).toBe("en");

    await streamTranslation({ sourceLang: "de", targetLang: "vi", sourceText: "Hallo", sourceLangHint: "en" },
      vi.fn(), vi.fn(), vi.fn(), vi.fn());
    expect(JSON.parse(fetchMock.mock.calls[1][1].body)).not.toHaveProperty("source_lang_hint");
  });
});
