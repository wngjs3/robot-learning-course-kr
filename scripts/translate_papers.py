# -*- coding: utf-8 -*-
"""논문 토론 자료를 한국어 웹페이지로 번역.

- arXiv 논문: ar5iv(HTML5) 버전을 가져와 수식(MathML)·그림·인용 링크를 placeholder로
  보호한 채 텍스트만 Gemini로 번역 → papers/<slug>.html 생성
- 블로그 글: 본문 추출 후 같은 방식으로 번역
- PDF 전용 자료: 건너뜀 (원문 링크만 유지)

사용: translate_papers.py <slug ...> | --all
재실행 시 papers/<slug>.html 있으면 건너뜀.
끝나면 assets/js/papers-data.js (원문 URL → 한국어 페이지 매핑) 재생성.
"""
import json
import os
import re
import sys
import time
import urllib.request

from bs4 import BeautifulSoup

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "papers")
os.makedirs(OUT_DIR, exist_ok=True)

API_KEY = ""
for line in open(os.path.join(ROOT, "scripts", ".env")):
    if line.startswith("GEMINI_API_KEY="):
        API_KEY = line.split("=", 1)[1].strip()
URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key={API_KEY}"

# (slug, 주차, 원문 URL, 제목, 저자/연도) — PDF 전용은 제외
PAPERS = [
    ("1803.07055", 2, "https://arxiv.org/abs/1803.07055", "Simple random search provides a competitive approach to RL", "Mania et al., 2018"),
    ("rl-hard", 2, "https://www.alexirpan.com/2018/02/14/rl-hard.html", "Deep RL Doesn't Work Yet", "Irpan, 2018"),
    ("1705.05363", 2, "https://arxiv.org/pdf/1705.05363", "Curiosity-driven Exploration by Self-supervised Prediction", "Pathak et al., 2017"),
    ("1905.11979", 3, "https://arxiv.org/abs/1905.11979", "Causal Confusion in Imitation Learning", "de Haan et al., 2019"),
    ("2112.01511", 3, "https://arxiv.org/abs/2112.01511", "The Surprising Effectiveness of Representation Learning for Visual Imitation", "Pari et al., 2021"),
    ("2010.14406", 3, "https://arxiv.org/pdf/2010.14406", "Transporter Networks", "Zeng et al., 2020"),
    ("1703.03864", 4, "https://arxiv.org/abs/1703.03864", "Evolution Strategies as a Scalable Alternative to RL", "Salimans et al., 2017"),
    ("1803.09956", 4, "https://arxiv.org/abs/1803.09956", "Learning Synergies between Pushing and Grasping", "Zeng et al., 2018"),
    ("2410.21845", 4, "https://arxiv.org/pdf/2410.21845", "Precise and Dexterous Robotic Manipulation via Human-in-the-Loop RL", "Luo et al., 2024"),
    ("1504.00702", 5, "https://arxiv.org/abs/1504.00702", "End-to-End Training of Deep Visuomotor Policies", "Levine et al., 2015"),
    ("2310.12931", 5, "https://arxiv.org/abs/2310.12931", "Eureka: Human-Level Reward Design via Coding LLMs", "Ma et al., 2023"),
    ("2209.08959", 5, "https://arxiv.org/pdf/2209.08959", "Latent Plans for Task Agnostic Offline RL", "Rosete-Beas et al., 2022"),
    ("2205.09991", 6, "https://arxiv.org/abs/2205.09991", "Planning with Diffusion for Flexible Behavior Synthesis", "Janner & Du et al., 2022"),
    ("2109.00137", 6, "https://arxiv.org/pdf/2109.00137", "Implicit Behavioral Cloning", "Florence et al., 2021"),
    ("2506.15799", 6, "https://arxiv.org/abs/2506.15799", "Steering Your Diffusion Policy with Latent Space RL", "Wagenmaker et al., 2025"),
    ("2106.01345", 7, "https://arxiv.org/abs/2106.01345", "Decision Transformer: RL via Sequence Modeling", "Chen et al., 2021"),
    ("2304.13705", 7, "https://arxiv.org/abs/2304.13705", "Learning Fine-Grained Bimanual Manipulation (ALOHA)", "Zhao et al., 2023"),
    ("2402.19469", 7, "https://arxiv.org/pdf/2402.19469", "Humanoid Locomotion as Next Token Prediction", "Radosavovic et al., 2024"),
    ("2302.00111", 8, "https://arxiv.org/abs/2302.00111", "Learning Universal Policies via Text-Guided Video Generation", "Du et al., 2023"),
    ("2509.24527", 8, "https://arxiv.org/abs/2509.24527", "Training Agents Inside of Scalable World Models", "Hafner et al., 2025"),
    ("2005.07648", 9, "https://arxiv.org/pdf/2005.07648", "Language Conditioned Imitation Learning over Unstructured Data", "Lynch et al., 2021"),
    ("2205.06175", 9, "https://arxiv.org/abs/2205.06175", "A Generalist Agent (Gato)", "Reed et al., 2022"),
    ("2511.14759", 9, "https://arxiv.org/abs/2511.14759", "π*0.6: a VLA That Learns From Experience", "Physical Intelligence, 2025"),
    ("2408.15980", 10, "https://arxiv.org/pdf/2408.15980", "In-Context Imitation Learning via Next-Token Prediction", "Fu et al., 2024"),
    ("2305.16291", 10, "https://arxiv.org/abs/2305.16291", "VOYAGER: An Open-Ended Embodied Agent with LLMs", "Wang et al., 2023"),
    ("2505.08243", 10, "https://arxiv.org/pdf/2505.08243", "Training Strategies for Efficient Embodied Reasoning", "Chen et al., 2025"),
    ("bitter-lesson", 11, "http://www.incompleteideas.net/IncIdeas/BitterLesson.html", "The Bitter Lesson", "Sutton, 2019"),
]


