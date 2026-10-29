import os
import json
import asyncio
import subprocess
import urllib.request
import edge_tts

API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
VOICE = "vi-VN-NamMinhNeural"  # Giọng Nam Minh đọc review phim kịch tính

def get_best_model():
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={API_KEY}"
    try:
        with urllib.request.urlopen(url, timeout=10) as res:
            data = json.loads(res.read().decode("utf-8"))
            models = []
            for m in data.get("models", []):
                name = m.get("name", "").replace("models/", "")
                if "generateContent" in m.get("supportedGenerationMethods", []) and "gemini" in name:
                    models.append(name)
            models.sort(key=lambda x: (0 if "lite" in x else (1 if "flash" in x else 2)))
            if models:
                return models[0]
    except Exception:
        pass
    return "gemini-3.8-flash"

def generate_movie_recap_script(movie_title, plot_summary, part_number):
    prompt = f"""
    Bạn là một biên kịch chuyên làm video "Tóm tắt phim / Review phim ngắn" triệu view trên TikTok.
    Hãy viết kịch bản thuyết minh (khoảng 80 - 110 chữ, đọc trong 25-35 giây) cho bộ phim:
    - Tên phim: {movie_title} ({part_number})
    - Tóm tắt tình tiết trong đoạn video này: {plot_summary}

    Quy tắc bắt buộc:
    1. Câu mở đầu (3 giây đầu) phải cực kỳ sốc, kịch tính để giữ chân người xem.
    2. Kể lại diễn biến với nhịp độ nhanh, dùng từ ngữ gay cấn, lôi cuốn.
    3. Kết thúc lửng lơ ở đoạn cao trào nhất và chốt câu: "Cái kết cho kẻ coi thường người khác sẽ ra sao? Bấm Follow kênh ngay vì Phần tiếp theo đã có trong trang cá nhân rồi nhé!"
    4. CHỈ TRẢ VỀ đúng đoạn văn bản để đọc thành tiếng, tuyệt đối không có ghi chú cảnh quay, không có dấu ngoặc hay emoji.
    """
    model_name = get_best_model()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={API_KEY}"
    try:
        payload = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=15) as res:
            data = json.loads(res.read().decode("utf-8"))
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        print(f"⚠️ Dùng kịch bản dự phòng do server bận: {e}")
        return (
            f"Không ai ngờ người đàn ông ăn mặc giản dị trước mặt lại đang nắm giữ vận mệnh của cả tập đoàn trong {movie_title}. "
            f"{plot_summary}. Ngay khi tất cả mọi người đều nghĩ anh sẽ phải cúi đầu chịu nhục, một chiếc siêu xe bất ngờ phanh gấp trước cửa làm cả khán phòng chết lặng. "
            f"Màn trả thù chấn động tiếp theo sẽ diễn ra thế nào? Bấm Follow kênh ngay để xem tiếp {part_number} cực gắt nhé!"
        )

async def create_voiceover(text, output_audio="movie_voice.mp3", output_sub="movie_sub.srt"):
    communicate = edge_tts.Communicate(text, VOICE, rate="+18%")
    submaker = edge_tts.SubMaker()
    with open(output_audio, "wb") as file:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                file.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                submaker.feed(chunk)
    with open(output_sub, "w", encoding="utf-8") as file:
        file.write(submaker.get_srt())
    print("✅ Đã thu âm xong giọng thuyết minh Review Phim!")

def download_movie_clip(video_url, output_raw="raw_movie.mp4"):
    print(f"📥 Đang tải đoạn phim gốc từ: {video_url}")
    cmd = [
        "yt-dlp",
        "--no-check-certificates",
        "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "--merge-output-format", "mp4",
        "-o", output_raw,
        video_url
    ]
    try:
        subprocess.run(cmd, check=True)
    except Exception as e:
        print(f"⚠️ Link video bị chặn tải trực tiếp ({e}), chuyển sang video mẫu dự phòng...")
        urllib.request.urlretrieve("https://files.catbox.moe/3ce2y5.mp4", output_raw)
    print("✅ Đã có file video gốc!")

def remix_movie_anti_copyright(raw_video="raw_movie.mp4", audio_file="movie_voice.mp3", final_video="phim_ngan_tiktok.mp4"):
    print("🎬 Đang xử lý lách bản quyền 5 lớp & ghép thuyết minh...")
    filter_complex = (
        "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=25:5[bg];"
        "[0:v]setpts=0.95*PTS,hflip,eq=contrast=1.08:saturation=1.12:brightness=0.02,"
        "scale=1080:1350:force_original_aspect_ratio=decrease[fg];"
        "[bg][fg]overlay=(W-w)/2:(H-h)/2,fps=30,format=yuv420p[v]"
    )
    cmd = [
        "ffmpeg", "-y",
        "-stream_loop", "-1", "-i", raw_video,
        "-i", audio_file,
        "-filter_complex", filter_complex,
        "-map", "[v]",
        "-map", "1:a",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        final_video
    ]
    subprocess.run(cmd, check=True)
    print(f"🎉 Xuất xưởng thành công: {final_video}")

async def main():
    movie_title = os.environ.get("MOVIE_TITLE", "Chủ Tịch Giả Làm Bảo Vệ")
    part_number = os.environ.get("PART_NUMBER", "Phần 1")
    plot_summary = os.environ.get("PLOT_SUMMARY", "Anh chàng mặc đồ bảo vệ đi họp lớp bị bạn cũ sỉ nhục, nào ngờ giám đốc khách sạn chạy ra cúi đầu chào")
    video_url = os.environ.get("VIDEO_URL", "https://files.catbox.moe/3ce2y5.mp4")

    script = generate_movie_recap_script(movie_title, plot_summary, part_number)
    print(f"📝 Lời bình AI vừa viết:\n{script}\n")

    await create_voiceover(script)
    download_movie_clip(video_url)
    remix_movie_anti_copyright()

    with open("caption_dang_bai.txt", "w", encoding="utf-8") as f:
        f.write(
            f"🎬 {movie_title} - {part_number} | Xem cuốn không rời mắt! 🔥\n"
            f"👉 Bấm Follow kênh để xem ngay phần tiếp theo nhé!\n"
            f"#reviewphim #phimngan #tomtatphim #phimhay #xuhuong\n\n"
            f"--- Lời thuyết minh ---\n{script}"
        )

if __name__ == "__main__":
    asyncio.run(main())
