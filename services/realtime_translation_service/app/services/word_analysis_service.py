import os
import spacy
import nltk
from app.utils.logger import logger
import asyncio
from typing import Optional, List, Dict, Any

def preload_nlp_models():
    """
    Downloads and preloads NLTK resources and spaCy models into RAM.
    This should be called during the FastAPI lifespan.
    """
    logger.info("Preloading NLP models for Word Analysis...")
    try:
        # Load spaCy model
        try:
            spacy.load("en_core_web_sm")
        except OSError:
            logger.info("Downloading spaCy model en_core_web_sm...")
            from spacy.cli import download
            download("en_core_web_sm")
            spacy.load("en_core_web_sm")
            
        logger.info("NLP models preloaded successfully.")
    except Exception as e:
        logger.error(f"Failed to preload NLP models: {e}")

# We will implement the actual analyze_word function here later.
import hashlib
import time
from app.schemas.translation import WordAnalysisRequest, WordAnalysisResponse, MeaningDef
from app.services.cache_service import get_cached_translation, set_cached_translation
from app.services.llm_service import get_nllb_translator, LANG_MAP

def get_wordnet_pos(treebank_tag):
    if treebank_tag.startswith('J'):
        return 'a'
    elif treebank_tag.startswith('V'):
        return 'v'
    elif treebank_tag.startswith('N'):
        return 'n'
    elif treebank_tag.startswith('R'):
        return 'r'
    else:
        return None

def spacy_to_wordnet_pos(spacy_pos):
    mapping = {
        'ADJ': 'a',
        'VERB': 'v',
        'NOUN': 'n',
        'ADV': 'r',
        'PROPN': 'n'
    }
    return mapping.get(spacy_pos, None)

