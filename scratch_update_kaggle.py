import json

with open('G:/Khoa_Luan/IUH_Academic_Counseling_Chatbot/services/doc_translation_service/kaggle/kaggle_marker_worker.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

for cell in nb['cells']:
    source = ''.join(cell['source'])
    if 'server_code =' in source:
        new_source = source.replace(
            'subprocess.run(cmd, check=False)',
            'res = subprocess.run(cmd, capture_output=True, text=True, check=False)\n    if res.returncode != 0:\n        return {"error": "Marker failed", "stdout": res.stdout, "stderr": res.stderr}\n    if not os.path.exists(doc_out_dir):\n        return {"error": "Marker output dir missing", "stdout": res.stdout}'
        )
        cell['source'] = [new_source]

with open('G:/Khoa_Luan/IUH_Academic_Counseling_Chatbot/services/doc_translation_service/kaggle/kaggle_marker_worker.ipynb', 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1)
