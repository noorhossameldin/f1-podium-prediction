"""Build the analytical report (report.html + report.pdf) from the executed notebook.

The report is the notebook without its code: every markdown cell, every computed
conclusion, every figure and the small result tables. Run the notebook first, then:

    python make_report.py
"""
import base64
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
TITLE = "Formula 1 Podium Prediction — Milestone 1 Analytical Report"
TEAM_MEMBERS = [
    ("58-20196", "Mohamed Ahmed Mohamed Abdelaziz"),
    ("58-3004", "Daniel Maged Shehata Youssef"),
    ("58-7146", "Marwan Montasser Morad Hassan Metwally"),
    ("58-2686", "Noor Hossameldin Ahmed Aboouf Ali"),
]

MAX_TABLE_ROWS, MAX_TABLE_COLS = 24, 10      # larger tables stay in the notebook only
MAX_TEXT_LINES, MAX_TEXT_WIDTH = 14, 150

CSS = """
@page { size: A4; margin: 16mm 15mm; }
body { font-family: Helvetica, Arial, sans-serif; font-size: 10pt; line-height: 1.42; color: #1a1a1a; }
h1 { font-size: 20pt; margin: 0 0 4pt; }
h2 { font-size: 14.5pt; margin-top: 22pt; padding-top: 6pt; border-top: 1.5px solid #2a78d6; break-after: avoid; }
h3 { font-size: 11.5pt; margin-top: 14pt; break-after: avoid; }
p, li { orphans: 3; widows: 3; }
img { max-width: 100%; display: block; margin: 8pt auto; break-inside: avoid; }
table { border-collapse: collapse; font-size: 8.3pt; margin: 8pt 0; break-inside: avoid; }
th, td { border: 0.6px solid #c9c8c2; padding: 2.5pt 5pt; text-align: left; vertical-align: top; }
th { background: #f1f0ec; }
code { font-family: Menlo, Consolas, monospace; font-size: 8.6pt; background: #f4f3ef; padding: 0 2pt; border-radius: 2pt; }
pre { font-family: Menlo, Consolas, monospace; font-size: 7.8pt; background: #f7f6f2; padding: 5pt 7pt; white-space: pre-wrap; break-inside: avoid; }
blockquote { border-left: 3px solid #eb6834; margin: 8pt 0; padding: 2pt 10pt; background: #fdf3ee; }
.team { color: #52514e; margin-bottom: 10pt; }
.note { color: #52514e; font-size: 9pt; }
"""

def md_to_html(text):
    return markdown.markdown(text, extensions=["tables", "sane_lists"])

def small_table(html):
    rows = html.count("<tr")
    header = re.search(r"<thead>(.*?)</thead>", html, re.S)
    cols = max((r.count("<th") for r in re.findall(r"<tr.*?</tr>", header.group(1), re.S)), default=0) if header else 0
    return rows <= MAX_TABLE_ROWS and cols <= MAX_TABLE_COLS

def clean_table(html):
    html = re.sub(r"<style.*?</style>", "", html, flags=re.S)          # drop pandas' notebook styling
    return re.sub(r'\s(class|border|style|id)="[^"]*"', "", html)

def short_text(text):
    lines = text.rstrip().split("\n")
    return len(lines) <= MAX_TEXT_LINES and max(len(l) for l in lines) <= MAX_TEXT_WIDTH

def escape(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def build():
    nb = nbformat.read(NOTEBOOK, as_version=4)
    code_cells = [c for c in nb.cells if c.cell_type == "code" and c.source.strip()]
    if not code_cells or any(c.get("execution_count") is None for c in code_cells):
        sys.exit("The notebook is not fully executed. Run All successfully before building the report.")
    if any(out.get("output_type") == "error" for c in code_cells for out in c.get("outputs", [])):
        sys.exit("The notebook contains execution errors. Fix them and Run All before building the report.")
    team_html = "<br>".join(f"{escape(name)} — {escape(student_id)}" for student_id, name in TEAM_MEMBERS)
    parts = [f"<h1>{TITLE}</h1>", f'<div class="team"><strong>Team members</strong><br>{team_html}</div>',
             '<p class="note">This report is generated from the executed notebook <code>f1_podium_prediction.ipynb</code>: it contains the '
             "notebook's explanations, computed conclusions, figures and small result tables, without the code. "
             "Section numbers are the same as in the notebook. Large tables are in the notebook only.</p>"]
    first = True
    for cell in nb.cells:
        if cell.cell_type == "markdown":
            src = cell.source
            if first:                                       # the notebook title cell: keep the description, drop the duplicate title
                src = re.sub(r"^# .*\n", "", src, count=1)
                first = False
            parts.append(md_to_html(src))
            continue
        for out in cell.get("outputs", []):
            data = out.get("data", {})
            if "image/png" in data:
                parts.append(f'<img src="data:image/png;base64,{data["image/png"].strip()}">')
            elif "text/markdown" in data:
                parts.append(md_to_html(data["text/markdown"]))
            elif "text/html" in data and "<table" in data["text/html"]:
                if small_table(data["text/html"]):
                    parts.append(clean_table(data["text/html"]))
            elif out.get("output_type") == "stream" and out.get("name") == "stdout" and short_text(out["text"]):
                parts.append(f"<pre>{escape(out['text'].rstrip())}</pre>")
    html = f"<!doctype html><html><head><meta charset='utf-8'><title>{TITLE}</title><style>{CSS}</style></head><body>{''.join(parts)}</body></html>"
    Path("report.html").write_text(html, encoding="utf-8")
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
            _, stderr = process.communicate(timeout=45)
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
    print("Wrote report.pdf")

if __name__ == "__main__":
    to_pdf(build())
