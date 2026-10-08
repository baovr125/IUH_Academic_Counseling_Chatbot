import os
import urllib.request
from huggingface_hub import snapshot_download

MODEL_ID = "JustFrederik/nllb-200-distilled-600M-ct2-int8"
MODELS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
LOCAL_DIR = os.path.join(MODELS_DIR, "nllb-200-distilled-600M-ct2-int8")
FASTTEXT_URL = "https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.ftz"
FASTTEXT_PATH = os.path.join(MODELS_DIR, "lid.176.ftz")

def download_model():
    print(f"Downloading model {MODEL_ID} to {LOCAL_DIR}...")
    snapshot_download(repo_id=MODEL_ID, local_dir=LOCAL_DIR)
    print("Download complete.")
    
    print(f"Downloading FastText model to {FASTTEXT_PATH}...")
    os.makedirs(MODELS_DIR, exist_ok=True)
    if not os.path.exists(FASTTEXT_PATH):
        urllib.request.urlretrieve(FASTTEXT_URL, FASTTEXT_PATH)
    print("FastText download complete.")

if __name__ == "__main__":
    download_model()
