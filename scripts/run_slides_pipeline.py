"""여러 강의의 슬라이드 파이프라인 일괄 실행:
다운로드(720p) → 슬라이드 추출 → Gemini 한국어 번역 → 웹 빌드 → 영상 삭제

사용: run_slides_pipeline.py <key ...>   (예: lec02 lec03 ... / guest02 ...)
각 단계는 결과물이 있으면 건너뛰므로 중단 후 재실행 가능.
"""
import os
import subprocess
import sys

from videos import VIDEOS

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = os.path.join(ROOT, ".venv", "bin", "python")
YTDLP = "/tmp/ytdlp-venv/bin/yt-dlp"
VID = {v[0]: v[1] for v in VIDEOS}


def run(key):
    print(f"\n===== {key} =====", flush=True)
    base = os.path.join(ROOT, "data", "slides", key)
    video = f"/tmp/{key}.mp4"

    if not os.path.exists(os.path.join(base, "slides.json")):
        if not os.path.exists(video):
            print("1) 다운로드...", flush=True)
            subprocess.run([
                YTDLP, "-f", "bestvideo[height<=720]/best[height<=720]",
                "--no-playlist", "-q", "--no-warnings",
                "-o", video, f"https://www.youtube.com/watch?v={VID[key]}",
            ], check=True)
        subprocess.run([PY, os.path.join(ROOT, "scripts", "extract_slides.py"), key, video], check=True)
    else:
        print("추출 결과 있음 — 건너뜀", flush=True)

    subprocess.run([PY, os.path.join(ROOT, "scripts", "translate_slides.py"), key], check=True)
    subprocess.run([PY, os.path.join(ROOT, "scripts", "build_slides_js.py"), key], check=True)

    if os.path.exists(video):
        os.remove(video)


if __name__ == "__main__":
    keys = sys.argv[1:]
    failed = []
    for k in keys:
        try:
            run(k)
        except Exception as e:
            print(f"!! {k} 실패: {e} — 다음 강의 계속", flush=True)
            failed.append(k)
    print("\n전체 완료." + (f" 실패: {', '.join(failed)}" if failed else ""))
