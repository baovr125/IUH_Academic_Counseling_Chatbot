import os
import re
import json
import hashlib
from typing import List, Dict

class MarkdownChunker:
    def __init__(self, max_chunk_size: int = 1500, overlap: int = 200):
        self.max_chunk_size = max_chunk_size
        self.overlap = overlap

    def extract_frontmatter(self, text: str) -> tuple[Dict, str]:
        """Extract YAML frontmatter and return (metadata, remaining_text)"""
        metadata = {
            "source_url": "",
            "title": "",
            "published_date": "",
            "breadcrumbs": ""
        }
        
        # Match the block between --- and ---
        match = re.match(r"^---\n(.*?)\n---\n+", text, re.DOTALL)
        if match:
            frontmatter = match.group(1)
            remaining_text = text[match.end():]
            
            # Simple regex to extract key-value pairs (handles JSON strings)
            for key in metadata.keys():
                val_match = re.search(fr'^{key}:\s*(.+)$', frontmatter, re.MULTILINE)
                if val_match:
                    raw_val = val_match.group(1).strip()
                    try:
                        # Parse the JSON string created by our crawler
                        metadata[key] = json.loads(raw_val)
                    except json.JSONDecodeError:
                        metadata[key] = raw_val.strip('"\'')
                        
            return metadata, remaining_text
            
        return metadata, text

    def chunk_by_headers(self, text: str, metadata: Dict) -> List[Dict]:
        """Split text by markdown headers and chunk them to respect max size"""
        chunks = []
        
        # Split by heading 1, 2, or 3
        # Keeps the delimiter in the result using capture group
        sections = re.split(r'(^#{1,3}\s+.+$)', text, flags=re.MULTILINE)
        
        current_chunk_text = ""
        current_headers = []
        
        if sections[0].strip():
            # Leading text before any header
            current_chunk_text = sections[0].strip()
            self._add_to_chunks(chunks, current_chunk_text, current_headers, metadata)
            current_chunk_text = ""
            
        for i in range(1, len(sections), 2):
            header = sections[i].strip()
            content = sections[i+1].strip() if i+1 < len(sections) else ""
            
            # Keep track of header hierarchy
            header_level = len(re.match(r'^(#+)', header).group(1))
            current_headers = [h for h in current_headers if len(re.match(r'^(#+)', h).group(1)) < header_level]
            current_headers.append(header)
            
            full_section = f"{header}\n{content}".strip()
            self._add_to_chunks(chunks, full_section, current_headers, metadata)

        return chunks

    def _add_to_chunks(self, chunks: List[Dict], text: str, current_headers: List[str], metadata: Dict):
        """Helper to recursively split if section is too large, and append to chunks list"""
        if not text:
            return
            
        if len(text) <= self.max_chunk_size:
            chunk = {
                "chunk_id": hashlib.md5((metadata['source_url'] + text).encode('utf-8')).hexdigest(),
                "text": text,
                "metadata": {
                    **metadata,
                    "headers": list(current_headers)
                }
            }
            chunks.append(chunk)
            return
            
        # If too large, split by paragraph
        paragraphs = text.split('\n\n')
        current_text = ""
        
        for p in paragraphs:
            if len(current_text) + len(p) + 2 <= self.max_chunk_size:
                current_text += ("\n\n" if current_text else "") + p
            else:
                if current_text:
                    chunk = {
                        "chunk_id": hashlib.md5((metadata['source_url'] + current_text).encode('utf-8')).hexdigest(),
                        "text": current_text,
                        "metadata": {
                            **metadata,
                            "headers": list(current_headers)
                        }
                    }
                    chunks.append(chunk)
                    
                # Handle edge case where a single paragraph is larger than max_chunk_size
                if len(p) > self.max_chunk_size:
                    # Break by sentence or hard split
                    sentences = p.split('. ')
                    temp_p = ""
                    for s in sentences:
                        if len(temp_p) + len(s) + 2 <= self.max_chunk_size:
                            temp_p += (". " if temp_p else "") + s
                        else:
                            if temp_p:
                                chunk = {
                                    "chunk_id": hashlib.md5((metadata['source_url'] + temp_p).encode('utf-8')).hexdigest(),
                                    "text": temp_p,
                                    "metadata": {
                                        **metadata,
                                        "headers": list(current_headers)
                                    }
                                }
                                chunks.append(chunk)
                            temp_p = s
                    current_text = temp_p
                else:
                    current_text = p
                    
        if current_text:
            chunk = {
                "chunk_id": hashlib.md5((metadata['source_url'] + current_text).encode('utf-8')).hexdigest(),
                "text": current_text,
                "metadata": {
                    **metadata,
                    "headers": list(current_headers)
                }
            }
            chunks.append(chunk)

    def process_directory(self, input_dir: str) -> List[Dict]:
        all_chunks = []
        for filename in os.listdir(input_dir):
            if not filename.endswith('.md'):
                continue
                
            filepath = os.path.join(input_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            metadata, text = self.extract_frontmatter(content)
            chunks = self.chunk_by_headers(text, metadata)
            all_chunks.extend(chunks)
            
        return all_chunks
