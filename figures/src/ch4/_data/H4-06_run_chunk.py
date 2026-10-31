import importlib.util, json, re, sys
ROOT = r"B:\KhoaLuan\IUH_Academic_Counseling_Chatbot\services\academic_chatbot_service\app\data_ingestion"
def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
hc = load("hc", ROOT + r"\chunkers\hybrid_chunker.py")
tc = load("tc", ROOT + r"\utils\text_cleaner.py")
log = open(r"B:\KhoaLuan\IUH_Academic_Counseling_Chatbot\logs\academic_chatbot\2026-10-29\142502-quy-trinh-ang-ky-hoc.md", encoding="utf-8").read()
part = log.split("### Chunk 1")[1].split("### Content:")[1].split("\n---")[0]
body = "\n".join(l[2:] if l.startswith("> ") else l.lstrip(">") for l in part.strip().split("\n"))
md = "---\nsource_url: https://camnang.iuh.edu.vn/quy-che-dao-tao-theo-he-thong-tin-chi.php\ntitle: Quy chế đào tạo theo hệ thống tín chỉ\nbreadcrumbs: \n---\n\n" + body
md = tc.clean_noise(md)
ch = hc.HybridChunker(max_child_size=600, overlap=100, max_parent_tokens=1200)
meta, text = ch.extract_frontmatter(md)
parents = ch.extract_parent_chunks(text, meta)
out = []
for p in parents:
    kids = ch.split_table(p["text"], p["metadata"], p["parent_id"]) if ch.is_table(p["text"]) else ch.split_text_window(p["text"], p["metadata"], p["parent_id"])
    out.append({"parent_len": len(p["text"]), "parent_tokens": ch.estimate_tokens(p["text"]), "headers": p["metadata"].get("headers"),
                "children": [k["text"] for k in kids]})
json.dump(out, open(__import__("pathlib").Path(__file__).with_name("H4-06_chunks.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for o in out:
    print("PARENT", o["parent_len"], "ký tự,", o["parent_tokens"], "token ước lượng, headers", o["headers"], "->", len(o["children"]), "child")
    for c in o["children"]:
        print("  ", len(c), repr(c[:90]))
