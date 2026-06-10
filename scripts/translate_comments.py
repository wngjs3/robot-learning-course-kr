"""파이썬 코드의 주석(#)과 독스트링만 한국어로 번역. 코드는 절대 변경하지 않음.

방식:
  1) tokenize로 # 주석 위치 추출, ast로 독스트링 위치 추출
  2) 텍스트만 모아 Gemini로 배치 번역 (JSON)
  3) 소스에 위치 기반 치환 → AST 구조 비교로 코드 불변 검증 (실패 시 원본 유지)

대상: homework/**/*.py (assets 제외), homework/hw1*/src/*.ipynb 코드 셀
사용: translate_comments.py
"""
import ast
import glob
import io
import json
import os
import re
import sys
import time
import tokenize
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API_KEY = ""
for line in open(os.path.join(ROOT, "scripts", ".env")):
    if line.startswith("GEMINI_API_KEY="):
        API_KEY = line.split("=", 1)[1].strip()
URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key={API_KEY}"


def gemini_json(prompt, retries=5):
    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2, "responseMimeType": "application/json",
                             "maxOutputTokens": 65536, "thinkingConfig": {"thinkingBudget": 0}},
    }).encode()
    delay = 8
    for _ in range(retries):
        try:
            req = urllib.request.Request(URL, data=body, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=300) as r:
                resp = json.load(r)
            text = "".join(p.get("text", "") for p in resp["candidates"][0]["content"]["parts"])
            t = text.strip()
            t = re.sub(r"^```(json)?\s*|\s*```$", "", t)
            t = re.sub(r'\\(?!["\\/bfnrtu])', r"\\\\", t)
            return json.loads(t)
        except Exception as e:
            print(f"  retry ({type(e).__name__}) — {delay}s")
            time.sleep(delay)
            delay = min(delay * 2, 60)
    raise RuntimeError("번역 실패")


def has_korean(s):
    return re.search(r"[가-힣]", s) is not None


def translate_texts(texts, context):
    """영문 텍스트 리스트 → 한국어 리스트 (이미 한국어면 그대로)."""
    todo = [(i, t) for i, t in enumerate(texts) if not has_korean(t) and re.search(r"[a-zA-Z]{2}", t)]
    out = list(texts)
    BATCH = 60
    for b in range(0, len(todo), BATCH):
        batch = todo[b:b + BATCH]
        items = json.dumps([{"i": i, "en": t} for i, t in batch], ensure_ascii=False)
        prompt = f"""로봇 러닝 강의 과제 코드({context})의 주석/독스트링입니다. 각 항목의 "en"을 자연스러운 한국어로 번역하세요.
- 코드 식별자(변수·함수명), 수식, URL, 플래그(예: --train), TODO/NOTE/FIXME 같은 마커는 원문 유지
- "TODO:" 로 시작하면 "TODO:" 는 유지하고 뒷부분만 번역
- 간결한 기술 문서 톤. 줄바꿈(\\n) 구조 유지
JSON 배열로만 출력: [{{"i": 번호, "ko": "번역"}}, ...]

{items}"""
        result = gemini_json(prompt)
        for item in result:
            try:
                idx = int(item["i"])
                if item.get("ko"):
                    out[idx] = str(item["ko"])
            except (KeyError, ValueError, TypeError):
                continue
        time.sleep(2)
    return out


def normalize_ast(src):
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if node.body and isinstance(node.body[0], ast.Expr) and \
               isinstance(node.body[0].value, ast.Constant) and isinstance(node.body[0].value.value, str):
                node.body[0].value.value = ""
    return ast.dump(tree)


def collect_comments(src):
    """[(row, col, text)] — '#' 주석."""
    res = []
    try:
        for tok in tokenize.generate_tokens(io.StringIO(src).readline):
            if tok.type == tokenize.COMMENT:
                res.append((tok.start[0], tok.start[1], tok.string))
    except (tokenize.TokenizeError, IndentationError, SyntaxError):
        return None
    return res


def collect_docstrings(src):
    """[(start_line, start_col, end_line, end_col, value)]"""
    res = []
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return None
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if node.body and isinstance(node.body[0], ast.Expr) and \
               isinstance(node.body[0].value, ast.Constant) and isinstance(node.body[0].value.value, str):
                c = node.body[0].value
                res.append((c.lineno, c.col_offset, c.end_lineno, c.end_col_offset, c.value))
    return res


