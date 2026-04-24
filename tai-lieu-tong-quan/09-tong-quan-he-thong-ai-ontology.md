# Tổng quan hệ thống AI Ontology

## 1. Hệ thống AI Ontology là gì?

AI Ontology là hệ thống giúp doanh nghiệp biến dữ liệu, tài liệu, quy trình và kinh nghiệm vận hành thành một bản đồ tri thức có thể hiểu, kiểm tra và kích hoạt hành động.

Cốt lõi của hệ thống là **Ontology Graph**: bản đồ thể hiện các đối tượng trong doanh nghiệp liên quan với nhau như thế nào. Ví dụ: tài sản thuộc bộ phận nào, áp dụng quy trình nào, ai phụ trách, khi nào phát sinh rủi ro và bước xử lý tiếp theo là gì.

AI trong hệ thống không tự suy đoán hoặc tự ra quyết định quan trọng. AI chủ yếu giúp người dùng hỏi đáp, diễn giải kết quả và trình bày thông tin bằng ngôn ngữ dễ hiểu. Các kết luận nghiệp vụ phải dựa trên dữ liệu thật, rule đã xác nhận và nguồn căn cứ rõ ràng.

## 2. Hệ thống giúp gì cho doanh nghiệp?

Hệ thống giải quyết vấn đề dữ liệu và tri thức vận hành đang bị phân tán ở nhiều file, nhiều hệ thống và nhiều phòng ban.

Giá trị chính:

- Kết nối dữ liệu rời rạc thành một chuỗi logic thống nhất.
- Phát hiện sớm rủi ro hoặc điều kiện cần xử lý.
- Chuẩn hóa cách xử lý theo rule nghiệp vụ đã được phê duyệt.
- Tạo cảnh báo, task, đề xuất hoặc luồng phê duyệt đúng người.
- Trả lời câu hỏi có căn cứ, không trả lời chung chung.
- Lưu lại lịch sử xử lý để kiểm soát trách nhiệm và audit.

Nói ngắn gọn, hệ thống không chỉ báo "có vấn đề", mà chỉ ra vấn đề nằm ở đâu, vì sao quan trọng, căn cứ từ đâu, ai cần xử lý và bước tiếp theo là gì.

## 3. Phạm vi ứng dụng

AI Ontology không bị giới hạn ở một nghiệp vụ cụ thể. Doanh nghiệp có thể bắt đầu từ một use case nhỏ, sau đó mở rộng dần sang các mảng khác.

Một số phạm vi phù hợp:

- **Tài sản và bảo trì:** theo dõi thiết bị, hạn kiểm tra, phụ tùng, task bảo trì.
- **PCCC:** quản lý thiết bị, thời hạn kiểm định, cảnh báo và quy trình xử lý.
- **Kho và mua hàng:** theo dõi tồn kho tối thiểu, lead time, đề xuất mua hàng.
- **Phê duyệt nội bộ:** xác định đúng người duyệt theo phòng ban, giá trị hoặc loại yêu cầu.
- **Vận hành tòa nhà/khách sạn:** liên kết sự cố, khu vực, người phụ trách, SLA và escalation.

## 4. Cơ chế hoạt động

Luồng tổng quát:

```text
Dữ liệu & tài liệu
  -> Chuẩn hóa tri thức
  -> Ontology Graph
  -> Rule nghiệp vụ
  -> Agent đề xuất hành động
  -> Người dùng xác nhận/phê duyệt
  -> Audit log
```

Diễn giải ngắn:

1. Thu thập dữ liệu, manual, quy trình, tài sản, nhân sự, tồn kho.
2. Chuẩn hóa thành thực thể, thuộc tính, quan hệ và điều kiện xử lý.
3. Xây Ontology Graph để thể hiện các mối liên kết nghiệp vụ.
4. Chạy rule đã được xác nhận để phát hiện rủi ro hoặc điều kiện cần xử lý.
5. Agent tạo cảnh báo, task, đề xuất hoặc luồng phê duyệt.
6. Người có thẩm quyền xác nhận các quyết định quan trọng.
7. Hệ thống ghi audit log để truy vết toàn bộ quá trình.

