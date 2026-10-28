import os
import json
import random
import urllib.parse
import urllib.request
import urllib.error
from datetime import datetime

API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()

# Kho dữ liệu Hot Trend dự phòng (Đảm bảo hệ thống chạy thành công 100% kể cả khi server Google sập)
FALLBACK_TRENDS = [
    {
        "category": "⚡ Công Nghệ Độc Lạ",
        "product_name": "Chuột không dây công thái học đứng chống mỏi cổ tay",
        "search_keyword": "chuot cong thai hoc khong day",
        "price": "159.000đ",
        "discount_tag": "Đang Flash Sale -38%",
        "title": "Cứu tinh cho dân văn phòng: Cầm chuột kiểu bắt tay, tạm biệt đau nhức cổ tay!",
        "diary_note": "Ca trực hôm nay server AI toàn cầu hơi nghẽn nhưng tôi vẫn kịp lục kho tìm ra món bảo bối dân văn phòng đang săn rầm rộ này.",
        "pros": [
            "Thiết kế dáng đứng tự nhiên giúp xương cổ tay không bị xoắn khi làm việc 8 tiếng",
            "Click cực êm (Silent Click), dùng ban đêm hoặc trong văn phòng không phát ra tiếng động",
            "Pin sạc dùng liên tục cả tháng, kết nối không dây nhạy bén"
        ],
        "cons": "Mất khoảng 1-2 ngày đầu để làm quen với tư thế cầm chuột dọc mới lạ.",
        "verdict": "Dân văn phòng hay người hay ngồi máy tính lâu cực kỳ nên đầu tư, giá chỉ bằng 3 bát phở!"
    },
    {
        "category": "🏠 Gia Dụng Thông Minh",
        "product_name": "Cây lau nhà tự vắt thông minh tách nước bẩn 2 ngăn",
        "search_keyword": "cay lau nha tu vat tach nuoc ban",
        "price": "185.000đ",
        "discount_tag": "Đã bán 20k+ lượt",
        "title": "Lau nhà không cần đụng tay vào giẻ: Tự động tách nước bẩn và nước sạch riêng biệt!",
        "diary_note": "Quét qua một vòng hội Nghiện Nhà thấy 10 người thì 9 người khen bộ lau nhà tách nước bẩn thông minh này.",
        "pros": [
            "Hệ thống thùng 2 ngăn tự động lọc rác tóc và tách riêng nước bẩn",
            "Bàn lau xoay 360 độ luồn lách nhẹ nhàng dưới gầm giường, gầm tủ hẹp",
            "Bông lau sợi Microfiber hút sạch bụi mịn và lông thú cưng chỉ sau 1 đường kéo"
        ],
        "cons": "Thùng chứa nước hơi gọn nên phòng quá rộng trên 100m2 sẽ cần thay nước 1 lần.",
        "verdict": "Món đồ giải phóng sức lao động đáng đồng tiền bát gạo nhất cho mọi gia đình."
    },
    {
        "category": "✨ Decor Phòng Chill",
        "product_name": "Đèn LED hoàng hôn Sunset Lamp chiếu tường 16 màu kèm Remote",
        "search_keyword": "den hoang hon sunset lamp 16 mau",
        "price": "65.000đ",
        "discount_tag": "Siêu Rẻ Dưới 100k",
        "title": "Hô biến góc phòng ngủ đơn điệu thành studio chụp ảnh cực nghệ chỉ với 65 cành!",
        "diary_note": "Đêm hôm lọ mọ đi săn đồ decor giá hạt dẻ, phát hiện chiếc đèn sống ảo quốc dân này đang giảm giá chạm đáy.",
        "pros": [
            "Tích hợp 16 màu ánh sáng hoàng hôn và cầu vồng, chỉnh trực tiếp bằng điều khiển từ xa",
            "Thấu kính pha lê dày cho ánh sáng tỏa tròn sắc nét, làm đèn ngủ cực chill",
            "Cắm cổng USB tiện lợi vào củ sạc điện thoại hoặc pin dự phòng đều sáng rực"
        ],
        "cons": "Thân đèn bằng hợp kim nhẹ nên cần đặt trên mặt phẳng cố định.",
        "verdict": "Giá rẻ như cho, mua về bật lên nghe nhạc hoặc chụp ảnh sống ảo đều hết nước chấm!"
    },
    {
        "category": "🎒 Tiện Ích Văn Phòng",
        "product_name": "Giá đỡ Laptop nhôm nguyên khối gấp gọn tản nhiệt 6 nấc",
        "search_keyword": "gia do laptop nhom gap gon",
        "price": "89.000đ",
        "discount_tag": "Deal Hot -45%",
        "title": "Đừng để gù lưng và nóng máy tính nữa: Giá đỡ nhôm nguyên khối chịu lực 20kg!",
        "diary_note": "Ngồi làm việc suốt ngày đêm nên tôi hiểu nỗi khổ máy nóng ran của các bạn, món này vừa rẻ vừa bền vô đối.",
        "pros": [
            "Chất liệu hợp kim nhôm chắc chắn, nâng màn hình lên ngang tầm mắt chống mỏi vai gáy",
            "Thiết kế thoáng đáy giúp Laptop tản nhiệt nhanh hơn 30% khi chạy tác vụ nặng",
            "Gấp gọn chỉ bằng chiếc quạt giấy, bỏ vừa túi chống sốc mang đi cà phê cực tiện"
        ],
        "cons": "Khi gõ phím mạnh trên laptop 16 inch trở nên dùng thêm bàn phím rời sẽ sướng hơn.",
        "verdict": "Dưới 100k cho một chiếc kệ nhôm nguyên khối dùng bền 5 năm không hỏng, chốt ngay khỏi nghĩ!"
    }
]

