"""papers/*.html 본문(참고문헌 제외)에서 영어로 남은 단락을 재번역."""
import glob
import json
import os
import re
import sys
import time
import urllib.request

from bs4 import BeautifulSoup

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API_KEY = ""
for line in open(os.path.join(ROOT, "scripts", ".env")):
    if line.startswith("GEMINI_API_KEY="):
        API_KEY = line.split("=", 1)[1].strip()
URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key={API_KEY}"


def translate_html(inner, retries=6):
    prompt = f"""다음은 논문의 HTML 단락입니다. 사람이 읽는 영어 텍스트만 자연스러운 학술 한국어("~한다" 체)로 번역하세요.
- HTML 태그/속성, <math>, 수식, 숫자, 고유명사, 인용은 그대로 유지
- 번역된 HTML 조각만 출력 (코드펜스 없이):

{inner}"""
    body = json.dumps({"contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2, "maxOutputTokens": 8000, "thinkingConfig": {"thinkingBudget": 0}}}).encode()
    delay = 5
    for _ in range(retries):
        try:
            req = urllib.request.Request(URL, data=body, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=180) as r:
                resp = json.load(r)
            t = "".join(p.get("text", "") for p in resp["candidates"][0]["content"]["parts"]).strip()
            t = re.sub(r"^```(html)?\s*|\s*```$", "", t)
            if t and re.search(r"[가-힣]", t):
                return t
        except Exception:
            pass
        time.sleep(delay); delay = min(delay*2, 40)
    return None


def needs_tr(tag):
    t = tag.get_text(" ", strip=True)
    if len(t) < 25 or re.search(r"[가-힣]", t):
        return False
    return bool(re.search(r"[A-Za-z]{4}.*[A-Za-z]{4}.*[A-Za-z]{4}", t))


for p in sorted(glob.glob(os.path.join(ROOT, "papers", "*.html"))):
    soup = BeautifulSoup(open(p, encoding="utf-8").read(), "lxml")
    body = soup.select_one(".paper-body")
    if not body:
        continue
    bib = body.select_one(".ltx_bibliography")
    changed = 0
    for tag in body.find_all(["p", "h2", "h3", "li"]):
        if bib and bib in tag.parents:
            continue
        if tag.find(["p", "li"]):  # 컨테이너 중복 방지
            continue
        if not needs_tr(tag):
            continue
        ko = translate_html(tag.decode_contents())
        if ko:
            frag = BeautifulSoup(ko, "lxml")
            inner = frag.body or frag
            tag.clear()
            for child in list(inner.children):
                tag.append(child.extract())
            changed += 1
        time.sleep(1)
    if changed:
        open(p, "w", encoding="utf-8").write(str(soup))
        print(f"{os.path.basename(p)}: {changed}개 단락 보강")
print("논문 단락 보강 완료")
