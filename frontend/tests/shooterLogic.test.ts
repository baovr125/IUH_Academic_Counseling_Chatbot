import { describe, expect, it } from "vitest";
import {
  ARENA, BUBBLE_RADIUS, BULLET_SPEED, CANNON, CHALLENGE_LIVES, LOOKAHEAD, MAX_FIELD, MISS_LINE, aimPoint, bubblePos, currentWord, fallSpeed,
  fireAt, fireAtBubble, initShooter, isShooterFinished, liveBubbles, pickMeaning, shooterResults, stepShooter, type ShooterState
} from "../src/components/flashcards/games/shooterLogic";
import type { GameCard } from "../src/components/flashcards/games/gameLogic";

const seeded = (seed = 1) => () => {
  seed = (seed * 1664525 + 1013904223) % 4294967296;
  return seed / 4294967296;
};

const card = (n: number): GameCard => ({ id: `c${n}`, term: `word${n}`, definition: `nghĩa ${n}`, lang_code: "en", is_due: true });
const cards = (n: number) => Array.from({ length: n }, (_, i) => card(i + 1));

/** Chạy mô phỏng tới khi điều kiện đúng (tối đa `seconds` giây ảo). */
function run(s: ShooterState, seconds: number, until?: (s: ShooterState) => boolean): ShooterState {
  for (let i = 0; i < seconds * 50 && !isShooterFinished(s); i++) {
    s = stepShooter(s, 0.02);
    if (until?.(s)) break;
  }
  return s;
}

const start = (n = 10, mode: "relax" | "challenge" = "relax", opts = {}) => initShooter(cards(n), mode, { rng: seeded(4), ...opts });
const active = (s: ShooterState) => s.bubbles.filter((b) => !b.popped && !b.revealed);
const answerId = (s: ShooterState) => currentWord(s)!.id;
const decoyId = (s: ShooterState) => liveBubbles(s).find((b) => b.id !== answerId(s))!.id;

/** Chờ bóng lọt vào sân (nếu đang trượt vào) rồi bắn nhắm thẳng vào bóng đó. */
function shootBubble(s: ShooterState, bubbleId: string): ShooterState {
  s = run(s, 8, (x) => liveBubbles(x).some((b) => b.id === bubbleId));
  s = fireAtBubble(s, bubbleId);
  return run(s, 3, (x) => x.bullet === null);
}

