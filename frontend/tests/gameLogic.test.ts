import { describe, expect, it } from "vitest";
import {
  BUILDER_MAX_HINTS_PER_WORD, builderClearWrong, builderHint, builderNext, builderPlace, builderSkip, builderUndo, builderWord,
  initBuilder, initMatch, initSpeed, matchClearWrong, matchResults, matchSelect, placedText, scramble, shuffle, speedAnswer, speedMultiplier,
  speedNext, speedTimeUp, SPEED_CHALLENGE_LIVES, SPEED_RELAX_QUESTIONS, type GameCard, type BuilderState
} from "../src/components/flashcards/games/gameLogic";

/** Bộ sinh số ngẫu nhiên có hạt giống để kết quả lặp lại được. */
const seeded = (seed = 1) => () => {
  seed = (seed * 1664525 + 1013904223) % 4294967296;
  return seed / 4294967296;
};

const card = (id: string, term = `word${id}`, extra: Partial<GameCard> = {}): GameCard => ({
  id, term, definition: `nghĩa ${id}`, lang_code: "en", is_due: true, choices: [`nghĩa ${id}`, "x1", "x2", "x3"], ...extra
});
const cards = (n: number) => Array.from({ length: n }, (_, i) => card(String(i + 1)));

describe("shuffle", () => {
  it("giữ nguyên phần tử, không sửa mảng gốc", () => {
    const src = [1, 2, 3, 4, 5, 6];
    const out = shuffle(src, seeded(7));
    expect([...out].sort()).toEqual(src);
    expect(src).toEqual([1, 2, 3, 4, 5, 6]);
  });
});

describe("Ghép cặp", () => {
  const start = () => initMatch(cards(4), seeded(3));

  it("ghép đúng: cặp được ghi nhận, lựa chọn được xóa", () => {
    let s = matchSelect(start(), "term", "1");
    expect(s.selectedTerm).toBe("1");
    s = matchSelect(s, "def", "1");
    expect(s.matched).toEqual(["1"]);
    expect(s.selectedTerm).toBeNull();
    expect(s.selectedDef).toBeNull();
    expect(s.mistakes).toBe(0);
  });

  it("ghép sai: tăng lỗi, ghi vào thẻ của TỪ, hiện lastWrong và chặn chạm tiếp tới khi xóa", () => {
    let s = matchSelect(matchSelect(start(), "term", "1"), "def", "2");
    expect(s.mistakes).toBe(1);
    expect(s.attempts).toEqual({ "1": 1 });
    expect(s.lastWrong).toEqual({ term: "1", def: "2" });
    expect(matchSelect(s, "term", "3")).toBe(s); // đang hiện lỗi
    s = matchClearWrong(s);
    expect(s.lastWrong).toBeNull();
    expect(s.selectedTerm).toBeNull();
  });

  it("chạm lại ô đã chọn thì bỏ chọn; không chọn được ô đã ghép", () => {
    let s = matchSelect(start(), "term", "1");
    s = matchSelect(s, "term", "1");
    expect(s.selectedTerm).toBeNull();
    s = matchSelect(matchSelect(s, "term", "2"), "def", "2");
    expect(matchSelect(s, "term", "2")).toBe(s);
  });

  it("chọn nghĩa trước rồi mới chọn từ vẫn ghép được", () => {
    const s = matchSelect(matchSelect(start(), "def", "3"), "term", "3");
    expect(s.matched).toEqual(["3"]);
  });

  it("hoàn thành khi ghép hết; kết quả từng thẻ kèm số lần sai", () => {
    let s = start();
    s = matchClearWrong(matchSelect(matchSelect(s, "term", "1"), "def", "4"));
    for (const id of ["1", "2", "3", "4"]) s = matchSelect(matchSelect(s, "term", id), "def", id);
    expect(s.done).toBe(true);
    const byId = Object.fromEntries(matchResults(s).map((r) => [r.card_id, r]));
    expect(byId["1"]).toEqual({ card_id: "1", correct: true, attempts: 1, hints: 0 });
    expect(byId["2"].attempts).toBe(0);
    expect(matchSelect(s, "term", "1")).toBe(s);
  });

  it("chưa xong thì thẻ chưa ghép là sai", () => {
    const s = matchSelect(matchSelect(start(), "term", "1"), "def", "1");
    expect(matchResults(s).filter((r) => r.correct)).toHaveLength(1);
  });

  it("hai cột chứa đúng cùng tập thẻ", () => {
    const s = start();
    expect([...s.defOrder].sort()).toEqual(["1", "2", "3", "4"]);
    expect(s.cards.map((c) => c.id).sort()).toEqual(["1", "2", "3", "4"]);
  });
});

