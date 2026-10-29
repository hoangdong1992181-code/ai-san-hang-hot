import os
import re
import json
import base64
import asyncio
import subprocess
import urllib.request
import edge_tts

API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
VOICE = "vi-VN-NamMinhNeural"

def get_best_model():
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={API_KEY}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as res:
            data = json.loads(res.read().decode("utf-8"))
            models = []
            for m in data.get("models", []):
                name = m.get("name", "").replace("models/", "")
                if "generateContent" in m.get("supportedGenerationMethods", []) and "gemini" in name:
                    models.append(name)
            models.sort(key=lambda x: (0 if "flash" in x and "lite" not in x else (1 if "lite" in x else 2)))
            if models:
                return models[0]
    except Exception:
        pass
    return "gemini-3.8-flash"

def download_movie_and_extract_info(video_url, output_raw="raw_movie.mp4"):
    print(f"📥 Đang tải video và trích xuất dữ liệu gốc từ: {video_url}")
    if not video_url or not video_url.startswith("http"):
        video_url = "https://raw.githubusercontent.com/intel-iot-devkit/sample-videos/master/person-bicycle-car-detection.mp4"

    cmd = [
        "yt-dlp",
        "--no-check-certificates",
        "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "--write-info-json",
        "--write-auto-sub", "--write-sub",
        "--sub-langs", "vi,en,zh-Hans,zh-Hant,zh.*",
        "--convert-subs", "srt",
        "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "--merge-output-format", "mp4",
        "-o", "raw_movie.%(ext)s",
        video_url
    ]
    try:
        subprocess.run(cmd, check=False, timeout=90)
    except Exception as e:
        print(f"⚠️ Cảnh báo yt-dlp: {e}")

    if not os.path.exists(output_raw) or os.path.getsize(output_raw) < 10000:
        fallback_url = "https://raw.githubusercontent.com/intel-iot-devkit/sample-videos/master/person-bicycle-car-detection.mp4"
        try:
            req = urllib.request.Request(fallback_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=25) as response, open(output_raw, "wb") as out_file:
                out_file.write(response.read())
        except Exception:
            subprocess.run([
                "ffmpeg", "-y", "-f", "lavfi", "-i", "testsrc2=size=1080x1920:rate=30",
                "-t", "30", "-c:v", "libx264", "-pix_fmt", "yuv420p", output_raw
            ], check=True)

    extracted_text = ""
    if os.path.exists("raw_movie.info.json"):
        try:
            with open("raw_movie.info.json", "r", encoding="utf-8") as f:
                info = json.load(f)
                extracted_text += f"Tiêu đề gốc: {info.get('title', '')}\n"
        except Exception:
            pass

    return extracted_text

def extract_video_frames(video_path="raw_movie.mp4", num_frames=4):
    frames_b64 = []
    try:
        subprocess.run([
            "ffmpeg", "-y", "-i", video_path,
            "-vf", "fps=1/5,scale=360:-1", "-frames:v", str(num_frames),
            "frame_%d.jpg"
        ], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        for i in range(1, num_frames + 1):
            fname = f"frame_{i}.jpg"
            if os.path.exists(fname):
                with open(fname, "rb") as img_f:
                    b64_data = base64.b64encode(img_f.read()).decode("utf-8")
                    frames_b64.append({
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": b64_data
                        }
                    })
    except Exception as e:
        print(f"⚠️ Không trích xuất được khung hình: {e}")
    return frames_b64

