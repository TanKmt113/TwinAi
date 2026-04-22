# Rủi ro và câu hỏi cần làm rõ

## Rủi ro 1: Nhầm lẫn chatbot với Ontology

Nếu đội AI chỉ đưa manual vào LLM và cho hỏi đáp, sản phẩm sẽ trở thành chatbot tài liệu. Điều này không đạt tầm nhìn của Chairman, vì chatbot không có khung lý trí đảm bảo tính đúng đắn.

Biện pháp:

- Bắt buộc tách ba lớp: tài liệu gốc, Ontology, LLM.
- Mỗi câu trả lời quan trọng phải có căn cứ từ rule hoặc source.
- LLM không được tạo logic ngoài schema.

## Rủi ro 2: Ontology quá rộng ngay từ đầu

Nếu cố gắng mô hình hóa toàn bộ công ty ngay lập tức, dự án sẽ chậm và khó kiểm chứng.

Biện pháp:

- Bắt đầu với 1 use case.
- Giới hạn 5-6 liên kết dữ liệu đầu tiên.
- Chỉ mở rộng khi use case đầu tiên chạy đúng.

## Rủi ro 3: Manual không đủ hoặc không phản ánh thực tế

Manual có thể cũ, thiếu chi tiết hoặc khác với cách vận hành thực tế. Nếu chỉ dựa vào tài liệu, logic có thể sai.

Biện pháp:

- Phỏng vấn trưởng bộ phận và người trực tiếp vận hành.
- Gắn mỗi rule với người xác nhận nghiệp vụ.
- Lưu trạng thái rule: draft, validated, approved.

## Rủi ro 4: Dữ liệu nguồn rời rạc và thiếu chuẩn hóa

Dữ liệu tồn kho, lịch sử bảo trì, danh mục tài sản và quy trình mua hàng có thể nằm ở nhiều file/hệ thống khác nhau.

Biện pháp:

- Lập data inventory.
- Định nghĩa ID chung cho tài sản, linh kiện, phụ tùng.
- Chấp nhận nhập dữ liệu mẫu thủ công trong MVP nếu cần.

## Rủi ro 5: LLM ảo giác hoặc diễn giải quá mức

LLM có thể trả lời tự tin dù thiếu dữ liệu. Đây là rủi ro lớn nếu người dùng xem kết quả như quyết định chính thức.

Biện pháp:

- Buộc LLM trả lời "không đủ dữ liệu" khi thiếu evidence.
- Tách câu trả lời thành: kết luận, căn cứ, dữ liệu thiếu, hành động đề xuất.
- Dùng test cases để kiểm tra lỗi ảo giác.

## Rủi ro 6: Không có chủ sở hữu nghiệp vụ

Nếu không có người nghiệp vụ xác nhận, đội AI sẽ phải tự đoán quy trình. Điều này trái với yêu cầu "không đoán mò".

Biện pháp:

- Mỗi use case phải có owner nghiệp vụ.
- Mỗi rule phải có người phê duyệt.
- Mỗi thay đổi logic phải có lịch sử cập nhật.

## Câu hỏi cần làm rõ với Chairman

1. Use case MVP đầu tiên nên là thang máy, PCCC, bãi xe hay một mảng khác?
2. Kết quả demo đầu tiên Chairman muốn nhìn thấy là bản đồ Ontology, chatbot truy vấn, hay agent tạo hành động?
3. Dữ liệu nào được phép đưa vào prototype?
4. Mức độ tự động hóa nào được chấp nhận trong MVP: chỉ đề xuất, tạo task, hay gửi yêu cầu thật?
5. Ai là người phê duyệt rule nghiệp vụ đầu tiên?
6. Hệ thống có cần chạy hoàn toàn nội bộ/local hay được phép dùng API bên ngoài?
7. Yêu cầu bảo mật và phân quyền dữ liệu cho từng bộ phận là gì?
8. Cần tích hợp với hệ thống nào hiện có: kho, mua hàng, bảo trì, email, chat nội bộ?

## Câu hỏi cần làm rõ với các bộ phận

1. Tài sản/thiết bị nào có rủi ro cao nhất nếu bảo trì chậm?
2. Sự cố nào xảy ra lặp lại nhiều nhất?
3. Dữ liệu nào hiện đang phải tìm thủ công?
4. Khi nào cần báo động, khi nào chỉ cần nhắc việc?
5. Ai nhận thông báo đầu tiên?
6. Ai có quyền phê duyệt hành động?
7. Cần bằng chứng nào để quyết định thay thế, mua mới hoặc hoãn kiểm tra?
8. Quy trình hiện tại mất bao lâu từ lúc phát hiện đến lúc hoàn thành?

