import re
from bs4 import BeautifulSoup
from typing import Dict, List, Tuple

class HTMLTranslator:
    def __init__(self):
        self.text_map: Dict[str, str] = {}
        self.counter = 0

    def extract_text(self, html: str) -> Tuple[str, List[str]]:
        """
        Parses HTML and extracts text nodes while preserving DOM structure.
        Replaces text nodes with unique placeholders.
        Returns:
            - html_with_placeholders: HTML string with placeholders
            - texts_to_translate: List of strings to be translated
        """
        if not html or not html.strip():
            return html, []

        soup = BeautifulSoup(html, "html.parser")
        
        # Protect specific tags
        protected_tags = ['script', 'style', 'code', 'pre']
        
        texts_to_translate = []
        
        # We need to find all Text nodes
        for text_node in soup.find_all(string=True):
            parent = text_node.parent
            if parent and parent.name in protected_tags:
                continue
                
            text = str(text_node).strip()
            if not text:
                continue
                
            # Skip HTML entities or pure symbols if needed
            if len(text) <= 1 and not text.isalnum():
                continue
                
            placeholder = f"__TR_{self.counter}__"
            self.text_map[placeholder] = text
            texts_to_translate.append(text)
            
            # Replace in soup
            text_node.replace_with(placeholder)
            self.counter += 1
            
        return str(soup), texts_to_translate

    def reconstruct_html(self, html_with_placeholders: str, translated_texts: List[str]) -> str:
        """
        Restores translated text into the HTML structure.
        """
        if len(translated_texts) != self.counter:
            # Fallback if mismatch
            pass
            
        result = html_with_placeholders
        for i, translated in enumerate(translated_texts):
            placeholder = f"__TR_{i}__"
            result = result.replace(placeholder, translated)
            
        return result
