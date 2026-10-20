-- ====================================================================================
-- 007_flashcard_game_shooter.sql  —  Thêm trò "Bắn bóng nghĩa" (shooter) vào bảng ván chơi (chạy trên Supabase SQL Editor)
--
-- Chỉ đổi ràng buộc CHECK của cột game để cho phép giá trị 'shooter'. Không đụng dữ liệu hiện có.
-- Chạy lại nhiều lần vẫn được (idempotent). Cần đã chạy 006_flashcard_games.sql trước.
-- Chưa chạy file này thì 3 trò cũ vẫn hoạt động; riêng việc LƯU ván "Bắn bóng nghĩa" trả 503 MIGRATION_REQUIRED.
-- ====================================================================================

ALTER TABLE flashcard_game_sessions DROP CONSTRAINT IF EXISTS flashcard_game_sessions_game_check;
ALTER TABLE flashcard_game_sessions
    ADD CONSTRAINT flashcard_game_sessions_game_check CHECK (game IN ('match', 'speed', 'builder', 'shooter'));

-- ====================================================================================
-- ROLLBACK (đang để dạng comment; xóa các ván 'shooter' trước khi đặt lại ràng buộc cũ):
--   DELETE FROM flashcard_game_sessions WHERE game = 'shooter';
--   ALTER TABLE flashcard_game_sessions DROP CONSTRAINT IF EXISTS flashcard_game_sessions_game_check;
--   ALTER TABLE flashcard_game_sessions ADD CONSTRAINT flashcard_game_sessions_game_check CHECK (game IN ('match', 'speed', 'builder'));
-- ====================================================================================
