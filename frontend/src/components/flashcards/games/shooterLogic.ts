/**
 * Luật chơi thuần của "Bắn bóng nghĩa" (không React, không đồng hồ thật): toàn bộ chuyển động tính theo `dt`,
 * nên kết quả lặp lại được và kiểm thử được. Giao diện chỉ gọi stepShooter/fireAt rồi vẽ.
 *
 * Sân chơi dùng hệ tọa độ 0..100 theo cả hai chiều (giao diện co giãn theo kích thước thật):
 *   - Trên sân luôn có một "cánh đồng" gồm tối đa MAX_FIELD bóng NHỎ, mỗi bóng chứa nghĩa của một từ trong danh sách đã lưu.
 *   - Súng ở đáy nạp MỘT từ; bắn trúng bóng có nghĩa đúng thì ghi điểm, súng nạp từ kế tiếp NGAY (không làm lại cả sân).
 *   - Mỗi bóng bị bắn trúng hoặc rơi mất chỉ được thay bằng ĐÚNG MỘT bóng mới ở mép trên (nghĩa của từ sắp tới, hoặc nghĩa
 *     của một từ khác trong danh sách làm bóng nhiễu); các bóng còn lại giữ nguyên vị trí.
 *   - Bắn sai: đạn bật ra, bóng rung, mất combo (KHÔNG mất mạng).
 *   - Bóng của từ đang nạp chạm đáy: tính là chưa nhớ; ở chế độ Thử thách mất 1 mạng.
 * Điểm chính thức do máy chủ tính từ `GameItemResult`; `score` ở đây chỉ để hiển thị.
 */
import { shuffle, speedMultiplier, type GameCard, type GameItemResult, type GameMode, type Rng } from "./gameLogic";

export const ARENA = 100;
export const CANNON = { x: 50, y: 94 };
/** Bóng chạm đường này là "rơi mất". */
export const MISS_LINE = 84;
export const BULLET_SPEED = 150; // đơn vị/giây
export const BULLET_RADIUS = 1.4;
/** Bán kính bóng (nhỏ). */
export const BUBBLE_RADIUS = 6.2;
/** Số bóng cùng lúc trên sân (tối đa). */
export const MAX_FIELD = 5;
/** Luôn giữ sẵn bóng của từ đang nạp và các từ kế tiếp trên sân. */
export const LOOKAHEAD = 3;
export const SHAKE_SECONDS = 0.4;
/** Bóng tan/bóng bị bỏ lỡ nán lại ngắn để người chơi thấy hiệu ứng. */
export const LINGER_SECONDS = 0.4;
export const MISS_LINGER_SECONDS = 0.7;
export const CHALLENGE_LIVES = 3;
const MAX_STEP = 0.05; // giây; chia nhỏ để đạn không xuyên qua bóng
const SUBSTEP = 0.012;

export interface Bubble {
  /** Id của thẻ sở hữu nghĩa này (một nghĩa chỉ xuất hiện một lần trên sân). Bóng đúng là bóng có id = id từ đang nạp. */
  id: string;
  text: string;
  baseX: number;
  y: number;
  phase: number;
  radius: number;
  /** Đã bị bắn trúng đúng (đang tan). */
  popped: boolean;
  /** Còn rung đến thời điểm này (bắn sai). */
  shakeUntil: number;
  /** Bóng đúng rơi mất: sáng lên để người chơi thấy đáp án. */
  revealed: boolean;
  /** Với bóng đang tan/bị lộ: thời điểm bị gỡ khỏi sân. */
  lingerUntil: number;
}

export interface Bullet {
  x: number;
  y: number;
  vx: number;
  vy: number;
  /** Đạn nhắm một bóng cụ thể (ngắm hỗ trợ/bàn phím): chỉ va chạm với bóng đó, bay xuyên các bóng khác. */
  targetId?: string;
}

export type ShooterEvent =
  | { type: "fire" }
  | { type: "pop"; bubbleId: string; points: number; combo: number }
  | { type: "wrong"; bubbleId: string }
  | { type: "miss"; bubbleId: string }
  | { type: "spawn"; bubbleId: string }
  | { type: "end" };

