# Kế hoạch hành động

## Nguyên tắc thực thi

Dự án phải bắt đầu từ vấn đề thực tế của từng bộ phận, không bắt đầu từ việc chọn framework hay viết code. Mỗi bước kỹ thuật phải phục vụ việc biến tri thức vận hành thành logic có thể kiểm chứng.

## Giai đoạn 1: Chuẩn bị và thu thập tài liệu

Thời gian gợi ý: 1-2 tuần

Việc cần làm:

- Lập danh sách bộ phận cần làm việc: kỹ thuật, PCCC, mua hàng, kho, hành chính/nhân sự, vận hành khách sạn, bãi xe.
- Thu thập manual, quy trình, biểu mẫu và danh mục dữ liệu hiện có.
- Phân loại tài liệu theo lĩnh vực và mức độ ưu tiên.
- Tạo danh mục tài liệu gốc và người sở hữu tài liệu.
- Xác định tài liệu nào có giá trị cho use case MVP đầu tiên.

Đầu ra:

- `document_inventory.md`: danh mục tài liệu.
- Bộ manual liên quan đến use case đầu tiên.
- Danh sách người phụ trách nghiệp vụ.

## Giai đoạn 2: Phỏng vấn bộ phận

Thời gian gợi ý: 1-2 tuần

Câu hỏi cần đặt:

- Bộ phận đang gặp vấn đề gì lặp lại nhiều lần?
- Điều gì gây tốn thời gian, chi phí hoặc rủi ro cao?
- Quy trình nào đang phụ thuộc vào kinh nghiệm cá nhân?
- Dữ liệu nào đang nằm rời rạc?
- Khi có sự cố, ai là người xử lý và quyết định dựa trên căn cứ nào?
- Nếu AI có thể chủ động cảnh báo/đề xuất hành động, đâu là tình huống hữu ích nhất?

Đầu ra:

- Danh sách pain points theo bộ phận.
- Use case ưu tiên.
- Bản đồ quy trình hiện tại.
- Nguồn dữ liệu cần kết nối.

## Giai đoạn 3: Thiết kế Ontology tối thiểu

Thời gian gợi ý: 1-2 tuần

Việc cần làm:

- Chọn 5-6 mối quan hệ dữ liệu quan trọng nhất.
- Định nghĩa các thực thể, thuộc tính và mối quan hệ.
- Định nghĩa quy tắc suy luận đầu tiên.
- Gắn mỗi quy tắc với nguồn tài liệu/manual.
- Xác định dữ liệu bắt buộc, dữ liệu tùy chọn và dữ liệu còn thiếu.

Đầu ra:

- `ontology_schema.md`: schema thực thể và quan hệ.
- `reasoning_rules.md`: quy tắc suy luận.
- `data_gap.md`: danh sách dữ liệu thiếu.

## Giai đoạn 4: Xây prototype

Thời gian gợi ý: 2-4 tuần

Chức năng cần có:

- Nạp dữ liệu mẫu từ manual và bảng dữ liệu nội bộ.
- Lưu được các thực thể và quan hệ.
- Chạy được một số quy tắc suy luận.
- Cho phép hỏi đáp bằng ngôn ngữ tự nhiên.
- Trả lời kèm căn cứ và hành động đề xuất.
- Tạo được task/cảnh báo dạng demo.

Đầu ra:

- Prototype chạy nội bộ.
- Demo use case thang máy/bảo trì.
- Báo cáo đánh giá lỗi sai của LLM.
- Danh sách cần hiệu chỉnh tiếp theo.

## Giai đoạn 5: Hiệu chỉnh và dạy AI

Thời gian gợi ý: liên tục sau prototype

Việc cần làm:

- Ghi nhận câu hỏi người dùng và câu trả lời của hệ thống.
- Đánh dấu câu trả lời sai, thiếu căn cứ hoặc diễn giải sai ngữ nghĩa.
- Bổ sung từ điển nội bộ, synonym, tên gọi viết tắt.
- Sửa mapping giữa câu hỏi tự nhiên và thực thể trong Ontology.
- Bổ sung quy tắc guardrail để ngăn LLM suy đoán.

Đầu ra:

- Tập test câu hỏi/câu trả lời.
- Bộ quy tắc guardrail cho LLM.
- Bảng lỗi đã sửa và lỗi còn tồn tại.

## Phân công nhân sự gợi ý

### Người 1: Manual và nghiệp vụ

Trách nhiệm:

- Thu thập tài liệu.
- Làm việc với bộ phận nghiệp vụ.
- Chuyển manual thành quy tắc và điều kiện.
- Xác minh logic với người phụ trách.

### Người 2: Ontology và hệ thống

Trách nhiệm:

- Thiết kế schema thực thể/mối quan hệ.
- Xây lớp lưu trữ và truy vấn Ontology.
- Kết nối LLM với Ontology.
- Xây prototype agent và guardrail.

## Mốc demo đề xuất

1. Demo 1: Hiển thị bản đồ liên kết dữ liệu cho use case thang máy.
2. Demo 2: Hỏi đáp bằng ngôn ngữ tự nhiên có trích nguồn.
3. Demo 3: Hệ thống tự phát hiện điều kiện cần kiểm tra.
4. Demo 4: Agent tạo đề xuất hành động và luồng phê duyệt.

