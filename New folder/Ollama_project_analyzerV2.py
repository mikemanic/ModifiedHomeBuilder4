from pathlib import Path
import subprocess
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# ================= CONFIG =================
WORKDIR = Path(r"C:\Users\DellWin11\AppData\Roaming\Blender Foundation\Blender\4.5\scripts\addons\home_builder_4")  # CHANGE THIS
MODEL = "qwen2.5-coder:14b"
INCLUDE_EXT = {".py"}
EXCLUDE_DIRS = {".git", ".venv", "__pycache__", "node_modules"}

# Context-safe chunking (≈16K tokens)
MAX_LINES_PER_CHUNK = 250

# Parallelism (Dual Xeon sweet spot)
MAX_WORKERS = 6

# =========================================

os.environ["PYTHONUTF8"] = "1"


def safe_read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def should_skip(path: Path) -> bool:
    return any(part in EXCLUDE_DIRS for part in path.parts)


def chunk_text(text: str, max_lines: int):
    lines = text.splitlines()
    for i in range(0, len(lines), max_lines):
        yield "\n".join(lines[i:i + max_lines])


def collect_chunks():
    chunks = []
    for file in WORKDIR.rglob("*"):
        if should_skip(file):
            continue
        if file.suffix.lower() in INCLUDE_EXT:
            content = safe_read(file)
            for idx, chunk in enumerate(chunk_text(content, MAX_LINES_PER_CHUNK), 1):
                chunks.append({
                    "file": file,
                    "index": idx,
                    "text": chunk
                })
    return chunks


def ollama_run(prompt: str) -> str:
    result = subprocess.run(
        ["ollama", "run", MODEL],
        input=prompt,
        text=True,
        encoding="utf-8",
        errors="ignore",
        capture_output=True
    )
    return result.stdout.strip()


def analyze_chunk(chunk):
    header = f"FILE: {chunk['file'].relative_to(WORKDIR)} (chunk {chunk['index']})"

    prompt = f"""
You are a senior Python engineer.

Analyze the following code.
Focus on:
- Bugs
- Refactoring
- Performance
- PEP8 issues

Respond concisely and technically.

--- CODE START ---
{chunk['text']}
--- CODE END ---
"""

    analysis = ollama_run(prompt)
    return header, analysis


# ============== MAIN =================
if __name__ == "__main__":
    start_time = time.time()

    print(f"📂 Project: {WORKDIR}")
    chunks = collect_chunks()
    total = len(chunks)
    print(f"🔍 Total chunks: {total}")

    output_path = WORKDIR / "ollama_project_analysis.md"

    completed = 0

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor, \
         open(output_path, "w", encoding="utf-8") as out:

        out.write("# Ollama Project Analysis\n\n")

        futures = {executor.submit(analyze_chunk, c): c for c in chunks}

        for future in as_completed(futures):
            completed += 1
            header, analysis = future.result()

            elapsed = time.time() - start_time
            eta = (elapsed / completed) * (total - completed)

            print(
                f"✅ {completed}/{total} | "
                f"Elapsed: {int(elapsed)}s | "
                f"ETA: {int(eta)}s"
            )

            out.write(f"## {header}\n\n")
            out.write(analysis + "\n\n")

    print(f"\n🏁 DONE in {int(time.time() - start_time)}s")
    print(f"📄 Output saved to: {output_path}")
