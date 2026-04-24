# Tóm tắt điều hành

Nguồn: `Biên bản họp ngày 17.04.2026.docx`  
Ngày họp: 17.04.2026  
Chủ đề chính: Xây dựng hệ thống Agentic AI dựa trên Ontology cho nội bộ công ty

## Kết luận chính

Buổi họp xác định một hướng đi mới cho đội AI: không xây thêm công cụ phần mềm theo mô hình ERP/SaaS truyền thống, mà xây một hệ thống có khả năng kết nối dữ liệu, suy luận và đề xuất hành động dựa trên logic nghiệp vụ của công ty.

Trong tư duy này, Ontology là xương sống logic của hệ thống. LLM chỉ là lớp giao diện ngôn ngữ tự nhiên và hỗ trợ diễn giải. Hệ thống không được đưa ra quyết định quan trọng chỉ dựa trên xác suất của LLM, vì LLM có nguy cơ ảo giác và không đảm bảo tính đúng đắn logic.

## Ghi chú trạng thái hiện tại

Theo code hiện tại, hướng đi này đã được hiện thực hóa tốt ở phần **Agentic Operations MVP**:

- dashboard vận hành,
- ontology map,
- rule engine deterministic,
- task/purchase draft,
- chat/RAG có citations,
- approval/routing/audit ở mức MVP.

Phần **Digital Twin realtime đầy đủ** với sensor model, telemetry history, realtime rule engine, sensor alert và 3D twin vẫn là bước tiếp theo, chưa có implementation hoàn chỉnh trong repo hiện tại.

## Thông điệp quan trọng từ Chairman

1. Thị trường đang dịch chuyển từ "bán công cụ" sang "bán kết quả".
2. ERP và SaaS truyền thống không còn là định hướng ưu tiên nếu chỉ đóng vai trò công cụ cho con người thao tác.
3. Công ty cần xây hệ thống AI có khả năng phát hiện vấn đề, liên kết dữ liệu và đề xuất hành động.
4. Ontology phải được thiết kế như một khung lý trí có quy tắc rõ ràng.
5. LLM chỉ nên đóng vai trò giao diện, thông dịch và hỗ trợ truy vấn.
6. Đội AI cần tiếp cận như FDSE: kỹ sư giải quyết vấn đề, không phải coder thuần túy.
7. Dự án đầu tiên chỉ cần là MVP rất nhỏ, khoảng 5-6 liên kết dữ liệu có ý nghĩa.

## Định nghĩa hướng đi sản phẩm

MVP không phải là:

- Một hệ thống ERP mới.
- Một chatbot hỏi đáp tài liệu đơn thuần.
- Một công cụ quản lý workflow có màn hình thao tác thủ công.

MVP cần là:

- Một hệ thống kết nối dữ liệu nội bộ bằng Ontology.
- Một lớp tri thức có quy tắc rõ ràng từ manual, quy trình và dữ liệu vận hành.
- Một agent có khả năng phát hiện điều kiện cần hành động.
- Một giao diện truy vấn bằng ngôn ngữ tự nhiên, có câu trả lời dựa trên căn cứ.

## Phạm vi khởi đầu

Phạm vi được gợi ý trong biên bản là nội bộ khách sạn/cơ sở vật chất, ưu tiên các mảng:

- Thang máy.
- Bảo trì kỹ thuật.
- Phòng cháy chữa cháy.
- Kho phụ tùng.
- Quy trình mua hàng.
- Phê duyệt nội bộ.

Ví dụ mẫu: thang máy sắp hết tuổi thọ cáp kéo thì hệ thống tự động phát hiện, yêu cầu kiểm tra, liên kết với kho phụ tùng, quy trình mua hàng và người phê duyệt.

## Việc cần làm ngay

1. Thu thập manual và quy trình của các bộ phận.
2. Phỏng vấn trưởng bộ phận để xác định vấn đề thực tế.
3. Chọn 1-2 use case có giá trị rõ nhất để làm MVP.
4. Định nghĩa các thực thể, thuộc tính và mối quan hệ trong Ontology.
5. Xây quy tắc suy luận có căn cứ từ manual.
6. Tạo lớp LLM chỉ để truy vấn, diễn giải và trình bày kết quả.
7. Thiết lập quy trình hiệu chỉnh để dạy AI hiểu đúng format và ngữ nghĩa nội bộ.
