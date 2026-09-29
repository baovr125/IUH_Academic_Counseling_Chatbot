import re

def build_morphology_pattern(term: str) -> str:
    """
    Builds a lightweight regex pattern to match common English morphological variations
    (plurals, past tense, present participle) for the given terminology.
    """
    tokens = term.strip().split()
    if not tokens:
        return ""
    
    # We only apply suffix expansion to the last token of the term
    last_token = tokens[-1]
    
    # Very basic lightweight suffix pattern for English
    # Covers: -s, -es, -ed, -ing
    suffix_pattern = r"(s|es|ed|ing)?"
    
    # If the word ends with 'y' following a consonant, it could become 'ies' or 'ied' (e.g., query -> queries/queried)
    if re.search(r'[^aeiou]y$', last_token, re.IGNORECASE):
        base = last_token[:-1] # remove 'y'
        last_token_pattern = rf"({re.escape(last_token)}|{re.escape(base)}(ies|ied))"
    # If it ends with 'e', it could become 'ed' or drop 'e' for 'ing' (e.g., cache -> caches/cached/caching)
    elif last_token.endswith('e'):
        base = last_token[:-1]
        last_token_pattern = rf"({re.escape(last_token)}(s|d)?|{re.escape(base)}ing)"
    else:
        last_token_pattern = rf"{re.escape(last_token)}{suffix_pattern}"
        
    if len(tokens) > 1:
        first_tokens_pattern = r'\s+'.join([re.escape(t) for t in tokens[:-1]])
        pattern = rf"\b{first_tokens_pattern}\s+{last_token_pattern}\b"
    else:
        pattern = rf"\b{last_token_pattern}\b"
        
    return pattern

def find_domain_terms(text: str, domain_dict: dict) -> dict:
    """
    Scans the text for domain terms considering basic morphological variations.
    Returns a dictionary of matched original terms and their translations.
    """
    found_terms = {}
    clean_lower = text.strip().lower()
    
    # Sort keys by length descending to match longer multi-word phrases first
    sorted_keys = sorted(domain_dict.keys(), key=len, reverse=True)
    
    for k in sorted_keys:
        pattern = build_morphology_pattern(k)
        # We use re.IGNORECASE just to be safe, though clean_lower is already lowercase
        if pattern and re.search(pattern, clean_lower, re.IGNORECASE):
            found_terms[k] = domain_dict[k]
            
    return found_terms

def build_context_aware_prompt(domain: str, found_terms: dict, source_lang: str, target_lang: str) -> str:
    """
    Builds the system prompt with context-aware glossary instructions.
    """
    glossary_lines = [f"- {term} -> {trans}" for term, trans in found_terms.items()]
    glossary_str = "\n".join(glossary_lines)
    
    prompt = (
        f"You are an expert translator specializing in the '{domain}' domain.\n\n"
        f"Use the following glossary as the preferred domain terminology:\n"
        f"{glossary_str}\n\n"
        f"Guidelines:\n"
        f"1. Only apply the glossary term if it matches the grammatical role (noun/verb) and domain context of the sentence.\n"
        f"2. Adapt the Vietnamese phrasing naturally to fit the grammatical structure and plural/singular forms.\n"
        f"3. Output ONLY the direct translation without explanation or notes. Preserve all HTML tags perfectly if present."
    )
    return prompt