describe("sân chơi ban đầu", () => {
  it("bóng NHỎ: bán kính nhỏ hơn bản cũ (9,5) và không quá 7% bề rộng sân", () => {
    expect(BUBBLE_RADIUS).toBeLessThan(7);
    expect(BUBBLE_RADIUS * 2).toBeLessThanOrEqual(ARENA * 0.14);
    expect(start().bubbles.every((b) => b.radius === BUBBLE_RADIUS)).toBe(true);
  });

  it("có tối đa MAX_FIELD bóng, mỗi nghĩa một lần, mỗi bóng mang nghĩa của một từ trong danh sách", () => {
    const s = start(10);
    expect(s.bubbles).toHaveLength(MAX_FIELD);
    expect(new Set(s.bubbles.map((b) => b.id)).size).toBe(MAX_FIELD);
    expect(new Set(s.bubbles.map((b) => b.text.toLowerCase())).size).toBe(MAX_FIELD);
    const all = new Map(cards(10).map((c) => [c.id, c.definition]));
    expect(s.bubbles.every((b) => all.get(b.id) === b.text)).toBe(true);
  });

  it("sân chỉ có tối đa 5 bóng cùng lúc, kể cả khi danh sách rất dài", () => {
    expect(MAX_FIELD).toBe(5);
    let s = start(20);
    expect(s.bubbles).toHaveLength(5);
    for (let i = 0; i < 6; i++) {
      s = shootBubble(s, answerId(s));
      s = run(s, 1);
      expect(active(s).length).toBeLessThanOrEqual(5);
    }
  });

  it("các từ đầu tiên rơi lệch nhau: từ đang nạp thấp nhất, từ kế tiếp cao hơn (không cùng chạm đáy một lúc)", () => {
    const s = start(10);
    const ys = s.words.slice(0, LOOKAHEAD).map((w) => s.bubbles.find((b) => b.id === w.id)!.y);
    expect(ys[0]).toBeGreaterThan(ys[1]);
    expect(ys[1]).toBeGreaterThan(ys[2]);
    expect(new Set(ys).size).toBe(LOOKAHEAD);
  });

  it("danh sách ít từ thì sân ít bóng hơn (không bao giờ nhiều hơn số từ)", () => {
    expect(start(5).bubbles).toHaveLength(5);
    expect(start(3).bubbles).toHaveLength(3);
  });

  it("có sẵn bóng của từ đang nạp và các từ kế tiếp", () => {
    const s = start(10);
    for (let i = 0; i < LOOKAHEAD; i++) expect(s.bubbles.some((b) => b.id === s.words[i].id)).toBe(true);
  });

  it("các bóng nằm trong sân và không chồng nhau", () => {
    const s = start(10);
    const r = BUBBLE_RADIUS;
    for (const b of s.bubbles) {
      expect(b.baseX - r).toBeGreaterThanOrEqual(0);
      expect(b.baseX + r).toBeLessThanOrEqual(ARENA);
    }
    for (let i = 0; i < s.bubbles.length; i++)
      for (let j = i + 1; j < s.bubbles.length; j++) {
        const a = s.bubbles[i], b = s.bubbles[j];
        expect(Math.hypot(a.baseX - b.baseX, a.y - b.y)).toBeGreaterThanOrEqual(2 * r - 1e-9);
      }
  });

  it("độ khó: Thư giãn chậm và cố định; Thử thách nhanh dần nhưng có trần; Thử thách có 3 mạng", () => {
    expect(fallSpeed("relax", 0)).toBe(fallSpeed("relax", 30));
    expect(fallSpeed("challenge", 5)).toBeGreaterThan(fallSpeed("challenge", 0));
    expect(fallSpeed("challenge", 1000)).toBe(12);
    expect(start(10, "challenge").lives).toBe(CHALLENGE_LIVES);
    expect(start(10, "relax").lives).toBeNull();
  });

  it("pickMeaning ưu tiên từ đang nạp/kế tiếp chưa có trên sân, rồi mới tới bóng nhiễu", () => {
    const s = start(10);
    const without = { ...s, bubbles: s.bubbles.filter((b) => b.id !== s.words[1].id) };
    expect(pickMeaning(without)!.id).toBe(s.words[1].id);
    const decoyFill = { ...s, bubbles: s.bubbles.filter((b) => b.id !== s.words[9].id && s.words.slice(0, LOOKAHEAD).some((w) => w.id === b.id)) };
    const pick = pickMeaning(decoyFill)!;
    expect(decoyFill.bubbles.some((b) => b.id === pick.id)).toBe(false);
  });
});

describe("bắn đúng: chỉ thêm MỘT bóng mới, không sinh lại cả sân", () => {
  it("bóng trúng tan, đúng một bóng mới xuất hiện ở mép trên, các bóng còn lại giữ nguyên", () => {
    let s = start(10);
    const before = new Map(s.bubbles.map((b) => [b.id, b]));
    const target = answerId(s);
    s = shootBubble(s, target);

    const nowIds = new Set(s.bubbles.map((b) => b.id));
    const added = [...nowIds].filter((id) => !before.has(id));
    expect(added).toHaveLength(1); // đúng MỘT bóng mới
    expect(s.bubbles.find((b) => b.id === target)!.popped).toBe(true);
    // các bóng cũ khác vẫn còn, cùng cột ngang, cùng nghĩa
    for (const [id, old] of before) {
      if (id === target) continue;
      const cur = s.bubbles.find((b) => b.id === id)!;
      expect(cur).toBeTruthy();
      expect(cur.baseX).toBe(old.baseX);
      expect(cur.text).toBe(old.text);
      expect(cur.y).toBeGreaterThan(old.y - 1e-9); // chỉ rơi xuống, không bị sinh lại ở đầu sân
    }
    // bóng mới nằm ở mép trên và mang nghĩa của một từ trong danh sách
    const fresh = s.bubbles.find((b) => b.id === added[0])!;
    expect(fresh.y).toBeLessThan(BUBBLE_RADIUS + 12);
    expect(cards(10).some((c) => c.id === fresh.id && c.definition === fresh.text)).toBe(true);
    expect(s.events.some((e) => e.type === "spawn")).toBe(true);
  });

  it("số bóng bắn được luôn được giữ đủ sau khi trúng", () => {
    let s = start(10);
    for (let i = 0; i < 4; i++) {
      s = shootBubble(s, answerId(s));
      s = run(s, 1);
      expect(active(s)).toHaveLength(MAX_FIELD);
    }
  });

  it("súng nạp từ kế tiếp NGAY sau khi trúng (không có đợt/pha nghỉ), bắn tiếp được liền", () => {
    let s = start(10);
    const first = answerId(s);
    s = shootBubble(s, first);
    expect(s.wordIndex).toBe(1);
    expect(answerId(s)).not.toBe(first);
    const aim = aimPoint(s, answerId(s))!;
    expect(fireAt(s, aim.x, aim.y).bullet).not.toBeNull();
  });

  it("luôn có bóng cho từ đang nạp trên sân suốt cả ván", () => {
    let s = start(12, "relax");
    for (let i = 0; i < 12 && !isShooterFinished(s); i++) {
      s = run(s, 0.3);
      expect(active(s).some((b) => b.id === answerId(s))).toBe(true);
      s = shootBubble(s, answerId(s));
    }
  });

  it("điểm: bắn đúng ngay ×1, ×1, ×1, ×2…; combo giữ qua các từ", () => {
    let s = start(10);
    const gained: number[] = [];
    let prev = 0;
    for (let i = 0; i < 4; i++) {
      s = shootBubble(s, answerId(s));
      gained.push(s.score - prev);
      prev = s.score;
    }
    expect(gained).toEqual([10, 10, 10, 20]);
    expect(s.bestCombo).toBe(4);
  });

  it("ghi kết quả từng từ và kết thúc khi hết từ", () => {
    let s = start(5);
    for (let i = 0; i < 5; i++) s = shootBubble(s, answerId(s));
    expect(isShooterFinished(s)).toBe(true);
    expect(shooterResults(s)).toHaveLength(5);
    expect(shooterResults(s).every((r) => r.correct && r.attempts === 0)).toBe(true);
    expect(new Set(shooterResults(s).map((r) => r.card_id)).size).toBe(5);
    expect(s.events.some((e) => e.type === "end")).toBe(true);
    expect(stepShooter(s, 0.02)).toBe(s);
  });
});

