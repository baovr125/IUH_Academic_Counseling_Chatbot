import os
import re
import sys
import json
import subprocess
import numpy as np
import soundfile as sf

def phonetic_vietnamese_clean(text: str) -> str:
    """
    Cleans raw markdown text and phoneticizes all English and technical terms into
    natural Vietnamese pronunciation for Vietnamese TTS models (Vieneu).
    Guarantees no symbols like *, #, **, etc. are spoken out loud.
    """
    s = text

    # 1. Remove markdown section titles and decorative lines
    s = re.sub(r'##\s*PHẦN\s*\d+:.*?\n', '', s)
    s = re.sub(r'---\s*', '', s)

    # 2. Convert markdown bold, italics, code, links, quotes, bullets
    s = re.sub(r'\*\*(.*?)\*\*', r'\1', s)
    s = re.sub(r'\*(.*?)\*', r'\1', s)
    s = re.sub(r'`(.*?)`', r'\1', s)
    s = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', s)
    s = re.sub(r'^[ \t]*[-\*•][ \t]+', '', s, flags=re.MULTILINE)
    s = re.sub(r'^[ \t]*>[ \t]+', '', s, flags=re.MULTILINE)

    # 3. Phonetize technical tags and code fragments
    s = re.sub(r'</retrieved_context>', 'thẻ đóng ri-tri-vừt con-tếch', s)
    s = re.sub(r'<retrieved_context>', 'thẻ mở ri-tri-vừt con-tếch', s)
    s = re.sub(r'<query_reminder>', 'thẻ nhắc câu hỏi kiu-ơ-ri ri-main-đơ', s)
    s = re.sub(r'</query_reminder>', 'thẻ đóng kiu-ơ-ri ri-main-đơ', s)
    s = re.sub(r'<source id=[^>]+>', 'thẻ nguồn soóc ai-đi', s)
    s = re.sub(r'</source>', 'thẻ đóng soóc', s)
    s = re.sub(r'<doc_relevance>YES</doc_relevance>', 'thẻ đốc re-lơ-vân là I-ét', s)
    s = re.sub(r'<doc_relevance>NO</doc_relevance>', 'thẻ đốc re-lơ-vân là Nô', s)
    s = re.sub(r'<doc_relevance>', 'thẻ đốc re-lơ-vân', s)
    s = re.sub(r'</doc_relevance>', 'thẻ đóng đốc re-lơ-vân', s)
    s = re.sub(r'<answer_confidence>HIGH</answer_confidence>', 'thẻ an-sơ con-phi-đần là Hai', s)
    s = re.sub(r'<answer_confidence>', 'thẻ an-sơ con-phi-đần', s)
    s = re.sub(r'</answer_confidence>', 'thẻ đóng an-sơ con-phi-đần', s)
    s = re.sub(r'<conflict_detected>', 'thẻ con-phờ-lích', s)
    s = re.sub(r'</conflict_detected>', 'thẻ đóng con-phờ-lích', s)
    s = re.sub(r'<thinking>', 'thẻ tinh-king', s)
    s = re.sub(r'</thinking>', 'thẻ đóng tinh-king', s)

    # 4. Code references & function names
    s = re.sub(r'\btest_guardrails\.py\b', 'tét gát-rê-u', s)
    s = re.sub(r'\btest_context_sandboxing\.py\b', 'tét con-tếch san-bóc-xinh', s)
    s = re.sub(r'\btest_rrf_algorithm\.py\b', 'tét thuật toán R-R-F', s)
    s = re.sub(r'\btest_self_rag\.py\b', 'tét seo-ph rát', s)
    s = re.sub(r'\bhybrid_chunker\.py\b', 'hai-brít chăn-cơ', s)
    s = re.sub(r'\brag_service\.py\b', 'rát sơ-vít', s)
    s = re.sub(r'\btests/unit/\b', 'thư mục tét u-nít', s)
    s = re.sub(r'\bmatch_chunks_hybrid_rrf\b', 'hàm tìm kiếm lai hợp R-R-F', s)
    s = re.sub(r'\b_sandwich_reorder\b', 'san-uýt ri-o-đơ', s)
    s = re.sub(r'\bmock_redis\.assert_not_called\(\)', 'khẳng định không gọi lệnh ghi đệm', s)
    s = re.sub(r'\bmock_redis\b', 'móc rê-đít', s)
    s = re.sub(r'\bparent_id\b', 'pe-rừn ai-đi', s)
    s = re.sub(r'\bREFUSAL_MESSAGE\b', 'thông báo từ chối an toàn Ri-phiu-zồ', s)
    s = re.sub(r'\bpytest\b', 'Pai-tét', s)
    s = re.sub(r'\[#1,\s*#3,\s*#5,\s*\.\.\.,\s*#4,\s*#2\]', 'tài liệu 1 lên đầu, tài liệu 2 xuống cuối, các tài liệu còn lại nằm ở giữa', s)
    s = re.sub(r'\[1,\s*3,\s*5,\s*4,\s*2\]', '1, 3, 5, 4, 2', s)
    s = re.sub(r'\[1,\s*2,\s*3,\s*4,\s*5\]', '1, 2, 3, 4, 5', s)

    # 5. Paper file names and institutions
    s = re.sub(r'Retrieval-Augmented Generation for Large Language Models: A Survey', 'Tổng quan về các thế hệ mô hình Rát', s)
    s = re.sub(r'Lost in the Middle: How Language Models Use Long Contexts', 'Mất chú ý ở giữa: Cách mô hình sử dụng ngữ cảnh dài', s)
    s = re.sub(r'Corrective Retrieval Augmented Generation \(CRAG\)', 'Mô hình Cờ-Rát sửa lỗi truy xuất', s)
    s = re.sub(r'Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection', 'Mô hình Seo-ph Rát tự phản tư', s)
    s = re.sub(r'Precise Zero-Shot Dense Retrieval without Relevance Labels \(HyDE\)', 'Mô hình Hai-Đi', s)
    s = re.sub(r'check_2312\.10997v5\.pdf', 'bài báo khoa học của tác giả Gao và cộng sự năm 2023', s)
    s = re.sub(r'check_2307\.03172v3\.pdf', 'nghiên cứu của đại học X-ten-phớt', s)
    s = re.sub(r'check_2401\.15884v3\.pdf', 'nghiên cứu Cờ-Rát của Gu-gồ Đíp-Mao', s)
    s = re.sub(r'check_2310\.11511v2\.pdf', 'nghiên cứu Seo-ph Rát của đại học Oa-sinh-tơn', s)
    s = re.sub(r'check_2212\.10496v3\.pdf', 'nghiên cứu Hai-Đi của Đại học Cát-nê-ghi Mê-lơn', s)
    s = re.sub(r'Microsoft Research', 'Mai-cờ-rô-xóp Ri-sơ-ch', s)
    s = re.sub(r'Google DeepMind', 'Gu-gồ Đíp-Mao', s)
    s = re.sub(r'Stanford University|Stanford', 'Đại học X-ten-phớt', s)
    s = re.sub(r'Carnegie Mellon University|Carnegie Mellon', 'Đại học Cát-nê-ghi Mê-lơn', s)
    s = re.sub(r'Rewrite-Retrieve-Read', 'Ri-rái Ri-tri-v Rít', s)

    # 6. Specific English phrases
    s = re.sub(r'\bContext Truncation\b', 'cắt vụn ngữ cảnh', s)
    s = re.sub(r'\bVocabulary Mismatch\b', 'xung đột từ khóa và ngữ nghĩa', s)
    s = re.sub(r'\bHallucination Amplification\b', 'khuếch đại ảo giác', s)
    s = re.sub(r'\bCompound Query Blindness\b', 'bất lực trước câu hỏi kép', s)
    s = re.sub(r'\bEngineering Trade-off\b', 'đánh đổi kỹ thuật', s)
    s = re.sub(r'\bFine-tuning / PPO\b', 'tinh chỉnh mô hình phức tạp', s)
    s = re.sub(r'\bFew-shot Structured Prompting\b', 'kỹ thuật p-rôm có cấu trúc', s)
    s = re.sub(r'\bPrimacy và Recency\b', 'ở đầu và ở cuối', s)
    s = re.sub(r'\bbrute-force permutation\b', 'hoán vị vét cạn', s)
    s = re.sub(r'\bURL nguồn\b', 'địa chỉ nguồn', s)
    s = re.sub(r'\bURL\b', 'u-r-l', s)
    s = re.sub(r'\bSecondary Regex\b', 'biểu thức chính quy rê-gếch phụ', s)
    s = re.sub(r'\bTable-Aware Splitter\b', 'bộ tách bảng Tây-bồ Ơ-que', s)
    s = re.sub(r'\bTable-Aware\b', 'Tây-bồ Ơ-que', s)
    s = re.sub(r'\bAugmented Context\b', 'ngữ cảnh tăng cường óc-men-tịt', s)
    s = re.sub(r'\bHierarchical Augmented Context\b', 'ngữ cảnh tăng cường phân cấp', s)
    s = re.sub(r'\bbreadcrumbs\b', 'đường dẫn bờ-rét-cờ-răm', s)
    s = re.sub(r'\bFrontmatter\b', 'phần đầu phờ-rôn-mát-tơ', s)

    # 7. Numbers, units, percentages, decimals
    s = re.sub(r'1\.15s\b|1\.15 giây\b', '1 phẩy 15 giây', s)
    s = re.sub(r'5ms\b', '5 mili giây', s)
    s = re.sub(r'1\.2s\b|1\.2 giây\b', '1 phẩy 2 giây', s)
    s = re.sub(r'8\.5s\b|8\.5 giây\b', '8 phẩy 5 giây', s)
    s = re.sub(r'1\.5s\b|1\.5 giây\b', '1 phẩy 5 giây', s)
    s = re.sub(r'0\.8s\b|0\.8 giây\b', '0 phẩy 8 giây', s)
    s = re.sub(r'768d\b', '768 chiều', s)
    s = re.sub(r'1200t\b', '1 nghìn 200 tô-cần', s)
    s = re.sub(r'1\.200', '1 nghìn 200', s)
    s = re.sub(r'3\.000', '3 nghìn', s)
    s = re.sub(r'5\.000', '5 nghìn', s)
    s = re.sub(r'30\.000', '30 nghìn', s)
    s = re.sub(r'100%', 'một trăm phần trăm', s)
    s = re.sub(r'64%', 'sáu mươi tư phần trăm', s)
    s = re.sub(r'54%', 'năm mươi tư phần trăm', s)
    s = re.sub(r'76%', 'bảy mươi sáu phần trăm', s)
    s = re.sub(r'0\.93\b', 'không phẩy 93', s)
    s = re.sub(r'0\.88\b', 'không phẩy 88', s)
    s = re.sub(r'0\.80\b', 'không phẩy 80', s)
    s = re.sub(r'0\.60\b', 'không phẩy 60', s)
    s = re.sub(r'0\.25\b', 'không phẩy 25', s)
    s = re.sub(r'0\.10\b', 'không phẩy 10', s)
    s = re.sub(r'0\.0322\b', 'không phẩy không ba hai hai', s)
    s = re.sub(r'0\.0163\b', 'không phẩy không một sáu ba', s)
    s = re.sub(r'k=60\b|k bằng 60\b', 'k bằng 60', s)
    s = re.sub(r'H1 đến H6|H1-H6', 'Hát 1 đến Hát 6', s)

    # 8. Cohorts and University
    s = re.sub(r'\bK19\b', 'khóa 19', s)
    s = re.sub(r'\bK20\b', 'khóa 20', s)
    s = re.sub(r'\bK21\b', 'khóa 21', s)
    s = re.sub(r'\bIUH\b', 'I-U-Hát', s)

    # 9. Core RAG and AI terms
    s = re.sub(r'\bNaive RAG\b', 'Nai-íp Rát', s)
    s = re.sub(r'\bAdvanced RAG\b', 'Át-van-xơ Rát', s)
    s = re.sub(r'\bModular RAG\b', 'Mô-đu-la Rát', s)
    s = re.sub(r'\bSelf-RAG\b', 'Seo-ph Rát', s)
    s = re.sub(r'\bCRAG\b', 'Cờ-Rát', s)
    s = re.sub(r'\bCF-RAG\b', 'C-F Rát', s)
    s = re.sub(r'\bHyDE\b', 'Hai-Đi', s)
    s = re.sub(r'\bRAG\b', 'Rát', s)
    s = re.sub(r'\bAI\b', 'Ây-Ai', s)
    s = re.sub(r'\bLLM\b', 'L-L-M', s)
    s = re.sub(r'\bChatbot\b', 'Chát-bót', s)
    s = re.sub(r'\bAcademic Chatbot\b', 'A-ca-đê-mích Chát-bót', s)

    s = re.sub(r'\bParent Chunks\b', 'các khối cha pe-rừn chăn-k', s)
    s = re.sub(r'\bParent Chunk\b', 'khối cha pe-rừn chăn-k', s)
    s = re.sub(r'\bChild Chunks\b', 'các khối con chai-ồ chăn-k', s)
    s = re.sub(r'\bChild Chunk\b', 'khối con chai-ồ chăn-k', s)
    s = re.sub(r'\bParent-Child\b', 'pe-rừn chai-ồ', s)
    s = re.sub(r'\bParent-Aware Quota Selection\b', 'phân bổ hạn ngạch theo khối cha', s)
    s = re.sub(r'\bParent-Aware Quota Deduplication\b', 'lọc trùng lặp hạn ngạch theo khối cha', s)
    s = re.sub(r'\bQuota Deduplication\b', 'lọc trùng lặp theo hạn ngạch', s)
    s = re.sub(r'\bSmall-to-Big Retrieval\b', 'truy xuất từ nhỏ sang lớn Sờ-mô tu Bích', s)
    s = re.sub(r'\bSmall-to-Big\b', 'Sờ-mô tu Bích', s)

    s = re.sub(r'\b2-Stage Semantic Cache\b', 'bộ đệm ngữ nghĩa hai giai đoạn xê-man-tích cét', s)
    s = re.sub(r'\bSemantic Cache\b', 'bộ đệm ngữ nghĩa xê-man-tích cét', s)
    s = re.sub(r'\bHigh Recall\b', 'Hai Ri-con', s)
    s = re.sub(r'\bHigh Precision\b', 'Hai Pờ-ri-si-sừn', s)
    s = re.sub(r'\bEntity Numbers Guard\b', 'bộ kiểm tra chữ số En-ti-ti Nâm-bơ Gát', s)
    s = re.sub(r'\bGated Write-back\b', 'cổng ghi đệm Gết-tịt Rái-bách', s)
    s = re.sub(r'\bWrite-back\b', 'ghi đệm rái-bách', s)
    s = re.sub(r'\bCache MISS\b|\bCache Miss\b|\bCACHE MISS\b', 'Cét Mít không trúng bộ đệm', s)
    s = re.sub(r'\bCache HIT\b|\bCache Hit\b|\bCACHE HIT\b', 'Cét Hít trúng bộ đệm', s)
    s = re.sub(r'\bCache\b|\bcache\b', 'bộ đệm cét', s)
    s = re.sub(r'\bRedis O\(1\)\b', 'Rê-đít ô một', s)
    s = re.sub(r'\bRedis\b', 'Rê-đít', s)
    s = re.sub(r'\bpgvector\b', 'pê-gờ-véc-tơ', s)
    s = re.sub(r'\bPostgreSQL\b', 'Pốt-gờ-rét', s)

    s = re.sub(r'\bBi-Encoder\b', 'Bai En-cô-đơ', s)
    s = re.sub(r'\bCross-Encoder\b', 'Cờ-rốt En-cô-đơ', s)
    s = re.sub(r'\bEncoder\b', 'En-cô-đơ', s)
    s = re.sub(r'\bReranker\b|\breranker\b', 'Ri-ranh-cơ', s)
    s = re.sub(r'\bBAAI/bge-reranker-v2-m3\b', 'B-G-E Ri-ranh-cơ', s)
    s = re.sub(r'\bBGE-Reranker v2-m3\b|\bBGE-Reranker-v2-m3\b|\bBGE-Reranker\b', 'B-G-E Ri-ranh-cơ', s)
    s = re.sub(r'\bbkai-foundation-models/vietnamese-bi-encoder\b', 'mô hình Bi-En-cô-đơ tiếng Việt', s)
    s = re.sub(r'\bVietnamese Bi-Encoder\b', 'Bi-En-cô-đơ tiếng Việt', s)
    s = re.sub(r'\bHNSW Cosine\b', 'H-N-S-W Cô-sin', s)
    s = re.sub(r'\bHNSW\b', 'H-N-S-W', s)
    s = re.sub(r'\bCosine\b', 'Cô-sin', s)
    s = re.sub(r'\bVector\b|\bvector\b', 'véc-tơ', s)
    s = re.sub(r'\bDense Search\b', 'tìm kiếm véc-tơ dày đặc Đen-sơ', s)
    s = re.sub(r'\bSparse Search\b', 'tìm kiếm từ khóa thưa thớt Sờ-pa-sơ', s)
    s = re.sub(r'\bDense\b', 'Đen-sơ', s)
    s = re.sub(r'\bSparse\b', 'Sờ-pa-sơ', s)
    s = re.sub(r'\bBM25\b', 'B-M 25', s)
    s = re.sub(r'\bfts\b', 'F-T-S', s)
    s = re.sub(r'\bFull-Text Search\b', 'tìm kiếm toàn văn', s)
    s = re.sub(r'\bReciprocal Rank Fusion \(RRF\)\b', 'hợp nhất thứ hạng R-R-F', s)
    s = re.sub(r'\bReciprocal Rank Fusion\b', 'hợp nhất thứ hạng R-R-F', s)
    s = re.sub(r'\bRRF\b', 'R-R-F', s)
    s = re.sub(r'\bFP16\b', 'F-P 16', s)
    s = re.sub(r'\bONNX\b', 'O-N-N-X', s)
    s = re.sub(r'\bQwen-2\.5\b|\bQwen 2\.5\b|\bQwen\b', 'Kiu-en 2 chấm 5', s)

    s = re.sub(r'\bLost-in-the-Middle\b|\bLost in the Middle\b', 'mất tập trung ở giữa Lót in đơ Mít-đồ', s)
    s = re.sub(r'\bSandwich Reordering\b', 'hoán vị bánh kẹp San-uýt Ri-o-đơ-ring', s)
    s = re.sub(r'\bXML Sandboxing\b', 'buồng cách ly Ích-Em-Eo San-bóc-xinh', s)
    s = re.sub(r'\bSandboxing\b', 'buồng cách ly san-bóc-xinh', s)
    s = re.sub(r'\bXML\b', 'Ích-Em-Eo', s)
    s = re.sub(r'\bPrompt Injection\b', 'tấn công tiêm mã p-rôm in-dếch-sừn', s)
    s = re.sub(r'\bPrompt\b|\bprompt\b', 'p-rôm', s)
    s = re.sub(r'\bPrompts\b|\bprompts\b', 'các p-rôm', s)
    s = re.sub(r'\bSpatioRoute\b', 'Sờ-pa-ti-ô Rút', s)
    s = re.sub(r'\bREGULATION\b', 'Réc-gu-lây-sừn quy chế', s)
    s = re.sub(r'\bArithmetic Chain-of-Thought\b', 'chuỗi suy nghĩ số học Chên ợp Thót', s)
    s = re.sub(r'\bChain-of-Thought\b', 'chuỗi suy nghĩ Chên ợp Thót', s)

    s = re.sub(r'\bAutomated Unit Tests\b', 'kiểm thử đơn vị tự động U-nít Tét', s)
    s = re.sub(r'\bUnit Tests\b|\bUnit tests\b|\bunit tests\b', 'U-nít Tét', s)
    s = re.sub(r'\bTest suites\b|\btest suites\b|\btest suite\b', 'các bộ tét suýt', s)
    s = re.sub(r'\bPASS 100%\b|\bPASSED\b', 'vượt qua một trăm phần trăm', s)
    s = re.sub(r'\bPASS\b', 'vượt qua', s)

    s = re.sub(r'\bToken\b|\btoken\b|\btokens\b', 'tô-cần', s)
    s = re.sub(r'\bChunk\b|\bchunk\b', 'khối chăn-k', s)
    s = re.sub(r'\bChunks\b|\bchunks\b', 'các khối chăn-k', s)
    s = re.sub(r'\bWeb Search\b', 'tìm kiếm mạng oét', s)
    s = re.sub(r'\bOffline\b', 'ọp-lai', s)
    s = re.sub(r'\bPipeline\b', 'quy trình pai-lai', s)
    s = re.sub(r'\bFramework\b', 'khung ph-rêm-uốc', s)
    s = re.sub(r'\bCodebase\b', 'mã nguồn', s)
    s = re.sub(r'\bRegex\b', 'biểu thức chính quy rê-gếch', s)
    s = re.sub(r'\bMarkdown\b', 'mác-đao', s)
    s = re.sub(r'\bSHA-256\b', 'mã băm S-H-A 256', s)
    s = re.sub(r'\bNon-IT\b', 'không chuyên công nghệ', s)
    s = re.sub(r'\bYES\b', 'I-ét', s)
    s = re.sub(r'\bNO\b', 'Nô', s)
    s = re.sub(r'\bHIGH\b', 'Hai', s)

    # 10. Clean any leftover symbols like #, *, _, ~, `, ^, |, <, >, {, }, [, ], \
    s = re.sub(r'[*#_~`^|<>{}\[\]\\]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()

    return s

def split_into_clean_sentences(text: str):
    text = re.sub(r'\s+', ' ', text).strip()
    raw_sentences = re.split(r'(?<=[.!?])\s+', text)
    sentences = []
    for s in raw_sentences:
        s = s.strip()
        if not s:
            continue
        if len(s) > 150:
            sub_parts = re.split(r'(?<=[,;:])\s+', s)
            curr = ""
            for p in sub_parts:
                if len(curr) + len(p) + 1 <= 140:
                    curr = f"{curr} {p}".strip()
                else:
                    if curr:
                        sentences.append(curr)
                    curr = p
            if curr:
                sentences.append(curr)
        else:
            sentences.append(s)
    return sentences

def parse_and_clean_voiceover(script_path: str):
    with open(script_path, "r", encoding="utf-8") as f:
        content = f.read()

    sections = re.split(r"## PHẦN (\d+):", content)
    scenes = {}
    for i in range(1, len(sections), 2):
        sec_num = int(sections[i])
        sec_text = sections[i+1].strip()
        lines = sec_text.splitlines()
        title = lines[0].strip()
        body = "\n".join(lines[1:]).strip()

        clean_body = phonetic_vietnamese_clean(body)

        scenes[f"scene{sec_num}"] = {
            "num": sec_num,
            "raw_title": title,
            "clean_body": clean_body
        }
    return scenes

def main():
    script_path = "video/voiceover-script.md"
    out_dir = "video/public/audio"
    os.makedirs(out_dir, exist_ok=True)

    print("Parsing and cleaning voiceover script for Vietnamese TTS...")
    scenes = parse_and_clean_voiceover(script_path)
    print(f"Loaded and cleaned {len(scenes)} scenes.")

    with open("video/public/audio/cleaned_voiceover_debug.txt", "w", encoding="utf-8") as f:
        for sid, d in scenes.items():
            f.write(f"=== {sid.upper()} ===\n{d['clean_body']}\n\n")
    print("Saved phonetic preview to video/public/audio/cleaned_voiceover_debug.txt")

    print("\nLoading Vieneu TTS model (mode=v3nano, voice=Minh Quân)...")
    from vieneu import Vieneu
    tts = Vieneu(mode="v3nano")
    voice_name = "Minh Quân"
    print("Vieneu loaded successfully on device.")

    durations = {}

    for scene_id, data in scenes.items():
        print(f"\n==========================================")
        print(f"Generating Audio for {scene_id.upper()}")
        print(f"==========================================")

        wav_path = os.path.join(out_dir, f"{scene_id}.wav")
        mp3_path = os.path.join(out_dir, f"{scene_id}.mp3")

        sentences = split_into_clean_sentences(data["clean_body"])
        print(f"Total sentence chunks: {len(sentences)}")

        audio_segments = []
        sample_rate = 24000

        for idx, sentence in enumerate(sentences, 1):
            if not sentence.strip():
                continue
            try:
                seg_audio = tts.infer(sentence, voice=voice_name)
                if hasattr(seg_audio, "cpu"):
                    seg_audio = seg_audio.cpu().numpy()
                elif hasattr(seg_audio, "numpy"):
                    seg_audio = seg_audio.numpy()

                audio_segments.append(seg_audio)
                silence = np.zeros(int(sample_rate * 0.18), dtype=seg_audio.dtype)
                audio_segments.append(silence)
                print(f"  [{idx}/{len(sentences)}] ({len(sentence)} chars) OK")
            except Exception as e:
                print(f"  [{idx}/{len(sentences)}] Error: {e}")

        if not audio_segments:
            print(f"Error: No audio segments generated for {scene_id}!")
            continue

        full_audio = np.concatenate(audio_segments)
        sf.write(wav_path, full_audio, sample_rate)
        duration_sec = len(full_audio) / sample_rate
        print(f"Saved WAV: {wav_path} ({duration_sec:.2f}s)")

        cmd = [
            "ffmpeg", "-y", "-i", wav_path,
            "-b:a", "192k",
            "-ar", "44100",
            mp3_path
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

        frames_30 = int(round(duration_sec * 30))
        frames_60 = int(round(duration_sec * 60))
        durations[scene_id] = {
            "duration": round(duration_sec, 3),
            "frames30": frames_30,
            "frames60": frames_60,
            "title": data["raw_title"]
        }
        print(f"Converted MP3: {duration_sec:.2f}s (~{frames_30} frames @ 30fps, ~{frames_60} frames @ 60fps)")

    durations_file = "video/src/data/audioDurations.json"
    os.makedirs(os.path.dirname(durations_file), exist_ok=True)
    with open(durations_file, "w", encoding="utf-8") as f:
        json.dump(durations, f, indent=2, ensure_ascii=False)
    print(f"\nWrote durations metadata to {durations_file}")
    print("ALL SCENES COMPLETED SUCCESSFULLY!")

if __name__ == "__main__":
    main()
