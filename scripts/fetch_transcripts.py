"""유튜브 자막(영문)을 다운로드해 data/raw/{key}.json 으로 저장. 이미 받은 파일은 건너뜀."""
import json
import os
import sys
import time

from youtube_transcript_api import YouTubeTranscriptApi
from videos import VIDEOS

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(ROOT, "data", "raw")
os.makedirs(RAW_DIR, exist_ok=True)

api = YouTubeTranscriptApi()
failed = []

for key, vid, title_en, title_ko, kind in VIDEOS:
    out = os.path.join(RAW_DIR, f"{key}.json")
    if os.path.exists(out):
        print(f"skip {key} (exists)")
        continue
    try:
        fetched = api.fetch(vid, languages=["en", "en-US", "en-GB"])
        data = {
            "key": key,
            "video_id": vid,
            "title_en": title_en,
            "title_ko": title_ko,
            "kind": kind,
            "language": fetched.language_code,
            "segments": fetched.to_raw_data(),
        }
        with open(out, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        n = len(data["segments"])
        dur = data["segments"][-1]["start"] if n else 0
        print(f"ok   {key} {vid}: {n} segments, ~{dur/60:.0f} min")
        time.sleep(1.5)
    except Exception as e:
        print(f"FAIL {key} {vid}: {type(e).__name__}: {e}")
        failed.append(key)
        time.sleep(3)

if failed:
    print("\nFailed:", ", ".join(failed))
    sys.exit(1)
print("\nAll transcripts downloaded.")