## 5. Hình minh họa hệ thống tổng thể

![Sơ đồ tổng quan hệ thống AI Ontology](https://github.com/TanKmt113/TwinAi/blob/main/tai-lieu-tong-quan/ChatGPT%20Image%2019_28_12%2023%20thg%204,%202026.png?raw=true)

## 6. Các tầng trong hệ thống

- **Dữ liệu và tài liệu gốc:** quy trình, manual, tài sản, kho, nhân sự, phê duyệt, lịch sử vận hành.
- **Ontology Graph:** bản đồ quan hệ giữa dữ liệu, quy trình, con người và hành động.
- **Rule Engine:** kiểm tra điều kiện nghiệp vụ đã được xác nhận.
- **AI / LLM:** diễn giải kết quả, trả lời câu hỏi, nêu căn cứ và dữ liệu còn thiếu.
- **Agent Workflow:** tạo cảnh báo, task, đề xuất, thông báo, phê duyệt và theo dõi trạng thái.
- **Giao diện Web:** dashboard, bản đồ quan hệ, chat, task, phê duyệt, báo cáo.
- **Audit & phân quyền:** kiểm soát ai được xem/làm gì và lưu lịch sử xử lý.

## 7. Khác biệt so với chatbot và ERP

| Loại hệ thống | Vai trò chính | Hạn chế nếu dùng riêng |
|---|---|---|
| Chatbot tài liệu | Hỏi đáp nội dung file | Không đủ để quyết định nghiệp vụ nếu thiếu rule và dữ liệu có cấu trúc |
| ERP | Lưu giao dịch và trạng thái nghiệp vụ | Không tự hiểu bối cảnh và quan hệ nhiều tầng giữa dữ liệu |
| AI Ontology | Hiểu quan hệ, chạy rule, đề xuất hành động có căn cứ | Cần dữ liệu và rule được chuẩn hóa ban đầu |

## 8. Timeline MVP use case thang máy

Use case thang máy là phạm vi thử nghiệm đầu tiên để chứng minh hệ thống có thể nối dữ liệu, rule, cảnh báo, task, tồn kho, mua hàng và phê duyệt trong một luồng hoàn chỉnh.

| Giai đoạn | Thời gian | Đầu ra |
|---|---:|---|
| Chốt phạm vi & dữ liệu | Ngày 1-2 | Danh sách thang máy, linh kiện ưu tiên, manual, tồn kho, mua hàng, phê duyệt |
| Thiết kế Ontology tối thiểu | Ngày 3-4 | Quan hệ: thang máy, linh kiện, rule, phụ tùng, tồn kho, người phê duyệt |
| Xác nhận rule nghiệp vụ | Ngày 5 | Rule cảnh báo đầu tiên và điều kiện tạo task/đề xuất được xác nhận |
| Xây prototype | Ngày 6-10 | Màn hình demo, rule engine, cảnh báo, task, đề xuất mua hàng |
| Kiểm thử & hiệu chỉnh | Ngày 11-12 | Sửa logic, bổ sung dữ liệu thiếu, kiểm tra câu trả lời có căn cứ |
| Demo MVP | Ngày 13-14 | Demo luồng hoàn chỉnh và danh sách việc cần làm sau MVP |

**Kết quả kỳ vọng sau 2 tuần:** hệ thống demo được luồng "thang máy -> linh kiện -> rule cảnh báo -> task kiểm tra -> tồn kho -> đề xuất mua hàng -> người phê duyệt", kèm lý do và nguồn căn cứ.

## 9. Kết luận

AI Ontology giúp doanh nghiệp chuyển từ vận hành thủ công, phụ thuộc vào tìm kiếm và kinh nghiệm cá nhân sang vận hành chủ động, có căn cứ và có thể kiểm soát.

Doanh nghiệp có thể bắt đầu từ một MVP nhỏ, sau đó mở rộng sang tài sản, bảo trì, kho, mua hàng, phê duyệt, PCCC và các quy trình nội bộ khác.