def generate_auto_movie_script(movie_title, plot_summary, part_number, duration_mode, auto_extracted_info, frames_b64):
    if duration_mode == "long":
        word_limit = "320 đến 420 chữ (đọc trong 80-110 giây)"
    else:
        word_limit = "100 đến 130 chữ (đọc trong 30-35 giây)"

    user_hint = plot_summary.strip()
    if not user_hint or "Tự động" in user_hint:
        user_hint_text = "Hãy quan sát hình ảnh và tự biên kịch câu chuyện kịch tính."
    else:
        user_hint_text = f"Gợi ý từ người dùng: {user_hint}"

    prompt = f"""
    Bạn là biên kịch chuyên làm video review phim ngắn triệu view.
    Hãy quan sát các khung hình và viết kịch bản thuyết minh tiếng Việt có độ dài {word_limit}:
    - Tên phim: {movie_title} ({part_number})
    - Thông tin: {auto_extracted_info}
    - {user_hint_text}

    Quy tắc:
    1. Câu đầu tiên phải cực kỳ sốc, kịch tính để giữ chân người xem.
    2. Kể lại diễn biến gay cấn, lôi cuốn.
    3. Kết thúc lửng lơ ở cao trào và chốt: "Bấm Follow kênh ngay vì phần tiếp theo đã có trong trang cá nhân rồi nhé!"
    4. CHỈ TRẢ VỀ văn bản thuần túy để đọc thành tiếng, không emoji, không dấu ngoặc.
    """

    parts = [{"text": prompt}]
    parts.extend(frames_b64)

    model_name = get_best_model()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={API_KEY}"
    try:
        payload = json.dumps({"contents": [{"parts": parts}]}).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=25) as res:
            data = json.loads(res.read().decode("utf-8"))
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception:
        return f"Không ngờ câu chuyện trong {movie_title} lại có cú lật kèo nghẹt thở đến vậy. Bấm Follow kênh ngay để xem tiếp {part_number} nhé!"

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

def remix_movie_anti_copyright(movie_title, part_number, raw_video="raw_movie.mp4", audio_file="movie_voice.mp3", sub_file="movie_sub.srt", final_video="phim_ngan_tiktok.mp4"):
    with open("banner_title.txt", "w", encoding="utf-8") as f:
        f.write(movie_title.upper())
    with open("banner_part.txt", "w", encoding="utf-8") as f:
        f.write(f"【 {part_number.upper()} 】")

    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    filter_complex = (
        "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=25:5,eq=brightness=-0.15[bg];"
        "[0:v]setpts=0.95*PTS,hflip,eq=contrast=1.08:saturation=1.15:brightness=0.02,"
        "scale=1080:1280:force_original_aspect_ratio=decrease[fg];"
        "[bg][fg]overlay=(W-w)/2:(H-h)/2[merged];"
        f"[merged]drawtext=fontfile={font_path}:textfile=banner_title.txt:fontcolor=#f59e0b:fontsize=46:borderw=4:bordercolor=black:x=(w-text_w)/2:y=140,"
        f"drawtext=fontfile={font_path}:textfile=banner_part.txt:fontcolor=#ffffff:fontsize=38:borderw=3:bordercolor=black:x=(w-text_w)/2:y=210,"
        f"subtitles={sub_file}:force_style='FontName=DejaVu Sans,FontSize=16,PrimaryColour=&H0000FFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=2,Shadow=1,Alignment=2,MarginV=65',"
        "fps=30,format=yuv420p[v]"
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

async def main():
    movie_title = os.environ.get("MOVIE_TITLE", "Siêu Phẩm Phim Ngắn")
    part_number = os.environ.get("PART_NUMBER", "Phần 1")
    duration_mode = os.environ.get("DURATION_MODE", "long")
    plot_summary = os.environ.get("PLOT_SUMMARY", "Tự động")
    video_url = os.environ.get("VIDEO_URL", "")

    auto_info = download_movie_and_extract_info(video_url)
    frames_b64 = extract_video_frames("raw_movie.mp4", num_frames=4)
    script = generate_auto_movie_script(movie_title, plot_summary, part_number, duration_mode, auto_info, frames_b64)
    
    await create_voiceover(script)
    remix_movie_anti_copyright(movie_title, part_number)

    with open("caption_dang_bai.txt", "w", encoding="utf-8") as f:
        f.write(f"🎬 {movie_title} - {part_number} | Xem cuốn không rời mắt! 🔥\n👉 Bấm Follow kênh nhé!\n\n{script}")

if __name__ == "__main__":
    asyncio.run(main())
