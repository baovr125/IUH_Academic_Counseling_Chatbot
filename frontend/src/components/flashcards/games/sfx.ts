/** Âm thanh hiệu ứng ngắn bằng WebAudio (không cần tệp âm thanh). Tắt/bật được, lưu lựa chọn trên trình duyệt. */

const KEY = "iuh_flashcard_game_muted";
let ctx: AudioContext | null = null;

export function isMuted(): boolean {
  try {
    return localStorage.getItem(KEY) === "1";
  } catch {
    return false;
  }
}

export function setMuted(value: boolean): void {
  try {
    localStorage.setItem(KEY, value ? "1" : "0");
  } catch {
    /* trình duyệt chặn lưu trữ: bỏ qua */
  }
}

export type Sfx = "correct" | "wrong" | "win" | "tick";

const TONES: Record<Sfx, { freq: number[]; ms: number; type: OscillatorType }> = {
  correct: { freq: [660, 880], ms: 110, type: "sine" },
  wrong: { freq: [220, 180], ms: 140, type: "triangle" },
  win: { freq: [523, 659, 784, 1047], ms: 130, type: "sine" },
  tick: { freq: [440], ms: 40, type: "square" }
};

export function playSfx(kind: Sfx): void {
  if (isMuted() || typeof window === "undefined") return;
  const Ctor = (window as any).AudioContext || (window as any).webkitAudioContext;
  if (!Ctor) return;
  try {
    ctx = ctx ?? new Ctor();
    const audio = ctx as AudioContext;
    const { freq, ms, type } = TONES[kind];
    let t = audio.currentTime;
    for (const f of freq) {
      const osc = audio.createOscillator();
      const gain = audio.createGain();
      osc.type = type;
      osc.frequency.value = f;
      gain.gain.setValueAtTime(0.0001, t);
      gain.gain.exponentialRampToValueAtTime(0.12, t + 0.01);
      gain.gain.exponentialRampToValueAtTime(0.0001, t + ms / 1000);
      osc.connect(gain).connect(audio.destination);
      osc.start(t);
      osc.stop(t + ms / 1000 + 0.02);
      t += ms / 1000;
    }
  } catch {
    /* âm thanh chỉ là phần thưởng thêm: lỗi thì bỏ qua */
  }
}
