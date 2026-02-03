import os
from pathlib import Path
import subprocess
import textwrap

# ===== CONFIGURATION =====
WORKDIR = Path(r"C:\Users\DellWin11\AppData\Roaming\Blender Foundation\Blender\4.5\scripts\addons\home_builder_4")  # <-- Change to your working directory
MODEL = "qwen2.5-coder:14b"  # Or "codellama:13b-python"
CONTEXT_SIZE = 16000  # Maximum context tokens (approximate)
CHUNK_SIZE = 4000     # Split each file into chunks of 4000 tokens (adjust if needed)
INCLUDE_EXT = [".py"] # File types to include

# ===== HELPER FUNCTIONS =====
def read_file_chunks(file_path, chunk_size=CHUNK_SIZE):
    """Split file content into chunks of roughly chunk_size lines."""
    content = file_path.read_text(errors="ignore")
    lines = content.splitlines()
    for i in range(0, len(lines), chunk_size):
        yield "\n".join(lines[i:i+chunk_size])

def collect_project_chunks(workdir):
    """Collect all files in the directory and split into chunks."""
    chunks = []
    for file in workdir.rglob("*"):
        if file.suffix.lower() in INCLUDE_EXT:
            for c in read_file_chunks(file):
                header = f"\n### FILE: {file.relative_to(workdir)}\n"
                chunks.append(header + c)
    return chunks

def analyze_chunk(chunk):
    """Send a chunk to Ollama and return the response."""
    prompt = f"""
You are a senior Python engineer.

Analyze the following code. Focus on:
- Code quality
- Refactoring suggestions
- Bugs and issues
- PEP8 compliance

Code:
{chunk}
"""
    result = subprocess.run(
        ["ollama", "run", MODEL],
        input=prompt,
        text=True,
        capture_output=True
    )
    return result.stdout

# ===== MAIN SCRIPT =====
if __name__ == "__main__":
    print(f"Scanning project folder: {WORKDIR}")
    chunks = collect_project_chunks(WORKDIR)
    print(f"Found {len(chunks)} chunks to analyze...")

    full_analysis = []

    for idx, chunk in enumerate(chunks, 1):
        print(f"\n=== Analyzing chunk {idx}/{len(chunks)} ===")
        try:
            output = analyze_chunk(chunk)
            full_analysis.append(f"--- Chunk {idx} ---\n{output}\n")
        except Exception as e:
            print(f"Error analyzing chunk {idx}: {e}")

    # ===== SAVE RESULTS =====
    output_file = WORKDIR / "ollama_project_analizat.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        f.writelines(full_analysis)

    print(f"\n✅ Analysis complete! Results saved to: {output_file}")

