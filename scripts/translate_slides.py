"""gemini-3.1-flash-image로 슬라이드 캡처를 한국어 번역 버전으로 재생성.

사용: translate_slides.py <key> [시작idx] [끝idx]
입력: data/slides/<key>/raw/NNN.png
출력: data/slides/<key>/ko/NNN.png  (이미 있으면 건너뜀 — 재실행 가능)
"""
import base64
import json
import os
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

API_KEY = os.environ.get("GEMINI_API_KEY", "")
if not API_KEY:
    for line in open(os.path.join(ROOT, "scripts", ".env")):
        if line.startswith("GEMINI_API_KEY="):
            API_KEY = line.split("=", 1)[1].strip()

MODEL = "gemini-3.1-flash-image"
URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={API_KEY}"

PROMPT = """이 이미지는 ETH Zurich의 'Robot Learning' 강의 슬라이드입니다.
이 슬라이드와 레이아웃·디자인·색상·사진·도표·로고를 최대한 동일하게 유지하면서, 텍스트만 자연스러운 한국어로 번역한 버전을 생성하세요.

규칙:
- 제목, 불릿, 캡션 등 모든 영어 텍스트를 한국어로 번역 (전문용어는 필요시 영어 병기)
- 고유명사(인명, 기관명, 논문명, 제품명)와 수식·기호·코드는 원문 유지
- 사진/그림/차트의 시각 요소는 그대로 유지
- 슬라이드 번호 등 레이아웃 요소 유지
- 깔끔하고 읽기 쉬운 한국어 폰트 스타일로"""


def translate_one(src, dst, retries=5):
    img_b64 = base64.b64encode(open(src, "rb").read()).decode()
    body = json.dumps({
        "contents": [{"parts": [
            {"inline_data": {"mime_type": "image/png", "data": img_b64}},
            {"text": PROMPT},
        ]}],
        "generationConfig": {"responseModalities": ["IMAGE"]},
    }).encode()
    delay = 10
    for attempt in range(retries):
        req = urllib.request.Request(URL, data=body, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                resp = json.load(r)
            for part in resp["candidates"][0]["content"]["parts"]:
                if "inlineData" in part:
                    open(dst, "wb").write(base64.b64decode(part["inlineData"]["data"]))
                    return True
            print(f"    이미지 파트 없음: {json.dumps(resp)[:200]}")
            return False
        except Exception as e:
            code = getattr(e, "code", None)
            detail = ""
            try:
                detail = e.read().decode()[:200]
            except Exception:
                pass
            print(f"    retry {attempt+1}/{retries} ({type(e).__name__} {code}) {detail} — {delay}s")
            time.sleep(delay)
            delay = min(delay * 2, 90)
    return False


def main():
    key = sys.argv[1]
    raw_dir = os.path.join(ROOT, "data", "slides", key, "raw")
    ko_dir = os.path.join(ROOT, "data", "slides", key, "ko")
    os.makedirs(ko_dir, exist_ok=True)
    files = sorted(f for f in os.listdir(raw_dir) if f.endswith(".png"))
    lo = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    hi = int(sys.argv[3]) if len(sys.argv) > 3 else len(files) - 1
    ok = fail = 0
    for f in files:
        idx = int(f.split(".")[0])
        if idx < lo or idx > hi:
            continue
        dst = os.path.join(ko_dir, f)
        if os.path.exists(dst):
            print(f"skip {f}")
            continue
        t0 = time.time()
        if translate_one(os.path.join(raw_dir, f), dst):
            ok += 1
            print(f"ok   {f} ({time.time()-t0:.0f}s)")
        else:
            fail += 1
            print(f"FAIL {f}")
        time.sleep(3)
    print(f"\n완료: {ok} ok, {fail} fail")


if __name__ == "__main__":
    main()
