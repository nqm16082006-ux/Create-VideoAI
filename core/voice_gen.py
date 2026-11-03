import asyncio
import json
from pathlib import Path
from typing import List, Dict, Tuple
import edge_tts
from config import DEFAULT_VOICE, TEMP_DIR

async def generate_speech(
    text: str,
    output_audio_path: str | Path,
    voice: str = DEFAULT_VOICE,
    rate: str = "+0%",
    pitch: str = "+0Hz"
) -> List[Dict]:
    """
    Tạo file âm thanh MP3 từ văn bản bằng edge-tts và trích xuất word-level timestamps.
    Tự động retry nếu mạng gián đoạn hoặc gặp lỗi NoAudioReceived.
    """
    output_audio_path = Path(output_audio_path)
    output_audio_path.parent.mkdir(parents=True, exist_ok=True)

    # Thử gọi TTS với retry và đổi giọng nếu nghẽn mạng
    voices_to_try = [voice, voice, "vi-VN-HoaiMyNeural" if voice != "vi-VN-HoaiMyNeural" else "vi-VN-NamMinhNeural", voice]

    for attempt, cur_voice in enumerate(voices_to_try):
        try:
            communicate = edge_tts.Communicate(text, cur_voice, rate=rate, pitch=pitch)
            audio_buffer = bytearray()
            words_data = []

            async for chunk in communicate.stream():
                chunk_type = chunk.get("type")
                if chunk_type == "audio":
                    audio_buffer.extend(chunk["data"])
                elif chunk_type == "WordBoundary":
                    start_sec = chunk["offset"] / 10_000_000
                    duration_sec = chunk["duration"] / 10_000_000
                    words_data.append({
                        "text": chunk["text"],
                        "start": round(start_sec, 3),
                        "end": round(start_sec + duration_sec, 3)
                    })
                elif chunk_type == "SentenceBoundary":
                    sentence_start = chunk["offset"] / 10_000_000
                    sentence_dur = chunk["duration"] / 10_000_000
                    sentence_text = chunk["text"].strip()
                    words = sentence_text.split()
                    if words:
                        total_chars = sum(len(w) for w in words)
                        cur_time = sentence_start
                        for w in words:
                            w_dur = (len(w) / total_chars) * sentence_dur
                            words_data.append({
                                "text": w,
                                "start": round(cur_time, 3),
                                "end": round(cur_time + w_dur, 3)
                            })
                            cur_time += w_dur

            # Chỉ ghi ra đĩa khi đã nhận được dữ liệu âm thanh hợp lệ
            if len(audio_buffer) > 1000:
                with open(output_audio_path, "wb") as audio_file:
                    audio_file.write(audio_buffer)
                return words_data

        except Exception as e:
            wait_time = (attempt + 1) * 1.5
            print(f"   [TTS Warning] Lần {attempt+1}/4 lỗi mạng: {e}. Đang đợi {wait_time:.1f}s để thử lại...")
            await asyncio.sleep(wait_time)

    # Fallback cứu cánh: nếu sau 4 lần mạng Microsoft vẫn lag, tạo 1 file audio im lặng 3s để FFmpeg không crash
    print("   [TTS Fallback] Tạo file âm thanh dự phòng an toàn...")
    from config import FFMPEG_EXE
    import subprocess
    cmd = [
        FFMPEG_EXE, "-y",
        "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
        "-t", "3",
        "-c:a", "mp3",
        str(output_audio_path)
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return words_data



def generate_voice_sync(text: str, output_audio_path: str | Path, voice: str = DEFAULT_VOICE) -> List[Dict]:
    """Hàm đồng bộ bọc hàm async để dễ gọi từ code thông thường."""
    return asyncio.run(generate_speech(text, output_audio_path, voice))

if __name__ == "__main__":
    test_out = TEMP_DIR / "sample_voice.mp3"
    print("Đang tạo thử giọng nói tiếng Việt...")
    timestamps = generate_voice_sync(
        "Khám phá vũ trụ bao la với những điều bí ẩn chưa từng được tiết lộ.",
        test_out
    )
    print(f"File âm thanh đã lưu tại: {test_out}")
    print(f"Tổng số từ nhận diện được timestamps: {len(timestamps)}")
    print("3 từ đầu tiên:", timestamps[:3])
