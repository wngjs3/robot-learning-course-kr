"""슬라이드 캡처를 '발표 슬라이드 vs 카메라/강의실 화면'으로 분류.

raw 프레임을 Gemini 비전으로 판별해 data/slides/<key>/exclude.json
(카메라 컷 인덱스 목록)을 생성. 결과는 classify.json에 캐시되어 재실행 가능.

사용: classify_slides.py <key ...>
"""
import base64
import io
import json
import os
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API_KEY = ""
for line in open(os.path.join(ROOT, "scripts", ".env")):
    if line.startswith("GEMINI_API_KEY="):
        API_KEY = line.split("=", 1)[1].strip()
MODEL = "gemini-2.5-flash-lite"
URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={API_KEY}"

PROMPT = """이 이미지는 대학 강의 녹화 영상의 한 프레임입니다. 다음 중 하나로만 답하세요:
- slide : 발표 슬라이드 화면 (텍스트, 도표, 그림, 데모 영상이 포함된 슬라이드 포함)
- camera : 강의실/발표자/청중을 찍은 카메라 화면 (사람이나 강의실이 화면의 주된 내용)
답은 단어 하나만."""


def classify_one(path, retries=4):
    img = Image.open(path).convert("RGB")
    img.thumbnail((480, 480))
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=70)
    b64 = base64.b64encode(buf.getvalue()).decode()
    body = json.dumps({
        "contents": [{"parts": [
            {"inline_data": {"mime_type": "image/jpeg", "data": b64}},
            {"text": PROMPT},
        ]}],
        "generationConfig": {"temperature": 0, "maxOutputTokens": 1500},
    }).encode()
    delay = 5
    for _ in range(retries):
        try:
            req = urllib.request.Request(URL, data=body, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=120) as r:
                resp = json.load(r)
            text = "".join(p.get("text", "") for p in resp["candidates"][0]["content"]["parts"]).strip().lower()
            if "camera" in text:
                return "camera"
            if "slide" in text:
                return "slide"
        except Exception:
            pass
        time.sleep(delay)
        delay *= 2
    return "slide"  # 판별 실패 시 보수적으로 유지


def process(key):
    base = os.path.join(ROOT, "data", "slides", key)
    slides = json.load(open(os.path.join(base, "slides.json")))
    cache_path = os.path.join(base, "classify.json")
    cache = json.load(open(cache_path)) if os.path.exists(cache_path) else {}

    todo = [s for s in slides if str(s["i"]) not in cache]
    if todo:
        def work(s):
            p = os.path.join(base, "raw", s["file"])
            if not os.path.exists(p):
                return s["i"], "slide"
            return s["i"], classify_one(p)
        with ThreadPoolExecutor(max_workers=12) as ex:
            for i, label in ex.map(work, todo):
                cache[str(i)] = label
        json.dump(cache, open(cache_path, "w"))

    exclude = [int(i) for i, v in cache.items() if v == "camera"]
    json.dump(sorted(exclude), open(os.path.join(base, "exclude.json"), "w"))
    print(f"{key}: {len(slides)}장 중 카메라 컷 {len(exclude)}장 제외 {sorted(exclude)[:12]}")


if __name__ == "__main__":
    for k in sys.argv[1:]:
        process(k)
