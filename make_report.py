"""Build the analytical report (report.html + report.pdf) from the executed notebook.

The report combines the main analysis with explained diagnostic appendices,
including every executed notebook figure. Result tables come from exported
artifacts. A companion HTML gallery provides the same figures for browsing.
Run the notebook first, then:

    python make_report.py
"""
import base64
import csv
import hashlib
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
from pathlib import Path

import markdown
import nbformat

NOTEBOOK = Path("f1_podium_prediction.ipynb")
CONTENT = Path("report_content.md")
TITLE = "Formula 1 Podium Prediction — Milestone 1 Analytical Report"
TEAM_NUMBER = 63
TEAM_MEMBERS = [
    ("58-20196", "Mohamed Ahmed Mohamed Abdelaziz"),
    ("58-3004", "Daniel Maged Shehata Youssef"),
    ("58-7146", "Marwan Montasser Morad Hassan Metwally"),
    ("58-2686", "Noor Hossameldin Ahmed Aboouf Ali"),
]

CSS = """
@page { size: A4; margin: 12mm 14mm; }
body { font-family: Helvetica, Arial, sans-serif; font-size: 10pt; line-height: 1.32; color: #1a1a1a; margin: 0; }
.page { break-after: page; position: relative; }
.page:last-child { break-after: auto; }
.folio { border-bottom: 1px solid #c9c8c2; color: #52514e; font-size: 8pt; padding-bottom: 3mm; margin-bottom: 3mm; }
h1 { font-size: 20pt; margin: 0 0 4pt; }
h2 { font-size: 14pt; margin: 0 0 8pt; color: #235ea2; break-after: avoid; }
h3 { font-size: 10.5pt; margin: 9pt 0 4pt; break-after: avoid; }
p { margin: 5pt 0; }
p, li { orphans: 3; widows: 3; }
figure { margin: 5pt 0; break-inside: avoid; }
figure img { width: 100%; display: block; object-fit: contain; }
figcaption { font-size: 8pt; line-height: 1.2; color: #52514e; margin-top: 2pt; }
.figure-pair { display: flex; gap: 4mm; break-inside: avoid; }
.figure-pair figure { flex: 1; min-width: 0; }
table { width: 100%; border-collapse: collapse; font-size: 8pt; margin: 6pt 0; break-inside: avoid; }
th, td { border: 0.6px solid #c9c8c2; padding: 2.5pt 4pt; text-align: left; vertical-align: top; overflow-wrap: anywhere; }
th { background: #f1f0ec; }
code { font-family: Menlo, Consolas, monospace; font-size: 8pt; background: #f4f3ef; padding: 0 2pt; border-radius: 2pt; overflow-wrap: anywhere; }
pre { font-family: Menlo, Consolas, monospace; font-size: 7.8pt; background: #f7f6f2; padding: 5pt 7pt; white-space: pre-wrap; break-inside: avoid; }
blockquote { border-left: 3px solid #eb6834; margin: 8pt 0; padding: 2pt 10pt; background: #fdf3ee; }
.team { color: #52514e; font-size: 9.5pt; line-height: 1.4; margin: 6pt 0 9pt; }
.team-title { color: #235ea2; font-weight: bold; margin-bottom: 3pt; }
.team-member { display: block; }
.note { color: #52514e; font-size: 8pt; }
a { color: #235ea2; }
ul { margin: 5pt 0; padding-left: 16pt; }
li { margin-bottom: 4pt; }
@media screen { body { background: #e9edf1; } .page { width: 182mm; min-height: 267mm; margin: 12px auto; padding: 12mm 14mm; background: white; box-shadow: 0 1px 8px #bdc5cf; } }
"""

def md_to_html(text):
    return markdown.markdown(text, extensions=["tables", "sane_lists"])

