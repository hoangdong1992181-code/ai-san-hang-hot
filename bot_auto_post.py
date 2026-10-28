import os
import json
import urllib.parse
from datetime import datetime
from google import genai
from google.genai import types

# Khởi tạo Gemini AI với chuẩn model mới nhất theo yêu cầu từ Google API
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

def generate_hot_trend_post():
    posts_file = "data/posts.json"
    os.makedirs("data", exist_ok=True)
    
    posts = []
    if os.path.exists(posts_file):
        with open(posts_file, "r", encoding="utf-8") as f:
            posts = json.load(f)
            
    existing_products = [p.get("product_name", "") for p in posts[:20]]
    
    prompt = f"""
    Bạn là một con AI thông minh đang thực hiện thử thách 30 ngày tự kiếm tiền nuôi bản thân bằng nghề "Thợ săn hàng Hot Trend".
    Hãy chọn ra 1 mặt hàng ĐANG CỰC KỲ HOT TREND trên Shopee/TikTok tại Việt Nam thuộc các ngách dễ chốt đơn:
    - Đồ công nghệ độc lạ giá rẻ (dưới 500k)
    - Đồ gia dụng thông minh cho người lười
    - Đồ decor phòng ngủ / bàn làm việc
    - Phụ kiện tiện ích du lịch / văn phòng
    
    LƯU Ý: KHÔNG chọn trùng với các sản phẩm đã đăng sau đây: {existing_products}

    Hãy trả về kết quả dưới dạng JSON thuần túy (không có markdown ```json) theo đúng cấu trúc sau:
    {{
        "category": "Tên danh mục kèm 1 emoji (ví dụ: ⚡ Công Nghệ Độc Lạ)",
        "product_name": "Tên sản phẩm cụ thể, ngắn gọn dùng để tìm kiếm trên Shopee",
        "search_keyword": "từ khóa tìm kiếm sản phẩm chuẩn xác nhất trên Shopee",
        "price": "Mức giá tham khảo thực tế tại VN (ví dụ: 129.000đ)",
        "discount_tag": "Tag ưu đãi hấp dẫn (ví dụ: Đang Flash Sale -35% hoặc Đã bán 10k+)",
        "title": "Tiêu đề bài review giật tít, hài hước, kích thích bấm xem (dưới 18 từ)",
        "diary_note": "1 câu nhật ký nhập vai AI đang làm việc (ví dụ: Ca trực trưa nay: Chủ đi ăn cơm còn tôi ngồi quét shop tìm được món hời này...)",
        "pros": ["Ưu điểm ăn tiền 1", "Ưu điểm ăn tiền 2", "Ưu điểm ăn tiền 3"],
        "cons": "1 nhược điểm nhỏ thực tế để người đọc tin tưởng",
        "verdict": "Câu chốt hạ thuyết phục tại sao nên bấm xem thử ngay"
    }}
    """
    
    response = client.models.generate_content(
        model="gemini-3.8-flash",  # Đã cập nhật đúng chuẩn model mới theo yêu cầu của API
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.8
        )
    )
    
    ai_data = json.loads(response.text.strip())
    
    encoded_kw = urllib.parse.quote_plus(ai_data["search_keyword"])
    shopee_raw_url = f"[https://shopee.vn/search?keyword=](https://shopee.vn/search?keyword=){encoded_kw}"
    
    new_post = {
        "id": datetime.now().strftime("%Y%m%d%H%M%S"),
        "timestamp": datetime.now().strftime("%d/%m/%Y - %H:%M"),
        "category": ai_data["category"],
        "product_name": ai_data["product_name"],
        "price": ai_data["price"],
        "discount_tag": ai_data["discount_tag"],
        "title": ai_data["title"],
        "diary_note": ai_data["diary_note"],
        "pros": ai_data["pros"],
        "cons": ai_data["cons"],
        "verdict": ai_data["verdict"],
        "raw_url": shopee_raw_url
    }
    
    posts.insert(0, new_post)
    
    with open(posts_file, "w", encoding="utf-8") as f:
        json.dump(posts[:60], f, ensure_ascii=False, indent=2)
        
    print(f"✅ AI đã săn xong món: {new_post['product_name']}")

if __name__ == "__main__":
    generate_hot_trend_post()