describe("bắn sai và đạn", () => {
  it("bắn sai: không thêm/bớt bóng, mất combo, tăng lần sai, KHÔNG mất mạng, bóng rung", () => {
    let s = start(10, "challenge");
    s = shootBubble(s, answerId(s));
    s = run(s, 1); // đợi bóng vừa tan được dọn và bóng mới vào sân
    const ids = active(s).map((b) => b.id).sort();
    const wrong = decoyId(s);
    s = shootBubble(s, wrong);
    expect(s.attempts).toBe(1);
    expect(s.combo).toBe(0);
    expect(s.lives).toBe(CHALLENGE_LIVES);
    expect(active(s).map((b) => b.id).sort()).toEqual(ids);
    expect(s.bubbles.find((b) => b.id === wrong)!.shakeUntil).toBeGreaterThan(s.t);
    expect(s.events.some((e) => e.type === "wrong")).toBe(true);
    expect(s.events.some((e) => e.type === "spawn")).toBe(false);
  });

  it("đúng sau khi bắn sai: điểm bị trừ, combo không tăng, ghi số lần sai", () => {
    let s = start(10);
    s = shootBubble(s, decoyId(s));
    s = shootBubble(s, decoyId(s));
    s = shootBubble(s, answerId(s));
    expect(s.score).toBe(Math.max(5, 10 - 3 * 2));
    expect(s.combo).toBe(0);
    expect(s.items[0]).toMatchObject({ correct: true, attempts: 2 });
  });

  it("không bắn được khi đang có đạn hoặc bắn xuống dưới súng; đạn bay thẳng với tốc độ cố định", () => {
    let s = start();
    expect(fireAt(s, 50, 98)).toBe(s);
    const shot = fireAt(s, CANNON.x, 10);
    expect(shot.bullet!.vx).toBeCloseTo(0, 6);
    expect(Math.hypot(shot.bullet!.vx, shot.bullet!.vy)).toBeCloseTo(BULLET_SPEED, 6);
    expect(fireAt(shot, 30, 10)).toBe(shot);
  });

  it("bắn hụt ra ngoài sân không bị tính là lần sai", () => {
    let s = fireAt(start(), 1, 90);
    s = run(s, 3, (x) => x.bullet === null);
    expect(s.attempts).toBe(0);
  });

  it("aimPoint dự đoán vị trí bóng đang rơi nên bắn trúng cả ở Thử thách; dt lớn không làm đạn xuyên bóng", () => {
    let s = start(10, "challenge");
    s = run(s, 1.2);
    const after = shootBubble(s, answerId(s));
    expect(after.items[0]).toMatchObject({ correct: true });

    let t = start(10);
    const aim = aimPoint(t, answerId(t))!;
    t = fireAt(t, aim.x, aim.y);
    for (let i = 0; i < 40 && t.bullet; i++) t = stepShooter(t, 1.0);
    expect(t.items[0]?.correct).toBe(true);
  });

  it("liveBubbles sắp theo chiều ngang và bỏ bóng đã tan", () => {
    let s = start();
    const xs = liveBubbles(s).map((b) => bubblePos(b, s.t).x);
    expect([...xs].sort((a, b) => a - b)).toEqual(xs);
    const target = answerId(s);
    s = shootBubble(s, target);
    expect(liveBubbles(s).some((b) => b.id === target)).toBe(false);
    expect(aimPoint(s, "khong-co")).toBeNull();
  });
});

