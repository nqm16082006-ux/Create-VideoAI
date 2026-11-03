import argparse
import sys
from pathlib import Path
from config import DEFAULT_VOICE
from pipeline import create_ai_video

def main():
    parser = argparse.ArgumentParser(
        description="Tool tự động sản xuất Video AI đa nền tảng (TikTok, Shorts, Reels) không dính bản quyền."
    )
    parser.add_argument(
        "--topic", "-t",
        type=str,
        help="Chủ đề video muốn tạo (ví dụ: 'Bí ẩn đáy biển sâu', 'Động lực phát triển bản thân')"
    )
    parser.add_argument(
        "--voice", "-v",
        type=str,
        default=DEFAULT_VOICE,
        help="Giọng đọc: vi-VN-NamMinhNeural (Nam) hoặc vi-VN-HoaiMyNeural (Nữ)"
    )
    parser.add_argument(
        "--bgm",
        type=str,
        default=None,
        help="Đường dẫn file nhạc nền MP3 tuỳ chọn"
    )

    args = parser.parse_args()

    topic = args.topic
    if not topic:
        print("\n=== AI VIDEO GENERATOR (SHORTS / TIKTOK / REELS) ===")
        print("💡 Gợi ý chủ đề: 'Bí ẩn tam giác quỷ Bermuda', 'Sự thật về sao Hỏa', '3 thói quen của người thành công'")
        try:
            topic = input("\n👉 Nhập chủ đề video của bạn: ").strip()
        except EOFError:
            topic = "Bí ẩn đáy biển sâu"

    if not topic:
        topic = "Bí ẩn vũ trụ kỳ vĩ"

    custom_bgm = Path(args.bgm) if args.bgm else None
    create_ai_video(topic=topic, voice=args.voice, custom_bgm=custom_bgm)

if __name__ == "__main__":
    main()