export interface ShooterState {
  mode: GameMode;
  reducedMotion: boolean;
  words: GameCard[];
  fieldSize: number;
  wordIndex: number;
  bubbles: Bubble[];
  bullet: Bullet | null;
  /** Số lần bắn sai ở từ hiện tại. */
  attempts: number;
  combo: number;
  bestCombo: number;
  score: number;
  lives: number | null;
  items: GameItemResult[];
  /** Thời gian đã chơi (giây). */
  t: number;
  phase: "playing" | "finished";
  /** Chế độ giảm chuyển động: ô trống để bóng mới xuất hiện đúng chỗ bóng vừa tan. */
  freeSlots: { x: number; y: number }[];
  rng: Rng;
  /** Sự kiện sinh ra bởi lần gọi gần nhất (giao diện dùng để phát âm thanh/hiệu ứng). */
  events: ShooterEvent[];
}

const norm = (s: string) => s.trim().toLowerCase();
const meaning = (c: GameCard) => c.definition.trim();

export interface InitOptions {
  reducedMotion?: boolean;
  rng?: Rng;
}

export function initShooter(cards: GameCard[], mode: GameMode, options: InitOptions = {}): ShooterState {
  const rng = options.rng ?? Math.random;
  const reduced = !!options.reducedMotion;
  const words = shuffle(cards, rng);
  const fieldSize = Math.min(MAX_FIELD, words.length);
  const base: ShooterState = {
    mode,
    reducedMotion: reduced,
    words,
    fieldSize,
    wordIndex: 0,
    bubbles: [],
    bullet: null,
    attempts: 0,
    combo: 0,
    bestCombo: 0,
    score: 0,
    // Chế độ giảm chuyển động: bóng đứng yên nên không thể rơi mất và không có mạng.
    lives: mode === "challenge" && !reduced ? CHALLENGE_LIVES : null,
    items: [],
    t: 0,
    phase: "playing",
    freeSlots: [],
    rng,
    events: [],
  };

  // Lấp đầy sân: nghĩa của các từ đầu tiên (từ đang nạp + vài từ kế) rồi tới bóng nhiễu, mỗi nghĩa một lần.
  const entries: GameCard[] = [];
  for (let i = 0; i < fieldSize; i++) {
    const pick = pickMeaning({ ...base, bubbles: entries.map((c) => ({ id: c.id, text: meaning(c) }) as Bubble) });
    if (!pick) break;
    entries.push(pick);
  }
  // Bố trí: cột (x) ngẫu nhiên; hàng (y) so le theo thứ tự từ. Từ đang nạp ở hàng THẤP nhất, các từ kế tiếp cao dần, nên hạn rơi
  // của từ này cách từ kia vài giây (không bao giờ hai từ liên tiếp cùng chạm đáy một lúc). Bóng nhiễu ở các hàng còn lại.
  const slot = ARENA / Math.max(1, entries.length);
  const xs = shuffle(entries.map((_, i) => slot * (i + 0.5)), rng);
  const r = BUBBLE_RADIUS;
  const rows = Math.min(LOOKAHEAD, Math.max(1, entries.length));
  const rowY = (e: number) => {
    const row = e < LOOKAHEAD ? rows - 1 - e : e - LOOKAHEAD; // từ thứ e < LOOKAHEAD: hàng (rows-1-e); bóng nhiễu: hàng 0,1,…
    return (reduced ? 30 : r + 1) + (row % rows) * (2 * r + 4);
  };
  return { ...base, bubbles: entries.map((c, e) => newBubble(c, xs[e], rowY(e), rng)) };
}

function newBubble(card: GameCard, x: number, y: number, rng: Rng): Bubble {
  return { id: card.id, text: meaning(card), baseX: x, y, phase: rng() * Math.PI * 2, radius: BUBBLE_RADIUS, popped: false, shakeUntil: 0, revealed: false, lingerUntil: 0 };
}

export const currentWord = (s: ShooterState): GameCard | undefined => s.words[s.wordIndex];