describe("bóng rơi mất", () => {
  it("bóng của từ đang nạp chạm đáy: chưa nhớ, sáng lên, súng nạp từ kế, đúng một bóng mới thay vào", () => {
    let s = start(10, "relax");
    const missedId = answerId(s);
    const others = s.bubbles.filter((b) => b.id !== missedId).map((b) => b.id);
    s = run(s, 80, (x) => x.items.length >= 1);
    expect(s.items[0]).toMatchObject({ card_id: missedId, correct: false, attempts: 0 });
    expect(s.combo).toBe(0);
    expect(s.lives).toBeNull();
    expect(s.events.some((e) => e.type === "miss")).toBe(true);
    expect(s.bubbles.find((b) => b.id === missedId)!.revealed).toBe(true);
    expect(answerId(s)).not.toBe(missedId);
    // các bóng khác không bị làm mới (không sinh lại cả sân): những bóng cũ còn trên sân vẫn là chính chúng
    const stillThere = s.bubbles.filter((b) => others.includes(b.id));
    expect(stillThere.length).toBeGreaterThan(0);
  });

  it("Thử thách: mỗi bóng đúng rơi mất trừ 1 mạng; hết 3 mạng thì kết thúc", () => {
    let s = start(10, "challenge");
    s = run(s, 300);
    expect(isShooterFinished(s)).toBe(true);
    expect(s.lives).toBe(0);
    expect(s.items).toHaveLength(CHALLENGE_LIVES);
    expect(s.items.every((i) => !i.correct)).toBe(true);
  });

  it("bóng KHÔNG phải từ đang nạp chạm đáy chỉ biến mất và được thay bằng một bóng mới (không mất mạng, không ghi kết quả)", () => {
    let s = start(10, "challenge");
    // bóng nhiễu thuần (không thuộc các từ sắp tới) để việc thay thế không trùng lại chính nó
    const decoy = liveBubbles(s).find((b) => !s.words.slice(0, LOOKAHEAD).some((w) => w.id === b.id))!;
    s = { ...s, bubbles: s.bubbles.map((b) => (b.id === decoy.id ? { ...b, y: MISS_LINE - 0.05 } : b)) };
    const before = active(s).length;
    s = run(s, 0.2);
    expect(s.bubbles.some((b) => b.id === decoy.id)).toBe(false);
    expect(active(s)).toHaveLength(before); // đã có đúng một bóng mới thay vào
    expect(s.lives).toBe(CHALLENGE_LIVES);
    expect(s.items).toHaveLength(0);
    expect(s.events.some((e) => e.type === "miss")).toBe(false);
  });

  it("nghĩa trên sân luôn khác nhau từng đôi và không bao giờ chồng bóng trong suốt một ván tự chơi", () => {
    let s = start(14, "challenge", { rng: seeded(11) });
    for (let i = 0; i < 400 && !isShooterFinished(s); i++) {
      s = stepShooter(s, 0.05);
      if (i % 25 === 0 && !s.bullet) {
        const live = liveBubbles(s).find((b) => b.id === answerId(s));
        if (live) {
          const p = aimPoint(s, live.id)!;
          s = fireAt(s, p.x, p.y);
        }
      }
      const act = active(s);
      expect(new Set(act.map((b) => b.id)).size).toBe(act.length);
      expect(new Set(act.map((b) => b.text.toLowerCase())).size).toBe(act.length);
      for (let a = 0; a < act.length; a++)
        for (let b = a + 1; b < act.length; b++) {
          expect(Math.hypot(act[a].baseX - act[b].baseX, act[a].y - act[b].y)).toBeGreaterThanOrEqual(1.6 * BUBBLE_RADIUS);
        }
    }
  });
});

