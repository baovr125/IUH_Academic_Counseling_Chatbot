-- ====================================================================================
-- 006_flashcard_games.sql  —  Trò chơi ôn từ vựng (Ghép cặp / Đua 60 giây / Xếp chữ) (chạy trên Supabase SQL Editor)
--
-- flashcard_game_sessions: mỗi dòng là MỘT ván chơi đã kết thúc. Điểm, sao, XP do MÁY CHỦ tự tính từ kết quả từng câu
-- (client không gửi điểm), nên bảng này là nguồn sự thật cho kỷ lục cá nhân, XP và cấp độ.
--
-- AN TOÀN: chỉ THÊM bảng; không đụng dữ liệu hiện có; chạy lại nhiều lần vẫn được (idempotent).
-- Chưa chạy file này thì mọi tính năng cũ vẫn hoạt động; riêng API /games trả 503 MIGRATION_REQUIRED kèm hướng dẫn.
-- ====================================================================================

CREATE TABLE IF NOT EXISTS flashcard_game_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    deck_id UUID REFERENCES flashcard_decks(id) ON DELETE SET NULL,     -- xóa sổ thì giữ lịch sử điểm
    lang_code VARCHAR(10) NOT NULL,                                     -- ngôn ngữ của sổ lúc chơi (máy chủ tự lấy)
    game VARCHAR(16) NOT NULL CHECK (game IN ('match', 'speed', 'builder', 'shooter')),
    mode VARCHAR(16) NOT NULL CHECK (mode IN ('relax', 'challenge')),
    client_request_id VARCHAR(64) NOT NULL,                             -- chống ghi trùng khi gửi lại
    total INT NOT NULL CHECK (total >= 0),                              -- số câu/cặp/từ
    correct INT NOT NULL CHECK (correct >= 0),
    mistakes INT NOT NULL DEFAULT 0 CHECK (mistakes >= 0),
    hints INT NOT NULL DEFAULT 0 CHECK (hints >= 0),
    best_combo INT NOT NULL DEFAULT 0 CHECK (best_combo >= 0),
    duration_ms INT NOT NULL DEFAULT 0 CHECK (duration_ms >= 0),
    score INT NOT NULL DEFAULT 0 CHECK (score >= 0),
    stars SMALLINT NOT NULL DEFAULT 0 CHECK (stars BETWEEN 0 AND 3),
    xp INT NOT NULL DEFAULT 0 CHECK (xp >= 0),
    applied_review BOOLEAN NOT NULL DEFAULT FALSE,                      -- người chơi có bật "Tính vào lịch ôn" không
    reviewed_count INT NOT NULL DEFAULT 0 CHECK (reviewed_count >= 0),  -- số thẻ thực sự được cập nhật lịch ôn (FSRS)
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_game_sessions_user_request
    ON flashcard_game_sessions (user_id, client_request_id);
CREATE INDEX IF NOT EXISTS idx_game_sessions_user_game
    ON flashcard_game_sessions (user_id, game, mode, score DESC);
CREATE INDEX IF NOT EXISTS idx_game_sessions_user_created
    ON flashcard_game_sessions (user_id, created_at DESC);

-- Bảo mật nhất quán với 002_auth_hardening.sql: bật RLS, không tạo policy => chỉ service_role truy cập được.
ALTER TABLE flashcard_game_sessions ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON flashcard_game_sessions FROM anon, authenticated;
GRANT ALL ON flashcard_game_sessions TO service_role;

-- ====================================================================================
-- ROLLBACK (đang để dạng comment):
--   DROP TABLE IF EXISTS flashcard_game_sessions;
-- ====================================================================================
