/**
 * Luật chơi thuần của 3 trò (Ghép cặp, Đua 60 giây, Xếp chữ) — không React, không mạng, dễ kiểm thử.
 * Điểm/sao/XP chính thức do MÁY CHỦ tính từ `GameItemResult`; hàm `speedStepScore` ở đây chỉ để hiển thị điểm tạm thời.
 */

export type GameKind = "match" | "speed" | "builder" | "shooter";
export type GameMode = "relax" | "challenge";
export type Rng = () => number;

export interface GameCard {
  id: string;
  term: string;
  definition: string;
  phonetic?: string | null;
  audio_url?: string | null;
  part_of_speech?: string | null;
  lang_code: string;
  /** Đã đến hạn ôn: chỉ những thẻ này mới được cập nhật lịch ôn khi chơi. */
  is_due: boolean;
  choices?: string[];
}

/** Kết quả một câu/cặp/từ (khớp với backend `GameItem`). */
export interface GameItemResult {
  card_id: string;
  correct: boolean;
  attempts: number;
  hints: number;
}

export function shuffle<T>(items: readonly T[], rng: Rng = Math.random): T[] {
  const copy = [...items];
  for (let i = copy.length - 1; i > 0; i--) {
    const j = Math.floor(rng() * (i + 1));
    [copy[i], copy[j]] = [copy[j], copy[i]];
  }
  return copy;
}

// ======================================================================================
// Ghép cặp
// ======================================================================================

export interface MatchState {
  cards: GameCard[];
  /** Thứ tự cột "nghĩa" (mỗi phần tử là id thẻ sở hữu nghĩa đó). */
  defOrder: string[];
  matched: string[];
  selectedTerm: string | null;
  selectedDef: string | null;
  attempts: Record<string, number>;
  mistakes: number;
  /** Cặp vừa ghép sai (để rung/đỏ ngắn rồi xóa). */
  lastWrong: { term: string; def: string } | null;
  done: boolean;
}

export function initMatch(cards: GameCard[], rng: Rng = Math.random): MatchState {
  return {
    cards: shuffle(cards, rng),
    defOrder: shuffle(cards.map((c) => c.id), rng),
    matched: [],
    selectedTerm: null,
    selectedDef: null,
    attempts: {},
    mistakes: 0,
    lastWrong: null,
    done: false,
  };
}

/** Chạm một ô. `id` luôn là id của thẻ sở hữu ô đó (cột từ hoặc cột nghĩa). */
export function matchSelect(state: MatchState, side: "term" | "def", id: string): MatchState {
  if (state.done || state.matched.includes(id) || state.lastWrong) return state;
  const next: MatchState = { ...state };
  if (side === "term") next.selectedTerm = state.selectedTerm === id ? null : id;
  else next.selectedDef = state.selectedDef === id ? null : id;

  if (next.selectedTerm && next.selectedDef) {
    if (next.selectedTerm === next.selectedDef) {
      next.matched = [...state.matched, next.selectedTerm];
      next.done = next.matched.length === state.cards.length;
    } else {
      next.mistakes = state.mistakes + 1;
      next.attempts = { ...state.attempts, [next.selectedTerm]: (state.attempts[next.selectedTerm] ?? 0) + 1 };
      next.lastWrong = { term: next.selectedTerm, def: next.selectedDef };
    }
    if (!next.lastWrong) {
      next.selectedTerm = null;
      next.selectedDef = null;
    }
  }
  return next;
}

export function matchClearWrong(state: MatchState): MatchState {
  return state.lastWrong ? { ...state, lastWrong: null, selectedTerm: null, selectedDef: null } : state;
}

export function matchResults(state: MatchState): GameItemResult[] {
  return state.cards.map((c) => ({
    card_id: c.id,
    correct: state.matched.includes(c.id),
    attempts: state.attempts[c.id] ?? 0,
    hints: 0,
  }));
}

// ======================================================================================
// Đua 60 giây
// ======================================================================================

export const SPEED_CHALLENGE_SECONDS = 60;
export const SPEED_CHALLENGE_LIVES = 3;
export const SPEED_RELAX_QUESTIONS = 10;

