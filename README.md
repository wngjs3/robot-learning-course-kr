# Robot Learning 한국어 🤖🇰🇷

> **ETH Zurich — Robot Learning: From Fundamentals to Foundation Models** (2026 봄학기, [Oier Mees](https://www.oiermees.com))
> 강의의 비공식 한국어 학습 사이트입니다. 원저자의 사전 허락을 받아 제작되었습니다.

전체 강의 영상(본강의 11개 + 게스트 강연 10개)에 대해 다음을 제공합니다:

- **📖 시간대별 한국어 해설** — 영상 재생 위치에 맞춰 챕터별 쉬운 해설이 자동으로 따라옵니다
- **💬 한국어 자막** — 전체 스크립트의 자연스러운 한국어 번역 (영어 원문 병기 가능)
- **✨ 강의 요약** — 전체 요약, 핵심 포인트, 핵심 용어 정리
- 클릭하면 해당 시간으로 영상이 이동하는 양방향 싱크

## 로컬에서 보기

```bash
python3 -m http.server 4173
# http://localhost:4173 접속
```

(데이터를 `<script>` 태그로 로드하므로 `index.html`을 그냥 열어도 동작합니다.)

## 구조

```
index.html              # 메인 — 코스 소개, 강의 일정, 실습 과제
lecture.html?id=lec01   # 강의 재생 — 영상 + 시간 동기화 해설/자막/요약
assets/js/course-data.js  # 강의 스케줄/논문/게스트 메타데이터
data/ko/*.js(.json)       # 강의별 한국어 번역 데이터
scripts/
  fetch_transcripts.py  # 유튜브 영문 자막 다운로드
  translate.py          # Gemini 3.5 Flash 번역/요약 파이프라인 (재실행 시 이어하기)
  build_data_js.py      # JSON → 웹 로드용 JS 변환
```

### 번역 파이프라인 재실행

```bash
python3 -m venv .venv && .venv/bin/pip install youtube-transcript-api
echo "GEMINI_API_KEY=<your-key>" > scripts/.env
.venv/bin/python scripts/fetch_transcripts.py
.venv/bin/python scripts/translate.py
.venv/bin/python scripts/build_data_js.py
```

## 크레딧 & 라이선스

- 원저작물(강의, 슬라이드, 영상) © [Oier Mees](https://www.oiermees.com) & [ETH Zurich CVG](https://cvg.ethz.ch/)
  — [원본 강의 페이지](https://cvg.ethz.ch/lectures/Robot-Learning/) · [공식 GitHub](https://github.com/mees-robot-learning-course/ethz-course-2026)
- 한국어 번역·사이트 제작: Juheon Choi (KAIST). 번역에는 Google Gemini가 사용되었으며 오역이 있을 수 있습니다.
- 본 사이트는 교육 목적의 비상업 자료입니다.
