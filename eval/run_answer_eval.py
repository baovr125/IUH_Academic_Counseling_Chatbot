"""Thí nghiệm E2 và E5: thu câu trả lời của hai phương án và đo thời gian từng giai đoạn. GỌI LLM (tốn hạn mức API).

V1  LLM trả lời trực tiếp, không có tài liệu (prompt chỉ có vai trò trợ lý học vụ IUH).
V2  Đường xử lý của hệ thống, lặp lại các bước của llm_generation_service.process_chat_message_stream nhưng KHÔNG ghi gì:
    bộ lọc an toàn -> bộ định tuyến -> truy xuất nhiều truy vấn -> dựng prompt -> sinh. Không đọc/ghi bộ nhớ đệm ngữ nghĩa,
    không lưu hội thoại, không ghi log (mỗi câu dùng một mã phiên mới nên không có lịch sử).
Chỉ đọc Supabase (truy xuất, ký ức phiên). Mỗi lượt V2 gọi LLM 2 lần (bộ định tuyến, sinh); V1 gọi 1 lần.

Cách chạy (ví dụ):
    python -B -X utf8 eval/run_answer_eval.py --limit 2            # thử nhanh
    python -B -X utf8 eval/run_answer_eval.py                      # cả bộ câu hỏi, cả hai phương án
    python -B -X utf8 eval/run_answer_eval.py --versions V2        # chỉ V2 (đo độ trễ)
    python -B -X utf8 eval/run_answer_eval.py --provider env       # dùng LLM_PROVIDER trong .env thay vì ép Gemini
Kết quả: eval/results/answers_V1.jsonl, answers_V2.jsonl (ghi nối tiếp, chạy lại sẽ bỏ qua câu đã có).
"""
import argparse
import asyncio
import json
import re
import time
import uuid

from common import DATA, RES, import_service, read_jsonl

ap = argparse.ArgumentParser()
ap.add_argument("--provider", choices=["gemini", "env"], default="gemini",
                help="gemini: ép cả bộ định tuyến và mô hình sinh dùng Gemini; env: theo .env của dự án")
ap.add_argument("--versions", default="V1,V2")
ap.add_argument("--limit", type=int, default=0)
ap.add_argument("--groups", default="", help="lọc theo nhóm, ví dụ quy_che,thu_tuc")
ap.add_argument("--gap", type=float, default=1.0, help="nghỉ giữa hai câu (giây) để tránh vượt hạn mức")
args = ap.parse_args()

force = {"LLM_PROVIDER": "gemini", "REWRITER_PROVIDER": "gemini"} if args.provider == "gemini" else None
rag = import_service(force)
from app.guardrails import query_filter as qf  # noqa: E402
from app.services.llm_generation_service import _strip_thinking_tags, parse_self_reflection  # noqa: E402
from app.services.llm_providers import get_llm_provider  # noqa: E402

V1_SYSTEM = ("Bạn là trợ lý tư vấn học vụ của Trường Đại học Công nghiệp Thành phố Hồ Chí Minh (IUH). "
             "Trả lời ngắn gọn bằng tiếng Việt.")
THINK = re.compile(r"<thinking>.*?</thinking>\s*", re.S)


def clean(raw: str) -> str:
    txt = _strip_thinking_tags(raw)
    txt = re.sub(r"<suggested_queries>.*?</suggested_queries>", "", txt, flags=re.S)
    return txt.strip()


def visible(text: str) -> bool:
    s = THINK.sub("", text)
    if "<thinking>" in s:
        s = s.split("<thinking>")[0]
    return bool(s.strip())


async def generate(provider, system, contents):
    t0 = time.perf_counter()
    first_chunk = first_visible = None
    text, ptok, ctok = "", 0, 0
    async for ch in provider.generate_stream(system, contents):
        now = (time.perf_counter() - t0) * 1000
        ptok = ch.get("prompt_tokens", ptok)
        ctok = ch.get("completion_tokens", ctok)
        t = ch.get("text", "")
        if t:
            first_chunk = first_chunk if first_chunk is not None else now
            text += t
            if first_visible is None and visible(text):
                first_visible = now
    return text, {"first_chunk_ms": first_chunk, "first_visible_ms": first_visible,
                  "gen_ms": (time.perf_counter() - t0) * 1000, "prompt_tokens": ptok, "completion_tokens": ctok}


