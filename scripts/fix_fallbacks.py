"""data/ko/*.json에서 영어로 남은 블록을 한 개씩 정밀 재번역."""
import json
import glob
import os
import re
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API_KEY = ""
for line in open(os.path.join(ROOT, "scripts", ".env")):
    if line.startswith("GEMINI_API_KEY="):
        API_KEY = line.split("=", 1)[1].strip()
URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key={API_KEY}"


def translate_one(text, title, retries=6):
    prompt = f"""ETH Zurich 로봇 러닝 강의 "{title}"의 자막 한 구절입니다. 자연스러운 한국어로 번역하세요 (구어체 강의 톤, "~합니다" 체). 번역문만 출력:

{text}"""
    body = json.dumps({"contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.3, "maxOutputTokens": 2000, "thinkingConfig": {"thinkingBudget": 0}}}).encode()
    delay = 5
    for _ in range(retries):
        try:
            req = urllib.request.Request(URL, data=body, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=120) as r:
                resp = json.load(r)
            t = "".join(p.get("text", "") for p in resp["candidates"][0]["content"]["parts"]).strip()
            if t and re.search(r"[가-힣]", t):
                return t
        except Exception:
            pass
        time.sleep(delay); delay = min(delay*2, 40)
    return None


for p in sorted(glob.glob(os.path.join(ROOT, "data", "ko", "*.json"))):
    d = json.load(open(p))
    changed = 0
    for b in d["blocks"]:
        if b["ko"].strip() == b["en"].strip() and re.search(r"[A-Za-z]{3}", b["en"]):
            ko = translate_one(b["en"], d["title_en"])
            if ko:
                b["ko"] = ko; changed += 1
            time.sleep(1)
    if changed:
        json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False)
        print(f"{d['key']}: {changed}개 보강")
print("자막 보강 완료")
