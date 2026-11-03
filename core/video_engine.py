import os
import subprocess
import json
import random
from pathlib import Path
from typing import List, Dict, Optional
from config import FFMPEG_EXE, VIDEO_WIDTH, VIDEO_HEIGHT, FPS, TEMP_DIR, BASE_DIR

def run_ffmpeg(cmd: List[str], check: bool = True) -> subprocess.CompletedProcess:
    """Chạy lệnh FFmpeg an toàn và in log nếu có lỗi."""
    res = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
        errors="replace",
        cwd=str(BASE_DIR)
    )
    if check and res.returncode != 0:
        print("[FFmpeg Error Log]:\n", (res.stderr or "")[-1000:])
        res.check_returncode()
    return res

def get_media_duration(file_path: str | Path) -> float:
    """Lấy độ dài chính xác của file âm thanh hoặc video (tính bằng giây)."""
    file_path = str(file_path)
    cmd = [
        FFMPEG_EXE,
        "-i", file_path,
        "-hide_banner"
    ]
    res = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
        errors="replace"
    )
    if res.stderr:
        for line in res.stderr.splitlines():
            if "Duration:" in line:
                try:
                    parts = line.split("Duration:")[1].split(",")[0].strip().split(":")
                    hrs = float(parts[0])
                    mins = float(parts[1])
                    secs = float(parts[2])
                    return hrs * 3600 + mins * 60 + secs
                except Exception:
                    pass
    return 3.0  # Mặc định an toàn


def make_scene_video(
    image_path: str | Path,
    audio_path: str | Path,
    output_clip_path: str | Path,
    motion_type: str = "zoom_in"
) -> Path:
    """
    Biến 1 ảnh tĩnh và 1 đoạn audio thành video clip 9:16 có chuyển động Ken Burns mượt mà.
    """
    image_path = Path(image_path).resolve()
    audio_path = Path(audio_path).resolve()
    output_clip_path = Path(output_clip_path).resolve()
    output_clip_path.parent.mkdir(parents=True, exist_ok=True)

    duration = get_media_duration(audio_path)
    # Thêm 0.2s đệm ở cuối mỗi cảnh để âm thanh không bị giật
    total_duration = duration + 0.2
    total_frames = int(total_duration * FPS)

    # Bộ lọc Ken Burns: Zoom in hoặc Zoom out
    # Chuẩn hoá kích thước ảnh về 1080x1920 trước khi zoom
    if motion_type == "zoom_in":
        zoom_expr = f"min(zoom+0.0015,1.15)"
    else:
        zoom_expr = f"if(lte(zoom,1.0),1.15,max(1.001,zoom-0.0015))"

    # Filter graph cho hình ảnh chuyển động
    filter_complex = (
        f"scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=increase,"
        f"crop={VIDEO_WIDTH}:{VIDEO_HEIGHT},"
        f"zoompan=z='{zoom_expr}':d={total_frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={VIDEO_WIDTH}x{VIDEO_HEIGHT}:fps={FPS}"
    )

    cmd = [
        FFMPEG_EXE, "-y",
        "-loop", "1",
        "-i", str(image_path),
        "-i", str(audio_path),
        "-filter_complex", filter_complex,
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-t", f"{total_duration:.2f}",
        str(output_clip_path)
    ]

    run_ffmpeg(cmd)
    return output_clip_path

def merge_scenes(clip_paths: List[Path], output_merged_path: str | Path) -> Path:
    """Nối danh sách các video cảnh thành 1 video duy nhất bằng Concat Demuxer."""
    output_merged_path = Path(output_merged_path).resolve()
    concat_list_file = TEMP_DIR / "concat_list.txt"

    with open(concat_list_file, "w", encoding="utf-8") as f:
        for p in clip_paths:
            # Trong file concat, đường dẫn cần dùng dấu gạch chéo /
            clean_path = str(p.resolve()).replace("\\", "/")
            f.write(f"file '{clean_path}'\n")

    cmd = [
        FFMPEG_EXE, "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_list_file),
        "-c", "copy",
        str(output_merged_path)
    ]
    run_ffmpeg(cmd)
    return output_merged_path

def burn_subtitles_and_audio(
    input_video: str | Path,
    ass_path: str | Path,
    output_final: str | Path,
    bgm_path: Optional[str | Path] = None
) -> Path:
    """
    Gắn phụ đề động (.ass) và lồng nhạc nền (BGM) nhẹ nhàng vào video thành phẩm.
    """
    input_video = Path(input_video).resolve()
    ass_path = Path(ass_path).resolve()
    output_final = Path(output_final).resolve()
    output_final.parent.mkdir(parents=True, exist_ok=True)

    # Chuyển ass_path thành relative path so với BASE_DIR để tránh lỗi colon Windows
    try:
        rel_ass = ass_path.relative_to(BASE_DIR).as_posix()
    except ValueError:
        rel_ass = str(ass_path).replace("\\", "/").replace(":", "\\:")

    video_duration = get_media_duration(input_video)

    # Bộ lọc phụ đề
    vf_sub = f"ass=filename='{rel_ass}'"

    if bgm_path and Path(bgm_path).exists():
        # Trộn Voice + BGM (Voice âm lượng 1.0, BGM âm lượng 0.12, fade out 1.5s cuối)
        bgm_path = Path(bgm_path).resolve()
        filter_complex = (
            f"[0:v]{vf_sub}[v];"
            f"[1:a]aloop=loop=-1:size=2e+09,volume=0.12,afade=t=out:st={max(0, video_duration - 1.5):.2f}:d=1.5[bgm];"
            f"[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=2[a]"
        )
        cmd = [
            FFMPEG_EXE, "-y",
            "-i", str(input_video),
            "-i", str(bgm_path),
            "-filter_complex", filter_complex,
            "-map", "[v]",
            "-map", "[a]",
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "20",
            "-c:a", "aac",
            "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-t", f"{video_duration:.2f}",
            str(output_final)
        ]
    else:
        # Không có BGM, chỉ burn phụ đề
        cmd = [
            FFMPEG_EXE, "-y",
            "-i", str(input_video),
            "-vf", vf_sub,
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "20",
            "-c:a", "copy",
            str(output_final)
        ]

    run_ffmpeg(cmd)
    return output_final
