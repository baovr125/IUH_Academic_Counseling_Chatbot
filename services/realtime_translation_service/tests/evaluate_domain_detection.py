import asyncio
import os
import sys

# Đảm bảo đường dẫn module được nhận dạng
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.domain_service import auto_detect_domain_long
from colorama import init, Fore, Style

init(autoreset=True)

# Tập validation test data: bao gồm các văn bản có nhãn rõ ràng và ngoài phạm vi
VALIDATION_DATA = [
    # Nhánh Y khoa
    {"text": "The patient presented with acute myocardial infarction and was immediately treated with beta-blockers.", "expected": "Y khoa / Sức khỏe"},
    {"text": "A standard echocardiogram revealed left ventricular hypertrophy.", "expected": "Y khoa / Sức khỏe"},
    
    # Nhánh Công nghệ Thông tin
    {"text": "We need to deploy the microservices using Docker and orchestrate them with Kubernetes to ensure high availability.", "expected": "Công nghệ Thông tin (IT)"},
    {"text": "A race condition occurred when two concurrent threads attempted to acquire the mutex lock simultaneously.", "expected": "Công nghệ Thông tin (IT)"},
    
    # Nhánh Kỹ thuật cơ khí
    {"text": "The tensile strength of the steel alloy was measured using a universal testing machine.", "expected": "Kỹ thuật Cơ khí"},
    {"text": "The internal combustion engine operates on a four-stroke thermodynamic cycle.", "expected": "Kỹ thuật Cơ khí"},
    
    # Nhánh Kinh tế / Tài chính
    {"text": "The Federal Reserve's decision to increase interest rates caused a significant drop in equity markets.", "expected": "Kinh tế / Tài chính"},
    {"text": "EBITDA margin improved by 200 basis points due to stringent cost control measures.", "expected": "Kinh tế / Tài chính"},
    
    # Nhánh Luật / Pháp lý
    {"text": "The plaintiff bears the burden of proof to demonstrate negligence by a preponderance of the evidence.", "expected": "Luật / Pháp lý"},
    {"text": "The contract is rendered voidable if there is mutual mistake of a material fact.", "expected": "Luật / Pháp lý"},
    
    # Nhánh Ngoài Danh Mục (Nên trả về None hoặc Rỗng vì không khớp)
    {"text": "The recipe calls for three cups of flour, two eggs, and a teaspoon of vanilla extract.", "expected": ""},
    {"text": "The protagonist of the novel struggles with existential dread and societal alienation.", "expected": ""},
    {"text": "I went to the supermarket yesterday to buy some apples and oranges for the party.", "expected": ""}
]

async def evaluate():
    print(f"{Fore.CYAN}Bắt đầu đánh giá độ tin cậy LLM Zero-shot Classification...{Style.RESET_ALL}\n")
    
    correct = 0
    total = len(VALIDATION_DATA)
    
    for idx, item in enumerate(VALIDATION_DATA):
        text = item["text"]
        expected = item["expected"]
        
        print(f"Test {idx+1}: {text[:60]}...")
        detected = await auto_detect_domain_long(text)
        
        if detected == expected:
            print(f"  {Fore.GREEN}[PASS]{Style.RESET_ALL} LLM đoán: '{detected}' | Mong đợi: '{expected}'")
            correct += 1
        else:
            print(f"  {Fore.RED}[FAIL]{Style.RESET_ALL} LLM đoán: '{detected}' | Mong đợi: '{expected}'")
            
    print(f"\n{Fore.YELLOW}Kết quả đánh giá:{Style.RESET_ALL}")
    print(f"Tổng số mẫu: {total}")
    print(f"Đoán đúng: {correct}")
    print(f"Độ chính xác (Accuracy): {round((correct/total)*100, 2)}%")

if __name__ == "__main__":
    asyncio.run(evaluate())