export interface SpeedState {
  mode: GameMode;
  queue: GameCard[];
  index: number;
  combo: number;
  bestCombo: number;
  lives: number | null;
  correct: number;
  mistakes: number;
  score: number;
  items: GameItemResult[];
  /** Đáp án vừa chọn (đang hiện phản hồi, chưa sang câu kế). */
  answered: { choice: string; correct: boolean } | null;
  finished: boolean;
  /** Thứ tự đáp án của câu hiện tại (xáo mỗi lần hiện). */
  choices: string[];
}

export const speedMultiplier = (comboBefore: number) => Math.min(1 + Math.floor(comboBefore / 3), 5);

/** Hàng đợi câu hỏi: xoay vòng các thẻ (đã xáo) cho tới khi đủ `length` câu. */
function buildQueue(cards: GameCard[], length: number, rng: Rng): GameCard[] {
  const out: GameCard[] = [];
  while (out.length < length) out.push(...shuffle(cards, rng));
  return out.slice(0, length);
}

export function initSpeed(cards: GameCard[], mode: GameMode, rng: Rng = Math.random): SpeedState {
  const queue = buildQueue(cards, mode === "relax" ? SPEED_RELAX_QUESTIONS : 80, rng);
  return {
    mode,
    queue,
    index: 0,
    combo: 0,
    bestCombo: 0,
    lives: mode === "challenge" ? SPEED_CHALLENGE_LIVES : null,
    correct: 0,
    mistakes: 0,
    score: 0,
    items: [],
    answered: null,
    finished: false,
    choices: shuffle(queue[0]?.choices ?? [], rng),
  };
}

export function speedAnswer(state: SpeedState, choice: string): SpeedState {
  if (state.finished || state.answered) return state;
  const card = state.queue[state.index];
  const correct = choice.trim().toLowerCase() === card.definition.trim().toLowerCase();
  const item: GameItemResult = { card_id: card.id, correct, attempts: correct ? 0 : 1, hints: 0 };
  const combo = correct ? state.combo + 1 : 0;
  return {
    ...state,
    answered: { choice, correct },
    items: [...state.items, item],
    combo,
    bestCombo: Math.max(state.bestCombo, combo),
    correct: state.correct + (correct ? 1 : 0),
    mistakes: state.mistakes + (correct ? 0 : 1),
    score: state.score + (correct ? 10 * speedMultiplier(state.combo) : 0),
    lives: state.lives === null ? null : state.lives - (correct ? 0 : 1),
  };
}

export function speedNext(state: SpeedState, rng: Rng = Math.random): SpeedState {
  // Chỉ sang câu kế sau khi đã trả lời (tránh nhảy cóc khi Enter vừa kích hoạt phím tắt vừa bấm nút).
  if (state.finished || !state.answered) return state;
  const nextIndex = state.index + 1;
  const outOfLives = state.lives !== null && state.lives <= 0;
  const outOfQuestions = nextIndex >= state.queue.length;
  if (outOfLives || outOfQuestions) return { ...state, answered: null, finished: true };
  return { ...state, index: nextIndex, answered: null, choices: shuffle(state.queue[nextIndex].choices ?? [], rng) };
}

/** Hết giờ (chỉ Thử thách). Câu đang trả lời dở không tính. */
export function speedTimeUp(state: SpeedState): SpeedState {
  return state.finished ? state : { ...state, answered: null, finished: true };
}

// ======================================================================================
// Xếp chữ
// ======================================================================================

export const BUILDER_MAX_HINTS_PER_WORD = 3;

export interface Tile {
  id: number;
  ch: string;
}

export interface BuilderState {
  words: GameCard[];
  index: number;
  tiles: Tile[];
  /** id các ô đã đặt, theo thứ tự. */
  placed: number[];
  attempts: number;
  hints: number;
  solved: boolean;
  /** Vừa xếp đủ chữ nhưng sai (UI rung rồi gọi builderClearWrong). */
  wrong: boolean;
  items: GameItemResult[];
  finished: boolean;
}

const chars = (word: string) => Array.from(word.trim());
const same = (a: string, b: string) => a.toLowerCase() === b.toLowerCase();

