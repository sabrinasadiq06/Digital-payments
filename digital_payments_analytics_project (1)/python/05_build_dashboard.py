"""
05_build_dashboard.py
-----------------------
Injects outputs/dashboard_data.json into dashboard/template.html to
produce the final, self-contained dashboard.html (no external data
fetches needed — everything is embedded for portability).
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
with open(ROOT / "outputs" / "dashboard_data.json", encoding="utf-8") as f:
    data = json.load(f)

template = (ROOT / "dashboard" / "template.html").read_text(encoding="utf-8")
final_html = template.replace("__DASHBOARD_DATA__", json.dumps(data))

out_path = ROOT / "outputs" / "dashboard.html"
out_path.write_text(final_html, encoding="utf-8")
print(f"Dashboard built -> {out_path} ({out_path.stat().st_size/1024:.1f} KB)")