/** Tốc độ rơi (đơn vị/giây): Thư giãn chậm; Thử thách nhanh dần theo số từ đã qua. */
export function fallSpeed(mode: GameMode, wordIndex: number): number {
  return mode === "relax" ? 2.6 : Math.min(5.5 + wordIndex * 0.45, 12);
}

const currentSpeed = (s: ShooterState) => (s.reducedMotion ? 0 : fallSpeed(s.mode, s.wordIndex));

/**
 * Chọn thẻ có nghĩa dùng cho bóng kế tiếp: ưu tiên từ đang nạp rồi các từ sắp tới mà nghĩa chưa có trên sân;
 * hết thì lấy nghĩa của một từ khác trong danh sách làm bóng nhiễu. Một nghĩa (và một thẻ) chỉ xuất hiện một lần trên sân.
 */
export function pickMeaning(s: Pick<ShooterState, "words" | "wordIndex" | "bubbles" | "rng">): GameCard | null {
  const used = new Set(s.bubbles.map((b) => b.id));
  const texts = new Set(s.bubbles.map((b) => norm(b.text)));
  const free = (c: GameCard) => !used.has(c.id) && !texts.has(norm(meaning(c)));
  const end = Math.min(s.wordIndex + Math.min(LOOKAHEAD, s.words.length), s.words.length);
  for (let i = s.wordIndex; i < end; i++) {
    if (free(s.words[i])) return s.words[i];
  }
  const decoys = shuffle(s.words.filter(free), s.rng);
  return decoys[0] ?? null;
}

export function bubblePos(b: Bubble, t: number, reducedMotion = false): { x: number; y: number } {
  const sway = reducedMotion ? 0 : Math.sin(t * 0.9 + b.phase) * 1.2;
  return { x: b.baseX + sway, y: b.y };
}

const active = (b: Bubble) => !b.popped && !b.revealed;
/** Bóng mới sinh có thể còn nằm phía trên mép sân (đang trượt vào): chưa bắn/chọn được cho tới khi lọt vào sân. */
const onScreen = (b: Bubble) => b.y >= 0;
const shootable = (b: Bubble) => active(b) && onScreen(b);

/** Điểm ngắm có dự đoán vị trí bóng đang rơi để bắn trúng ngay cả khi bóng di chuyển. */
export function aimPoint(s: ShooterState, bubbleId: string): { x: number; y: number } | null {
  const b = s.bubbles.find((x) => x.id === bubbleId && shootable(x));
  if (!b) return null;
  const now = bubblePos(b, s.t, s.reducedMotion);
  const flight = Math.hypot(now.x - CANNON.x, now.y - CANNON.y) / BULLET_SPEED;
  return { x: now.x, y: now.y + currentSpeed(s) * flight };
}

/** Các bóng còn bắn được, từ trái sang phải (dùng cho phím ←/→ và phím số). */
export function liveBubbles(s: ShooterState): Bubble[] {
  return s.bubbles.filter(shootable).sort((a, b) => bubblePos(a, s.t, s.reducedMotion).x - bubblePos(b, s.t, s.reducedMotion).x);
}

/** Bắn nhắm thẳng vào một bóng (ngắm hỗ trợ / bàn phím): đạn chỉ trúng bóng đó, không bị bóng khác chắn. */
export function fireAtBubble(s: ShooterState, bubbleId: string): ShooterState {
  const p = aimPoint(s, bubbleId);
  if (!p) return s;
  const shot = fireAt(s, p.x, p.y);
  return shot === s ? s : { ...shot, bullet: { ...shot.bullet!, targetId: bubbleId } };
}

/** Bắn tự do theo hướng ngắm: đạn trúng bóng ĐẦU TIÊN nó gặp trên đường bay. */
export function fireAt(s: ShooterState, x: number, y: number): ShooterState {
  if (s.phase !== "playing" || s.bullet) return s;
  const dx = x - CANNON.x;
  const dy = y - CANNON.y;
  const len = Math.hypot(dx, dy);
  if (len < 1e-6 || dy >= -1) return s; // chỉ bắn lên phía trên súng
  return {
    ...s,
    bullet: { x: CANNON.x, y: CANNON.y, vx: (dx / len) * BULLET_SPEED, vy: (dy / len) * BULLET_SPEED },
    events: [{ type: "fire" }],
  };
}