def http_get(url, timeout=120):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (paper-ko-translator)"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


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
            text = "".join(p.get("text", "") for p in resp["candidates"][0]["content"]["parts"]).strip()
            text = re.sub(r"^```(json)?\s*|\s*```$", "", text)
            try:
                return json.loads(text)
            except Exception:
                t = re.sub(r'\\(?!["\\/bfnrtu])', r"\\\\", text)
                return json.loads(t)
        except Exception as e:
            print(f"    retry ({type(e).__name__} {getattr(e, 'code', '')}) — {delay}s")
            time.sleep(delay)
            delay = min(delay * 2, 90)
    raise RuntimeError("Gemini 실패")


PROTECT_TAGS = ["math", "img", "svg", "code", "pre", "table"]
PROTECT_CLASSES = ["ltx_ref", "ltx_cite", "ltx_Math", "ltx_equation", "ltx_eqn_table"]


def _is_protect(el):
    if getattr(el, "name", None) in PROTECT_TAGS:
        return True
    return bool(getattr(el, "attrs", None)) and bool(set(el.get("class", [])) & set(PROTECT_CLASSES))


def protect_block(tag, soup):
    """블록 내 수식/그림/인용을 ⟦n⟧로 치환. 저장된 원본 html 목록 반환."""
    targets = []
    for el in tag.descendants:
        if not _is_protect(el):
            continue
        # 보호 대상 안에 중첩된 보호 대상은 부모가 통째로 치환되므로 제외
        if any(_is_protect(a) for a in el.parents if a is not tag and a.name != "[document]"):
            continue
        targets.append(el)
    saved = []
    for el in targets:
        marker = f"⟦{len(saved)}⟧"
        saved.append(str(el))
        el.replace_with(soup.new_string(marker))
    return saved


def restore_markers(html, saved):
    for i, s in enumerate(saved):
        html = html.replace(f"⟦{i}⟧", s, 1)
    return html


