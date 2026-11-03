import os
import sys
from pathlib import Path
import imageio_ffmpeg
from dotenv import load_dotenv

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
FONTS_DIR = ASSETS_DIR / "fonts"
BGM_DIR = ASSETS_DIR / "bgm"
OUTPUT_DIR = BASE_DIR / "output"
TEMP_DIR = BASE_DIR / "temp"

# Ensure directories exist
for p in [ASSETS_DIR, FONTS_DIR, BGM_DIR, OUTPUT_DIR, TEMP_DIR]:
    p.mkdir(parents=True, exist_ok=True)

# FFmpeg Executable
FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()

# Default Video Configuration (Vertical 9:16 for Shorts / TikTok / Reels)
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
FPS = 30

# Font Configuration
DEFAULT_FONT = FONTS_DIR / "Arial-Bold.ttf"

# Voice Configuration
# Edge-TTS voices: vi-VN-NamMinhNeural (Male), vi-VN-HoaiMyNeural (Female)
DEFAULT_VOICE = os.getenv("DEFAULT_VOICE", "vi-VN-NamMinhNeural")

# API Keys (optional if using free fallback)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
FAL_KEY = os.getenv("FAL_KEY", "")
