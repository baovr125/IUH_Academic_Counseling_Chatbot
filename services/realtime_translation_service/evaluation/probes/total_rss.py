import os, sys, time, logging
ROOT = str(__import__("pathlib").Path(__file__).resolve().parents[2])
sys.path.insert(0, ROOT)
os.chdir(ROOT)
os.environ["TESTING"] = "1"
os.environ["NLLB_DEVICE"] = "cpu"
os.environ["NLLB_MODEL_DIR"] = os.path.join(ROOT, "models", "nllb-200-distilled-600M-ct2-int8")
logging.disable(logging.CRITICAL)
import psutil
p = psutil.Process()
rss = lambda: round(p.memory_info().rss / 1e6)
print("baseline", rss())
from app.services import llm_service
t = time.perf_counter(); ok = llm_service.preload_models(); print("NLLB preload ok=%s  %.1fs  RSS=%d MB" % (ok, time.perf_counter() - t, rss()))
try:
    from app.services.word_analysis_service import preload_nlp_models
    t = time.perf_counter(); preload_nlp_models(); print("spaCy/NLTK preload %.1fs  RSS=%d MB" % (time.perf_counter() - t, rss()))
except Exception as e:
    print("word analysis preload skipped:", type(e).__name__, str(e)[:100])
from app.services import language_detection as ld
before = rss()
t = time.perf_counter(); ld.warm_up(); print("language detection warm-up %.2fs  RSS=%d MB (+%d MB)" % (time.perf_counter() - t, rss(), rss() - before))
