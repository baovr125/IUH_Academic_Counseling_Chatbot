import os
import sys

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from app.services.pdf2zh.pdf2zh import main

# Mock sys.argv to run main
sys.argv = [
    "pdf2zh",
    r"G:\Khoa_Luan\IUH_Academic_Counseling_Chatbot\services\doc_translation_service\eval_outputs\run_20260912_214521\01_NEJMoa2035389\original.pdf",
    "-o", r"G:\Khoa_Luan\IUH_Academic_Counseling_Chatbot\services\doc_translation_service\eval_outputs\run_20260912_214521\01_NEJMoa2035389",
    "-p", "1,2",
    "-li", "en",
    "-lo", "vi",
    "-s", "ollama_pdf:qwen2.5:7b"
]

try:
    main()
    print("Translation completed successfully.")
except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"Translation failed: {e}")
