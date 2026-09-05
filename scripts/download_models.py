import os
import subprocess
import sys

def main():
    print("==================================================")
    print("🤖 Downloading ML Models for IUH Academic Chatbot")
    print("==================================================")

    # Repository names (Replace these with the actual Hugging Face repo names)
    HF_REPO_BI_ENCODER = "AnhHao0107/vietnamese-bi-encoder-onnx"
    HF_REPO_RERANKER = "AnhHao0107/bge-reranker-v2-m3-onnx"

    # Get project root (parent of scripts/)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    hf_models_dir = os.path.join(project_root, "hf_models")

    # Ensure huggingface_hub is installed
    try:
        import huggingface_hub
    except ImportError:
        print("Installing huggingface_hub...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "huggingface_hub[cli]"])

    # Create directory
    os.makedirs(hf_models_dir, exist_ok=True)
    os.chdir(hf_models_dir)

    print(f"\n📥 Downloading {HF_REPO_BI_ENCODER}...")
    subprocess.run(["huggingface-cli", "download", HF_REPO_BI_ENCODER, "--local-dir", "vietnamese-bi-encoder-onnx"], check=True)

    print(f"\n📥 Downloading {HF_REPO_RERANKER}...")
    subprocess.run(["huggingface-cli", "download", HF_REPO_RERANKER, "--local-dir", "bge-reranker-v2-m3-onnx"], check=True)

    print("\n✅ Models downloaded successfully to ./hf_models/")
    print("You can now run 'docker compose up -d'!")

if __name__ == "__main__":
    main()
