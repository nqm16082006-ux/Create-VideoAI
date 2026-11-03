import os
import random
import io
import re
import urllib.parse
from pathlib import Path
from typing import Optional
import requests
from PIL import Image
from config import TEMP_DIR, FAL_KEY

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "")

def crop_to_vertical(image_bytes: bytes, target_w: int = 720, target_h: int = 1280) -> Image.Image:
    """Cắt và chỉnh tỷ lệ ảnh chuẩn 9:16 (720x1280 hoặc 1080x1920) không bị méo hình."""
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    target_ratio = target_w / target_h
    img_ratio = img.width / img.height

    if img_ratio > target_ratio:
        # Ảnh gốc rộng hơn tỷ lệ 9:16 -> scale theo chiều cao và crop 2 bên
        new_h = target_h
        new_w = int(img.width * (target_h / img.height))
        img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        left = (new_w - target_w) // 2
        img = img.crop((left, 0, left + target_w, target_h))
    else:
        # Ảnh gốc hẹp hơn tỷ lệ 9:16 -> scale theo chiều rộng và crop trên dưới
        new_w = target_w
        new_h = int(img.height * (target_w / img.width))
        img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        top = (new_h - target_h) // 2
        img = img.crop((0, top, target_w, top + target_h))

    return img

def extract_search_keywords(prompt: str) -> str:
    """Rút gọn prompt dài thành 2-4 từ khóa tiếng Anh trọng tâm để tìm ảnh."""
    # Bỏ các từ phụ trợ thường gặp trong prompt AI
    cleaned = re.sub(
        r"(cinematic|vertical|9:16|shot of|photorealistic|8k|dramatic lighting|volumetric|composition|detailed|close-up of|view of|atmosphere)",
        "",
        prompt,
        flags=re.IGNORECASE
    ).strip()
    words = [w for w in cleaned.split() if len(w) > 2][:4]
    return " ".join(words) if words else "nature landscape"

def fetch_image_pexels(query: str, output_path: Path, width: int = 720, height: int = 1280) -> bool:
    """Tải ảnh chất lượng cao từ Pexels API (nếu có key trong .env)."""
    if not PEXELS_API_KEY:
        return False
    try:
        headers = {"Authorization": PEXELS_API_KEY}
        url = f"https://api.pexels.com/v1/search?query={urllib.parse.quote(query)}&orientation=portrait&per_page=5"
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code == 200:
            photos = resp.json().get("photos", [])
            if photos:
                img_url = random.choice(photos)["src"]["large2x"]
                img_data = requests.get(img_url, timeout=20).content
                cropped = crop_to_vertical(img_data, width, height)
                cropped.save(output_path, quality=95)
                return True
    except Exception as e:
        print(f"   [Pexels Notice] {e}")
    return False

def fetch_image_wikimedia(query: str, output_path: Path, width: int = 720, height: int = 1280) -> bool:
    """Tìm kiếm và tải ảnh thực tế bản quyền mở từ Wikimedia Commons (Miễn phí 100%, không cần key)."""
    try:
        headers = {"User-Agent": "CreateVideosAI/1.0 (contact@creativeai.local)"}
        search_url = (
            f"https://en.wikipedia.org/w/api.php?action=query&format=json&prop=pageimages"
            f"&generator=search&gsrsearch={urllib.parse.quote(query)}&gsrlimit=6&piprop=thumbnail&pithumbsize=1280"
        )
        resp = requests.get(search_url, headers=headers, timeout=12)
        if resp.status_code == 200:
            pages = resp.json().get("query", {}).get("pages", {})
            thumbnails = [p["thumbnail"]["source"] for pid, p in pages.items() if "thumbnail" in p]
            if thumbnails:
                chosen_url = random.choice(thumbnails)
                img_data = requests.get(chosen_url, headers=headers, timeout=20).content
                cropped = crop_to_vertical(img_data, width, height)
                cropped.save(output_path, quality=95)
                return True
    except Exception as e:
        print(f"   [Wiki Notice] {e}")
    return False

