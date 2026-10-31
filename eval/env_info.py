"""Ghi cấu hình máy và phiên bản thư viện dùng để chạy các thí nghiệm (eval/results/env_info.json)."""
import json
import platform
import subprocess
import sys
from importlib import metadata
from pathlib import Path

OUT = Path(__file__).parent / "results"
OUT.mkdir(exist_ok=True)


def run(cmd):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=30, encoding="utf-8", errors="replace").stdout.strip()
    except Exception as e:  # noqa: BLE001
        return f"không đọc được: {e}"


def ps(expr):
    return run(["powershell", "-NoProfile", "-Command", expr])


info = {
    "os": platform.platform(),
    "cpu": ps("(Get-CimInstance Win32_Processor | Select-Object -First 1 -ExpandProperty Name)"),
    "cpu_cores_logical": ps("(Get-CimInstance Win32_Processor | Measure-Object -Property NumberOfLogicalProcessors -Sum).Sum"),
    "ram_gb": ps("[math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory/1GB,1)"),
    "gpu": run(["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"]),
    "python": sys.version.split()[0],
    "packages": {},
}
for pkg in ["torch", "sentence-transformers", "transformers", "ctranslate2", "fsrs", "fastapi", "pydantic",
            "pytest", "supabase", "redis", "numpy", "onnxruntime"]:
    try:
        info["packages"][pkg] = metadata.version(pkg)
    except metadata.PackageNotFoundError:
        info["packages"][pkg] = None
(OUT / "env_info.json").write_text(json.dumps(info, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(info, ensure_ascii=False, indent=1))
