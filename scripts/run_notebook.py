"""Execute the notebook in the project's Python environment, saving only on success."""

import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
for variable, directory in {
    "MPLCONFIGDIR": ".venv/var/matplotlib",
    "IPYTHONDIR": ".venv/var/ipython",
    "JUPYTER_RUNTIME_DIR": ".venv/var/jupyter",
}.items():
    path = ROOT / directory
    path.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault(variable, str(path))

# Limit native parallelism: the dataset is small and nested thread pools slow it down.
for variable in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(variable, "1")

import nbformat
from nbclient import NotebookClient

path = ROOT / "f1_podium_prediction.ipynb"
notebook = nbformat.read(path, as_version=4)
start = time.monotonic()
count = sum(cell.cell_type == "code" for cell in notebook.cells)
completed = 0


def progress(cell, cell_index, **kwargs):
    global completed
    if cell.cell_type == "code":
        completed += 1
        first_line = cell.source.splitlines()[0][:100]
        print(f"[{completed}/{count}] Cell {cell_index + 1}: {first_line}", flush=True)


print(f"Python: {sys.executable}", flush=True)
client = NotebookClient(
    notebook,
    timeout=1800,
    kernel_name="f1-podium",
    resources={"metadata": {"path": str(ROOT)}},
    on_cell_start=progress,
)
client.execute()
notebook.metadata.kernelspec = {
    "display_name": "F1 Podium (.venv, Python 3.12)",
    "language": "python",
    "name": "f1-podium",
}
nbformat.write(notebook, path)
print(f"Saved executed notebook: {path} ({time.monotonic() - start:.0f}s)")
