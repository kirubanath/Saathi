"""
Run this after placing your transcripts file at data/transcripts_raw.py.

Usage:
    python data/write_transcripts.py
"""

from pathlib import Path
import importlib.util
import sys

TRANSCRIPT_MAP = {
    "vid_001": "aspiration/career_and_jobs/interview_confidence/vid_001.txt",
    "vid_002": "aspiration/career_and_jobs/interview_confidence/vid_002.txt",
    "vid_003": "aspiration/career_and_jobs/interview_confidence/vid_003.txt",
    "vid_004": "aspiration/career_and_jobs/career_foundations/vid_004.txt",
    "vid_005": "aspiration/career_and_jobs/career_foundations/vid_005.txt",
    "vid_006": "aspiration/english_speaking/spoken_english_basics/vid_006.txt",
    "vid_007": "aspiration/english_speaking/spoken_english_basics/vid_007.txt",
}

ROOT = Path(__file__).parent
SEED_DIR = ROOT / "seed_transcripts"
RAW_FILE = ROOT / "transcripts_raw.py"


def main():
    if not RAW_FILE.exists():
        print(f"Not found: {RAW_FILE}")
        sys.exit(1)

    spec = importlib.util.spec_from_file_location("transcripts_raw", RAW_FILE)
    raw = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(raw)

    for var, rel_path in TRANSCRIPT_MAP.items():
        text = getattr(raw, var, None)
        if text is None:
            print(f"SKIP {var} — not found in transcripts_raw.py")
            continue
        dest = SEED_DIR / rel_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(text.strip())
        print(f"OK   {dest.relative_to(ROOT.parent)}")


if __name__ == "__main__":
    main()