async def run_v1(q):
    provider = get_llm_provider()
    text, tm = await generate(provider, V1_SYSTEM, [{"role": "user", "content": q["question"]}])
    return {"id": q["id"], "group": q["group"], "version": "V1", "llm_model": provider.last_used_model,
            "answer_raw": text, "answer": clean(text), **{k: round(v, 1) if isinstance(v, float) else v for k, v in tm.items()}}


async def run_v2(q):
    text_q = q["question"]
    rec = {"id": q["id"], "group": q["group"], "version": "V2", "path": "rag", "intent": None, "queries": [],
           "retrieved_sources": [], "top_doc_score": None}
    t_start = time.perf_counter()
    blocked = qf.check_safety_and_jailbreak(text_q)
    if blocked:
        rec.update(path="guardrail", answer_raw=blocked, answer=blocked)
        return rec
    t = time.perf_counter()
    need, queries, router_model, intent, reason = await rag.generate_standalone_query([], text_q)
    rec.update(router_ms=round((time.perf_counter() - t) * 1000, 1), router_model=router_model, intent=intent,
               queries=queries, need_retrieval=need)
    if any("REJECTED_QUERY" in str(x).upper() for x in queries):
        from app.guardrails.query_filter import OFF_TOPIC_MESSAGE
        rec.update(path="router_reject", answer_raw=OFF_TOPIC_MESSAGE, answer=OFF_TOPIC_MESSAGE)
        return rec
    t = time.perf_counter()
    emb = await rag.get_query_embedding(queries[0] if queries else text_q)
    if not need:
        rec["path"] = "no_retrieval"
        system = rag.build_dynamic_system_instruction(
            intent, "", "<retrieved_context>\nKhông yêu cầu tra cứu tài liệu mới cho lượt hội thoại này.\n</retrieved_context>", text_q)
        contents = [{"role": "user", "content": text_q}]
        rec["retrieval_ms"] = 0.0
    else:
        _h, _rq, citations, _ids, system, contents, top, rag_data = await rag.build_rag_payload(
            str(uuid.uuid4()), text_q, queries, emb, intent)
        rec["retrieval_ms"] = float(rag_data["retrieval_latency_ms"])
        rec["top_doc_score"] = round(top, 4)
        rec["retrieved_sources"] = [c.get("source_url") or (c.get("metadata") or {}).get("source_url") for c in rag_data["chunks"]]
        rec["citations"] = [{"title": c.sourceTitle, "section": c.pageOrSection, "url": c.url} for c in citations]
    rec["build_ms"] = round((time.perf_counter() - t) * 1000, 1)
    provider = get_llm_provider()
    raw, tm = await generate(provider, system, contents)
    pre = rec.get("router_ms", 0) + rec["build_ms"]
    rec.update(llm_model=provider.last_used_model, answer_raw=raw, answer=clean(raw),
               reflection=parse_self_reflection(raw),
               **{k: round(v, 1) if isinstance(v, float) else v for k, v in tm.items()})
    if tm["first_visible_ms"] is not None:
        rec["ttft_ms"] = round(pre + tm["first_visible_ms"], 1)      # từ lúc nhận câu hỏi đến chữ đầu tiên hiển thị
    rec["total_ms"] = round((time.perf_counter() - t_start) * 1000, 1)
    return rec


async def main():
    questions = read_jsonl(DATA / "questions.jsonl")
    if args.groups:
        keep = set(args.groups.split(","))
        questions = [q for q in questions if q["group"] in keep]
    if args.limit:
        questions = questions[:args.limit]
    await rag.get_query_embedding("khởi động")      # làm nóng mô hình nhúng
    for v in args.versions.split(","):
        out = RES / f"answers_{v}.jsonl"
        done = {json.loads(l)["id"] for l in out.read_text(encoding="utf-8").splitlines() if l.strip()} if out.exists() else set()
        for q in questions:
            if q["id"] in done:
                continue
            try:
                rec = await (run_v1(q) if v == "V1" else run_v2(q))
            except Exception as e:  # noqa: BLE001 - ghi lỗi từng câu, chạy tiếp
                rec = {"id": q["id"], "group": q["group"], "version": v, "error": f"{type(e).__name__}: {e}"[:300]}
            with out.open("a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            print(v, q["id"], rec.get("path", ""), rec.get("error", ""), rec.get("total_ms", rec.get("gen_ms", "")), flush=True)
            await asyncio.sleep(args.gap)


asyncio.run(main())
