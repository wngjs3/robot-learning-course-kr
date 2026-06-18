"""Gemini 3.5 Flash로 자막을 한국어로 번역/요약.

산출물 data/ko/{key}.json:
  blocks:   ~40초 단위로 묶은 자막 블록의 자연스러운 한국어 번역 (시간 동기화 자막용)
  chapters: ~5분 단위 챕터 — 제목 + 쉬운 한국어 해설 (영상 옆 설명 패널용)
  summary:  전체 요약 + 핵심 포인트 + 핵심 용어

배치 단위로 캐시(data/cache)에 저장되므로 중단 후 재실행해도 이어서 진행됨.
사용법: .venv/bin/python scripts/translate.py [key ...]   (인자 없으면 전체)
"""
import json
import os
import re
import sys
import time
import urllib.request

from videos import VIDEOS

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(ROOT, "data", "raw")
KO_DIR = os.path.join(ROOT, "data", "ko")
CACHE_DIR = os.path.join(ROOT, "data", "cache")
os.makedirs(KO_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)

API_KEY = os.environ.get("GEMINI_API_KEY", "")
if not API_KEY:
    env_path = os.path.join(ROOT, "scripts", ".env")
    if os.path.exists(env_path):
        for line in open(env_path):
            if line.startswith("GEMINI_API_KEY="):
                API_KEY = line.split("=", 1)[1].strip()
if not API_KEY:
    sys.exit("GEMINI_API_KEY가 없습니다. scripts/.env 또는 환경변수로 설정하세요.")

MODEL = "gemini-3.5-flash"
URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={API_KEY}"

BLOCK_SECONDS = 40       # 자막 블록 길이
BATCH_BLOCKS = 30        # 한 번의 API 호출로 번역할 블록 수


def salvage_json(text):
    """잘린/지저분한 JSON 응답 복구 시도."""
    t = text.strip()
    if t.startswith("```"):
        t = re.sub(r"^```(json)?\s*|\s*```$", "", t)
    try:
        return json.loads(t)
    except Exception:
        pass
    # LaTeX 등에서 나온 잘못된 이스케이프(\pi, \( 등)를 리터럴 백슬래시로 정정
    t = re.sub(r'\\(?!["\\/bfnrtu])', r"\\\\", t)
    try:
        return json.loads(t)
    except Exception:
        pass
    # 배열이 중간에 잘린 경우: 마지막 완전한 객체까지 자르고 닫기
    if t.lstrip().startswith("["):
        last = t.rfind("}")
        if last > 0:
            try:
                return json.loads(t[: last + 1] + "]")
            except Exception:
                pass
    raise ValueError("JSON 복구 실패")


