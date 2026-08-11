import os
from typing import Optional
import docx
from pptx import Presentation
from app.services.ollama_translator import call_ollama_generate, OLLAMA_DEFAULT_MODEL
from app.utils.logger import logger

def translate_single_text(
    text: str,
    source_lang: str = "en",
    target_lang: str = "vi",
    model: str = OLLAMA_DEFAULT_MODEL
) -> str:
    """Helper dịch một chuỗi văn bản ngắn/đoạn qua Ollama."""
    clean_text = text.strip()
    if not clean_text or len(clean_text) <= 3:
        return text

    prompt = (
        f"Dịch ngắn gọn đoạn văn bản sau từ tiếng {source_lang.upper()} sang tiếng {target_lang.upper()}.\n"
        f"Chỉ trả về bản dịch, không giải thích thừa.\n\n"
        f"Text:\n{clean_text}"
    )
    try:
        translated = call_ollama_generate(prompt=prompt, model=model)
        return translated if translated else text
    except Exception as e:
        logger.warning(f"Lỗi dịch đoạn ngắn trong Office document: {e}")
        return text

def translate_docx_document(
    input_path: str,
    output_path: str,
    source_lang: str = "en",
    target_lang: str = "vi",
    model: str = OLLAMA_DEFAULT_MODEL
) -> str:
    """
    Dịch file Microsoft Word (.docx) In-place:
    - Duyệt qua doc.paragraphs, dịch các đoạn > 5 ký tự và gán lại para.text.
    - Duyệt qua doc.tables, từng row, cell. Dịch cell.text và gán lại.
    """
    logger.info(f"Bắt đầu dịch file Word .docx: {input_path} -> {output_path}")
    doc = docx.Document(input_path)

    # 1. Dịch các đoạn văn (paragraphs)
    for para in doc.paragraphs:
        if para.text and len(para.text.strip()) > 5:
            translated_text = translate_single_text(
                para.text, source_lang=source_lang, target_lang=target_lang, model=model
            )
            para.text = translated_text

    # 2. Dịch các bảng biểu (tables) giữ nguyên cấu trúc khung bảng (borders & layout)
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for para in cell.paragraphs:
                    if para.text and len(para.text.strip()) > 2:
                        translated_para = translate_single_text(
                            para.text, source_lang=source_lang, target_lang=target_lang, model=model
                        )
                        para.text = translated_para


    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    doc.save(output_path)
    logger.info(f"Đã hoàn thành dịch file Word .docx và lưu tại {output_path}")
    return output_path

def translate_pptx_document(
    input_path: str,
    output_path: str,
    source_lang: str = "en",
    target_lang: str = "vi",
    model: str = OLLAMA_DEFAULT_MODEL
) -> str:
    """
    Dịch file Microsoft PowerPoint (.pptx) In-place:
    - Duyệt qua các slide -> shapes -> text_frame.
    - Dịch paragraph.text và gán lại.
    - Bật thuộc tính AutoFit (word_wrap = True) để chữ tiếng Việt dài không tràn khỏi box.
    """
    logger.info(f"Bắt đầu dịch file PowerPoint .pptx: {input_path} -> {output_path}")
    prs = Presentation(input_path)

    for slide_idx, slide in enumerate(prs.slides, 1):
        for shape in slide.shapes:
            if shape.has_text_frame:
                text_frame = shape.text_frame
                text_frame.word_wrap = True # AutoFit / word wrap
                
                for para in text_frame.paragraphs:
                    if para.text and len(para.text.strip()) > 2:
                        translated_text = translate_single_text(
                            para.text, source_lang=source_lang, target_lang=target_lang, model=model
                        )
                        para.text = translated_text

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    prs.save(output_path)
    logger.info(f"Đã hoàn thành dịch file PowerPoint .pptx và lưu tại {output_path}")
    return output_path
