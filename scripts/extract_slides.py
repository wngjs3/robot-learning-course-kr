"""강의 영상에서 슬라이드 전환 구간을 감지해 슬라이드별 대표 프레임을 캡처.

방식:
  1) 영상을 2초 간격 저해상도 프레임으로 샘플링
  2) 인접 프레임의 perceptual hash(dhash) 거리로 전환 지점 감지
  3) 각 안정 구간(>=MIN_SEG초)의 끝부분에서 고해상도 프레임 캡처
     (빌드업 애니메이션이 완성된 상태를 캡처하기 위함)

사용: extract_slides.py <key> <video.mp4>
출력: data/slides/<key>/raw/NNN.png + data/slides/<key>/slides.json
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLE_EVERY = 2.0   # 초
HASH_THRESH = 10     # dhash 해밍 거리 임계값 (64비트 중)
MIN_SEG = 8.0        # 이보다 짧은 구간은 전환 애니메이션/카메라 컷으로 보고 무시


def dhash(img, size=8):
    g = img.convert("L").resize((size + 1, size))
    px = list(g.getdata())
    bits = 0
    for r in range(size):
        for c in range(size):
            bits = (bits << 1) | (1 if px[r * (size + 1) + c] > px[r * (size + 1) + c + 1] else 0)
    return bits


def hamming(a, b):
    return bin(a ^ b).count("1")


def main(key, video):
    out_dir = os.path.join(ROOT, "data", "slides", key)
    raw_dir = os.path.join(out_dir, "raw")
    os.makedirs(raw_dir, exist_ok=True)

    tmp = tempfile.mkdtemp(prefix="slides_")
    print("1) 저해상도 샘플링...")
    subprocess.run([
        "ffmpeg", "-loglevel", "error", "-i", video,
        "-vf", f"fps=1/{SAMPLE_EVERY},scale=320:-1",
        os.path.join(tmp, "%05d.jpg"),
    ], check=True)
    files = sorted(os.listdir(tmp))
    print(f"   {len(files)} samples")

    print("2) 전환 지점 감지...")
    hashes = [dhash(Image.open(os.path.join(tmp, f))) for f in files]
    boundaries = [0]
    for i in range(1, len(hashes)):
        if hamming(hashes[i - 1], hashes[i]) > HASH_THRESH:
            boundaries.append(i)
    boundaries.append(len(hashes))

    segments = []
    for a, b in zip(boundaries, boundaries[1:]):
        t0, t1 = a * SAMPLE_EVERY, b * SAMPLE_EVERY
        if t1 - t0 >= MIN_SEG:
            segments.append((t0, t1))
    print(f"   {len(segments)} stable segments")

    print("3) 고해상도 캡처...")
    slides = []
    for i, (t0, t1) in enumerate(segments):
        cap_t = max(t0, t1 - 3.0)  # 구간 끝 3초 전 (완성된 슬라이드)
        fn = f"{i:03d}.png"
        subprocess.run([
            "ffmpeg", "-loglevel", "error", "-ss", str(cap_t), "-i", video,
            "-frames:v", "1", os.path.join(raw_dir, fn),
        ], check=True)
        slides.append({"i": i, "start": round(t0, 1), "end": round(t1, 1), "file": fn})

    json.dump(slides, open(os.path.join(out_dir, "slides.json"), "w"), ensure_ascii=False, indent=1)
    shutil.rmtree(tmp)
    print(f"완료: {len(slides)}장 -> data/slides/{key}/raw/")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