describe("Đua 60 giây", () => {
  const answerAll = (s: ReturnType<typeof initSpeed>, plan: boolean[]) => {
    for (const ok of plan) {
      if (s.finished) break;
      const card = s.queue[s.index];
      s = speedNext(speedAnswer(s, ok ? card.definition : "sai"), seeded(2));
    }
    return s;
  };

  it("Thư giãn: đúng 10 câu, không có mạng", () => {
    const s = initSpeed(cards(5), "relax", seeded(1));
    expect(s.queue).toHaveLength(SPEED_RELAX_QUESTIONS);
    expect(s.lives).toBeNull();
    const done = answerAll(s, Array(20).fill(false));
    expect(done.finished).toBe(true);
    expect(done.items).toHaveLength(SPEED_RELAX_QUESTIONS);
  });

  it("Thử thách: 3 mạng, hết mạng thì kết thúc", () => {
    const s = initSpeed(cards(5), "challenge", seeded(1));
    expect(s.lives).toBe(SPEED_CHALLENGE_LIVES);
    const done = answerAll(s, [true, false, true, false, false, true]);
    expect(done.finished).toBe(true);
    expect(done.mistakes).toBe(3);
    expect(done.items).toHaveLength(5); // câu thứ 6 không được chơi
  });

  it("combo và điểm giống backend: ×1 cho 3 câu đầu rồi ×2; sai thì về 0", () => {
    expect([0, 2, 3, 5, 6, 12, 40].map(speedMultiplier)).toEqual([1, 1, 2, 2, 3, 5, 5]);
    const done = answerAll(initSpeed(cards(5), "challenge", seeded(1)), [true, true, true, true, false, true, true]);
    expect(done.score).toBe(10 * 3 + 20 + 10 * 2);
    expect(done.bestCombo).toBe(4);
  });

  it("so sánh đáp án không phân biệt hoa thường/khoảng trắng; mỗi câu chỉ trả lời một lần", () => {
    let s = initSpeed(cards(4), "relax", seeded(1));
    const def = s.queue[0].definition;
    s = speedAnswer(s, `  ${def.toUpperCase()} `);
    expect(s.answered?.correct).toBe(true);
    expect(speedAnswer(s, "khác")).toBe(s);
  });

  it("câu hỏi lặp lại khi sổ ít thẻ nhưng mỗi câu có đủ 4 đáp án", () => {
    const s = initSpeed(cards(4), "relax", seeded(1));
    expect(s.queue.every((c) => c.choices?.length === 4)).toBe(true);
    expect(s.choices).toHaveLength(4);
  });

  it("hết giờ: kết thúc, không tính câu đang dở", () => {
    let s = initSpeed(cards(5), "challenge", seeded(1));
    s = speedNext(speedAnswer(s, s.queue[0].definition), seeded(1));
    const end = speedTimeUp(s);
    expect(end.finished).toBe(true);
    expect(end.items).toHaveLength(1);
    expect(speedNext(end)).toBe(end);
  });

  it("không sang câu kế khi chưa trả lời (chống bấm Enter hai lần)", () => {
    const s = initSpeed(cards(5), "relax", seeded(1));
    expect(speedNext(s)).toBe(s);
  });

  it("mỗi lượt sai ghi attempts=1, đúng ghi 0", () => {
    const done = answerAll(initSpeed(cards(5), "relax", seeded(1)), [true, false]);
    expect(done.items.map((i) => [i.correct, i.attempts])).toEqual([[true, 0], [false, 1]]);
  });
});

