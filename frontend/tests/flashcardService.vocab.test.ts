import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  cloneCatalogDeck,
  commitGeneratedVocabulary,
  extractErrorMessage,
  fetchCatalogDecks,
  fetchReviewStreak,
  fetchStudyQueue,
  fetchStudyStats,
  generateVocabulary,
  generateVocabularyFromImage
} from "../src/services/flashcardService";

type FetchMock = ReturnType<typeof vi.fn>;

function mockFetch(status: number, body: unknown): FetchMock {
  const fn = vi.fn(async () => ({ ok: status >= 200 && status < 300, status, json: async () => body }) as Response);
  vi.stubGlobal("fetch", fn);
  return fn;
}

const lastCall = (fn: FetchMock) => {
  const [url, init] = fn.mock.calls[fn.mock.calls.length - 1] as [string, RequestInit];
  return { url, init, body: init?.body && typeof init.body === "string" ? JSON.parse(init.body) : init?.body };
};

beforeEach(() => {
  sessionStorage.setItem("iuh_portal_ai_token", "tok");
  localStorage.setItem("iuh_portal_ai_token", "tok");
});
afterEach(() => vi.unstubAllGlobals());

describe("extractErrorMessage", () => {
  it("prefers string detail", () => expect(extractErrorMessage({ detail: "Không có quyền" }, "x")).toBe("Không có quyền"));
  it("reads FastAPI validation arrays and strips the 'Value error' prefix", () =>
    expect(extractErrorMessage({ detail: [{ msg: "Value error, Vui lòng nhập chủ đề" }] }, "x")).toBe("Vui lòng nhập chủ đề"));
  it("reads the {error:{message}} envelope", () =>
    expect(extractErrorMessage({ ok: false, error: { code: "QUOTA_EXCEEDED", message: "Hết lượt" } }, "x")).toBe("Hết lượt"));
  it("falls back for unknown shapes", () => {
    expect(extractErrorMessage(null, "dự phòng")).toBe("dự phòng");
    expect(extractErrorMessage({ detail: [] }, "dự phòng")).toBe("dự phòng");
    expect(extractErrorMessage({}, "dự phòng")).toBe("dự phòng");
  });
});

describe("generateVocabulary", () => {
  it("sends only the fields relevant to the mode", async () => {
    const fetchMock = mockFetch(200, { ok: true, data: { items: [] } });
    await generateVocabulary({ mode: "topic", topic: "Env", text: "ignored", level: "B1", count: 20, purpose: "ielts", instruction: "", excludeTerms: ["a"], deckId: "d1" });
    const { url, init, body } = lastCall(fetchMock);
    expect(url).toContain("/api/v1/flashcards/vocabulary/generate");
    expect(init.method).toBe("POST");
    expect((init.headers as Record<string, string>).Authorization).toBe("Bearer tok");
    expect(body).toMatchObject({ mode: "topic", topic: "Env", level: "B1", count: 20, purpose: "ielts", exclude_terms: ["a"], deck_id: "d1" });
    expect(body.text).toBeUndefined();
    expect(body.instruction).toBeUndefined();
  });

  it("sends text for text mode and not the topic", async () => {
    const fetchMock = mockFetch(200, { ok: true, data: {} });
    await generateVocabulary({ mode: "text", topic: "ignored", text: "A passage of text here.", level: "A2", count: 10 });
    const { body } = lastCall(fetchMock);
    expect(body.text).toBe("A passage of text here.");
    expect(body.topic).toBeUndefined();
    expect(body.exclude_terms).toEqual([]);
  });

  it("maps the backend error envelope to code + message", async () => {
    mockFetch(429, { ok: false, error: { code: "QUOTA_EXCEEDED", message: "Bạn đã dùng hết lượt" } });
    const res = await generateVocabulary({ mode: "topic", topic: "x1", level: "B1", count: 5 });
    expect(res).toEqual({ ok: false, error: { message: "Bạn đã dùng hết lượt", code: "QUOTA_EXCEEDED" } });
  });

  it("maps FastAPI 422 validation errors to a readable message", async () => {
    mockFetch(422, { detail: [{ loc: ["body"], msg: "Value error, Đoạn văn quá ngắn" }] });
    const res = await generateVocabulary({ mode: "text", text: "short", level: "B1", count: 5 });
    expect(res.ok).toBe(false);
    if (!res.ok) expect(res.error.message).toBe("Đoạn văn quá ngắn");
  });

  it("reports network failures without throwing", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => { throw new Error("Failed to fetch"); }));
    const res = await generateVocabulary({ mode: "topic", topic: "x1", level: "B1", count: 5 });
    expect(res.ok).toBe(false);
  });
});