def translate_blocks(blocks, title):
    """blocks: [(id, marked_html)] → {id: ko_html}"""
    out = {}
    BATCH = 18
    for b in range(0, len(blocks), BATCH):
        batch = blocks[b:b + BATCH]
        items = json.dumps([{"i": i, "html": h} for i, h in batch], ensure_ascii=False)
        prompt = f"""당신은 로봇 러닝 분야 논문 전문 번역가입니다. 논문 "{title}"의 HTML 조각들을 한국어로 번역하세요.

규칙:
- 사람이 읽는 텍스트만 자연스러운 학술 한국어("~한다" 체)로 번역
- ⟦숫자⟧ 마커는 수식/그림/인용 자리표시자 — 절대 변경/삭제/순서변경 금지, 문장 내 적절한 위치에 유지
- HTML 태그와 속성은 그대로 유지 (태그 안 텍스트만 번역)
- 전문용어는 한국어 관례 + 필요시 영어 병기, 고유명사·기호·숫자는 원문 유지
- 섹션 제목의 번호(예: "3.1 ")는 유지

JSON 배열로만 출력: [{{"i": 번호, "ko": "번역된 HTML"}}, ...] ({len(batch)}개 모두 포함)

{items}"""
        result = gemini_json(prompt)
        got = 0
        if isinstance(result, dict):  # 모델이 객체로 감싼 경우
            result = result.get("translations") or result.get("items") or []
        for item in result:
            if not isinstance(item, dict):
                continue
            ko = item.get("ko") or item.get("html") or item.get("translation")
            try:
                if ko:
                    out[int(item["i"])] = str(ko)
                    got += 1
            except (KeyError, ValueError, TypeError):
                continue
        print(f"    blocks {b}-{b+len(batch)-1}: {got}/{len(batch)}")
        time.sleep(2)
    return out


PAGE_TMPL = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{title_ko} — Robot Learning 논문 한국어판</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Nanum+Gothic:wght@400;700;800&display=swap" />
<link rel="stylesheet" href="../assets/css/style.css" />
<link rel="stylesheet" href="../assets/css/paper.css" />
</head>
<body class="paper-page">
<div class="paper-shell">
  <div class="paper-top">
    <a href="../index.html">← Robot Learning 홈</a>
  </div>
  <header class="paper-head">
    <div class="paper-week">Week {week} · 논문 토론</div>
    <h1>{title_ko}</h1>
    <div class="paper-orig-title">{title_en} <span>— {authors}</span></div>
    <div class="paper-links">
      <a class="chip" href="{orig_url}" target="_blank" rel="noopener">원문 보기 ↗</a>
    </div>
    <p class="paper-note">이 번역은 AI(Gemini)로 생성된 비공식 번역으로 오역이 있을 수 있습니다.
    그림·수식은 원문( {source_name} )에서 가져왔으며, 저작권은 원저자에게 있습니다.</p>
  </header>
  <article class="paper-body">
{body}
  </article>