function record(s: ShooterState, correct: boolean): GameItemResult[] {
  return [...s.items, { card_id: s.words[s.wordIndex].id, correct, attempts: s.attempts, hints: 0 }];
}

/** Kết thúc từ hiện tại (trúng hoặc rơi mất) và nạp ngay từ kế tiếp; hết từ hoặc hết mạng thì kết thúc ván. */
function resolveWord(s: ShooterState, correct: boolean, extra: Partial<ShooterState>, events: ShooterEvent[]): ShooterState {
  const next: ShooterState = { ...s, ...extra, items: record(s, correct), bullet: null, attempts: 0, wordIndex: s.wordIndex + 1 };
  const outOfLives = next.lives !== null && next.lives <= 0;
  if (outOfLives || next.wordIndex >= next.words.length) {
    return { ...next, wordIndex: next.words.length - 1, phase: "finished", events: [...events, { type: "end" }] };
  }
  return { ...next, events };
}

function popPoints(s: ShooterState): number {
  const mult = s.attempts === 0 ? speedMultiplier(s.combo) : 1;
  return Math.max(5, 10 * mult - 3 * s.attempts);
}

/** Một bước nhỏ của đạn: di chuyển và xét va chạm. */
function stepBullet(s: ShooterState, dt: number): ShooterState {
  const bullet = s.bullet;
  if (!bullet) return s;
  const moved: Bullet = { ...bullet, x: bullet.x + bullet.vx * dt, y: bullet.y + bullet.vy * dt };
  if (moved.y < -4 || moved.x < -4 || moved.x > ARENA + 4) return { ...s, bullet: null };

  const word = currentWord(s)!;
  for (const b of s.bubbles) {
    if (!shootable(b)) continue;
    if (bullet.targetId && b.id !== bullet.targetId) continue;
    const p = bubblePos(b, s.t, s.reducedMotion);
    if (Math.hypot(moved.x - p.x, moved.y - p.y) > b.radius + BULLET_RADIUS) continue;

    if (b.id === word.id) {
      const points = popPoints(s);
      const clean = s.attempts === 0;
      const combo = clean ? s.combo + 1 : 0;
      const gone: Bubble = { ...b, popped: true, lingerUntil: s.t + LINGER_SECONDS };
      return resolveWord(
        s,
        true,
        {
          bubbles: s.bubbles.map((x) => (x.id === b.id ? gone : x)),
          freeSlots: s.reducedMotion ? [...s.freeSlots, { x: b.baseX, y: b.y }] : s.freeSlots,
          combo,
          bestCombo: Math.max(s.bestCombo, combo),
          score: s.score + points,
        },
        [...s.events, { type: "pop", bubbleId: b.id, points, combo }]
      );
    }
    // Bắn sai: mất combo, đạn bật ra, bóng rung; KHÔNG mất mạng.
    return {
      ...s,
      bullet: null,
      attempts: s.attempts + 1,
      combo: 0,
      bubbles: s.bubbles.map((x) => (x.id === b.id ? { ...x, shakeUntil: s.t + SHAKE_SECONDS } : x)),
      events: [...s.events, { type: "wrong", bubbleId: b.id }],
    };
  }
  return { ...s, bullet: moved };
}

/**
 * Tìm chỗ cho một bóng mới ở mép trên: chọn cột có chỗ cao nhất. Nếu mép trên đang đông, bóng mới được đặt NGAY TRÊN bóng
 * cao nhất của cột đó (có thể còn nằm phía trên mép sân và trượt vào), nên bóng mới xuất hiện sớm mà không chồng lên ai.
 * Trả null nếu phải xếp quá xa phía trên.
 */
