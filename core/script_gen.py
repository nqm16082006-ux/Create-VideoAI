import os
import json
import re
from typing import Dict, List, Any
import requests
from config import OPENAI_API_KEY, GEMINI_API_KEY, GROQ_API_KEY

SYSTEM_PROMPT = """
Bạn là một đạo diễn và biên kịch video ngắn triệu view chuyên nghiệp cho TikTok, YouTube Shorts và Facebook Reels.
Nhiệm vụ của bạn: Khi nhận được một chủ đề hoặc yêu cầu, hãy viết kịch bản dạng kịch tính, hấp dẫn và chia thành 4 đến 5 cảnh (scenes).

QUY TẮC BẮT BUỘC:
1. Mỗi scene tương ứng với 1 câu ngắn gọn, súc tích (khoảng 8-15 từ), cuốn hút ngay từ 3 giây đầu tiên (Hook).
2. Viết prompt hình ảnh AI chi tiết bằng tiếng Anh (cho mô hình FLUX / Midjourney), mô tả rõ ánh sáng, góc máy, chủ thể, phong cách cinematic 9:16.
3. Trả về DUY NHẤT một chuỗi JSON hợp lệ, KHÔNG thêm bất kỳ lời giải thích nào khác ngoài JSON.

Cấu trúc JSON yêu cầu:
{
  "title": "Tiêu đề video",
  "scenes": [
    {
      "scene_id": 1,
      "text": "Câu thoại tiếng Việt hấp dẫn...",
      "image_prompt": "Cinematic vertical 9:16 shot of ... dramatic lighting, photorealistic 8k"
    }
  ]
}
"""

def generate_script_gemini(topic: str) -> Dict[str, Any]:
    """Gọi Gemini API chính thức (hỗ trợ các key AIzaSy... từ Google AI Studio)."""
    # Thử qua các model đang hoạt động của Google AI Studio
    for model_name in ["gemini-2.5-flash", "gemini-flash-latest", "gemini-2.0-flash"]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_API_KEY}"
        payload = {
            "contents": [
                {"parts": [{"text": f"{SYSTEM_PROMPT}\n\nChủ đề: {topic}"}]}
            ],
            "generationConfig": {
                "response_mime_type": "application/json"
            }
        }
        try:
            resp = requests.post(url, json=payload, timeout=20)
            if resp.status_code == 200:
                raw_text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(raw_text)
        except Exception:
            continue
    raise ValueError("Gemini API call failed")

def generate_script_openai(topic: str) -> Dict[str, Any]:
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Chủ đề: {topic}"}
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.7
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    resp.raise_for_status()
    content = resp.json()["choices"][0]["message"]["content"]
    return json.loads(content)

def generate_script_groq(topic: str) -> Dict[str, Any]:
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    # Danh sách các mô hình đang hoạt động trên Groq
    models_to_try = ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.8-27b"]

    for model in models_to_try:
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Chủ đề: {topic}"}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.7
        }
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=25)
            if resp.status_code == 200:
                content = resp.json()["choices"][0]["message"]["content"]
                return json.loads(content)
        except Exception:
            continue

    raise ValueError("All Groq models failed")


