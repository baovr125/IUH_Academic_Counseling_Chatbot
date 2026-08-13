import os
from huggingface_hub import snapshot_download

MODEL_ID = "JustFrederik/nllb-200-distilled-600M-ct2-int8"
LOCAL_DIR = "/app/models/nllb-200-distilled-600M-ct2-int8"

def download_model():
    print(f"Downloading model {MODEL_ID} to {LOCAL_DIR}...")
    snapshot_download(repo_id=MODEL_ID, local_dir=LOCAL_DIR)
    print("Download complete.")

if __name__ == "__main__":
    download_model()
