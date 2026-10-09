"""
Kịch bản đánh giá chất lượng dịch thuật tự động (Auto-Evaluation Script).
Yêu cầu cài đặt: pip install sacrebleu tabulate
Chạy lệnh: python run_bleu_chrf.py
"""
import json
import sacrebleu
from tabulate import tabulate

def load_data(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def evaluate_metrics():
    dataset = load_data('eval_dataset.json')
    
    categories = {}
    
    # Giả lập dữ liệu kết quả dịch từ các models (Để hội đồng thấy luồng hoạt động)
    # Trong thực tế, đoạn này bạn sẽ call API (requests.post) tới endpoint /text của bạn
    # và call tới Google Translate API để lấy kết quả điền vào mảng predictions.
    
    for item in dataset:
        cat = item['category']
        if cat not in categories:
            categories[cat] = {'refs': [], 'sys_google': [], 'sys_proposed': []}
            
        categories[cat]['refs'].append(item['reference'])
        categories[cat]['sys_google'].append(item['sys_google'])
        categories[cat]['sys_proposed'].append(item['sys_proposed'])

    results_table = []
    
    for cat, data in categories.items():
        refs = [[ref] for ref in data['refs']] # sacrebleu yêu cầu list of list cho references
        
        # Tính điểm Google
        google_bleu = sacrebleu.corpus_bleu(data['sys_google'], refs).score
        google_chrf = sacrebleu.corpus_chrf(data['sys_google'], refs).score
        
        # Tính điểm Hệ thống đề xuất (NLLB + Glossary)
        prop_bleu = sacrebleu.corpus_bleu(data['sys_proposed'], refs).score
        prop_chrf = sacrebleu.corpus_chrf(data['sys_proposed'], refs).score
        
        results_table.append([
            cat, 
            f"{google_bleu:.1f} / {google_chrf:.1f}", 
            f"{prop_bleu:.1f} / {prop_chrf:.1f}"
        ])
        
    print("\n" + "="*60)
    print(" KẾT QUẢ ĐÁNH GIÁ CHẤT LƯỢNG DỊCH THUẬT (BLEU / chrF)")
    print("="*60)
    headers = ["Category", "Google Translate (BLEU/chrF)", "Proposed System (BLEU/chrF)"]
    print(tabulate(results_table, headers=headers, tablefmt="grid"))

if __name__ == "__main__":
    evaluate_metrics()
