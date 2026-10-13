import os
import re
import json
import hashlib
from typing import List, Dict, Tuple

class HybridChunker:
    def __init__(
        self,
        max_child_size: int = 600,
        overlap: int = 100,
        max_parent_tokens: int = 1200
    ):
        """
        :param max_child_size: Maximum character length of a child chunk.
        :param overlap: Character overlap between text child chunks.
        :param max_parent_tokens: Giới hạn token tối đa cho 1 parent chunk (mặc định 1200 tokens).
        """
        self.max_child_size = max_child_size
        self.overlap = overlap
        self.max_parent_tokens = max_parent_tokens

    def extract_frontmatter(self, text: str) -> Tuple[Dict, str]:
        """Extract YAML frontmatter and return (metadata, remaining_text)"""
        metadata = {
            "source_url": "",
            "title": "",
            "published_date": "",
            "breadcrumbs": ""
        }
        
        match = re.match(r"^---\n(.*?)\n---\n+", text, re.DOTALL)
        if match:
            frontmatter = match.group(1)
            remaining_text = text[match.end():]
            
            for key in metadata.keys():
                val_match = re.search(fr'^{key}:\s*(.+)$', frontmatter, re.MULTILINE)
                if val_match:
                    raw_val = val_match.group(1).strip()
                    try:
                        metadata[key] = json.loads(raw_val)
                    except json.JSONDecodeError:
                        metadata[key] = raw_val.strip('"\'')
                        
            return metadata, remaining_text
            
        return metadata, text

    def estimate_tokens(self, text: str) -> int:
        """Ước lượng số token của văn bản (dựa trên số từ hoặc ký tự)."""
        if not text:
            return 0
        word_count = len(text.split())
        char_count = len(text) // 4
        return max(word_count, char_count)

    def _split_by_paragraphs(self, text: str, max_tokens: int = None) -> List[str]:
        """
        Cơ chế Fallback Chunking cho Parent:
        Bẻ nhỏ văn bản vượt quá max_parent_tokens theo ranh giới đoạn văn (\n\n),
        đảm bảo không cắt cụt giữa các đoạn văn nếu kích thước còn cho phép.
        Nếu một đoạn văn đơn lẻ vượt quá max_tokens, chia tiếp theo dòng đơn (\n).
        """
        if max_tokens is None:
            max_tokens = self.max_parent_tokens

        paragraphs = text.split("\n\n")
        chunks = []
        current = []

        for p in paragraphs:
            p_str = p.strip()
            if not p_str:
                continue

            cand = "\n\n".join(current + [p_str])
            # Nếu thêm đoạn này vào bị vượt quá max_tokens
            if self.estimate_tokens(cand) > max_tokens and current:
                chunks.append("\n\n".join(current))
                current = []

            # Nếu bản thân đoạn p_str đã vượt max_tokens (ví dụ bảng dài hoặc đoạn văn siêu dài)
            if self.estimate_tokens(p_str) > max_tokens:
                lines = p_str.split("\n")
                line_chunk = []
                for l in lines:
                    cand_l = "\n".join(line_chunk + [l])
                    if self.estimate_tokens(cand_l) > max_tokens and line_chunk:
                        chunks.append("\n".join(line_chunk))
                        line_chunk = []
                    if self.estimate_tokens(l) > max_tokens:
                        if line_chunk:
                            chunks.append("\n".join(line_chunk))
                            line_chunk = []
                        words = l.split()
                        for s in range(0, len(words), max_tokens):
                            slice_str = " ".join(words[s:s+max_tokens])
                            if slice_str:
                                chunks.append(slice_str)
                    else:
                        line_chunk.append(l)
                if line_chunk:
                    chunks.append("\n".join(line_chunk))
            else:
                current.append(p_str)

        if current:
            chunks.append("\n\n".join(current))

        return chunks

    def extract_parent_chunks(self, text: str, global_metadata: Dict) -> List[Dict]:
        """
        Bước 2: Cắt text thành các Parent Chunks dựa trên Markdown Header.
        Nếu một section vượt quá max_parent_tokens (> 1200 tokens), chỉ khi đó
        mới kích hoạt regex nhận diện heading bổ trợ (số La Mã / in đậm)
        và cơ chế Fallback Chunking theo đoạn văn (\n\n).
        """
        parents = []
        # Tách dựa trên header chuẩn Markdown (# đến ######)
        sections = re.split(r'(^#{1,6}\s+.+$)', text, flags=re.MULTILINE)

        current_headers = []
        initial_sections = []

        # Text trước khi có bất kỳ header nào
        if sections[0].strip():
            initial_sections.append(([], sections[0].strip()))

        for i in range(1, len(sections), 2):
            header = sections[i].strip()
            content = sections[i+1].strip() if i+1 < len(sections) else ""

            header_level = len(re.match(r'^(#+)', header).group(1))
            current_headers = [h for h in current_headers if len(re.match(r'^(#+)', h).group(1)) < header_level]
            current_headers.append(header)

            if not content:
                continue

            full_section = f"{header}\n{content}".strip()
            if not full_section:
                continue

            initial_sections.append((list(current_headers), full_section))

        # Secondary regex cho heading bổ trợ: số La Mã và in đậm
        # Ví dụ: **I. Nguyên tắc chung**, **1. Phương thức xét tuyển**
        secondary_pattern = re.compile(r'(^\*\*(?:[IVXLCDMivxlcdm]+|[0-9]+)\..+\*\*)', flags=re.MULTILINE)

        for headers, sec_text in initial_sections:
            # KIỂM TRA ĐỘ DÀI: Chỉ khi vượt quá max_parent_tokens (1200 tokens) mới kích hoạt tách phụ bằng regex
            if self.estimate_tokens(sec_text) <= self.max_parent_tokens:
                # Dưới ngưỡng: Giữ nguyên vẹn section ban đầu
                header_key = headers[-1] if headers else ""
                parent_id = hashlib.md5((global_metadata['source_url'] + header_key + sec_text[:50]).encode('utf-8')).hexdigest()
                parents.append({
                    "parent_id": parent_id,
                    "text": sec_text,
                    "metadata": {**global_metadata, "headers": list(headers)}
                })
            else:
                # VƯỢT QUÁ 1200 TOKENS: Sử dụng secondary regex để bóc tách heading phụ
                sub_splits = secondary_pattern.split(sec_text)

                if len(sub_splits) > 1:
                    # Tìm thấy các heading phụ
                    # sub_splits[0] là preamble trước heading phụ đầu tiên
                    preamble = sub_splits[0].strip()
                    if preamble:
                        if self.estimate_tokens(preamble) > self.max_parent_tokens:
                            for idx, sub_txt in enumerate(self._split_by_paragraphs(preamble)):
                                pid = hashlib.md5((global_metadata['source_url'] + (headers[-1] if headers else "") + f"_pre_{idx}_" + sub_txt[:50]).encode('utf-8')).hexdigest()
                                parents.append({
                                    "parent_id": pid,
                                    "text": sub_txt,
                                    "metadata": {**global_metadata, "headers": list(headers)}
                                })
                        else:
                            pid = hashlib.md5((global_metadata['source_url'] + (headers[-1] if headers else "") + "_pre_" + preamble[:50]).encode('utf-8')).hexdigest()
                            parents.append({
                                "parent_id": pid,
                                "text": preamble,
                                "metadata": {**global_metadata, "headers": list(headers)}
                            })

                    for j in range(1, len(sub_splits), 2):
                        sub_header = sub_splits[j].strip()
                        sub_content = sub_splits[j+1].strip() if j+1 < len(sub_splits) else ""
                        sub_full = f"{sub_header}\n{sub_content}".strip()
                        sub_headers = list(headers) + [sub_header]

                        # Nếu sau khi tách theo heading phụ mà section vẫn vượt quá max_parent_tokens
                        if self.estimate_tokens(sub_full) > self.max_parent_tokens:
                            header_tokens = self.estimate_tokens(sub_header)
                            content_limit = max(10, self.max_parent_tokens - header_tokens - 1)
                            content_chunks = self._split_by_paragraphs(sub_content, max_tokens=content_limit) if sub_content else [sub_header]
                            for idx, sub_txt in enumerate(content_chunks):
                                sub_chunk_text = f"{sub_header}\n{sub_txt}".strip() if sub_content else sub_txt
                                pid = hashlib.md5((global_metadata['source_url'] + sub_header + f"_{idx}_" + sub_txt[:50]).encode('utf-8')).hexdigest()
                                parents.append({
                                    "parent_id": pid,
                                    "text": sub_chunk_text,
                                    "metadata": {**global_metadata, "headers": list(sub_headers)}
                                })
                        else:
                            pid = hashlib.md5((global_metadata['source_url'] + sub_header + sub_full[:50]).encode('utf-8')).hexdigest()
                            parents.append({
                                "parent_id": pid,
                                "text": sub_full,
                                "metadata": {**global_metadata, "headers": list(sub_headers)}
                            })
                else:
                    # Vượt quá 1200 tokens nhưng KHÔNG tìm thấy secondary heading nào:
                    # Kích hoạt Fallback Chunking theo đoạn văn (\n\n)
                    for idx, sub_txt in enumerate(self._split_by_paragraphs(sec_text)):
                        header_key = headers[-1] if headers else ""
                        pid = hashlib.md5((global_metadata['source_url'] + header_key + f"_fb_{idx}_" + sub_txt[:50]).encode('utf-8')).hexdigest()
                        parents.append({
                            "parent_id": pid,
                            "text": sub_txt,
                            "metadata": {**global_metadata, "headers": list(headers)}
                        })
            
        return parents

    def is_table(self, text: str) -> bool:
        """Kiểm tra xem text có phải chủ yếu là một bảng Markdown không."""
        # Simple heuristic: if it has table formatting like |---|---|
        return bool(re.search(r'\|.*\|.*\n\|[-: ]+\|[-: ]+\|', text))

    def split_table(self, text: str, metadata: Dict, parent_id: str) -> List[Dict]:
        """Bước 3A: Table-Aware Splitter (Tách bảng giữ nguyên Header)"""
        children = []
        lines = text.strip().split('\n')
        
        table_start_idx = -1
        table_header = []
        
        # Tìm header của bảng (dòng có chữ | và dòng phân cách |---|)
        for i in range(len(lines) - 1):
            if '|' in lines[i] and re.search(r'\|[-: ]+\|', lines[i+1]):
                table_start_idx = i
                table_header = [lines[i], lines[i+1]]
                break
                
        if table_start_idx == -1:
            # Fallback nếu không parse được bảng
            return self.split_text_window(text, metadata, parent_id)
            
        # Tách phần chữ trước và sau bảng
        pre_table = "\n".join(lines[:table_start_idx]).strip()
        if pre_table:
            children.extend(self.split_text_window(pre_table, metadata, parent_id))
            
        # Lấy data rows
        data_rows = []
        post_table_idx = len(lines)
        for i in range(table_start_idx + 2, len(lines)):
            if not '|' in lines[i]:
                post_table_idx = i
                break
            data_rows.append(lines[i])
            
        # Gom các row thành khối nhỏ (VD: mỗi khối tối đa max_child_size ký tự)
        current_block = []
        current_len = len(table_header[0]) + len(table_header[1]) + 2
        
        for row in data_rows:
            # Nếu 1 row đơn lẻ cộng với header đã lớn hơn max_child_size
            if len(table_header[0]) + len(table_header[1]) + 2 + len(row) > self.max_child_size:
                # Flush block hiện tại nếu có
                if current_block:
                    table_chunk = "\n".join(table_header + current_block)
                    children.append(self._create_child(table_chunk, metadata, parent_id))
                    current_block = []
                    current_len = len(table_header[0]) + len(table_header[1]) + 2
                
                # Cắt trực tiếp cái row khổng lồ này
                row_table = "\n".join(table_header + [row])
                if len(row_table) > self.max_child_size:
                    children.extend(self.split_text_window(row_table, metadata, parent_id))
                else:
                    children.append(self._create_child(row_table, metadata, parent_id))
                continue
                
            if current_len + len(row) > self.max_child_size and current_block:
                table_chunk = "\n".join(table_header + current_block)
                children.append(self._create_child(table_chunk, metadata, parent_id))
                current_block = [row]
                current_len = len(table_header[0]) + len(table_header[1]) + 2 + len(row)
            else:
                current_block.append(row)
                current_len += len(row) + 1
                
        if current_block:
            table_chunk = "\n".join(table_header + current_block)
            children.append(self._create_child(table_chunk, metadata, parent_id))
            
        post_table = "\n".join(lines[post_table_idx:]).strip()
        if post_table:
            children.extend(self.split_text_window(post_table, metadata, parent_id))
            
        return children

    def _recursive_split(self, text: str, delimiters: List[str]) -> List[str]:
        """Chia văn bản đệ quy theo danh sách các ký tự phân cách (delimiters)."""
        if len(text) <= self.max_child_size:
            return [text]
            
        if not delimiters:
            # Nếu hết delimiter mà vẫn dài, bắt buộc cắt ngang chuỗi (cắt cứng)
            return [text[i:i+self.max_child_size] for i in range(0, len(text), self.max_child_size)]
            
        delimiter = delimiters[0]
        # Xử lý đặc biệt cho delimiter trống (cắt từng ký tự)
        if delimiter == "":
            return self._recursive_split(text, [])
            
        splits = text.split(delimiter)
        final_chunks = []
        current_chunk = ""
        
        for part in splits:
            if not part:
                continue
                
            # Cần cộng thêm độ dài của delimiter khi ghép
            added_len = len(delimiter) if current_chunk else 0
            if len(current_chunk) + len(part) + added_len <= self.max_child_size:
                current_chunk += (delimiter if current_chunk else "") + part
            else:
                if current_chunk:
                    final_chunks.append(current_chunk)
                    
                if len(part) > self.max_child_size:
                    # Nếu chính part này lớn hơn giới hạn, đệ quy chia nhỏ tiếp với delimiter tiếp theo
                    sub_chunks = self._recursive_split(part, delimiters[1:])
                    final_chunks.extend(sub_chunks[:-1])
                    current_chunk = sub_chunks[-1] if sub_chunks else ""
                else:
                    current_chunk = part
                    
        if current_chunk:
            final_chunks.append(current_chunk)
            
        return final_chunks

    def split_text_window(self, text: str, metadata: Dict, parent_id: str) -> List[Dict]:
        """Bước 3B: Semantic/Window Chunking cho text thông thường với Overlap, có hard split."""
        children = []
        
        # Danh sách delimiter giảm dần độ ưu tiên: đoạn văn -> dòng -> câu -> từ -> ký tự
        delimiters = ["\n\n", "\n", ". ", " ", ""]
        text_chunks = self._recursive_split(text, delimiters)
        
        # Áp dụng overlap giữa các chunks
        for i, chunk_text in enumerate(text_chunks):
            if i > 0 and self.overlap > 0:
                prev_chunk = text_chunks[i-1]
                overlap_str = prev_chunk[-self.overlap:]
                # Tránh cắt ngang từ trong overlap
                space_idx = overlap_str.find(' ')
                if space_idx != -1:
                    overlap_str = overlap_str[space_idx:]
                chunk_text = overlap_str + ("\n" if overlap_str else "") + chunk_text
                
            # Đảm bảo cắt gọt lại nếu overlap làm lố quá nhiều (rất hiếm khi lố nhiều)
            if len(chunk_text) > self.max_child_size + self.overlap:
                chunk_text = chunk_text[:self.max_child_size + self.overlap]
                
            children.append(self._create_child(chunk_text, metadata, parent_id))
            
        return children

    def _create_child(self, text: str, metadata: Dict, parent_id: str) -> Dict:
        # Nhúng header hierarchy vào thẳng child text để Vector model có đủ thông tin
        # Example: "H1: Tuyển sinh > H2: Ở TP.HCM\n\nChi tiết ngành..."
        header_path = " > ".join(metadata.get('headers', []))
        augmented_text = f"[{header_path}]\n{text}" if header_path else text
        
        return {
            "chunk_id": hashlib.md5((metadata['source_url'] + text[:50] + parent_id).encode('utf-8')).hexdigest(),
            "parent_id": parent_id,
            "text": augmented_text,
            "metadata": metadata
        }

    def process_directory(self, input_dir: str) -> Tuple[List[Dict], List[Dict]]:
        """
        Trích xuất ra 2 danh sách:
        - all_parents: Dùng để lưu trữ vào Document Store cho LLM đọc.
        - all_children: Dùng để Embed thành Vector phục vụ Search.
        """
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from utils.text_cleaner import clean_noise

        all_parents = []
        all_children = []
        
        for filename in os.listdir(input_dir):
            if not filename.endswith('.md'):
                continue
                
            filepath = os.path.join(input_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # --- PREPROCESSING STEP ---
            content = clean_noise(content)
                
            metadata, text = self.extract_frontmatter(content)
            
            parents = self.extract_parent_chunks(text, metadata)
            for parent in parents:
                all_parents.append(parent)
                
                # Route sang xử lý Bảng hoặc Text thông thường
                if self.is_table(parent['text']):
                    children = self.split_table(parent['text'], parent['metadata'], parent['parent_id'])
                else:
                    children = self.split_text_window(parent['text'], parent['metadata'], parent['parent_id'])
                    
                all_children.extend(children)
                
        return all_parents, all_children
