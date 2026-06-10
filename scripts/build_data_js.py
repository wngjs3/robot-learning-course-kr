"""data/ko/*.json → data/ko/*.js (window.__LECTURES 등록).
file:// 환경에서도 fetch 없이 동작하도록 스크립트 태그로 로드하는 형태로 변환."""
import glob
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KO_DIR = os.path.join(ROOT, "data", "ko")

for path in sorted(glob.glob(os.path.join(KO_DIR, "*.json"))):
    key = os.path.splitext(os.path.basename(path))[0]
    data = json.load(open(path))
    js = (
        "window.__LECTURES = window.__LECTURES || {};\n"
        f"window.__LECTURES[{json.dumps(key)}] = "
        + json.dumps(data, ensure_ascii=False)
        + ";\n"
    )
    out = os.path.join(KO_DIR, f"{key}.js")
    with open(out, "w", encoding="utf-8") as f:
        f.write(js)
    print(f"built data/ko/{key}.js ({os.path.getsize(out)//1024} KB)")
