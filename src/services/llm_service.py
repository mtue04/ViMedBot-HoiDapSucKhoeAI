import google.generativeai as genai
from typing import List
from src.core.config import settings, gemini_key_manager

class LLMService:
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)

    def generate_similar_queries(self, original_query: str, num_queries: int = 3) -> List[str]:
        prompt = f"""Bạn là một chuyên gia y tế. Hãy tạo ra {num_queries-1} câu hỏi tương tự với câu hỏi sau, 
nhưng diễn đạt khác đi để có thể tìm kiếm được nhiều thông tin liên quan hơn.

Câu hỏi gốc: {original_query}

Yêu cầu:
- Mỗi câu hỏi trên một dòng
- Giữ nguyên ý nghĩa chính
- Thay đổi cách diễn đạt, từ ngữ
- Chỉ trả về các câu hỏi, không giải thích

Ví dụ:
- Với câu hỏi gốc 'Những ai có nguy cơ gục ngã bất ngờ vì đột quỵ, đột tử?' có thể đổi thành 'Các nhóm người nào có khả năng bị đột tử mà không báo trước?'
- Với câu hỏi gốc 'Bệnh COVID-19 có lây không?' có thể đổi thành 'Bệnh COVID-19 lây lan qua những con đường nào?'
- Với câu hỏi gốc 'Ung thư phổi có chữa được không?' có thể đổi thành 'Khả năng điều trị ung thư phổi hiện nay như thế nào?'

Các câu hỏi tương tự:"""

        try:
            response = self.model.generate_content(prompt)
            generated_queries = [q.strip() for q in response.text.strip().split('\n') if q.strip()]
            
            # add original to list
            all_queries = [original_query] + generated_queries[:num_queries-1]
            return all_queries
        except Exception as e:
            print(f"Error generating similar queries: {e}")
            return [original_query]
        
    def generate_answer(self, query: str, context: str) -> str:
        prompt = f"""Bạn là ViMedBot — trợ lý sức khỏe gia đình trả lời ngắn gọn, dễ hiểu. 
Chỉ sử dụng thông tin có trong {context}. Không thêm thông tin ngoài {context}. Không chẩn đoán, không kê đơn hay chỉ định điều trị. 
Nếu {context} không đủ để trả lời, viết nguyên văn: "Xin lỗi, tôi chưa có đủ thông tin để trả lời câu hỏi này".

PHONG CÁCH & MỞ BÀI
- Viết một câu dẫn nhập tự nhiên, phù hợp ngữ cảnh câu hỏi, không dùng các cụm khuôn mẫu như “Về [chủ đề]…”, “Những điểm bạn nên biết…”, “Tóm tắt nhanh…”, “Nếu bạn đang tìm hiểu…”, “Dưới đây là…”, “Trao đổi ngắn gọn…”.
- Câu dẫn nhập nhắc lại trọng tâm câu hỏi bằng ngôn ngữ đời thường, 1–2 câu, không dùng ngoặc vuông, không dùng từ “chủ đề”.

KẾT CẤU NỘI DUNG
- Tóm tắt ngắn: 1–2 câu nêu cốt lõi theo {context}.
- Các điểm chính: 
  - Sử dụng gạch đầu dòng Markdown (`- `) cho các ý chính, tối đa 3–5 ý.
  - Nếu ý chính có chi tiết phụ, sử dụng bullet con với thụt đầu dòng (2 khoảng trắng trước `- `, ví dụ: `  - `).
  - Đảm bảo mỗi bullet con liên quan trực tiếp đến bullet cha, không để bullet con đứng độc lập.
- Khi nào nên đi khám: Chỉ liệt kê nếu {context} có nêu dấu hiệu/nguy cơ/cảnh báo, dùng gạch đầu dòng (`- `).
- Lưu ý:
  - Thông tin chỉ mang tính tham khảo chung.
  - Khi có triệu chứng bất thường, đang mang thai, có bệnh nền, hoặc đang dùng thuốc, hãy tham khảo bác sĩ chuyên khoa.

QUY TẮC
- Ngắn gọn, rõ ràng, tránh thuật ngữ khó; nếu dùng thuật ngữ từ {context}, giải thích ngắn gọn.
- Sử dụng ký tự Markdown chuẩn: `- ` cho bullet, `**text**` cho in đậm, `*text*` cho nghiêng.
- Không nêu nguồn, không viết “theo tài liệu/nguồn/tham khảo”.
- Không suy diễn ngoài {context}, không kết luận điều trị.
- Đảm bảo định dạng Markdown rõ ràng, dễ đọc, với các bullet lồng nhau đúng cú pháp, không bold text.
- Nếu câu hỏi vượt ngoài phạm vi {context}, trả lời: "Xin lỗi, tôi chưa có đủ thông tin để trả lời câu hỏi này".

CÂU HỎI: {query}

TRẢ LỜI:"""
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Xin lỗi, có lỗi xảy ra khi tạo câu trả lời: {str(e)}"