# Lịch sử git theo tuần (gợi ý cho Nhật ký làm việc)

Tổng 191 commit.

## Tuần 08/06/2026 – 14/06/2026: 1 commit (Baovr125)

- Làm mới toàn bộ mã nguồn

## Tuần 15/06/2026 – 21/06/2026: 5 commit (Baovr125, Hao0107)

- chunking strategies (incomplete)
- Restructure project
- Restructure project
- Restructure project
- Cập nhật lại toàn bộ cấu trúc dự án

## Tuần 06/07/2026 – 12/07/2026: 6 commit (Baovr125)

- final Retrival
- update Retrival
- update Retrival
- Test Retrieval
- Test Retrieval
- Test Retrieval

## Tuần 27/07/2026 – 02/08/2026: 6 commit (AnhHao0107, Baovr125, Trần Anh Hào)

- Merge pull request #1 from baovr125/chatbot_deploy
- Add chatbot demo use gemini api
- update
- update
- push on to supabase
- Update fontend

## Tuần 03/08/2026 – 09/08/2026: 30 commit (AnhHao0107, Baovr125, Trần Anh Hào)

- add Semantic cache (first version)
- update source
- fix some minor text error
- remove unuse files
- add package.json
- Merge pull request #2 from baovr125/chatbot
- modify .gitignore
- chore: ignore .agent directory and remove from tracking
- update PROJECT_LOG.md
- Update `useChat` to expose pagination state (`hasMoreMessages`, `loadMoreMessages`) Modify `ChatPage` to trigger message loading when scrolling to the top Add "Load More" controls and pagination to `ChatHistoryPanel` Fix TypeScript type checking error in `AnalyticsPage` (bypassed strict typing issue on API result)
- Load only conversation metadata initially lazy-load messages when user clicks a session
- feat: implement structured logging, rate limiting, and analytics dashboard
- … và 18 commit khác

## Tuần 10/08/2026 – 16/08/2026: 23 commit (AnhHao0107, Baovr125, Trần Anh Hào)

- aklsjdf
- Merge main into Bao
- fix bug security
- Merge pull request #4 from baovr125/semantic-cache
- modify dockerfile torch lib add supabase embedder fix logs duplicate, minor error in rag pipeline
- update system
- fix bug
- fix bug
- finish crawl and extract information pipeline add hybrid chunking and script to visualize it.
- update voi
- Update neural voi
- update realtime translation
- … và 11 commit khác

## Tuần 17/08/2026 – 23/08/2026: 14 commit (AnhHao0107, Baovr125, Trần Anh Hào)

- add retrived chunks logs function for debuging
- feat: setup automated test suites and ci cd quality gates
- fix bug
- update
- Merge pull request #8 from baovr125/Bao
- fix bug
- update
- add README.md to data_pipeline
- update network
- update sercurity
- update doc translation
- update voice
- … và 2 commit khác

## Tuần 24/08/2026 – 30/08/2026: 21 commit (AnhHao0107, Baovr125, Trần Anh Hào)

- fix(ci): upgrade node to v22 and add robust dependency installation
- update redme
- fix bug doc translation
- fix(ci): upgrade node to v22 and add robust dependency installation
- update redme
- fix bug doc translation
- Change frontend hardcoded "localhost" to VITE_API_BASE_URL Hide admin token in logs
- Merge Bao into main
- resolve docker-compose duplicate cause by auto merge
- Merge pull request #9 from baovr125/semantic-cache
- Merge branch 'main' into semantic-cache
- Add search feature to admin page Change OCR module to pymupdf Change out of quota log from exception to warning
- … và 9 commit khác

## Tuần 31/08/2026 – 06/09/2026: 4 commit (AnhHao0107, Trần Anh Hào)

- Merge pull request #12 from baovr125/semantic-cache
- Merge pull request #11 from baovr125/Bao
- Merge pull request #10 from baovr125/main
- CI test

## Tuần 07/09/2026 – 13/09/2026: 3 commit (AnhHao0107, Baovr125)

- delete unused code
- Cập nhật file .gitignore
- update doc translation service and admin

## Tuần 14/09/2026 – 20/09/2026: 2 commit (Baovr125)

- update source
- update source

## Tuần 21/09/2026 – 27/09/2026: 2 commit (Baovr125)

- update realtime
- update realtime

