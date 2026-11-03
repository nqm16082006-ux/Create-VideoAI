from pathlib import Path
from typing import List, Dict

def format_ass_time(seconds: float) -> str:
    """Chuyển đổi số giây thành định dạng thời gian ASS: H:MM:SS.cs (centiseconds)"""
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    csecs = int(round((seconds - int(seconds)) * 100))
    if csecs >= 100:
        csecs = 99
    return f"{hrs}:{mins:02d}:{secs:02d}.{csecs:02d}"

def generate_ass_subtitles(
    words_data: List[Dict],
    output_ass_path: str | Path,
    video_width: int = 1080,
    video_height: int = 1920,
    words_per_group: int = 4
) -> Path:
    """
    Tạo file phụ đề .ass chuẩn phong cách Shorts/TikTok:
    - Chữ in hoa nổi bật, viền đen dày, bóng đổ.
    - Highlight màu vàng chanh (&H0000E5FF) cho từ đang đọc.
    - Nhóm 3-5 từ một lần hiển thị để tránh rối mắt người xem.
    """
    output_ass_path = Path(output_ass_path)
    output_ass_path.parent.mkdir(parents=True, exist_ok=True)

    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {video_width}
PlayResY: {video_height}
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,58,&H00FFFFFF,&H0000E5FF,&H00000000,&H80000000,-1,0,0,0,100,100,2,0,1,5,3,2,60,60,400,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events = []

    if not words_data:
        output_ass_path.write_text(header, encoding="utf-8")
        return output_ass_path

    # Nhóm các từ thành từng cụm ngắn (3-4 từ)
    groups = []
    for i in range(0, len(words_data), words_per_group):
        groups.append(words_data[i:i + words_per_group])

    for grp in groups:
        grp_start = grp[0]["start"]
        grp_end = grp[-1]["end"]

        # Cho mỗi từ trong cụm, tạo 1 event hiển thị cụm đó với từ hiện tại được tô sáng màu vàng
        for active_idx, active_word in enumerate(grp):
            word_start = active_word["start"]
            word_end = active_word["end"]
            if word_end <= word_start:
                word_end = word_start + 0.1

            start_str = format_ass_time(word_start)
            end_str = format_ass_time(word_end)

            # Xây dựng chuỗi text của cụm với từ active được highlight
            line_parts = []
            for j, w in enumerate(grp):
                txt = w["text"].upper()
                if j == active_idx:
                    # Tô màu vàng chanh và phóng to nhẹ 105%
                    line_parts.append(r"{\c&H002BFF&\fscx108\fscy108}" + txt + r"{\r}")
                else:
                    # Màu trắng tiêu chuẩn
                    line_parts.append(r"{\c&H00FFFFFF&}" + txt)

            formatted_text = " ".join(line_parts)
            events.append(f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{formatted_text}")

    full_content = header + "\n".join(events) + "\n"
    output_ass_path.write_text(full_content, encoding="utf-8")
    return output_ass_path

if __name__ == "__main__":
    from core import *
    from config import TEMP_DIR

    sample_words = [
        {"text": "Bí", "start": 0.0, "end": 0.3},
        {"text": "ẩn", "start": 0.3, "end": 0.6},
        {"text": "dưới", "start": 0.6, "end": 0.9},
        {"text": "đáy", "start": 0.9, "end": 1.2},
        {"text": "biển", "start": 1.2, "end": 1.6},
        {"text": "sâu", "start": 1.6, "end": 2.0},
    ]

    out_file = TEMP_DIR / "sample_sub.ass"
    generate_ass_subtitles(sample_words, out_file)
    print(f"File phụ đề ASS mẫu đã được tạo tại: {out_file}")
