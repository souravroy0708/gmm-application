"""Run ONCE on a computer with internet:  python tools/fetch_fonts.py
Downloads Anek Bangla + Hind Siliguri into static/fonts/ and writes static/css/fonts.css,
so the app no longer needs Google Fonts (works offline, loads faster on slow networks)."""
import re, urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
CSS_URL = ("https://fonts.googleapis.com/css2?family=Anek+Bangla:wght@500;700;800"
           "&family=Hind+Siliguri:wght@400;500;600;700&display=swap")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0 Safari/537.36"  # makes Google return woff2

def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=60).read()

css = get(CSS_URL).decode()
out = BASE / "static" / "fonts"; out.mkdir(parents=True, exist_ok=True)
blocks = re.findall(r"/\*\s*([\w-]+)\s*\*/\s*(@font-face\s*\{.*?\})", css, re.S)
keep, total = [], 0
for subset, blk in blocks:
    if subset not in ("bengali", "latin", "latin-ext"):   # skip devanagari etc. - not needed
        continue
    fam = re.search(r"font-family:\s*'([^']+)'", blk).group(1).replace(" ", "")
    wt = re.search(r"font-weight:\s*(\d+)", blk).group(1)
    url = re.search(r"url\((https://[^)]+)\)", blk).group(1)
    name = f"{fam}-{wt}-{subset}.woff2"
    data = get(url); (out / name).write_bytes(data); total += len(data)
    keep.append(blk.replace(url, f"../fonts/{name}"))
    print("saved", name, len(data) // 1024, "KB")
(BASE / "static" / "css" / "fonts.css").write_text("\n".join(keep) + "\n")
print(f"done: {len(keep)} files, {total // 1024} KB total -> static/css/fonts.css")
