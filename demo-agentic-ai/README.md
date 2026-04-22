# Demo Agentic AI Ontology

Đây là bản demo web tĩnh được dựng từ các tài liệu:

- `03-thiet-ke-mvp-agentic-ai.md`
- `04-ke-hoach-hanh-dong.md`
- `05-rui-ro-va-cau-hoi-can-lam-ro.md`

## Nội dung demo

Demo mô phỏng một MVP nhỏ cho use case bảo trì thang máy:

- Lớp dữ liệu: danh sách thang máy, linh kiện, tuổi thọ còn lại, tồn kho và lead time mua hàng.
- Lớp Ontology: chuỗi liên kết thang máy -> linh kiện -> quy tắc -> tồn kho -> mua hàng -> phê duyệt.
- Lớp Reasoning: rule phát hiện linh kiện còn dưới 6 tháng và rule tạo đề xuất mua hàng.
- Lớp LLM interface: hộp hỏi đáp bằng tiếng Việt, nhưng chỉ trả lời dựa trên dữ liệu/rule có sẵn.
- Lớp Agent: tạo log task kiểm tra và đề xuất mua hàng.

## Cách chạy

Mở file sau bằng trình duyệt:

`demo-agentic-ai/index.html`

Không cần cài dependency và không cần chạy server.

## Câu hỏi mẫu

- Có thang máy nào sắp cần kiểm tra hoặc thay linh kiện không?
- Vì sao cần mua cáp kéo từ Đức?
- Ai là người phê duyệt yêu cầu này?
- Dự báo doanh thu tháng sau là bao nhiêu?

Ở câu hỏi ngoài phạm vi, demo sẽ trả lời "không đủ dữ liệu" để thể hiện guardrail chống ảo giác.