describe("Xếp chữ", () => {
  const start = (words = ["house", "tree"]) => initBuilder(words.map((w, i) => card(String(i + 1), w)), seeded(5));
  const typeWord = (s: BuilderState, word = builderWord(s)) => {
    for (const ch of Array.from(word)) {
      const tile = s.tiles.find((t) => !s.placed.includes(t.id) && t.ch.toLowerCase() === ch.toLowerCase())!;
      s = builderPlace(s, tile.id);
    }
    return s;
  };

  it("xáo chữ luôn khác thứ tự gốc (nếu có thể) và giữ đủ chữ cái", () => {
    for (let seed = 1; seed < 40; seed++) {
      const tiles = scramble("house", seeded(seed));
      expect(tiles.map((t) => t.ch).join("")).not.toBe("house");
      expect(tiles.map((t) => t.ch).sort().join("")).toBe("ehosu");
    }
    expect(scramble("aaa", seeded(1)).map((t) => t.ch).join("")).toBe("aaa"); // không thể khác
    expect(scramble("Straße", seeded(2)).map((t) => t.ch).sort()).toEqual(Array.from("Straße").sort());
    expect(scramble("привет", seeded(2))).toHaveLength(6);
  });

  it("xếp đúng thì giải xong, không phân biệt hoa thường", () => {
    let s = typeWord(start());
    expect(s.solved).toBe(true);
    expect(s.wrong).toBe(false);
    expect(placedText(s).toLowerCase()).toBe(builderWord(s).toLowerCase());
  });

  it("xếp sai: đánh dấu wrong, tăng lỗi, chặn thao tác tới khi xóa", () => {
    let s = start(["ab"]);
    const [a, b] = ["a", "b"].map((ch) => s.tiles.find((t) => t.ch === ch)!.id);
    s = builderPlace(builderPlace(s, b), a); // "ba" sai
    expect(s.wrong).toBe(true);
    expect(s.attempts).toBe(1);
    expect(builderPlace(s, a)).toBe(s);
    s = builderClearWrong(s);
    expect(s.placed).toEqual([]);
    expect(s.wrong).toBe(false);
  });

  it("hoàn tác bỏ chữ cuối; không đặt một ô hai lần", () => {
    let s = start();
    const id = s.tiles[0].id;
    s = builderPlace(s, id);
    expect(builderPlace(s, id)).toBe(s);
    expect(builderUndo(s).placed).toEqual([]);
  });

  it("gợi ý đặt đúng chữ kế tiếp, bỏ phần sai, tối đa 3 lần/từ", () => {
    let s = start(["house"]);
    const wrongTile = s.tiles.find((t) => t.ch !== "h")!;
    s = builderPlace(s, wrongTile.id);
    s = builderHint(s);
    expect(placedText(s)).toBe("h");
    expect(s.hints).toBe(1);
    s = builderHint(builderHint(s));
    expect(placedText(s)).toBe("hou");
    expect(builderHint(s)).toBe(s); // hết 3 lần
    expect(BUILDER_MAX_HINTS_PER_WORD).toBe(3);
  });

  it("giải xong rồi sang từ kế: ghi kết quả kèm số gợi ý/lỗi", () => {
    let s = start();
    s = builderHint(s);
    s = typeWord({ ...s, placed: [] } as BuilderState); // đặt lại và tự xếp đúng
    expect(s.solved).toBe(true);
    s = builderNext(s, seeded(1));
    expect(s.index).toBe(1);
    expect(s.items).toEqual([{ card_id: s.words[0].id, correct: true, attempts: 0, hints: 1 }]);
    expect(s.placed).toEqual([]);
  });

  it("chưa giải thì không sang từ kế bằng builderNext; bỏ qua ghi sai", () => {
    let s = start();
    expect(builderNext(s)).toBe(s);
    s = builderSkip(s, seeded(1));
    expect(s.items[0]).toMatchObject({ correct: false, attempts: 0 });
    expect(s.index).toBe(1);
  });

  it("từ cuối cùng: kết thúc ván", () => {
    let s = start(["ab"]);
    s = builderNext(typeWord(s), seeded(1));
    expect(s.finished).toBe(true);
    expect(s.items).toHaveLength(1);
    expect(builderPlace(s, 0)).toBe(s);
  });

  it("từ có dấu / chữ Cyrillic / ß xếp được", () => {
    for (const word of ["été", "niño", "привет", "Straße"]) {
      const s = typeWord(initBuilder([card("1", word)], seeded(3)));
      expect(s.solved).toBe(true);
    }
  });
});