def generate_dynamic_smart_script(topic: str) -> Dict[str, Any]:
    """
    Tự động phân tích chủ đề bất kỳ của người dùng và sinh kịch bản phù hợp 100%
    ngay cả khi chưa có API Key hoặc API ngoài bị lỗi.
    """
    topic_lower = topic.lower()

    # Chủ đề: Động lực, thói quen, lười biếng, thành công, phát triển bản thân
    if any(k in topic_lower for k in ["lười", "động lực", "thói quen", "thành công", "phát triển", "kỷ luật", "thay đổi", "bản thân"]):
        return {
            "title": f"Bí Quyết Vượt Lười: {topic}",
            "scenes": [
                {
                    "scene_id": 1,
                    "text": "Sự thoải mái tạm thời chính là liều thuốc độc đang từ từ hủy hoại tương lai của bạn.",
                    "image_prompt": "Cinematic 9:16 vertical shot of a tired person sitting in dark room staring at glowing phone screen, moody cinematic lighting, photorealistic 8k"
                },
                {
                    "scene_id": 2,
                    "text": "Người thành công không phải không lười, mà họ biết cách bắt đầu ngay cả khi không có hứng.",
                    "image_prompt": "Determined athlete tying shoes at sunrise, golden hour light breaking through morning fog, inspirational atmosphere, 9:16 vertical"
                },
                {
                    "scene_id": 3,
                    "text": "Chỉ cần 5 phút hành động mỗi ngày, bạn đã đánh bại 90 phần trăm những người chỉ biết trì hoãn.",
                    "image_prompt": "Close-up of hourglass with glowing golden sand flowing rapidly, dramatic rim light, conceptual art, 9:16 vertical"
                },
                {
                    "scene_id": 4,
                    "text": "Kỷ luật hôm nay chính là tấm vé dẫn đến sự tự do thực sự của ngày mai.",
                    "image_prompt": "Successful modern professional standing on top floor glass balcony overlooking city skyline at dawn, triumphant mood, 9:16 vertical"
                },
                {
                    "scene_id": 5,
                    "text": "Đừng chần chừ nữa, hãy đứng dậy và bắt đầu hành động ngay lúc này!",
                    "image_prompt": "Silhouette of a person taking bold confident step forward onto a shining golden path into the horizon, epic cinematic masterpiece, 9:16 vertical"
                }
            ]
        }

    # Chủ đề: Tiền bạc, tài chính, làm giàu, kinh doanh
    elif any(k in topic_lower for k in ["tiền", "giàu", "tài chính", "đầu tư", "kinh doanh", "triệu phú"]):
        return {
            "title": f"Tư Duy Tài Chính: {topic}",
            "scenes": [
                {
                    "scene_id": 1,
                    "text": "Người nghèo làm việc vì tiền, nhưng người giàu bắt tiền phải làm việc cho họ.",
                    "image_prompt": "Cinematic vertical 9:16 shot of ancient golden coins transforming into digital neon data streams, dramatic financial lighting"
                },
                {
                    "scene_id": 2,
                    "text": "Sai lầm lớn nhất của đa số mọi người là tiêu tiền trước rồi mới tiết kiệm phần còn lại.",
                    "image_prompt": "A stylish modern wallet with glowing credit cards on a sleek dark marble table, luxury aesthetic, 9:16 vertical"
                },
                {
                    "scene_id": 3,
                    "text": "Đầu tư vào tri thức bản thân luôn đem lại mức lãi suất cao nhất trong đời.",
                    "image_prompt": "A sophisticated library with glowing holographic financial charts floating in mid-air, 8k cinematic resolution, 9:16 vertical"
                },
                {
                    "scene_id": 4,
                    "text": "Xây dựng nhiều nguồn thu nhập thụ động là chìa khóa duy nhất để tự do tài chính.",
                    "image_prompt": "A modern futuristic penthouse overlooking global financial district illuminated at twilight, 9:16 vertical"
                },
                {
                    "scene_id": 5,
                    "text": "Hãy thay đổi tư duy quản lý tài chính của bạn ngay từ ngày hôm nay!",
                    "image_prompt": "A glowing golden key unlocking a massive vault door revealing radiant light, symbolic success, 9:16 vertical"
                }
            ]
        }

    # Chủ đề: Vũ trụ, thiên văn, hố đen, sao hỏa, công nghệ
    elif any(k in topic_lower for k in ["vũ trụ", "hố đen", "sao hỏa", "thiên văn", "ngôi sao", "hành tinh", "ai", "robot"]):
        return {
            "title": f"Bí Ẩn Vũ Trụ: {topic}",
            "scenes": [
                {
                    "scene_id": 1,
                    "text": f"Những bí ẩn sâu thẳm ngoài không gian về {topic} luôn vượt xa trí tưởng tượng của con người.",
                    "image_prompt": f"Cinematic 9:16 vertical shot of cosmic void with glowing celestial phenomenon related to {topic}, volumetric starlight, 8k"
                },
                {
                    "scene_id": 2,
                    "text": "Nơi mà quy luật vật lý thông thường bị bẻ cong và thời gian dường như ngưng đọng.",
                    "image_prompt": "A massive supermassive black hole with radiant accretion disk bending space and time, deep space background, 9:16 vertical"
                },
                {
                    "scene_id": 3,
                    "text": "Các nhà khoa học phát hiện ra những tín hiệu kỳ lạ đang truyền đi khắp dải ngân hà.",
                    "image_prompt": "Giant radio telescope array under vibrant Milky Way galaxy and aurora borealis, mystical cosmic atmosphere, 9:16 vertical"
                },
                {
                    "scene_id": 4,
                    "text": "Liệu chúng ta có thực sự đơn độc trong vũ trụ bao la vô tận này?",
                    "image_prompt": "An astronaut standing on alien cratered planet gazing into a swirling spiral galaxy in the colorful sky, 9:16 vertical"
                },
                {
                    "scene_id": 5,
                    "text": "Đăng ký kênh để cùng khám phá những điều kỳ diệu của vũ trụ mỗi ngày!",
                    "image_prompt": "A glowing cosmic beacon pulsing light into deep nebula clouds, breathtaking cinematic 8k, 9:16 vertical"
                }
            ]
        }

    # Mặc định thông minh cho mọi chủ đề tự do khác:
    else:
        return {
            "title": f"Khám Phá: {topic}",
            "scenes": [
                {
                    "scene_id": 1,
                    "text": f"Có những sự thật chấn động về {topic} mà rất ít người trong chúng ta từng được nghe đến.",
                    "image_prompt": f"Cinematic 9:16 vertical shot representing {topic}, dramatic lighting, mystery and curiosity atmosphere, photorealistic 8k"
                },
                {
                    "scene_id": 2,
                    "text": "Mọi chuyện bắt đầu từ những chi tiết tưởng chừng nhỏ bé nhưng lại thay đổi toàn bộ cuộc chơi.",
                    "image_prompt": f"Close-up intriguing artistic visual connected to {topic}, high detail, cinematic studio lighting, 9:16 vertical"
                },
                {
                    "scene_id": 3,
                    "text": "Các chuyên gia đã dành nhiều năm nghiên cứu và tìm ra câu trả lời vô cùng bất ngờ.",
                    "image_prompt": f"Dramatic discovery scene about {topic}, illuminated subject with soft shadows, rich textures, 9:16 vertical"
                },
                {
                    "scene_id": 4,
                    "text": "Điều này nhắc nhở chúng ta luôn phải mở rộng góc nhìn để đón nhận những tri thức mới.",
                    "image_prompt": f"Inspirational aesthetic scene symbolizing enlightenment and deep understanding of {topic}, 9:16 vertical"
                },
                {
                    "scene_id": 5,
                    "text": "Bạn nghĩ sao về điều này? Hãy để lại ý kiến dưới phần bình luận nhé!",
                    "image_prompt": f"Thought-provoking visual related to {topic}, glowing neon elements, epic closing frame, 9:16 vertical"
                }
            ]
        }

