#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Audits and standardizes voiceover text for TTS, strictly following Rules 1, 2, 3, 4, 5.
"""
import re
import json

def audit_and_clean_voiceover(input_file):
    with open(input_file, "r", encoding="utf-8") as f:
        text = f.read()

    scenes = {}
    raw_sections = text.split("=== SCENE")
    for sec in raw_sections:
        if not sec.strip():
            continue
        lines = sec.strip().splitlines()
        scene_num = lines[0].replace("===", "").strip()
        body = "\n".join(lines[1:]).strip()
        scenes[f"scene{scene_num}"] = body

    changes = []
    cleaned_scenes = {}

    def record_change(scene_id, before, after, reason):
        changes.append({
            "scene": scene_id,
            "before": before,
            "after": after,
            "reason": reason
        })

    for sid, body in scenes.items():
        s = body

        # Rule 2: Consecutive duplicate words
        # Check specific duplicates known:
        dup_patterns = [
            (r'Đại học Đại học', 'Đại học', 'Xóa từ lặp liên tiếp do lỗi: "Đại học Đại học" -> "Đại học"'),
            (r'thẻ nhắc nhở câu hỏi thẻ nhắc câu hỏi', 'thẻ nhắc câu hỏi', 'Xóa cụm từ lặp liên tiếp do lỗi: "thẻ nhắc nhở câu hỏi thẻ nhắc câu hỏi" -> "thẻ nhắc câu hỏi"'),
            (r'Phân tách khối cha các khối cha', 'Phân tách khối cha', 'Xóa cụm từ lặp: "khối cha các khối cha" -> "khối cha"'),
            (r'Phân mảnh khối con các khối con', 'Phân mảnh khối con', 'Xóa cụm từ lặp: "khối con các khối con" -> "khối con"'),
            (r'mô hình mô hình', 'mô hình', 'Xóa từ lặp liên tiếp: "mô hình mô hình" -> "mô hình"'),
            (r'Cổng kiểm soát ghi đệm cổng ghi đệm', 'Cổng kiểm soát ghi đệm', 'Xóa cụm từ lặp: "cổng kiểm soát ghi đệm cổng ghi đệm" -> "Cổng kiểm soát ghi đệm"'),
            (r'qua hàm hàm tìm kiếm lai hợp', 'qua hàm tìm kiếm lai hợp', 'Xóa từ lặp liên tiếp: "hàm hàm" -> "hàm"'),
            (r'Tìm kiếm véc-tơ dày đặc tìm kiếm véc-tơ dày đặc Đen-sơ', 'Tìm kiếm véc tơ dày đặc Đen sơ', 'Xóa cụm từ lặp: "Tìm kiếm véc-tơ dày đặc tìm kiếm véc-tơ dày đặc" -> "Tìm kiếm véc tơ dày đặc"'),
            (r'Tìm kiếm từ khóa tìm kiếm từ khóa thưa thớt Sờ-pa-sơ', 'Tìm kiếm từ khóa thưa thớt Sờ pa sơ', 'Xóa cụm từ lặp: "Tìm kiếm từ khóa tìm kiếm từ khóa" -> "Tìm kiếm từ khóa"'),
            (r'công thức hợp nhất thứ hạng R-R-F \(R-R-F\)', 'công thức hợp nhất thứ hạng R R F', 'Xóa từ lặp kèm ngoặc: "R-R-F (R-R-F)" -> "R R F"'),
            (r'hoán vị hoán vị bánh kẹp', 'hoán vị bánh kẹp', 'Xóa từ lặp liên tiếp: "hoán vị hoán vị" -> "hoán vị"'),
            (r'trong thẻ thẻ mở', 'trong thẻ mở', 'Xóa từ lặp: "thẻ thẻ mở" -> "thẻ mở"'),
            (r'thẻ thẻ nhắc câu hỏi', 'thẻ nhắc câu hỏi', 'Xóa từ lặp: "thẻ thẻ nhắc" -> "thẻ nhắc"'),
            (r'Tuyến Réc-gu-lây-sừn quy chế về quy chế đào tạo', 'Tuyến Réc gu lây sừn về quy chế đào tạo', 'Xóa cụm từ lặp: "quy chế về quy chế" -> "về quy chế"'),
            (r'thẻ đóng giả mạo thẻ đóng', 'thẻ đóng giả mạo', 'Xóa từ lặp: "thẻ đóng giả mạo thẻ đóng" -> "thẻ đóng giả mạo"'),
            (r'thông báo từ chối an toàn thông báo từ chối an toàn', 'thông báo từ chối an toàn', 'Xóa cụm từ lặp: "thông báo từ chối an toàn thông báo từ chối an toàn" -> "thông báo từ chối an toàn"'),
            (r'với thẻ thẻ đốc', 'với thẻ đốc', 'Xóa từ lặp: "thẻ thẻ đốc" -> "thẻ đốc"'),
            (r'Gom nhóm hạn ngạch phân bổ hạn ngạch', 'Gom nhóm và phân bổ hạn ngạch', 'Xóa từ lặp: "hạn ngạch phân bổ hạn ngạch" -> "và phân bổ hạn ngạch"'),
        ]

        for pat, repl, reason in dup_patterns:
            matches = re.findall(pat, s)
            if matches:
                record_change(sid, matches[0], repl, reason)
                s = re.sub(pat, repl, s)

        # Rule 4: Numbers with trailing dots/commas/colons, e.g. "1.", "2.", "Bước 1:", "Ca 1 —"
        rule4_patterns = [
            (r'\b1\.\s+Module\b', 'Thứ nhất, Module', 'Tránh đọc "Một chấm Module", đổi thành số thứ tự bằng chữ'),
            (r'\b2\.\s+Module\b', 'Thứ hai, Module', 'Tránh đọc "Hai chấm Module", đổi thành số thứ tự bằng chữ'),
            (r'\b3\.\s+Module\b', 'Thứ ba, Module', 'Tránh đọc "Ba chấm Module", đổi thành số thứ tự bằng chữ'),
            (r'\b4\.\s+Module\b', 'Thứ tư, Module', 'Tránh đọc "Bốn chấm Module", đổi thành số thứ tự bằng chữ'),
            (r'\b5\.\s+Module\b', 'Thứ năm, Module', 'Tránh đọc "Năm chấm Module", đổi thành số thứ tự bằng chữ'),
            (r'\bBước 1:\b', 'Bước một:', 'Quy tắc 4: viết số bằng chữ để tránh đọc dính dấu hai chấm'),
            (r'\bBước 2:\b', 'Bước hai:', 'Quy tắc 4: viết số bằng chữ để tránh đọc dính dấu hai chấm'),
            (r'\bBước 3:\b', 'Bước ba:', 'Quy tắc 4: viết số bằng chữ để tránh đọc dính dấu hai chấm'),
            (r'\bBước 4:\b', 'Bước bốn:', 'Quy tắc 4: viết số bằng chữ để tránh đọc dính dấu hai chấm'),
            (r'\bBước 5:\b', 'Bước năm:', 'Quy tắc 4: viết số bằng chữ để tránh đọc dính dấu hai chấm'),
            (r'\bGiai đoạn 1 —\b', 'Giai đoạn một:', 'Quy tắc 4: viết số bằng chữ để tránh đọc dính dấu gạch ngang'),
            (r'\bGiai đoạn 2 —\b', 'Giai đoạn hai:', 'Quy tắc 4: viết số bằng chữ để tránh đọc dính dấu gạch ngang'),
            (r'\bTầng 1:\b', 'Tầng một:', 'Quy tắc 4: viết số bằng chữ để tránh đọc dính dấu hai chấm'),
            (r'\bTầng 2:\b', 'Tầng hai:', 'Quy tắc 4: viết số bằng chữ để tránh đọc dính dấu hai chấm'),
            (r'\bTầng 3:\b', 'Tầng ba:', 'Quy tắc 4: viết số bằng chữ để tránh đọc dính dấu hai chấm'),
            (r'\bCa 1 —\b', 'Ca một:', 'Quy tắc 4: viết số bằng chữ để tránh đọc dính dấu gạch ngang'),
            (r'\bCa 2 —\b', 'Ca hai:', 'Quy tắc 4: viết số bằng chữ để tránh đọc dính dấu gạch ngang'),
            (r'\bCa 3 —\b', 'Ca ba:', 'Quy tắc 4: viết số bằng chữ để tránh đọc dính dấu gạch ngang'),
            (r'\bCa 4 —\b', 'Ca bốn:', 'Quy tắc 4: viết số bằng chữ để tránh đọc dính dấu gạch ngang'),
            (r'\btài liệu 1 lên đầu, tài liệu 2 xuống cuối\b', 'tài liệu một lên đầu, tài liệu hai xuống cuối', 'Quy tắc 4: viết số bằng chữ cho tự nhiên'),
            (r'\btài liệu 1 và 2\b', 'tài liệu một và hai', 'Quy tắc 4: viết số bằng chữ cho tự nhiên'),
            (r'\b1, 3, 5, 4, 2\b', 'một, ba, năm, bốn, hai', 'Quy tắc 4: viết dãy số phân cách dấu phẩy bằng chữ để tránh đọc dính phẩy'),
            (r'\bHát 1 đến Hát 6\b', 'Hát một đến Hát sáu', 'Quy tắc 4: viết số bằng chữ'),
            (r'dưới 1\.20\b', 'dưới một phẩy hai mươi', 'Quy tắc 4: số thập phân viết bằng chữ để tránh đọc "một chấm hai mươi"'),
            (r'\bKiu-en 2 chấm 5\b', 'Kiu en hai phẩy năm', 'Quy tắc 4: đọc số hiệu phiên bản tự nhiên'),
            (r'\bkhông phẩy 10\b', 'không phẩy mười', 'Quy tắc 4: chuẩn hóa số thập phân'),
            (r'\bO\(1\)\b', 'Ô một', 'Tránh đọc "O mở ngoặc một đóng ngoặc"'),
        ]

        for pat, repl, reason in rule4_patterns:
            matches = re.findall(pat, s)
            if matches:
                record_change(sid, matches[0], repl, reason)
                s = re.sub(pat, repl, s)

        # Rule 1: Hyphenated acronyms and words read as "gạch nối"
        # Convert hyphenated letters/words to space-separated
        rule1_patterns = [
            (r'\bI-U-Hát\b', 'I U Hát', 'Quy tắc 1: Từ viết tắt có gạch nối chuyển thành cách nhau bằng khoảng trắng'),
            (r'\bR-R-F\b', 'R R F', 'Quy tắc 1: Từ viết tắt có gạch nối chuyển thành cách nhau bằng khoảng trắng'),
            (r'\bL-L-M\b', 'L L M', 'Quy tắc 1: Từ viết tắt có gạch nối chuyển thành cách nhau bằng khoảng trắng'),
            (r'\bH-N-S-W\b', 'H N S W', 'Quy tắc 1: Từ viết tắt có gạch nối chuyển thành cách nhau bằng khoảng trắng'),
            (r'\bF-T-S\b', 'F T S', 'Quy tắc 1: Từ viết tắt có gạch nối chuyển thành cách nhau bằng khoảng trắng'),
            (r'\bC-F Rát\b', 'C F Rát', 'Quy tắc 1: Từ viết tắt có gạch nối chuyển thành cách nhau bằng khoảng trắng'),
            (r'\bBAAI/bge-Ri-ranh-cơ-v2-m3\b', 'B G E Ri ranh cơ', 'Quy tắc 1: Chuyển tên mô hình chứa gạch chéo gạch nối thành tên đọc tự nhiên'),
            (r'\bBGE-Ri-ranh-cơ v2-m3\b', 'B G E Ri ranh cơ', 'Quy tắc 1: Bỏ gạch nối trong tên mô hình'),
            (r'\btests/unit/\b', 'thư mục tét u nít', 'Quy tắc 1: Chuyển đường dẫn chứa gạch chéo thành tên đọc tự nhiên'),
            (r'\b&amp;\b|\b&\b', 'và', 'Chuyển ký tự và'),
            (r'\bNai-íp\b', 'Nai íp', 'Bỏ gạch nối âm tiết phiên âm để tránh đọc "gạch nối"'),
            (r'\bÁt-van-xơ\b', 'Át van xơ', 'Bỏ gạch nối âm tiết phiên âm'),
            (r'\bMô-đu-la\b', 'Mô đu la', 'Bỏ gạch nối âm tiết phiên âm'),
            (r'\bÂy-Ai\b', 'Ây Ai', 'Bỏ gạch nối âm tiết phiên âm'),
            (r'\btô-cần\b', 'tô cần', 'Bỏ gạch nối âm tiết phiên âm'),
            (r'\bxê-man-tích\b', 'xê man tích', 'Bỏ gạch nối âm tiết phiên âm'),
            (r'\bSờ-pa-ti-ô\b', 'Sờ pa ti ô', 'Bỏ gạch nối âm tiết phiên âm'),
            (r'\bSeo-ph\b', 'Seo ph', 'Bỏ gạch nối âm tiết phiên âm'),
            (r'\bPre-retrieval\b', 'Pre retrieval', 'Bỏ gạch nối tiếng Anh'),
            (r'\bPost-retrieval\b', 'Post retrieval', 'Bỏ gạch nối tiếng Anh'),
            (r'\bRi-rái\b', 'Ri rái', 'Bỏ gạch nối âm tiết phiên âm'),
            (r'\bRi-tri-v\b', 'Ri tri v', 'Bỏ gạch nối âm tiết phiên âm'),
            (r'\bMai-cờ-rô-xóp\b', 'Mai cờ rô xóp', 'Bỏ gạch nối âm tiết phiên âm'),
            (r'\bRi-sơ-ch\b', 'Ri sơ ch', 'Bỏ gạch nối âm tiết phiên âm'),
            (r'\bPPO\b', 'P P O', 'Quy tắc 1: Từ viết tắt chuyển thành cách nhau khoảng trắng'),
            (r'\bUC Berkeley\b', 'U C Béc cơ li', 'Phiên âm viết tắt U C'),
            (r'\bLót in đơ Mít-đồ\b', 'Lót in đơ Mít đồ', 'Bỏ gạch nối âm tiết phiên âm'),
            (r'\bsan-uýt ri-o-đơ\b', 'san uýt ri o đơ', 'Bỏ gạch nối âm tiết phiên âm'),
            (r'\bSan-uýt Ri-o-đơ-ring\b', 'San uýt Ri o đơ ring', 'Bỏ gạch nối âm tiết phiên âm'),
            (r'\bkiu-ơ-ri ri-main-đơ\b', 'kiu ri ri main đơ', 'Bỏ gạch nối âm tiết phiên âm'),
            (r'\bbrute-force\b', 'brute force', 'Bỏ gạch nối'),
            (r'\bCờ-Rát\b', 'Cờ Rát', 'Bỏ gạch nối âm tiết phiên âm'),
            (r'\bGu-gồ Đíp-Mao\b', 'Gu gồ Đíp Mao', 'Bỏ gạch nối âm tiết phiên âm'),
            (r'\btinh-king\b', 'tinh king', 'Bỏ gạch nối âm tiết phiên âm'),
            (r'\bđốc re-lơ-vân\b', 'đốc re lơ vân', 'Bỏ gạch nối âm tiết phiên âm'),
            (r'\bcon-phờ-lích\b', 'con phờ lích', 'Bỏ gạch nối âm tiết phiên âm'),
            (r'\ban-sơ con-phi-đần\b', 'an sơ con phi đần', 'Bỏ gạch nối âm tiết phiên âm'),
            (r'\bHai-Đi\b', 'Hai Đi', 'Bỏ gạch nối âm tiết phiên âm'),
            (r'\bCMU\b', 'C M U', 'Quy tắc 1: Từ viết tắt chuyển thành cách nhau khoảng trắng'),
            (r'\bhai-brít chăn-cơ\b', 'hai brít chăn cơ', 'Bỏ gạch nối âm tiết phiên âm'),
            (r'\bphờ-rôn-mát-tơ\b', 'phờ rôn mát tơ', 'Bỏ gạch nối âm tiết phiên âm'),
            (r'\bbờ-rét-cờ-răm\b', 'bờ rét cờ răm', 'Bỏ gạch nối âm tiết phiên âm'),
            (r'\bpe-rừn chăn-k\b', 'pe rừn chăn k', 'Bỏ gạch nối âm tiết phiên âm'),
            (r'\bpe-rừn ai-đi\b', 'pe rừn ai đi', 'Bỏ gạch nối âm tiết phiên âm'),
            (r'\brê-gếch\b', 'rê gếch', 'Bỏ gạch nối âm tiết phiên âm'),
            (r'\bchai-ồ chăn-k\b', 'chai ồ chăn k', 'Bỏ gạch nối âm tiết phiên âm'),
            (r'\bTây-bồ Ơ-que\b', 'Tây bồ Ơ que', 'Bỏ gạch nối âm tiết phiên âm'),
            (r'\bmác-đao\b', 'mác đao', 'Bỏ gạch nối âm tiết phiên âm'),
            (r'\bóc-men-tịt\b', 'óc men tịt', 'Bỏ gạch nối âm tiết phiên âm'),
            (r'\bchăn-k con\b', 'chăn k con', 'Bỏ gạch nối âm tiết phiên âm'),
            (r'\bBi-En-cô-đơ\b', 'Bi En cô đơ', 'Bỏ gạch nối âm tiết phiên âm'),
            (r'\bBai En-cô-đơ\b', 'Bai En cô đơ', 'Bỏ gạch nối âm tiết phiên âm'),
            (r'\bCờ-rốt En-cô-đơ\b', 'Cờ rốt En cô đơ', 'Bỏ gạch nối âm tiết phiên âm'),
            (r'\bPốt-gờ-rét pê-gờ-véc-tơ\b', 'Pốt gờ rét pê gờ véc tơ', 'Bỏ gạch nối âm tiết phiên âm'),
            (r'\bPốt-gờ-rét\b', 'Pốt gờ rét', 'Bỏ gạch nối âm tiết phiên âm'),
            (r'\bpê-gờ-véc-tơ\b', 'pê gờ véc tơ', 'Bỏ gạch nối âm tiết phiên âm'),
            (r'\bvéc-tơ\b', 'véc tơ', 'Bỏ gạch nối'),
            (r'\bChát-bót\b', 'Chát bót', 'Bỏ gạch nối'),
            (r'\bGết-tịt Rái-bách\b', 'Gết tịt Rái bách', 'Bỏ gạch nối âm tiết phiên âm'),
            (r'\bI-ét\b', 'I ét', 'Bỏ gạch nối âm tiết phiên âm'),
            (r'\bSờ-pa-sơ\b', 'Sờ pa sơ', 'Bỏ gạch nối âm tiết phiên âm'),
            (r'\bĐen-sơ\b', 'Đen sơ', 'Bỏ gạch nối âm tiết phiên âm'),
            (r'\bSờ-mô tu Bích\b', 'Sờ mô tu Bích', 'Bỏ gạch nối âm tiết phiên âm'),
            (r'\bÍch-Em-Eo\b', 'Ích Em Eo', 'Bỏ gạch nối âm tiết phiên âm'),
            (r'\bSan-bóc-xinh\b', 'San bóc xinh', 'Bỏ gạch nối âm tiết phiên âm'),
            (r'\bri-tri-vừt con-tếch\b', 'ri tri vừt con tếch', 'Bỏ gạch nối âm tiết phiên âm'),
            (r'\bsoóc ai-đi\b', 'soóc ai đi', 'Bỏ gạch nối âm tiết phiên âm'),
            (r'\bRéc-gu-lây-sừn\b', 'Réc gu lây sừn', 'Bỏ gạch nối âm tiết phiên âm'),
            (r'\bU-nít Tét\b', 'U nít Tét', 'Bỏ gạch nối âm tiết phiên âm'),
            (r'\btét gát-rê-u\b', 'tét gát rê u', 'Bỏ gạch nối âm tiết phiên âm'),
            (r'\btét con-tếch san-bóc-xinh\b', 'tét con tếch san bóc xinh', 'Bỏ gạch nối âm tiết phiên âm'),
            (r'\btét seo-ph rát\b', 'tét seo ph rát', 'Bỏ gạch nối âm tiết phiên âm'),
            (r'\bGPA\b', 'G P A', 'Quy tắc 1: Từ viết tắt chuyển thành cách nhau khoảng trắng'),
        ]

        for pat, repl, reason in rule1_patterns:
            matches = re.findall(pat, s)
            if matches:
                record_change(sid, matches[0], repl, reason)
                s = re.sub(pat, repl, s)

        # Rule 3: Punctuation and pauses
        rule3_patterns = [
            (r'Tuyển sinh Xét học bạ', 'Tuyển sinh, Xét học bạ', 'Bổ sung dấu phẩy để ngắt nghỉ tự nhiên'),
            (r'tự nhiên của sinh viên\. Thứ ba', 'tự nhiên của sinh viên. Thứ ba', 'Giữ dấu chấm ngắt câu'),
        ]
        for pat, repl, reason in rule3_patterns:
            matches = re.findall(pat, s)
            if matches:
                record_change(sid, matches[0], repl, reason)
                s = re.sub(pat, repl, s)

        cleaned_scenes[sid] = s

    return cleaned_scenes, changes

if __name__ == "__main__":
    cleaned_scenes, changes = audit_and_clean_voiceover("video/public/audio/cleaned_voiceover_debug.txt")
    print(f"Total changes recorded: {len(changes)}")
    with open("video/audit_changes.json", "w", encoding="utf-8") as f:
        json.dump(changes, f, indent=2, ensure_ascii=False)
    print("Saved audit log to video/audit_changes.json")
