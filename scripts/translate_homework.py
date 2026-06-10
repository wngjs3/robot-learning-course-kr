"""공식 과제 저장소의 문서를 한국어로 번역.

- homework/hw*/README.md, Installation_Guide.md → 한국어 마크다운으로 교체
- homework/hw*/src/*.ipynb → 마크다운 셀만 한국어로 교체 (코드 셀은 그대로)

사용: translate_homework.py <homework_dir>
원본은 .en.bak 확장자로 보존. 이미 .en.bak이 있으면 건너뜀(재실행 가능).
"""
import glob
import json
import os
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API_KEY = ""
for line in open(os.path.join(ROOT, "scripts", ".env")):
    if line.startswith("GEMINI_API_KEY="):
        API_KEY = line.split("=", 1)[1].strip()

URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key={API_KEY}"

RULES = """번역 규칙:
- 자연스럽고 정확한 한국어("~합니다" 체)로 번역
- 코드 블록, 셸 명령어, 파일 경로, URL, LaTeX 수식, 변수/함수명은 절대 변경하지 않음
- 마크다운 구조(헤딩 레벨, 리스트, 표, 링크)를 그대로 유지
- 전문용어는 한국어 관례를 따르되 처음 등장 시 영어 병기 (예: 모방 학습(Imitation Learning))
- 과제 점수, 마감일, 제출 방법 등의 정보는 정확히 보존"""


def gemini_text(prompt, retries=5):
    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2, "maxOutputTokens": 65536,
                             "thinkingConfig": {"thinkingBudget": 0}},
    }).encode()
    delay = 10
    for _ in range(retries):
        try:
            req = urllib.request.Request(URL, data=body, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=300) as r:
                resp = json.load(r)
            parts = resp["candidates"][0]["content"]["parts"]
            text = "".join(p.get("text", "") for p in parts).strip()
            if text:
                return text
        except Exception as e:
            print(f"  retry ({type(e).__name__} {getattr(e, 'code', '')}) — {delay}s")
        time.sleep(delay)
        delay = min(delay * 2, 90)
    raise RuntimeError("번역 실패")


def strip_fence(text):
    t = text.strip()
    if t.startswith("```"):
        lines = t.split("\n")
        if lines[0].startswith("```") and lines[-1].strip() == "```":
            return "\n".join(lines[1:-1])
    return t


def translate_md(path):
    bak = path + ".en.bak"
    if os.path.exists(bak):
        print(f"skip {path}")
        return
    src = open(path, encoding="utf-8").read()
    prompt = f"""아래는 ETH Zurich 'Robot Learning' 강의 과제의 마크다운 문서입니다. 전체를 한국어로 번역하세요.
{RULES}

번역된 마크다운 본문만 출력하세요 (코드펜스로 감싸지 말 것).

---
{src}"""
    out = strip_fence(gemini_text(prompt))
    os.rename(path, bak)
    open(path, "w", encoding="utf-8").write(out)
    print(f"ok   {path} ({len(src)} -> {len(out)} chars)")
    time.sleep(3)


def translate_ipynb(path):
    bak = path + ".en.bak"
    if os.path.exists(bak):
        print(f"skip {path}")
        return
    nb = json.load(open(path, encoding="utf-8"))
    md_cells = [(i, "".join(c["source"])) for i, c in enumerate(nb["cells"]) if c["cell_type"] == "markdown"]
    if not md_cells:
        return
    numbered = "\n\n".join(f"<<<CELL {i}>>>\n{src}" for i, src in md_cells)
    prompt = f"""아래는 Jupyter 노트북의 마크다운 셀들입니다 (ETH Zurich 'Robot Learning' 과제). 각 셀을 한국어로 번역하세요.
{RULES}

출력 형식: 각 셀마다 동일하게 <<<CELL 번호>>> 마커 다음 줄부터 번역문. 마커는 그대로, 셀 수({len(md_cells)}개)와 번호를 정확히 유지하세요.

{numbered}"""
    out = gemini_text(prompt)
    # 마커 기준으로 파싱
    import re
    chunks = re.split(r"<<<CELL (\d+)>>>", out)
    translated = {}
    for j in range(1, len(chunks) - 1, 2):
        translated[int(chunks[j])] = chunks[j + 1].strip()
    ok = 0
    for i, _ in md_cells:
        if i in translated and translated[i]:
            lines = translated[i].split("\n")
            nb["cells"][i]["source"] = [l + "\n" for l in lines[:-1]] + [lines[-1]]
            ok += 1
    import shutil
    shutil.copy(path, bak)
    json.dump(nb, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"ok   {path} ({ok}/{len(md_cells)} cells)")
    time.sleep(3)


def main(hw_dir):
    for md in sorted(glob.glob(os.path.join(hw_dir, "hw*", "*.md"))):
        translate_md(md)
    for nb in sorted(glob.glob(os.path.join(hw_dir, "hw*", "**", "*.ipynb"), recursive=True)):
        if ".ipynb_checkpoints" not in nb:
            translate_ipynb(nb)
    print("완료")


if __name__ == "__main__":
    main(sys.argv[1])