def generate_script(topic: str) -> Dict[str, Any]:
    """Tự động lựa chọn nhà cung cấp AI phù hợp dựa trên API Key có sẵn."""
    if GROQ_API_KEY:
        try:
            return generate_script_groq(topic)
        except Exception as e:
            print(f"[Warning] Groq error: {e}, falling back...")

    # Kiểm tra key Gemini (chỉ gọi nếu key hợp lệ dạng AIzaSy...)
    if GEMINI_API_KEY and GEMINI_API_KEY.startswith("AIzaSy"):
        try:
            return generate_script_gemini(topic)
        except Exception as e:
            print(f"[Warning] Gemini error: {e}, falling back...")

    if OPENAI_API_KEY and OPENAI_API_KEY.startswith("sk-"):
        try:
            return generate_script_openai(topic)
        except Exception as e:
            print(f"[Warning] OpenAI error: {e}, falling back...")

    # Chế độ Kịch bản động thông minh theo chủ đề
    print(f"[Info] Đang tự động tạo kịch bản chuyên sâu theo chủ đề: '{topic}'...")
    return generate_dynamic_smart_script(topic)

if __name__ == "__main__":
    from core import *
    data = generate_script("6 thói quen khiến bạn ngày càng nghèo đi")
    print("Tiêu đề:", data["title"])
    for s in data["scenes"]:
        print(f"Cảnh {s['scene_id']}: {s['text']}")