def doc_literal(text, indent):
    body = text.replace("\\", "\\\\").replace('"""', '\\"\\"\\"')
    if "\n" in body:
        # 여러 줄: 닫는 따옴표를 들여쓰기에 맞춰
        if not body.endswith("\n"):
            body += "\n"
        return '"""' + body + " " * indent + '"""'
    return '"""' + body + '"""'


def translate_python_source(src, context):
    """소스 → (번역된 소스 | None). 코드 불변 검증 포함."""
    comments = collect_comments(src)
    docs = collect_docstrings(src)
    if comments is None or docs is None:
        return None
    c_texts = [re.sub(r"^#\s?", "", c[2]) for c in comments]
    d_texts = [d[4] for d in docs]
    if not c_texts and not d_texts:
        return src  # 번역할 것 없음
    translated = translate_texts(c_texts + d_texts, context)
    c_ko, d_ko = translated[: len(c_texts)], translated[len(c_texts):]

    lines = src.split("\n")
    # 1) 주석 치환 (라인 끝부분만 교체)
    for (row, col, _), ko in zip(comments, c_ko):
        line = lines[row - 1]
        lines[row - 1] = line[:col] + "# " + ko.replace("\n", " ")
    # 2) 독스트링 치환 (뒤쪽 라인부터, 멀티라인 병합)
    for (sl, sc, el, ec, _), ko in zip(sorted(docs, reverse=True), list(reversed(d_ko))):
        lit = doc_literal(ko, sc)
        new_segment = lines[sl - 1][:sc] + lit + lines[el - 1][ec:]
        lines[sl - 1: el] = new_segment.split("\n")
    out = "\n".join(lines)

    try:
        if normalize_ast(out) != normalize_ast(src):
            return None
    except SyntaxError:
        return None
    return out


def do_py(path):
    bak = path + ".en.bak"
    if os.path.exists(bak):
        print(f"skip {path}")
        return "skip"
    src = open(path, encoding="utf-8").read()
    out = translate_python_source(src, os.path.basename(path))
    if out is None:
        print(f"FAIL {path} (검증 실패, 원본 유지)")
        return "fail"
    if out != src:
        open(bak, "w", encoding="utf-8").write(src)
        open(path, "w", encoding="utf-8").write(out)
    print(f"ok   {path}")
    return "ok"


def do_ipynb(path):
    marker = path + ".comments.done"
    if os.path.exists(marker):
        print(f"skip {path}")
        return "skip"
    nb = json.load(open(path, encoding="utf-8"))
    changed = 0
    for cell in nb["cells"]:
        if cell["cell_type"] != "code":
            continue
        src = "".join(cell["source"])
        # 주피터 매직(%·!)은 tokenize를 깨므로 임시 주석화
        masked = re.sub(r"^([%!].*)$", r"#__MAGIC__\1", src, flags=re.M)
        out = translate_python_source(masked, os.path.basename(path))
        if out is None:
            continue
        out = re.sub(r"^#__MAGIC__", "", out, flags=re.M)
        # 매직 임시주석이 번역되어 깨졌으면 셀 건너뜀
        if "__MAGIC__" in out:
            continue
        if out != src:
            cell["source"] = [l + "\n" for l in out.split("\n")[:-1]] + [out.split("\n")[-1]]
            changed += 1
    json.dump(nb, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    open(marker, "w").write("done")
    print(f"ok   {path} ({changed} code cells)")
    return "ok"


if __name__ == "__main__":
    stats = {"ok": 0, "fail": 0, "skip": 0}
    for p in sorted(glob.glob(os.path.join(ROOT, "homework", "**", "*.py"), recursive=True)):
        if "assets" in p or p.endswith(".en.bak"):
            continue
        stats[do_py(p)] += 1
    for p in sorted(glob.glob(os.path.join(ROOT, "homework", "**", "*.ipynb"), recursive=True)):
        if ".ipynb_checkpoints" in p:
            continue
        stats[do_ipynb(p)] += 1
    print(f"\n완료: {stats}")