/** Xáo chữ cái của từ; đảm bảo khác thứ tự gốc khi có thể. */
export function scramble(word: string, rng: Rng = Math.random): Tile[] {
  const letters = chars(word);
  const original = letters.join("").toLowerCase();
  let tiles: Tile[] = letters.map((ch, id) => ({ id, ch }));
  const distinct = new Set(letters.map((c) => c.toLowerCase())).size > 1;
  for (let attempt = 0; attempt < 12 && distinct; attempt++) {
    tiles = shuffle(letters.map((ch, id) => ({ id, ch })), rng);
    if (tiles.map((t) => t.ch).join("").toLowerCase() !== original) break;
  }
  if (distinct && tiles.map((t) => t.ch).join("").toLowerCase() === original) tiles = [...tiles.slice(1), tiles[0]];
  return tiles;
}

const startWord = (words: GameCard[], index: number, rng: Rng) => ({
  index,
  tiles: scramble(words[index].term, rng),
  placed: [] as number[],
  attempts: 0,
  hints: 0,
  solved: false,
  wrong: false,
});

export function initBuilder(cards: GameCard[], rng: Rng = Math.random): BuilderState {
  const words = shuffle(cards, rng);
  return { words, ...startWord(words, 0, rng), items: [], finished: false };
}

export const builderWord = (s: BuilderState) => s.words[s.index]?.term.trim() ?? "";
export const placedText = (s: BuilderState) => s.placed.map((id) => s.tiles.find((t) => t.id === id)?.ch ?? "").join("");

function evaluate(s: BuilderState): BuilderState {
  const word = builderWord(s);
  if (s.placed.length !== chars(word).length) return s;
  return placedText(s).toLowerCase() === word.toLowerCase() ? { ...s, solved: true, wrong: false } : { ...s, wrong: true, attempts: s.attempts + 1 };
}

export function builderPlace(s: BuilderState, tileId: number): BuilderState {
  if (s.solved || s.wrong || s.finished || s.placed.includes(tileId) || !s.tiles.some((t) => t.id === tileId)) return s;
  return evaluate({ ...s, placed: [...s.placed, tileId] });
}

export function builderUndo(s: BuilderState): BuilderState {
  if (s.solved || s.finished || s.placed.length === 0) return s;
  return { ...s, placed: s.placed.slice(0, -1), wrong: false };
}

export function builderClearWrong(s: BuilderState): BuilderState {
  return s.wrong ? { ...s, placed: [], wrong: false } : s;
}

/** Gợi ý: bỏ phần đặt sai ở đuôi rồi đặt đúng chữ kế tiếp. Mỗi từ tối đa 3 lần. */
export function builderHint(s: BuilderState): BuilderState {
  if (s.solved || s.finished || s.hints >= BUILDER_MAX_HINTS_PER_WORD) return s;
  const target = chars(builderWord(s));
  let placed = [...s.placed];
  const text = (ids: number[]) => ids.map((id) => s.tiles.find((t) => t.id === id)!.ch);
  while (placed.length > 0 && !text(placed).every((c, i) => same(c, target[i]))) placed = placed.slice(0, -1);
  const need = target[placed.length];
  const tile = s.tiles.find((t) => !placed.includes(t.id) && same(t.ch, need));
  if (!tile) return s;
  return evaluate({ ...s, placed: [...placed, tile.id], hints: s.hints + 1, wrong: false });
}

function record(s: BuilderState, correct: boolean): GameItemResult[] {
  return [...s.items, { card_id: s.words[s.index].id, correct, attempts: s.attempts, hints: s.hints }];
}

/** Bỏ qua từ hiện tại (tính là chưa xếp được). */
export function builderSkip(s: BuilderState, rng: Rng = Math.random): BuilderState {
  if (s.finished) return s;
  return advance({ ...s, items: record(s, false) }, rng);
}

/** Sang từ kế sau khi đã xếp đúng. */
export function builderNext(s: BuilderState, rng: Rng = Math.random): BuilderState {
  if (!s.solved || s.finished) return s;
  return advance({ ...s, items: record(s, true) }, rng);
}

function advance(s: BuilderState, rng: Rng): BuilderState {
  const next = s.index + 1;
  if (next >= s.words.length) return { ...s, finished: true };
  return { ...s, ...startWord(s.words, next, rng) };
}
