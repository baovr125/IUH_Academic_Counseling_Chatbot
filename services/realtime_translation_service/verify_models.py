import os


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "models")
NLLB_DIR = os.path.join(MODELS_DIR, "nllb-200-distilled-600M-ct2-int8")

NLLB_REQUIRED_FILES = (
    "config.json",
    "model.bin",
    "sentencepiece.bpe.model",
    "shared_vocabulary.txt",
    "tokenizer.json",
)


def main() -> None:
    missing = [
        os.path.join(NLLB_DIR, name)
        for name in NLLB_REQUIRED_FILES
        if not os.path.isfile(os.path.join(NLLB_DIR, name))
    ]

    fasttext_path = os.path.join(MODELS_DIR, "lid.176.ftz")
    if not os.path.isfile(fasttext_path):
        missing.append(fasttext_path)

    if missing:
        raise SystemExit("Model verification failed. Missing files:\n" + "\n".join(missing))

    try:
        from transformers import AutoTokenizer
        AutoTokenizer.from_pretrained(NLLB_DIR, local_files_only=True)
    except Exception as exc:
        raise SystemExit(f"Tokenizer verification failed: {exc}") from exc

    print("Model verification passed: NLLB and FastText artifacts are present.")


if __name__ == "__main__":
    main()