function topSpot(s: ShooterState): { x: number; y: number } | null {
  if (s.reducedMotion) return s.freeSlots[0] ?? null;
  const r = BUBBLE_RADIUS;
  const gap = 2 * r + 3;
  const xs: number[] = [];
  for (let x = r + 1; x <= ARENA - r - 1; x += r) xs.push(x);
  let best: { x: number; y: number } | null = null;
  for (const x of shuffle(xs, s.rng)) {
    let y = r + 1;
    for (const b of s.bubbles) {
      if (!b.popped && Math.abs(b.baseX - x) < gap) y = Math.min(y, b.y - gap);
    }
    if (!best || y > best.y) best = { x, y };
  }
  return best && best.y >= -4 * r ? best : null;
}

/**
 * Bổ sung ĐÚNG những bóng còn thiếu, mỗi lần một bóng: giữ đủ fieldSize bóng bắn được, và luôn có bóng cho từ đang nạp
 * (kể cả khi sân đã đầy bóng nhiễu). Không làm lại các bóng đang có.
 */
function refill(s: ShooterState): ShooterState {
  let cur = s;
  for (let guard = 0; guard < 3 && cur.phase === "playing"; guard++) {
    const present = cur.bubbles.filter(active);
    const word = currentWord(cur)!;
    const needsWord = !present.some((b) => b.id === word.id);
    if (!(present.length < cur.fieldSize || needsWord)) break;
    const card = needsWord ? word : pickMeaning(cur);
    if (!card) break;
    const spot = topSpot(cur);
    if (!spot) break; // mép trên đang đông: thử lại ở bước sau
    const bubble = newBubble(card, spot.x, spot.y, cur.rng);
    cur = {
      ...cur,
      bubbles: [...cur.bubbles.filter((b) => b.id !== card.id), bubble], // gỡ bóng cũ đang tan (nếu cùng thẻ) để id không trùng
      freeSlots: cur.reducedMotion ? cur.freeSlots.slice(1) : cur.freeSlots,
      events: [...cur.events, { type: "spawn", bubbleId: bubble.id }],
    };
  }
  return cur;
}

export function stepShooter(state: ShooterState, dtSeconds: number): ShooterState {
  if (state.phase === "finished" || dtSeconds <= 0) return state;
  let s: ShooterState = { ...state, events: [] };
  let remaining = Math.min(dtSeconds, MAX_STEP);

  while (remaining > 1e-9 && s.phase !== "finished") {
    const dt = Math.min(SUBSTEP, remaining);
    remaining -= dt;
    const speed = currentSpeed(s);
    s = {
      ...s,
      t: s.t + dt,
      bubbles: speed === 0 ? s.bubbles : s.bubbles.map((b) => (b.popped ? b : { ...b, y: b.y + speed * dt })),
    };

    s = stepBullet(s, dt);
    if (s.phase === "finished") break;

    // Dọn bóng đã tan/lộ xong.
    if (s.bubbles.some((b) => (b.popped || b.revealed) && b.lingerUntil <= s.t)) {
      s = { ...s, bubbles: s.bubbles.filter((b) => !((b.popped || b.revealed) && b.lingerUntil <= s.t)) };
    }

    // Bóng chạm đáy: bóng của từ đang nạp = rơi mất (chưa nhớ); bóng khác chỉ biến mất rồi được thay bằng bóng mới.
    if (!s.reducedMotion) {
      for (const b of s.bubbles.filter((x) => active(x) && x.y >= MISS_LINE)) {
        const word = currentWord(s);
        if (word && b.id === word.id) {
          s = resolveWord(
            s,
            false,
            {
              bubbles: s.bubbles.map((x) => (x.id === b.id ? { ...x, revealed: true, lingerUntil: s.t + MISS_LINGER_SECONDS } : x)),
              combo: 0,
              lives: s.lives === null ? null : s.lives - 1,
            },
            [...s.events, { type: "miss", bubbleId: b.id }]
          );
          if (s.phase === "finished") break;
        } else {
          s = { ...s, bubbles: s.bubbles.filter((x) => x.id !== b.id) };
        }
      }
    }
    if (s.phase === "finished") break;

    s = refill(s);
  }
  return s;
}

export function shooterResults(s: ShooterState): GameItemResult[] {
  return s.items;
}

export const isShooterFinished = (s: ShooterState) => s.phase === "finished";
