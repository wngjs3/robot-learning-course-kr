"""번역된 슬라이드를 웹용으로 빌드.

- data/slides/<key>/ko/NNN.png → data/slides/<key>/web/NNN.webp (용량 절감)
- data/slides/<key>/slides.js 생성 (window.__SLIDES["<key>"] = [...])
  번역본이 있는 슬라이드만 포함.
"""
import json
import os
import sys

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def build(key):
    base = os.path.join(ROOT, "data", "slides", key)
    ko_dir = os.path.join(base, "ko")
    web_dir = os.path.join(base, "web")
    os.makedirs(web_dir, exist_ok=True)
    slides = json.load(open(os.path.join(base, "slides.json")))

    # 카메라 컷(사람/강의실 화면) 제외 목록
    excl_path = os.path.join(base, "exclude.json")
    exclude = set(json.load(open(excl_path))) if os.path.exists(excl_path) else set()

    out = []
    for s in slides:
        name = s["file"].replace(".png", ".webp")
        dst = os.path.join(web_dir, name)
        if s["i"] in exclude:
            if os.path.exists(dst):
                os.remove(dst)
            continue
        src = os.path.join(ko_dir, s["file"])
        if not os.path.exists(src):
            continue
        if not os.path.exists(dst):
            img = Image.open(src)
            if img.width > 1280:
                img = img.resize((1280, int(img.height * 1280 / img.width)))
            img.save(dst, "WEBP", quality=82)
        out.append({"i": s["i"], "start": s["start"], "file": "web/" + name})

    # 목록 첫 슬라이드를 썸네일로 복사 (카메라 컷이 0번이어도 안전)
    if out:
        import shutil
        shutil.copy(os.path.join(base, out[0]["file"]), os.path.join(base, "thumb.webp"))

    js = (
        "window.__SLIDES = window.__SLIDES || {};\n"
        f"window.__SLIDES[{json.dumps(key)}] = "
        + json.dumps(out, ensure_ascii=False)
        + ";\n"
    )
    with open(os.path.join(base, "slides.js"), "w", encoding="utf-8") as f:
        f.write(js)
    total_kb = sum(os.path.getsize(os.path.join(web_dir, f)) for f in os.listdir(web_dir)) // 1024
    print(f"{key}: {len(out)}장 빌드 (web {total_kb} KB)")


if __name__ == "__main__":
    for k in sys.argv[1:]:
        build(k)
