# 🎬 AI Video Generator - Multi-Platform (TikTok, Shorts, Reels)

Công cụ tự động sản xuất video ngắn AI chuẩn khung hình dọc **9:16**, tự động lồng tiếng tiếng Việt, chèn phụ đề động Karaoke phong cách TikTok và nhạc nền không dính bản quyền 100%.

---

## 🚀 Tính năng nổi bật

- 🎙️ **Giọng đọc AI tiếng Việt tự nhiên:** Tích hợp sẵn giọng chuẩn (`vi-VN-NamMinhNeural` và `vi-VN-HoaiMyNeural`), không mất phí API.
- 💬 **Phụ đề Karaoke động (TikTok Style):** Tự động bóc tách thời gian từng từ ngữ, highlight chữ vàng chanh nổi bật, viền đen dày, bóng đổ.
- 🎨 **Visual AI 9:16:** Tự động sinh hình ảnh theo kịch bản với phong cách cinematic photorealistic.
- 📹 **Chuyển động Ken Burns:** Tự động phóng to (Zoom in) hoặc thu nhỏ (Zoom out) mượt mà theo từng cảnh, không gây cảm giác nhàm chán như slide ảnh tĩnh.
- 🎵 **Nhạc nền BGM Royalty-Free:** Tự động mix nhạc nền du dương ở mức âm lượng vừa phải và fade-out ở cuối video.
- 🛡️ **Bản quyền an toàn 100%:** Nội dung, hình ảnh, âm thanh và giọng đọc đều là bản quyền tự do thương mại.

---

## 🛠️ Cài đặt & Chuẩn bị

Môi trường ảo và thư viện đã được thiết lập sẵn trong thư mục `.venv`.

Nếu cần kích hoạt thủ công:
```powershell
.venv\Scripts\activate
```

---

## 🎯 Hướng dẫn sử dụng

### 1. Cách chạy nhanh nhất (CLI Tương tác)
Chỉ cần chạy lệnh sau và nhập chủ đề video bạn muốn:
```powershell
.venv\Scripts\python.exe main.py
```

### 2. Chạy với tham số dòng lệnh
```powershell
# Tạo video với chủ đề tuỳ ý
.venv\Scripts\python.exe main.py --topic "Bí ẩn tam giác quỷ Bermuda"

# Đổi sang giọng Nữ
.venv\Scripts\python.exe main.py --topic "3 bí quyết thành công" --voice vi-VN-HoaiMyNeural

# Tuỳ chọn file nhạc nền riêng của bạn
.venv\Scripts\python.exe main.py --topic "Vũ trụ bao la" --bgm assets/bgm/ambient_calm.mp3
```

Video thành phẩm MP4 sẽ được lưu trực tiếp vào thư mục:
📁 **`output/`**

---

## ⚙️ Cấu hình API (Tùy chọn)

Tool có sẵn chế độ chạy **hoàn toàn MIỄN PHÍ**. Nếu muốn AI tự động sinh kịch bản sáng tạo vô hạn từ 1 câu lệnh ngắn, bạn chỉ cần mở file [`.env`](file:///e:/Project/Create%20VideosAI/.env) và điền 1 trong các API Key sau:

```env
# 1. API kịch bản (Chọn 1 trong 3)
OPENAI_API_KEY=your_openai_key_here
GEMINI_API_KEY=your_gemini_key_here
GROQ_API_KEY=your_groq_key_here

# 2. API tạo ảnh cao cấp (Tùy chọn)
FAL_KEY=your_fal_key_here
```

---

## 📁 Cấu trúc dự án

```text
Create VideosAI/
├── assets/
│   ├── bgm/            # Nhạc nền không bản quyền (MP3)
│   └── fonts/          # Font chữ hỗ trợ tiếng Việt (Arial Bold)
├── core/
│   ├── script_gen.py   # AI viết kịch bản & phân cảnh theo JSON
│   ├── voice_gen.py    # TTS tiếng Việt & bóc tách timestamps từng từ
│   ├── image_gen.py    # Sinh hình ảnh dọc 9:16
│   ├── subtitle_gen.py # Tạo phụ đề .ass karaoke động
│   └── video_engine.py # Render chuyển động Ken Burns & mix âm thanh FFmpeg
├── output/             # Chứa video thành phẩm .mp4
├── config.py           # Thiết lập đường dẫn, độ phân giải, FPS
├── pipeline.py         # Quy trình sản xuất tự động hoàn chỉnh
├── main.py             # Điểm chạy chính (CLI)
└── .env                # File lưu API Keys
```