def gemini(prompt, retries=4):
    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.3,
            "responseMimeType": "application/json",
            "maxOutputTokens": 65536,
            "thinkingConfig": {"thinkingBudget": 0},
        },
    }).encode()
    delay = 10
    for attempt in range(retries):
        req = urllib.request.Request(URL, data=body, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                resp = json.load(r)
            cand = resp.get("candidates", [{}])[0]
            finish = cand.get("finishReason")
            parts = cand.get("content", {}).get("parts", [])
            text = "".join(p.get("text", "") for p in parts)
            if not text:
                print(f"    빈 응답 (finishReason={finish})")
                raise ValueError("empty response")
            try:
                return salvage_json(text)
            except ValueError:
                print(f"    JSON 파싱 실패 (finishReason={finish}) head={text[:120]!r} tail={text[-120:]!r}")
                raise
        except Exception as e:
            code = getattr(e, "code", None)
            print(f"    retry {attempt+1}/{retries} ({type(e).__name__} {code}) — {delay}s 대기")
            time.sleep(delay)
            delay = min(delay * 2, 120)
    raise RuntimeError("Gemini 호출 반복 실패")


def make_blocks(segments):
    """캡션 조각을 ~BLOCK_SECONDS초 블록으로 병합."""
    blocks = []
    cur_text, cur_start = [], None
    for seg in segments:
        text = re.sub(r"\s+", " ", seg["text"]).strip()
        if not text or text in ("[Music]", "[Applause]", "[Laughter]"):
            continue
        if cur_start is None:
            cur_start = seg["start"]
        cur_text.append(text)
        if seg["start"] + seg.get("duration", 0) - cur_start >= BLOCK_SECONDS:
            blocks.append({"start": round(cur_start, 1), "en": " ".join(cur_text)})
            cur_text, cur_start = [], None
    if cur_text:
        blocks.append({"start": round(cur_start, 1), "en": " ".join(cur_text)})
    return blocks


def cache_path(key, name):
    return os.path.join(CACHE_DIR, f"{key}_{name}.json")


def cached_call(key, name, prompt):
    p = cache_path(key, name)
    if os.path.exists(p):
        return json.load(open(p))
    result = gemini(prompt)
    json.dump(result, open(p, "w"), ensure_ascii=False)
    time.sleep(4)  # rate limit 완화
    return result


def translate_batch(key, title_en, blocks, bi, size, translations):
    """blocks[bi:bi+size] 번역 시도. 실패 시 반으로 쪼개 재귀."""
    batch = blocks[bi:bi + size]
    if not batch:
        return
    name = f"blocks_{bi:04d}_{size}"
    numbered = "\n".join(f"[{i}] {b['en']}" for i, b in enumerate(batch))
    prompt = f"""당신은 로봇 러닝(robot learning) 분야 전문 번역가입니다.
아래는 ETH Zurich 강의 "{title_en}"의 영어 자막 블록들입니다 (자동 생성 자막이라 문장 부호가 없고 오인식 단어가 있을 수 있음).

각 블록을 자연스럽고 읽기 쉬운 한국어로 번역하세요.
- 전문 용어는 한국어 관례를 따르되, 필요하면 영어를 병기 (예: 모방 학습(imitation learning), policy는 '정책')
- 자동 자막의 오인식은 문맥으로 바로잡아 번역
- 구어체 강의 톤을 살리되 깔끔한 문어체로 정리 ("~합니다" 체)
- 수식/기호 언급은 그대로 유지
- 시간 동기화 자막으로 쓰이므로 각 블록의 영어 텍스트 범위 안에 있는 내용만 번역
- 앞/뒤 블록의 문장을 당겨오거나 넘겨서 번역하지 말 것. 블록이 문장 중간에서 끊기면 그 범위 안에서만 자연스럽게 처리

JSON 배열로만 출력: [{{"i": 블록번호, "ko": "번역문"}}, ...] (블록 수: {len(batch)}개, 모든 블록 포함 필수)

{numbered}"""
    try:
        result = cached_call(key, name, prompt)
    except Exception:
        if size <= 6:
            print(f"    blocks {bi}-{bi+size-1}: 포기 (원문 유지)")
            return
        half = size // 2
        print(f"    blocks {bi}-{bi+size-1}: 실패 → {half}개씩 분할 재시도")
        translate_batch(key, title_en, blocks, bi, half, translations)
        translate_batch(key, title_en, blocks, bi + half, size - half, translations)
        return
    got = 0
    for item in result:
        try:
            idx = bi + int(item["i"])
        except (KeyError, ValueError, TypeError):
            continue
        if bi <= idx < min(bi + size, len(blocks)) and item.get("ko"):
            translations[idx] = str(item["ko"]).strip()
            got += 1
    print(f"    blocks {bi}-{bi+size-1}: {got}/{size} 번역됨")


def translate_blocks(key, title_en, blocks):
    """블록을 배치로 나눠 번역. 결과: ko 텍스트 리스트(블록 순서대로)."""
    translations = [None] * len(blocks)
    for bi in range(0, len(blocks), BATCH_BLOCKS):
        translate_batch(key, title_en, blocks, bi, min(BATCH_BLOCKS, len(blocks) - bi), translations)
    missing = [i for i, t in enumerate(translations) if t is None]
    if missing:
        print(f"    누락 {len(missing)}개 → 원문 유지: {missing[:10]}")
        for i in missing:
            translations[i] = blocks[i]["en"]
    return translations


def make_chapters_and_summary(key, title_en, title_ko, blocks):
    def fmt(s):
        return f"{int(s//60):02d}:{int(s%60):02d}"
    full = "\n".join(f"[{fmt(b['start'])}] {b['en']}" for b in blocks)
    total_min = int(blocks[-1]["start"] // 60) + 1 if blocks else 0
    n_chapters = max(5, min(16, total_min // 5))
    prompt = f"""당신은 로봇 러닝을 한국 학생들에게 가르치는 친절한 조교입니다.
아래는 ETH Zurich 강의 "{title_en}" ({title_ko}, 총 약 {total_min}분)의 영어 자막 전문입니다 (타임스탬프 [mm:ss] 포함).

다음 JSON 객체를 출력하세요:
{{
  "summary": "강의 전체를 4-6문장으로 요약한 한국어 문단",
  "takeaways": ["핵심 포인트 한국어 문장", ... 5-7개],
  "terms": [{{"term": "영어 용어", "ko": "한국어 용어", "desc": "한 문장 설명"}}, ... 6-10개],
  "chapters": [
    {{"start": 시작초(정수), "title": "챕터 제목(한국어, 간결)", "explain": "이 구간에서 다루는 내용을 학부생도 이해할 수 있게 3-5문장으로 쉽게 풀어 쓴 한국어 해설. 직관적 예시나 비유가 있으면 포함."}},
    ... 약 {n_chapters}개, 강의 흐름이 바뀌는 지점 기준, start는 반드시 오름차순
  ]
}}

자막 전문:
{full}"""
    return cached_call(key, "chapters", prompt)


def process(key):
    raw = json.load(open(os.path.join(RAW_DIR, f"{key}.json")))
    out_path = os.path.join(KO_DIR, f"{key}.json")
    if os.path.exists(out_path):
        print(f"skip {key} (완료됨)")
        return
    print(f"== {key}: {raw['title_en']}")
    blocks = make_blocks(raw["segments"])
    print(f"    {len(blocks)} blocks")
    translations = translate_blocks(key, raw["title_en"], blocks)
    meta = make_chapters_and_summary(key, raw["title_en"], raw["title_ko"], blocks)
    out = {
        "key": key,
        "video_id": raw["video_id"],
        "title_en": raw["title_en"],
        "title_ko": raw["title_ko"],
        "kind": raw["kind"],
        "summary": meta.get("summary", ""),
        "takeaways": meta.get("takeaways", []),
        "terms": meta.get("terms", []),
        "chapters": meta.get("chapters", []),
        "blocks": [
            {"start": b["start"], "en": b["en"], "ko": t}
            for b, t in zip(blocks, translations)
        ],
    }
    json.dump(out, open(out_path, "w", encoding="utf-8"), ensure_ascii=False)
    print(f"    -> data/ko/{key}.json 저장")


if __name__ == "__main__":
    keys = sys.argv[1:] or [v[0] for v in VIDEOS]
    errors = []
    for k in keys:
        try:
            process(k)
        except Exception as e:
            print(f"!! {k} 실패: {type(e).__name__}: {e} — 다음 영상 계속")
            errors.append(k)
    if errors:
        print("\n실패한 영상:", ", ".join(errors))
        sys.exit(1)
    print("\n번역 완료.")
