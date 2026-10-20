import { queryClient } from "../queryClient";
import { addCardToDeck, LANG_CONFIG, normalizeLangCode } from "./deckStorage";
import { saveCardFromTranslation, type BackendCardItem, type SaveFromTranslationParams } from "./flashcardService";

/** Mã lỗi nghiệp vụ của backend (xem flashcard_service/app/utils/errors.py). */
const ERROR_MESSAGES: Record<string, string> = {
  LANG_REQUIRED: "Chưa xác định được ngôn ngữ của từ này. Hãy chọn ngôn ngữ rồi lưu lại.",
  LANG_UNSUPPORTED: "Ngôn ngữ này chưa được hỗ trợ trong Flashcard.",
  LANG_MISMATCH: "Sổ thẻ đã chọn thuộc ngôn ngữ khác. Hãy chọn sổ cùng ngôn ngữ hoặc dùng sổ mặc định.",
  DECK_LANG_UNCONFIRMED: "Sổ thẻ này chưa xác nhận ngôn ngữ. Hãy xác nhận ngôn ngữ cho sổ trong trang Flashcard trước.",
  MIGRATION_REQUIRED: "Hệ thống chưa được cập nhật cơ sở dữ liệu (migration 005). Hãy liên hệ quản trị viên.",
};

export type SaveOutcome =
  | { kind: "saved"; created: boolean; updated: boolean; deckId: string; deckTitle: string; card: BackendCardItem; langCode: string }
  | { kind: "duplicate"; langCode: string; deckId?: string; deckTitle?: string; existing: Pick<BackendCardItem, "id" | "term" | "definition"> }
  | { kind: "pending"; langCode: string; deckTitle: string }
  | { kind: "error"; code?: string; message: string };

/** Làm mới mọi màn hình Flashcard đang hiển thị dữ liệu bị ảnh hưởng. */
export function invalidateFlashcardQueries(deckId?: string) {
  void queryClient.invalidateQueries({ queryKey: ["flashcard_decks"] });
  void queryClient.invalidateQueries({ queryKey: ["flashcard_language_summary"] });
  void queryClient.invalidateQueries({ queryKey: ["flashcard_language_cards"] });
  void queryClient.invalidateQueries({ queryKey: deckId ? ["flashcard_cards", deckId] : ["flashcard_cards"] });
}

export function newRequestId(): string {
  const c: any = globalThis.crypto;
  if (c?.randomUUID) return `fc-${c.randomUUID()}`;
  return `fc-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
}

/**
 * Lưu một từ vào đúng bộ sưu tập ngôn ngữ (backend là nguồn sự thật).
 * - Thành công / trùng / lỗi nghiệp vụ: phản ánh đúng kết quả, KHÔNG ghi LocalStorage.
 * - Chỉ khi KHÔNG kết nối được máy chủ mới lưu tạm vào LocalStorage (đánh dấu pendingSync).
 */
export async function saveWordToCollection(params: SaveFromTranslationParams, userId?: string): Promise<SaveOutcome> {
  const lang = normalizeLangCode(params.sourceLang);
  if (!lang || lang === "vi") {
    return { kind: "error", code: "LANG_REQUIRED", message: ERROR_MESSAGES.LANG_REQUIRED };
  }

  const res = await saveCardFromTranslation({ ...params, sourceLang: lang });

  if (res.ok) {
    invalidateFlashcardQueries(res.data.deck?.id);
    return {
      kind: "saved",
      created: !!res.data.created,
      updated: !!res.data.updated,
      deckId: res.data.deck?.id,
      deckTitle: res.data.deck?.title ?? LANG_CONFIG[lang].defaultTitle,
      card: res.data.card,
      langCode: lang,
    };
  }

  const { error } = res;
  if (error.code === "DUPLICATE_CARD") {
    const card = error.data?.card;
    return {
      kind: "duplicate",
      langCode: lang,
      deckId: error.data?.deck?.id,
      deckTitle: error.data?.deck?.title,
      existing: { id: card?.id ?? "", term: card?.term ?? params.term, definition: card?.definition ?? "" },
    };
  }

  if (error.network) {
    try {
      const { deck } = addCardToDeck(lang, params.term, params.translation, params.example, params.partOfSpeech, undefined, userId, {
        pendingSync: true,
      });
      return { kind: "pending", langCode: lang, deckTitle: deck.title };
    } catch {
      return { kind: "error", message: "Không kết nối được máy chủ và không thể lưu tạm trên thiết bị." };
    }
  }

  return { kind: "error", code: error.code, message: (error.code && ERROR_MESSAGES[error.code]) || error.message };
}