describe("giảm chuyển động", () => {
  it("bóng đứng yên, không rơi mất, không có mạng", () => {
    let s = start(10, "challenge", { reducedMotion: true });
    expect(s.lives).toBeNull();
    const y0 = s.bubbles[0].y;
    s = run(s, 120);
    expect(s.bubbles[0].y).toBe(y0);
    expect(s.items).toHaveLength(0);
    expect(s.phase).toBe("playing");
  });

  it("bắn đúng: bóng mới xuất hiện ngay chỗ bóng vừa tan, các bóng khác đứng yên", () => {
    let s = start(10, "relax", { reducedMotion: true });
    const target = s.bubbles.find((b) => b.id === answerId(s))!;
    const slot = { x: target.baseX, y: target.y };
    const others = s.bubbles.filter((b) => b.id !== target.id).map((b) => ({ id: b.id, x: b.baseX, y: b.y }));
    s = shootBubble(s, target.id);
    s = run(s, 1);
    expect(active(s)).toHaveLength(MAX_FIELD);
    const fresh = s.bubbles.find((b) => !b.popped && !others.some((o) => o.id === b.id) && b.id !== target.id)!;
    expect(fresh).toBeTruthy();
    expect(fresh.baseX).toBe(slot.x);
    expect(fresh.y).toBe(slot.y);
    for (const o of others) {
      const cur = s.bubbles.find((b) => b.id === o.id)!;
      expect([cur.baseX, cur.y]).toEqual([o.x, o.y]);
    }
  });
});


describe("va chạm: đạn nhắm bóng vs bắn tự do", () => {
  /** Dựng sân với bóng chắn (thấp) đứng trước bóng đúng (cao) trên cùng một đường bắn thẳng đứng. */
  function lineUp() {
    let s = start(10);
    const answer = s.bubbles.find((b) => b.id === answerId(s))!;
    const blocker = s.bubbles.find((b) => b.id !== answer.id)!;
    s = {
      ...s,
      bubbles: s.bubbles.map((b) => {
        if (b.id === answer.id) return { ...b, baseX: 50, y: 30, phase: 0 };
        if (b.id === blocker.id) return { ...b, baseX: 50, y: 60, phase: 0 };
        return { ...b, baseX: b.baseX < 50 ? 10 : 90, y: b.y }; // đẩy các bóng khác ra xa đường bắn
      }),
    };
    return { s, answer, blocker };
  }

  it("bắn tự do: đạn trúng bóng ĐẦU TIÊN trên đường bay (bóng chắn) nên tính là bắn sai", () => {
    const { s, blocker } = lineUp();
    const p = bubblePos(s.bubbles.find((b) => b.id === s.words[0].id)!, s.t);
    let t = fireAt({ ...s, t: 0 }, p.x, p.y);
    t = run(t, 3, (x) => x.bullet === null);
    expect(t.attempts).toBe(1);
    expect(t.bubbles.find((b) => b.id === blocker.id)!.shakeUntil).toBeGreaterThan(0);
    expect(t.items).toHaveLength(0);
  });

  it("đạn nhắm bóng (ngắm hỗ trợ/bàn phím) bay xuyên bóng chắn và trúng đúng bóng được chọn", () => {
    const { s, answer } = lineUp();
    const t = run(fireAtBubble(s, answer.id), 3, (x) => x.bullet === null);
    expect(t.attempts).toBe(0);
    expect(t.items[0]).toMatchObject({ card_id: answer.id, correct: true });
  });

  it("không bắn nhắm được bóng chưa lọt vào sân", () => {
    const s0 = start(10);
    const b = s0.bubbles[0];
    const s = { ...s0, bubbles: s0.bubbles.map((x) => (x.id === b.id ? { ...x, y: -5 } : x)) };
    expect(aimPoint(s, b.id)).toBeNull();
    expect(fireAtBubble(s, b.id)).toBe(s);
    expect(liveBubbles(s).some((x) => x.id === b.id)).toBe(false);
  });
});

describe("bóng mới xuất hiện kịp thời", () => {
  it("dù mép trên đang đông, bóng thay thế vẫn được sinh ngay (trượt vào từ phía trên) và không chồng lên bóng khác", () => {
    let s = start(10);
    s = shootBubble(s, answerId(s));
    const spawned = s.events.find((e) => e.type === "spawn") ?? null;
    s = run(s, 0.3);
    expect(active(s)).toHaveLength(MAX_FIELD);
    const fresh = [...s.bubbles].sort((a, b) => a.y - b.y)[0];
    expect(fresh.y).toBeLessThan(BUBBLE_RADIUS + 1 + 1.2); // vừa sinh ở mép trên, mới rơi được một chút
    for (const o of s.bubbles.filter((b) => b.id !== fresh.id && !b.popped)) {
      expect(Math.hypot(o.baseX - fresh.baseX, o.y - fresh.y)).toBeGreaterThanOrEqual(1.6 * BUBBLE_RADIUS);
    }
    expect(spawned === null || spawned.type === "spawn").toBe(true);
  });
});