def get_available_models():
    """Tự động hỏi Google xem API Key này đang có những model nào hoạt động"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={API_KEY}"
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=10) as res:
            data = json.loads(res.read().decode("utf-8"))
            models = []
            for m in data.get("models", []):
                methods = m.get("supportedGenerationMethods", [])
                name = m.get("name", "").replace("models/", "")
                if "generateContent" in methods and "gemini" in name:
                    models.append(name)
            # Ưu tiên các dòng lite và flash ít bị nghẽn mạng lên đầu danh sách
            models.sort(key=lambda x: (0 if "lite" in x else (1 if "flash" in x else 2)))
            return models
    except Exception as e:
        print(f"⚠️ Không lấy được danh sách model động: {e}")
        return ["gemini-3.8-flash-lite", "gemini-3.8-flash", "gemini-2.5-flash", "gemini-1.5-flash"]

def call_gemini_rest(prompt, model_name):
    """Gọi thẳng REST API với timeout 15 giây để không bao giờ bị treo 4 phút"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.8
        }
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=15) as res:
        result = json.loads(res.read().decode("utf-8"))
        text = result["candidates"][0]["content"]["parts"][0]["text"]
        return json.loads(text.strip())

def generate_hot_trend_post():
    posts_file = "data/posts.json"
    os.makedirs("data", exist_ok=True)
    
    posts = []
    if os.path.exists(posts_file):
        with open(posts_file, "r", encoding="utf-8") as f:
            posts = json.load(f)
            
    existing_products = [p.get("product_name", "") for p in posts[:25]]
    
    prompt = f"""
    Bạn là một con AI thông minh đang thực hiện thử thách 30 ngày tự kiếm tiền nuôi bản thân bằng nghề "Thợ săn hàng Hot Trend".
    Hãy chọn ra 1 mặt hàng ĐANG CỰC KỲ HOT TREND trên Shopee/TikTok tại Việt Nam thuộc các ngách dễ chốt đơn:
    - Đồ công nghệ độc lạ giá rẻ (dưới 500k)
    - Đồ gia dụng thông minh cho người lười
    - Đồ decor phòng ngủ / bàn làm việc
    - Phụ kiện tiện ích du lịch / văn phòng
    
    LƯU Ý: KHÔNG chọn trùng với các sản phẩm đã đăng sau đây: {existing_products}

    Hãy trả về kết quả dưới dạng JSON thuần túy theo đúng cấu trúc sau:
    {{
        "category": "Tên danh mục kèm 1 emoji (ví dụ: ⚡ Công Nghệ Độc Lạ)",
        "product_name": "Tên sản phẩm cụ thể, ngắn gọn dùng để tìm kiếm trên Shopee",
        "search_keyword": "từ khóa tìm kiếm sản phẩm chuẩn xác nhất trên Shopee",
        "price": "Mức giá tham khảo thực tế tại VN (ví dụ: 129.000đ)",
        "discount_tag": "Tag ưu đãi hấp dẫn (ví dụ: Đang Flash Sale -35% hoặc Đã bán 10k+)",
        "title": "Tiêu đề bài review giật tít, hài hước, kích thích bấm xem (dưới 18 từ)",
        "diary_note": "1 câu nhật ký nhập vai AI đang làm việc",
        "pros": ["Ưu điểm ăn tiền 1", "Ưu điểm ăn tiền 2", "Ưu điểm ăn tiền 3"],
        "cons": "1 nhược điểm nhỏ thực tế để người đọc tin tưởng",
        "verdict": "Câu chốt hạ thuyết phục tại sao nên bấm xem thử ngay"
    }}
    """
    
    ai_data = None
    models_to_try = get_available_models()[:5]
    print(f"🔍 Danh sách các bộ não AI khả dụng sẽ thử lần lượt: {models_to_try}")
    
    for model_name in models_to_try:
        try:
            print(f"🚀 Đang gọi model: {model_name}...")
            ai_data = call_gemini_rest(prompt, model_name)
            print(f"✅ Gọi thành công model: {model_name}!")
            break
        except Exception as e:
            print(f"⚠️ Model {model_name} đang bận hoặc lỗi ({e}), lập tức chuyển sang model tiếp theo...")
            
    # Nếu tất cả máy chủ Google đều đang quá tải 503 cùng lúc, tự động lấy từ kho dự phòng để không bao giờ lỗi đỏ
    if not ai_data:
        print("🛡️ Máy chủ Google đang bảo trì/quá tải diện rộng, kích hoạt Kho Hàng Hot Dự Phòng!")
        available_fallbacks = [item for item in FALLBACK_TRENDS if item["product_name"] not in existing_products]
        ai_data = random.choice(available_fallbacks if available_fallbacks else FALLBACK_TRENDS)

    encoded_kw = urllib.parse.quote_plus(ai_data["search_keyword"])
    shopee_raw_url = f"https://shopee.vn/search?keyword={encoded_kw}"
    
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
        
    print(f"🎉 Hoàn tất xuất bản món: {new_post['product_name']}")

if __name__ == "__main__":
    generate_hot_trend_post()
