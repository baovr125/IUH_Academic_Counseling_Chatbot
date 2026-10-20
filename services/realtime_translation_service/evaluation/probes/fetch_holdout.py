"""Dựng bộ hold-out công khai từ phần mở đầu của các bài Wikipedia tiếng Anh (độc lập với dev/val).

Nhãn lấy theo chủ đề bài viết (chọn trước, không nhìn kết quả mô hình) nên có thể nhiễu ở vài bài giáp ranh.
"""
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

IT, MED, ECO, MEC, LAW, MKT = (
    "Công nghệ Thông tin (IT)", "Y khoa / Sức khỏe", "Kinh tế / Tài chính",
    "Kỹ thuật Cơ khí", "Luật / Pháp lý", "Marketing",
)
TOPICS = {
    IT: ["Docker (software)", "Kubernetes", "Hash table", "Operating system", "SQL injection", "Load balancing (computing)", "Version control", "Compiler"],
    MED: ["Diabetes", "Appendicitis", "Asthma", "Penicillin", "Hypertension", "Anesthesia", "Vaccine", "Pneumonia"],
    ECO: ["Inflation", "Stock market", "Gross domestic product", "Central bank", "Bond (finance)", "Exchange rate", "Monopoly", "Supply and demand"],
    MEC: ["Gear", "Turbine", "Bearing (mechanical)", "Hydraulic machinery", "Welding", "Lathe", "Torque", "Internal combustion engine"],
    LAW: ["Tort", "Contract", "Copyright", "Trademark", "Jury", "Perjury", "Arbitration", "Eminent domain"],
    MKT: ["Marketing", "Brand", "Advertising", "Market segmentation", "Public relations", "Search engine optimization", "Customer relationship management", "Product placement"],
    "unknown": ["Giraffe", "Eiffel Tower", "Pizza", "Mount Everest", "Jazz", "Association football", "Amazon River", "Chess", "Cherry blossom", "Venice", "Violin", "Rainbow"],
}


def clean(text: str) -> str:
    text = re.sub(r"\s*\([^)]*\)", "", text)  # bỏ ngoặc (phát âm, năm sinh...)
    text = re.sub(r"\s+", " ", text).strip()
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z])", text)
    out = ""
    for s in sentences:
        if len(out) + len(s) > 380 and out:
            break
        out = (out + " " + s).strip()
    return out


def fetch(title: str) -> str:
    url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + urllib.parse.quote(title.replace(" ", "_"))
    req = urllib.request.Request(url, headers={"User-Agent": "thesis-eval/1.0 (academic project)"})
    for attempt in range(6):
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                return json.loads(resp.read().decode("utf-8")).get("extract", "")
        except urllib.error.HTTPError as exc:
            if exc.code != 429 or attempt == 5:
                raise
            time.sleep(4 * (attempt + 1))


rows = []
for domain, titles in TOPICS.items():
    for title in titles:
        try:
            text = clean(fetch(title))
        except Exception as exc:  # noqa: BLE001
            print("LỖI", title, exc)
            continue
        if len(text) < 60:
            print("BỎ (quá ngắn)", title)
            continue
        rows.append({"domain": domain, "kind": "in_domain" if domain != "unknown" else "ood", "text": text, "source": f"wikipedia:{title}"})
        time.sleep(1.5)

out = sys.argv[1]
with open(out, "w", encoding="utf-8", newline="\n") as f:
    for i, r in enumerate(rows, 1):
        r["id"] = f"hold-{i:03d}"
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
print("đã ghi", len(rows), "mẫu ->", out)