def escape(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def read_csv(name):
    with (Path("outputs") / name).open() as stream:
        return list(csv.DictReader(stream))


def result_tables():
    """Read numerical comparison tables from current artifacts, not prose copies."""
    comparison = read_csv("model_comparison.csv")
    names = {
        "Grid-frequency rule (no ML)": "Grid rule",
        "Logistic regression (baseline, default)": "Logistic baseline / tuned*",
        "Random forest": "Random forest",
        "Gradient boosting": "Gradient boosting",
        "Shallow neural network": "Neural network",
    }
    scores = "| Model | Set | AP | ROC-AUC | F1 | Precision | Recall | Brier | Accuracy |\n|---|---|---:|---:|---:|---:|---:|---:|---:|\n"
    for name, label in names.items():
        entries = {r["set"]: r for r in comparison if r["model"] == name}
        compact_label = "Logistic*" if name.startswith("Logistic") else label
        for split, split_label in [("train", "Train"), ("val", "Validation"), ("test", "Holdout")]:
            scores += "| " + compact_label + " | " + split_label + " | " + " | ".join(f"{float(entries[split][m]):.3f}" for m in ["PR-AUC", "ROC-AUC", "F1", "Precision", "Recall", "Brier", "Accuracy"]) + " |\n"
    scores += "\n*The tuned logistic model selects the baseline settings and has identical recorded scores. All split metrics for both variants are retained in `outputs/model_comparison.csv`."
    orders = read_csv("preprocessing_order_experiments.csv")
    delta = "| Change from chosen order A to B | Logistic Δ AP | Boosting Δ AP |\n|---|---:|---:|\n"
    for number, label in [("1.", "Fit on development rather than train"), ("2.", "Restart histories within each split"), ("3.", "Scale before imputing")]:
        values = []
        for model in ["Logistic regression", "Gradient boosting"]:
            group = [r for r in orders if r["experiment"].startswith(number) and r["model"] == model]
            a = next(r for r in group if r["order"].startswith("A:"))
            b = next(r for r in group if r["order"].startswith("B:"))
            values.append(f"{float(b['PR-AUC']) - float(a['PR-AUC']):+.4f}")
        delta += "| " + label + " | " + " | ".join(values) + " |\n"
    ablation = read_csv("ablation_results.csv")
    full = next(r for r in ablation if r["model"] == "Gradient boosting" and r["setting"] == "full")
    abl = "| Group removed (boosting) | Validation Δ AP | Holdout Δ AP |\n|---|---:|---:|\n"
    for row in ablation:
        if row["model"] == "Gradient boosting" and row["setting"] == "drop":
            abl += "| " + row["group"].replace("_", " ") + " | " + " | ".join(f"{float(row[m]) - float(full[m]):+.4f}" for m in ["val PR-AUC", "test PR-AUC"]) + " |\n"
    return {"model_scores": scores, "order_deltas": delta, "ablation_deltas": abl}


def notebook_figures(nb):
    figures = {}
    special = {
        "shap_beeswarm": ["xai_shap_beeswarm_best_statistical", "xai_shap_beeswarm_neural_network"],
        "local_waterfall": ["xai_local_shap_case_A", "xai_local_shap_case_B"],
    }
    for index, cell in enumerate(nb.cells):
        images = [out["data"]["image/png"] for out in cell.get("outputs", []) if "image/png" in out.get("data", {})]
        if not images:
            continue
        names = re.findall(r'savefig\("([^"\n]+)"\)', cell.source)
        if not names:
            if "shap.plots.beeswarm" in cell.source:
                names = special["shap_beeswarm"]
            elif "shap.plots.waterfall" in cell.source:
                names = special["local_waterfall"]
        if len(names) != len(images):
            sys.exit(f"Cannot map notebook figures in cell {index}: {names} / {len(images)} images")
        for name, png in zip(names, images):
            figures[name] = {"png": png.strip(), "notebook_cell": index}
    return figures

def build():
    nb = nbformat.read(NOTEBOOK, as_version=4)
    code_cells = [c for c in nb.cells if c.cell_type == "code" and c.source.strip()]
    if not code_cells or any(c.get("execution_count") is None for c in code_cells):
        sys.exit("The notebook is not fully executed. Run All successfully before building the report.")
    if any(out.get("output_type") == "error" for c in code_cells for out in c.get("outputs", [])):
        sys.exit("The notebook contains execution errors. Fix them and Run All before building the report.")
    figures = notebook_figures(nb)
    source = CONTENT.read_text()
    team_html = "".join(f'<div class="team-member">{escape(name)} — {escape(student_id)}</div>' for student_id, name in TEAM_MEMBERS)
    source = source.replace("{{team}}", f'<div class="team"><div class="team-title">Team {TEAM_NUMBER}</div>{team_html}</div>')
    for key, value in result_tables().items():
        source = source.replace("{{" + key + "}}", value)
    included = []

    def insert_figure(match):
        name, height, caption = match.groups()
        if name not in figures:
            sys.exit(f"Missing notebook figure: {name}")
        included.append(name)
        return (f'<figure data-source="{name}" id="{name}"><img src="data:image/png;base64,{figures[name]["png"]}" '
                f'style="height:{height}mm" alt="{escape(caption)}"><figcaption>{escape(caption)}</figcaption></figure>')

    source = re.sub(r"\{\{figure:([^|}]+)\|(\d+)\|([^}]+)\}\}", insert_figure, source)
    if "{{" in source:
        sys.exit("Unresolved report template placeholder")
    pages = source.split("<!-- page -->")
    if len(included) != len(figures) or set(included) != set(figures):
        sys.exit("The assignment requires every notebook plot in the report, once each.")
    parts = [f'<section class="page"><div class="folio">F1 podium prediction · Team {TEAM_NUMBER} · Milestone 1 <span style="float:right">{i} / {len(pages)}</span></div>{md_to_html(page)}</section>'
             for i, page in enumerate(pages, 1)]
    html = f"<!doctype html><html><head><meta charset='utf-8'><title>{TITLE}</title><style>{CSS}</style></head><body>{''.join(parts)}</body></html>"
    Path("report.html").write_text(html, encoding="utf-8")
    gallery = ["<h1>F1 report: complete figure gallery</h1><p>All original executed notebook figures also appear, with explanations, in the analytical PDF and its appendices. Numerical tables and code remain in the notebook.</p>"]
    for number, (name, fig) in enumerate(figures.items(), 1):
        status = "Included in report PDF"
        gallery.append(f'<section id="{name}"><h2>{number}. {escape(name.replace("_", " "))}</h2><p>{status}; notebook cell index {fig["notebook_cell"]} (zero-based).</p><img style="width:100%" src="data:image/png;base64,{fig["png"]}"></section>')
    Path("report_figures.html").write_text("<!doctype html><html><head><meta charset='utf-8'><title>F1 complete figure gallery</title><style>body{font:15px Arial;max-width:1100px;margin:30px auto}section{margin:40px 0}h2{font-size:20px}</style></head><body>" + "".join(gallery) + "</body></html>")
    manifest = {
        "editorial_pages": len(pages), "notebook_sha256": hashlib.sha256(NOTEBOOK.read_bytes()).hexdigest(),
        "content_sha256": hashlib.sha256(CONTENT.read_bytes()).hexdigest(),
        "main_figures": included, "supplementary_figures": [name for name in figures if name not in included],
        "notebook_figures": {name: {"notebook_cell": fig["notebook_cell"], "image_sha256": hashlib.sha256(base64.b64decode(fig["png"])).hexdigest()} for name, fig in figures.items()},
    }
    Path("outputs/report_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Wrote report.html: {len(pages)} editorial pages, all {len(included)} notebook figures; report_figures.html provides the same figure gallery.")
    return Path("report.html").resolve()

def to_pdf(html_path):
    candidates = ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", shutil.which("google-chrome"),
                  shutil.which("chromium"), shutil.which("chromium-browser"), shutil.which("chrome")]
    chrome = next((c for c in candidates if c and Path(c).exists()), None)
    if chrome is None:
        print("Chrome not found: open report.html in a browser and use Print -> Save as PDF.")
        return
    pdf_path = Path("report.pdf").resolve()
    previous_mtime = pdf_path.stat().st_mtime_ns if pdf_path.exists() else None
    with tempfile.TemporaryDirectory(prefix="f1-report-chrome-") as profile:
        process = subprocess.Popen(
            [chrome, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
             f"--user-data-dir={profile}", f"--print-to-pdf={pdf_path}", html_path.as_uri()],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True,
        )
        try:
            for _ in range(9):
                try:
                    _, stderr = process.communicate(timeout=5)
                    break
                except subprocess.TimeoutExpired:
                    # Chrome can remain alive after export. Stop its isolated
                    # group once a newly written, complete PDF is available.
                    if pdf_path.exists() and pdf_path.stat().st_mtime_ns != previous_mtime:
                        current_pdf = pdf_path.read_bytes()
                        if current_pdf.startswith(b"%PDF-") and current_pdf.rstrip().endswith(b"%%EOF"):
                            os.killpg(process.pid, signal.SIGKILL)
                            _, stderr = process.communicate()
                            break
            else:
                raise subprocess.TimeoutExpired(process.args, 45)
        except subprocess.TimeoutExpired:
            # Some Chrome versions stay alive after printing. Stop only this
            # isolated process group, then verify a newly completed PDF below.
            os.killpg(process.pid, signal.SIGKILL)
            _, stderr = process.communicate()
        if not pdf_path.exists() or pdf_path.stat().st_mtime_ns == previous_mtime:
            sys.exit(f"Chrome did not produce a new report.pdf: {stderr.decode(errors='replace')[-1000:]}")
        pdf = pdf_path.read_bytes()
        if not pdf.startswith(b"%PDF-") or not pdf.rstrip().endswith(b"%%EOF"):
            sys.exit("Chrome produced an incomplete PDF; open report.html and export it manually.")
    from pypdf import PdfReader
    page_count = len(PdfReader(pdf_path).pages)
    expected = json.loads(Path("outputs/report_manifest.json").read_text())["editorial_pages"]
    if page_count != expected:
        sys.exit(f"Report layout overflow: {page_count} PDF pages; expected {expected}. Adjust report_content.md figure sizes or prose.")
    print(f"Wrote report.pdf ({page_count} pages)")

if __name__ == "__main__":
    to_pdf(build())