async def process_word_analysis(request: WordAnalysisRequest) -> WordAnalysisResponse:
    start_time = time.perf_counter()
    
    word = request.selected_text.strip()
    context = request.text.strip()
    
    # 1. Cache Check
    cache_key = f"wa_{request.target_lang}_{hashlib.md5(context.encode('utf-8')).hexdigest()}_{hashlib.md5(word.encode('utf-8')).hexdigest()}"
    cached_data = await asyncio.to_thread(get_cached_translation, cache_key)
    if cached_data:
        # We need to return WordAnalysisResponse. If cache stores JSON string, we should deserialize. 
        # For simplicity, if get_cached_translation returns string (from Redis), we can parse it.
        # But wait, get_cached_translation returns string. Let's assume we store JSON string.
        import json
        try:
            data = json.loads(cached_data)
            data['cached'] = True
            data['latency_ms'] = round((time.perf_counter() - start_time) * 1000, 2)
            return WordAnalysisResponse(**data)
        except:
            pass
            
    # Fallback to NLLB if source_lang is not English
    if request.source_lang != "en":
        return await _fallback_analysis(request, start_time, cache_key)
        
    try:
        nlp = spacy.load("en_core_web_sm")
    except Exception as e:
        logger.error(f"spaCy model not loaded: {e}")
        return await _fallback_analysis(request, start_time, cache_key)
        
    # 2. Extract POS and Lemma
    doc = nlp(context)
    
    target_token = None
    # Find the matching token in context (approximate)
    for token in doc:
        if token.text.lower() == word.lower() or word.lower() in token.text.lower():
            target_token = token
            break
            
    if not target_token:
        # If not found exactly, just process the word itself
        doc_word = nlp(word)
        target_token = doc_word[0] if len(doc_word) > 0 else None
        
    if not target_token:
        return await _fallback_analysis(request, start_time, cache_key)
        
    lemma = target_token.lemma_
    pos = target_token.pos_
    wn_pos = spacy_to_wordnet_pos(pos)
    
    # 3. Word Sense Disambiguation using Lesk
    contextual_synset = None
    try:
        from pywsd.lesk import simple_lesk
        from nltk.corpus import wordnet as wn
        nltk_available = True
    except (LookupError, ImportError) as e:
        logger.warning(f"NLTK data is missing, PyWSD failed to import: {e}")
        nltk_available = False
        
    all_synsets = []
    if nltk_available:
        if wn_pos:
            try:
                contextual_synset = simple_lesk(context, lemma, pos=wn_pos)
            except Exception as e:
                logger.warning(f"Lesk algorithm failed: {e}")
                
        # If Lesk fails or no wn_pos, just get the most common synset
        all_synsets = wn.synsets(lemma, pos=wn_pos) if wn_pos else wn.synsets(lemma)
        if not contextual_synset and all_synsets:
            contextual_synset = all_synsets[0]
        
    if not all_synsets:
        # No WordNet definitions found
        return await _fallback_analysis(request, start_time, cache_key, lemma=lemma, pos=pos)
        
    # 4. Collect definitions and examples
    texts_to_translate = []
    
    def extract_synset_info(syn):
        definition = syn.definition()
        examples = syn.examples()[:2] # Take up to 2 examples
        return definition, examples
        
    contextual_def, contextual_ex = "", []
    other_synsets_info = []
    
    if contextual_synset:
        contextual_def, contextual_ex = extract_synset_info(contextual_synset)
        texts_to_translate.append(contextual_def)
        texts_to_translate.extend(contextual_ex)
        
    for syn in all_synsets:
        d, ex = extract_synset_info(syn)
        if not contextual_synset or d != contextual_def:
            other_synsets_info.append({"syn": syn, "def": d, "ex": ex})
            texts_to_translate.append(d)
            texts_to_translate.extend(ex)
            
    # 5. Batch Translate using NLLB
    translated_texts = []
    if texts_to_translate:
        translator, tokenizer = get_nllb_translator()
        if translator and tokenizer:
            nllb_src = LANG_MAP.get("en", "eng_Latn")
            nllb_tgt = LANG_MAP.get(request.target_lang, "vie_Latn")
            tokenizer.src_lang = nllb_src
            source_tokens_list = [tokenizer.convert_ids_to_tokens(tokenizer.encode(t)) for t in texts_to_translate]
            target_prefix = [nllb_tgt]
            
            try:
                results = await asyncio.to_thread(
                    translator.translate_batch,
                    source_tokens_list,
                    target_prefix=[target_prefix] * len(texts_to_translate)
                )
                for res in results:
                    target_tokens = res.hypotheses[0][1:]
                    translated = tokenizer.decode(tokenizer.convert_tokens_to_ids(target_tokens))
                    translated_texts.append(translated)
            except Exception as e:
                logger.error(f"NLLB batch translation failed in analyze_word: {e}")
                
    # Reconstruct data
    idx = 0
    contextual_meaning = None
    if contextual_synset:
        t_def = translated_texts[idx] if idx < len(translated_texts) else ""
        idx += 1
        t_ex = []
        for _ in contextual_ex:
            t_ex.append(translated_texts[idx] if idx < len(translated_texts) else "")
            idx += 1
            
        contextual_meaning = MeaningDef(
            pos=contextual_synset.pos() if callable(getattr(contextual_synset, 'pos', None)) else getattr(contextual_synset, 'pos', 'unknown'),
            english_definition=contextual_def,
            target_language_meaning=t_def,
            examples=contextual_ex,
            target_language_examples=t_ex
        )
        
    other_meanings = []
    for info in other_synsets_info:
        t_def = translated_texts[idx] if idx < len(translated_texts) else ""
        idx += 1
        t_ex = []
        for _ in info["ex"]:
            t_ex.append(translated_texts[idx] if idx < len(translated_texts) else "")
            idx += 1
            
        other_meanings.append(MeaningDef(
            pos=info["syn"].pos() if callable(getattr(info["syn"], 'pos', None)) else getattr(info["syn"], 'pos', 'unknown'),
            english_definition=info["def"],
            target_language_meaning=t_def,
            examples=info["ex"],
            target_language_examples=t_ex
        ))
        
    response = WordAnalysisResponse(
        word=word,
        lemma=lemma,
        part_of_speech=pos,
        context=context,
        contextual_meaning=contextual_meaning,
        other_meanings=other_meanings,
        cached=False,
        latency_ms=round((time.perf_counter() - start_time) * 1000, 2)
    )
    
    # Save to Cache
    import json
    await asyncio.to_thread(set_cached_translation, cache_key, response.model_dump_json())
    
    return response

async def _fallback_analysis(request: WordAnalysisRequest, start_time: float, cache_key: str, lemma="", pos="") -> WordAnalysisResponse:
    """Fallback if WordNet fails or language is not English. Just translates the word."""
    from app.services.translation_service import run_nllb_only
    
    try:
        translated = await run_nllb_only(request.selected_text, request.source_lang, request.target_lang)
    except:
        translated = "Error"
        
    meaning = MeaningDef(
        pos=pos or "unknown",
        english_definition=request.selected_text,
        target_language_meaning=translated,
        examples=[],
        target_language_examples=[]
    )
    
    res = WordAnalysisResponse(
        word=request.selected_text,
        lemma=lemma or request.selected_text,
        part_of_speech=pos or "unknown",
        context=request.text,
        contextual_meaning=meaning,
        other_meanings=[],
        cached=False,
        latency_ms=round((time.perf_counter() - start_time) * 1000, 2)
    )
    
    import json
    await asyncio.to_thread(set_cached_translation, cache_key, res.model_dump_json())
    return res