</div>
</body>
</html>
"""


def arxiv_id(url):
    m = re.search(r"arxiv\.org/(?:abs|pdf|html)/([0-9.]+[0-9])", url)
    return m.group(1) if m else None


def fetch_article(url):
    """(article_soup, base_img_url, source_name) 반환."""
    aid = arxiv_id(url)
    if aid:
        for base, name in [(f"https://ar5iv.labs.arxiv.org/html/{aid}", "ar5iv"),
                           (f"https://arxiv.org/html/{aid}", "arXiv HTML")]:
            try:
                html = http_get(base)
            except Exception:
                continue
            soup = BeautifulSoup(html, "lxml")
            art = soup.find("article") or soup.find(class_="ltx_document")
            if art:
                return art, base + "/", name, soup
        return None, None, None, None
    # 블로그/일반 HTML
    html = http_get(url)
    soup = BeautifulSoup(html, "lxml")
    art = (soup.find("article") or soup.find(class_="post") or
           soup.find(id="content") or soup.body)
    return art, url.rsplit("/", 1)[0] + "/", "원문 사이트", soup


def clean_article(art, soup):
    # 불필요 요소 제거
    for sel in [".ltx_page_footer", ".ltx_role_affiliation", "script", "style",
                ".ltx_pagination", "footer", "nav", ".post-nav", "#comments", ".sharedaddy"]:
        for el in art.select(sel):
            el.decompose()
    return art


BLOCK_SELECTOR = "h1, h2, h3, h4, h5, h6, p, figcaption, li, dd, dt, blockquote"


def process(slug, week, url, title_en, authors):
    out_path = os.path.join(OUT_DIR, f"{slug}.html")
    if os.path.exists(out_path):
        print(f"skip {slug}")
        return True
    print(f"== {slug}: {title_en}")
    art, img_base, source_name, soup = fetch_article(url)
    if art is None:
        print("    HTML 버전 없음 — 건너뜀")
        return False
    art = clean_article(art, soup)

    # 이미지: 절대 URL 계산 후 로컬로 다운로드 (papers/img/<slug>/)
    from urllib.parse import urljoin
    img_dir = os.path.join(OUT_DIR, "img", slug)
    for k, img in enumerate(art.find_all("img")):
        src = img.get("src", "")
        if not src or src.startswith("data:"):
            continue
        abs_url = src if src.startswith("http") else urljoin(img_base, src)
        ext = os.path.splitext(abs_url.split("?")[0])[1] or ".png"
        local = f"img/{slug}/{k:02d}{ext}"
        local_path = os.path.join(OUT_DIR, local)
        if not os.path.exists(local_path):
            try:
                os.makedirs(img_dir, exist_ok=True)
                data = http_get(abs_url)
                open(local_path, "wb").write(data)
            except Exception as e:
                print(f"    이미지 실패 {abs_url}: {e}")
                img["src"] = abs_url
                continue
        img["src"] = local

    # 참고문헌은 번역 제외
    bib = art.select_one(".ltx_bibliography")

    blocks, saved_map = [], {}
    for n, tag in enumerate(art.select(BLOCK_SELECTOR)):
        if bib and bib in tag.parents:
            continue
        if tag.find(BLOCK_SELECTOR.split(", ")):  # 자식에 블록 있으면 (li>p 등) 중복 방지
            inner_blocks = tag.find_all(["p", "h1", "h2", "h3", "h4", "h5", "h6"])
            if inner_blocks:
                continue
        text = tag.get_text(" ", strip=True)
        if not text or len(text) < 2 or not re.search(r"[A-Za-z]{2}", text):
            continue
        if len(text) > 4000:  # 비정상적으로 큰 블록은 원문 유지
            continue
        saved = protect_block(tag, soup)
        marked = tag.decode_contents()
        tag["data-koid"] = str(n)
        blocks.append((n, marked))
        saved_map[n] = saved

    print(f"    {len(blocks)} blocks")
    ko = translate_blocks(blocks, title_en)

    title_ko = ko.get(-1)  # 없음 — 제목은 별도 호출 대신 첫 h1 블록에서
    for n, marked in blocks:
        tag = art.find(attrs={"data-koid": str(n)})
        if tag is None:
            continue
        html = ko.get(n) or marked
        # 마커 검증: 누락 시 원문 유지
        for i in range(len(saved_map[n])):
            if f"⟦{i}⟧" not in html:
                html = marked
                break
        html = restore_markers(html, saved_map[n])
        tag.clear()
        frag = BeautifulSoup(html, "lxml")
        body = frag.body or frag
        for child in list(body.children if body.name in ("body", "[document]") else [body]):
            tag.append(child.extract())
        del tag["data-koid"]

    # 제목: 문서 첫 h1 텍스트
    h1 = art.find("h1")
    title_ko_text = h1.get_text(" ", strip=True) if h1 is not None else title_en
    if h1 is not None:
        h1.decompose()  # 헤더에 별도 표기하므로 본문 중복 제거

    page = PAGE_TMPL.format(
        title_ko=title_ko_text, title_en=title_en, authors=authors,
        week=week, orig_url=url, source_name=source_name,
        body=str(art),
    )
    open(out_path, "w", encoding="utf-8").write(page)
    print(f"    -> papers/{slug}.html ({os.path.getsize(out_path)//1024} KB)")
    return True


def build_index():
    done = {}
    for slug, week, url, title_en, authors in PAPERS:
        if os.path.exists(os.path.join(OUT_DIR, f"{slug}.html")):
            done[url] = f"papers/{slug}.html"
    js = "window.__PAPERS_KO = " + json.dumps(done, ensure_ascii=False, indent=1) + ";\n"
    open(os.path.join(ROOT, "assets", "js", "papers-data.js"), "w", encoding="utf-8").write(js)
    print(f"papers-data.js: {len(done)}편")


if __name__ == "__main__":
    args = sys.argv[1:]
    targets = PAPERS if "--all" in args else [p for p in PAPERS if p[0] in args]
    fails = []
    for p in targets:
        try:
            if not process(*p):
                fails.append(p[0])
        except Exception as e:
            print(f"!! {p[0]} 실패: {type(e).__name__}: {e}")
            fails.append(p[0])
    build_index()
    if fails:
        print("실패/건너뜀:", ", ".join(fails))