describe("generateVocabularyFromImage", () => {
  it("posts multipart form data with the options", async () => {
    const fetchMock = mockFetch(200, { ok: true, data: { items: [] } });
    const file = new File([new Uint8Array([1, 2, 3])], "pic.png", { type: "image/png" });
    await generateVocabularyFromImage(file, { level: "A2", count: 12, purpose: "toeic", instruction: "signs", deckId: "d9" });
    const { url, init } = lastCall(fetchMock);
    expect(url).toContain("/vocabulary/generate-image");
    const form = init.body as FormData;
    expect(form.get("level")).toBe("A2");
    expect(form.get("count")).toBe("12");
    expect(form.get("purpose")).toBe("toeic");
    expect(form.get("deck_id")).toBe("d9");
    expect((form.get("file") as File).name).toBe("pic.png");
    expect((init.headers as Record<string, string>)["Content-Type"]).toBeUndefined(); // để trình duyệt tự đặt boundary
  });

  it("surfaces the 415/413 errors from the backend", async () => {
    mockFetch(415, { ok: false, error: { code: "UNSUPPORTED_IMAGE", message: "Chỉ hỗ trợ ảnh JPG, PNG hoặc WEBP." } });
    const res = await generateVocabularyFromImage(new File(["x"], "a.png"), { level: "B1", count: 5 });
    expect(res).toEqual({ ok: false, error: { message: "Chỉ hỗ trợ ảnh JPG, PNG hoặc WEBP.", code: "UNSUPPORTED_IMAGE" } });
  });

  it("explains timeouts", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => { throw Object.assign(new Error("t"), { name: "TimeoutError" }); }));
    const res = await generateVocabularyFromImage(new File(["x"], "a.png"), { level: "B1", count: 5 });
    expect(res.ok).toBe(false);
    if (!res.ok) expect(res.error.message).toMatch(/quá lâu/);
  });
});

describe("commitGeneratedVocabulary", () => {
  it("maps camelCase params to the snake_case API contract", async () => {
    const fetchMock = mockFetch(200, { ok: true, data: { inserted: 1 } });
    await commitGeneratedVocabulary({
      clientRequestId: "req-12345678",
      deck: { title: "T", description: "D", langCode: "en" },
      cards: [{ term: "a", definition: "b", partOfSpeech: "noun", phonetic: "", example: "An a.", exampleTranslation: "Một a.", level: "B1" }],
      source: { mode: "topic", topic: "Env", level: "B1" }
    });
    const { url, body } = lastCall(fetchMock);
    expect(url).toContain("/decks/from-generated");
    expect(body.client_request_id).toBe("req-12345678");
    expect(body.deck).toEqual({ title: "T", description: "D", lang_code: "en" });
    expect(body.deck_id).toBeUndefined();
    expect(body.cards[0]).toEqual({ term: "a", definition: "b", part_of_speech: "noun", example: "An a.", example_translation: "Một a.", level: "B1" });
    expect(body.cards[0].phonetic).toBeUndefined(); // chuỗi rỗng không được gửi
  });

  it("adds to an existing deck without sending deck metadata", async () => {
    const fetchMock = mockFetch(200, { ok: true, data: {} });
    await commitGeneratedVocabulary({ clientRequestId: "req-12345678", deckId: "d1", cards: [{ term: "a", definition: "b" }], source: { mode: "image" } });
    const { body } = lastCall(fetchMock);
    expect(body.deck_id).toBe("d1");
    expect(body.deck).toBeUndefined();
  });
});

describe("study + catalog + streak endpoints", () => {
  it("builds the study-queue query string", async () => {
    const fetchMock = mockFetch(200, { ok: true, data: [] });
    await fetchStudyQueue("d1");
    expect(lastCall(fetchMock).url).toContain("/decks/d1/study-queue?limit=50&new_limit=20");
    await fetchStudyQueue("d1", { limit: 100, newLimit: 0, weakOnly: true });
    expect(lastCall(fetchMock).url).toContain("limit=100&new_limit=0&weak_only=true");
  });

  it("fetches study stats and streak", async () => {
    const fetchMock = mockFetch(200, { ok: true, data: { total: 3 } });
    expect((await fetchStudyStats("d1")).ok).toBe(true);
    expect(lastCall(fetchMock).url).toContain("/decks/d1/study-stats");
    await fetchReviewStreak(30);
    expect(lastCall(fetchMock).url).toContain("/stats/streak?days=30");
  });

  it("encodes catalog filters", async () => {
    const fetchMock = mockFetch(200, { ok: true, data: [] });
    await fetchCatalogDecks({ category: "food", level: "A2", q: "nhà hàng & bar" });
    const { url } = lastCall(fetchMock);
    expect(url).toContain("category=food");
    expect(url).toContain("level=A2");
    expect(url).toContain("q=nh%C3%A0+h%C3%A0ng+%26+bar");
    await fetchCatalogDecks();
    expect(lastCall(fetchMock).url.endsWith("/catalog/decks")).toBe(true);
  });

  it("clones a catalog deck with POST", async () => {
    const fetchMock = mockFetch(200, { ok: true, data: { created: true } });
    await cloneCatalogDeck("abc");
    const { url, init } = lastCall(fetchMock);
    expect(url).toContain("/catalog/decks/abc/clone");
    expect(init.method).toBe("POST");
  });
});
