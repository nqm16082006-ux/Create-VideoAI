import time
import shutil
from pathlib import Path
from typing import Dict, Any, Optional

from config import (
    TEMP_DIR, OUTPUT_DIR, BGM_DIR, DEFAULT_VOICE,
    VIDEO_WIDTH, VIDEO_HEIGHT
)
from core.script_gen import generate_script
from core.voice_gen import generate_speech
from core.image_gen import generate_image
from core.subtitle_gen import generate_ass_subtitles
from core.video_engine import (
    get_media_duration, make_scene_video, merge_scenes,
    burn_subtitles_and_audio
)

def create_ai_video(
    topic: str,
    voice: str = DEFAULT_VOICE,
    custom_bgm: Optional[Path] = None,
    output_filename: Optional[str] = None
) -> Path:
    """
    Quy trình hoàn chỉnh từ Kịch bản -> Giọng nói -> Hình ảnh FLUX -> Ghép Video + Nhạc nền + Phụ đề động.
    """
    timestamp = int(time.time())
    work_dir = TEMP_DIR / f"project_{timestamp}"
    work_dir.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 60)
    print(f"🎬 BẮT ĐẦU SẢN XUẤT VIDEO AI CHO CHỦ ĐỀ: '{topic}'")
    print("=" * 60)

    # 1. Tạo kịch bản
    print("\n[1/5] 📝 Đang sinh kịch bản và phân cảnh bằng AI...")
    script_data = generate_script(topic)
    title = script_data.get("title", f"Video_{timestamp}")
    scenes = script_data.get("scenes", [])
    print(f"-> Tiêu đề: {title}")
    print(f"-> Tổng số phân cảnh: {len(scenes)}")

    # 2. Xử lý từng cảnh (Voice, Image, Motion)
    scene_clips = []
    all_words_timeline = []
    cumulative_time = 0.0

    print("\n[2/5] 🎙️ & 🎨 Đang tạo Giọng đọc tiếng Việt và Hình ảnh AI 9:16 cho từng cảnh...")
    for idx, scene in enumerate(scenes, start=1):
        scene_id = scene.get("scene_id", idx)
        text = scene.get("text", "")
        img_prompt = scene.get("image_prompt", "")

        print(f"\n--- Xử lý Cảnh {scene_id}/{len(scenes)} ---")
        print(f"   Thoại: \"{text}\"")
        print(f"   Prompt ảnh: {img_prompt[:60]}...")

        # A. Tạo giọng đọc
        audio_path = work_dir / f"audio_{scene_id}.mp3"
        import asyncio
        words_data = asyncio.run(generate_speech(text, audio_path, voice=voice))
        scene_duration = get_media_duration(audio_path)
        actual_clip_duration = scene_duration + 0.2

        # B. Dồn timeline cho phụ đề toàn bài
        for w in words_data:
            all_words_timeline.append({
                "text": w["text"],
                "start": round(cumulative_time + w["start"], 3),
                "end": round(cumulative_time + w["end"], 3)
            })

        # C. Sinh hình ảnh AI
        image_path = work_dir / f"image_{scene_id}.jpg"
        generate_image(img_prompt, image_path)
        time.sleep(1.5)  # Tránh rate-limit khi gọi API ảnh miễn phí liên tục

        # D. Tạo video clip cho cảnh kèm hiệu ứng Ken Burns
        # Luân phiên zoom_in và zoom_out để tạo nhịp điệu thị giác
        motion = "zoom_in" if scene_id % 2 != 0 else "zoom_out"
        clip_path = work_dir / f"clip_{scene_id}.mp4"
        print(f"   Render clip chuyển động: {motion} ({actual_clip_duration:.1f}s)...")
        make_scene_video(image_path, audio_path, clip_path, motion_type=motion)
        scene_clips.append(clip_path)


        cumulative_time += actual_clip_duration
        time.sleep(1.0)  # Giãn cách giữa các phân cảnh để kết nối TTS & API ổn định 100%

    # 3. Nối các cảnh thành 1 video liền mạch

    print("\n[3/5] 🎞️ Đang ghép các phân cảnh thành video thô...")
    raw_video = work_dir / "raw_concat.mp4"
    merge_scenes(scene_clips, raw_video)

    # 4. Tạo phụ đề động Karaoke
    print("\n[4/5] 💬 Đang tạo file phụ đề Karaoke động phong cách TikTok...")
    ass_path = work_dir / "subtitles.ass"
    generate_ass_subtitles(
        all_words_timeline,
        ass_path,
        video_width=VIDEO_WIDTH,
        video_height=VIDEO_HEIGHT,
        words_per_group=3
    )

    # 5. Hoàn thiện: Lồng nhạc nền & Gắn phụ đề
    print("\n[5/5] 🎶 Đang mix nhạc nền & gắn phụ đề thành phẩm...")
    bgm_file = custom_bgm or (BGM_DIR / "ambient_calm.mp3")

    import unicodedata
    nfkd_form = unicodedata.normalize('NFKD', title)
    ascii_title = "".join([c for c in nfkd_form if not unicodedata.combining(c)])
    clean_title = "".join(c if c.isalnum() else "_" for c in ascii_title).strip("_")
    clean_title = clean_title[:25] or "video"

    out_name = output_filename or f"{clean_title}_{timestamp}.mp4"
    final_output = OUTPUT_DIR / out_name

    burn_subtitles_and_audio(raw_video, ass_path, final_output, bgm_path=bgm_file)


    print("\n" + "=" * 60)
    print(f"🎉 HOÀN THÀNH VIDEO THÀNH PHẨM!")
    print(f"📁 Vị trí file: {final_output}")
    print(f"⏱️ Độ dài video: {get_media_duration(final_output):.1f} giây")
    print("=" * 60 + "\n")

    return final_output