def generate_image_fal(prompt: str, output_path: Path, width: int = 720, height: int = 1280) -> bool:
    """Sinh ảnh AI bằng Fal.ai Flux.1 Schnell (nếu FAL_KEY có số dư)."""
    if not FAL_KEY:
        return False
    try:
        headers = {
            "Authorization": f"Key {FAL_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "prompt": f"{prompt}, cinematic lighting, photorealistic 8k, 9:16 vertical",
            "image_size": {"width": width, "height": height}
        }
        resp = requests.post("https://fal.run/fal-ai/flux/schnell", headers=headers, json=payload, timeout=25)
        if resp.status_code == 200:
            img_url = resp.json()["images"][0]["url"]
            img_data = requests.get(img_url, timeout=20).content
            cropped = crop_to_vertical(img_data, width, height)
            cropped.save(output_path, quality=95)
            return True
    except Exception:
        pass
    return False

def generate_image_pollinations(prompt: str, output_path: Path, width: int = 720, height: int = 1280) -> bool:
    """Gọi Pollinations AI (có thể bị giới hạn 1 ảnh / 35s ở bản miễn phí)."""
    try:
        enhanced = f"{prompt}, cinematic 9:16, 8k"
        encoded = urllib.parse.quote(enhanced)
        url = f"https://image.pollinations.ai/prompt/{encoded}?nologo=true"
        resp = requests.get(url, timeout=25)
        if resp.status_code == 200 and len(resp.content) > 2000:
            cropped = crop_to_vertical(resp.content, width, height)
            cropped.save(output_path, quality=95)
            return True
    except Exception:
        pass
    return False

def generate_image(prompt: str, output_path: str | Path) -> Path:
    """
    Hàm tổng hợp tạo hình ảnh đa tầng:
    1. Ưu tiên Fal.ai nếu có key và có số dư.
    2. Sử dụng Pexels API nếu có key.
    3. Tìm ảnh thực tế độ nét cao từ Wikimedia Commons theo từ khóa.
    4. Thử Pollinations AI.
    5. Fallback cuối cùng nếu toàn bộ mạng ngoại tuyến.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    keywords = extract_search_keywords(prompt)

    # 1. Thử Fal.ai
    if FAL_KEY and generate_image_fal(prompt, output_path):
        print(f"   [Visual] Sinh ảnh FLUX qua Fal.ai thành công!")
        return output_path

    # 2. Thử Pexels API
    if PEXELS_API_KEY and fetch_image_pexels(keywords, output_path):
        print(f"   [Visual] Lấy ảnh chân thực từ Pexels: '{keywords}'")
        return output_path

    # 3. Thử tìm kiếm ảnh chuẩn nội dung từ Wikimedia Commons
    if fetch_image_wikimedia(keywords, output_path):
        print(f"   [Visual] Lấy ảnh sắc nét phù hợp nội dung: '{keywords}'")
        return output_path

    # 4. Thử Pollinations
    if generate_image_pollinations(prompt, output_path):
        print(f"   [Visual] Sinh ảnh AI qua Pollinations thành công!")
        return output_path

    # 5. Fallback khẩn cấp nếu toàn bộ mạng quốc tế bị ngắt
    print(f"   [Visual Fallback] Tạo ảnh nền chủ đề '{keywords}'...")
    from PIL import ImageDraw, ImageFont
    img = Image.new("RGB", (720, 1280), color=(18, 24, 38))
    draw = ImageDraw.Draw(img)
    for y in range(1280):
        r = int(18 + (30 * y / 1280))
        g = int(24 + (15 * y / 1280))
        b = int(38 + (50 * y / 1280))
        draw.line([(0, y), (720, y)], fill=(r, g, b))
    img.save(output_path, quality=95)
    return output_path

if __name__ == "__main__":
    from config import TEMP_DIR
    test_out = TEMP_DIR / "test_visual.jpg"
    generate_image("Cinematic vertical 9:16 shot of Mars red planet surface with astronauts", test_out)
    print(f"File tạo thành công: {test_out} (Kích thước: {test_out.stat().st_size} bytes)")
