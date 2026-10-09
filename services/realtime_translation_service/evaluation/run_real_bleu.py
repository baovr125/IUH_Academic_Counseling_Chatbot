import json
import time
import os
import requests
import sacrebleu

# Configuration
API_URL = "http://localhost:8003/api/v1/translate/text"
HEADERS = {
    "X-User-ID": "admin-evaluation",
    "Content-Type": "application/json"
}
DATASET_PATH = "dataset/ground_truth_dataset.json"

RAW_RESULTS_DIR = "raw_results"
METRICS_DIR = "metrics"
LOGS_DIR = "logs"

for d in [RAW_RESULTS_DIR, METRICS_DIR, LOGS_DIR]:
    if not os.path.exists(d):
        os.makedirs(d)

def main():
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(LOGS_DIR, f"translation_eval_{timestamp}.log")
    raw_file = os.path.join(RAW_RESULTS_DIR, f"translation_run_{timestamp}.json")
    metrics_file = os.path.join(METRICS_DIR, f"bleu_chrf_{timestamp}.json")

    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    results = []
    sys_outputs = []
    refs = []

    print(f"Loaded {len(dataset)} items from ground truth dataset.")
    
    with open(log_file, "w", encoding="utf-8") as lf:
        lf.write(f"--- EVALUATION RUN {timestamp} ---\n")
        
        for idx, item in enumerate(dataset):
            print(f"Translating item {idx+1}/{len(dataset)}: {item['id']}")
            
            payload = {
                "text": item["source"],
                "source_lang": "en",
                "target_lang": "vi",
                "domain": "academic" if item["category"] == "Academic" else "general"
            }
            
            try:
                start_time = time.time()
                resp = requests.post(API_URL, json=payload, headers=HEADERS, timeout=10)
                resp.raise_for_status()
                latency = time.time() - start_time
                
                data = resp.json()
                translated_text = data.get("data", {}).get("translated_text", "")
                
                result_item = {
                    "id": item["id"],
                    "source": item["source"],
                    "reference": item["reference"],
                    "category": item["category"],
                    "sys_proposed": translated_text,
                    "latency_ms": round(latency * 1000, 2),
                    "status": "success",
                    "error": None
                }
                
                sys_outputs.append(translated_text)
                refs.append(item["reference"])
                
                lf.write(f"[{item['id']}] SUCCESS | Latency: {result_item['latency_ms']}ms\n")
                
            except Exception as e:
                print(f"Error on item {item['id']}: {e}")
                result_item = {
                    "id": item["id"],
                    "source": item["source"],
                    "reference": item["reference"],
                    "category": item["category"],
                    "sys_proposed": "",
                    "latency_ms": 0,
                    "status": "error",
                    "error": str(e)
                }
                lf.write(f"[{item['id']}] ERROR | {e}\n")
                
            results.append(result_item)
            time.sleep(0.5) # Prevent rate limiting

    # Calculate Metrics overall
    bleu = sacrebleu.corpus_bleu(sys_outputs, [refs])
    chrf = sacrebleu.corpus_chrf(sys_outputs, [refs])
    
    metrics = {
        "overall": {
            "bleu": round(bleu.score, 2),
            "chrf": round(chrf.score, 2)
        }
    }
    
    # Calculate by category
    categories = set([item["category"] for item in results])
    for cat in categories:
        cat_sys = [res["sys_proposed"] for res in results if res["category"] == cat and res["status"] == "success"]
        cat_ref = [res["reference"] for res in results if res["category"] == cat and res["status"] == "success"]
        
        if cat_sys:
            c_bleu = sacrebleu.corpus_bleu(cat_sys, [cat_ref])
            c_chrf = sacrebleu.corpus_chrf(cat_sys, [cat_ref])
            metrics[cat] = {
                "bleu": round(c_bleu.score, 2),
                "chrf": round(c_chrf.score, 2)
            }
            
    print(f"\n--- RESULTS ---")
    print(f"Overall BLEU: {metrics['overall']['bleu']}")
    print(f"Overall chrF: {metrics['overall']['chrf']}")
    
    with open(raw_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
        
    with open(metrics_file, "w", encoding="utf-8") as f:
        json.dump(metrics, f, ensure_ascii=False, indent=4)
        
    print(f"\nSaved raw results to {raw_file}")
    print(f"Saved metrics to {metrics_file}")
    print(f"Saved logs to {log_file}")

if __name__ == "__main__":
    main()