## Tuần 28/09/2026 – 04/10/2026: 5 commit (AnhHao0107, Baovr125)

- update automation testing
- Change in semantic cache - Implement 2 stage cache - first step use bi-encoder - second use CROSS-ENCODER RERANKER
- Modulize LLM model for 2 stage "rewrite query" and "Answer gen" Add original query to log file Change rewrite query model to Local LLM Add fallback for off topic after rewrite stage
- changed log system (add time stamp, token usage,...) changed LLM generate module to local LLM New LLM provider to navigate between local and API call LLMs.
- update automation testing

## Tuần 05/10/2026 – 11/10/2026: 11 commit (AnhHao0107, Baovr125, Trần Anh Hào)

- Save local realtime translation work
- Merge main into Bao keeping local frontend and realtime changes
- UI: Add regenerate button for user ì they not happy with cache answer System: Add model name, date into log file RAG: Modify LLM gen prompt
- Merge main into Bao
- Save local realtime translation work
- fix UI error where <thinking> not hidden.
- Use Runpod vLLM to create API for LLM service change prompt to fit Qwen 3.6 35B fix llm_providers issues add {"enable_thinking": False} to prevent Qwen 3.6 from CoT.
- Restore all-in-one docker-compose for Runpod Ubuntu Template
- change docker file to fit vLLM
- Merge pull request #14 from baovr125/semantic-cache
- add docker-compose prod prepare for runpod deploy

## Tuần 12/10/2026 – 18/10/2026: 26 commit (AnhHao0107, Baovr125, Trần Anh Hào)

- refactor: shrink prompt size in "REGULATION"
- chore: delete junk files & ignore .bat / .sh test files
- feat: block prompt injection tags and special tokens (#17)
- Merge pull request #16 from baovr125/lostinthemiddle
- Upgrade: Sort retrieved chunk to [#1, #3, #5, ..., #4, #2] to avoid lost in the middle problem add user query to the end of prompt (after <retrieved_context>)
- Merge branch 'main' of https://github.com/baovr125/IUH_Academic_Counseling_Chatbot into semantic-cache
- Fix: reranker 2 time error raise reranker_threshold to 0.20 to avoid unrelevant chunks
- Use the IUH mark as the sidebar logo
- Harden auth service and gateway; redesign login/register UI
- Rework language detection and domain detection for realtime translation
- Upgrade: New crawl pipeline - crawl more site - remove max pages - Add recursive chunk to prevent "too large" parent chunks
- feat: add Parent-Aware Quota Selection in retrieval stage fix: timeout for supabase client
- … và 14 commit khác

## Tuần 19/10/2026 – 25/10/2026: 9 commit (AnhHao0107, Baovr125)

- chore: modify report
- chore: modify system architech report
- chore: add system architech report
- chore: correcting Local LLM model ==> "QuantTrio/Qwen3.6-35B-A3B-AWQ" delete video/ folder from codebase
- chore: add video/ paper/ to .gitignore
- update service flashcard and realtime
- chore: add video/ paper/ to .gitignore
- Merge origin/main into Bao
- update service flashcard and realtime

## Tuần 26/10/2026 – 01/11/2026: 23 commit (AnhHao0107, BaoHocHoi, Baovr125, Trần Anh Hào)

- feat(frontend): giao diện responsive, hệ màu trắng-xanh và khung liền
- Merge pull request #22 from baovr125/docs/deploy-guide
- docs: thêm chế độ tiết kiệm VRAM (card 6 GB) và hướng dẫn chạy song song hai máy
- docs: thêm DEPLOY_QUICKSTART.md hướng dẫn từng bước kèm ngữ cảnh cho người chưa biết dự án
- docs: thêm DEPLOY.md hướng dẫn tự triển khai demo và script kiểm tra deploy_smoke.py
- Merge pull request #21 from baovr125/deploy/demo
- deploy: lớp phủ docker-compose.prod.yml và cấu hình demo công khai qua tunnel
- feat: khóa tính năng Dịch tài liệu khi không triển khai doc-translation
- feat: add vercel.json - prepare for deploy
- Merge pull request #20 from baovr125/Bao
- test: sửa hai check CI đang lỗi sẵn trên main (doc_translation, realtime)
- config: đưa tên model, URL công khai và nguồn crawl vào cấu hình dùng chung
- … và 11 commit khác
