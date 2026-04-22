# Phase 00: Tổng quan roadmap

## Mục tiêu

Chia hệ thống MVP Agentic AI Ontology thành các giai đoạn phát triển có thể triển khai, kiểm thử và nghiệm thu độc lập.

## Nguyên tắc triển khai

1. Ontology và Rule Engine đi trước LLM.
2. Neo4j được dùng ngay từ MVP để lưu Ontology graph.
3. PostgreSQL giữ dữ liệu giao dịch, audit, task, purchase request.
4. LLM chỉ là lớp giao diện, không tự quyết định nghiệp vụ.
5. Mỗi phase phải có deliverable chạy được.
6. Không tự động gửi đơn mua hàng thật trong MVP.

## Roadmap tổng quát

| Phase | Tên | Mục tiêu chính |
|---|---|---|
| 01 | Nền tảng kiến trúc | Dựng repo, Docker Compose, PostgreSQL, Neo4j, MinIO, FastAPI |
| 02 | Data + Neo4j + Rule Engine | Seed dữ liệu, tạo graph Ontology, chạy rule `R-ELV-CABLE-001` |
| 03 | Dashboard + Ontology Map | Xây UI quản trị, dashboard và bản đồ Ontology |
| 04 | Manual + RAG + Chat | Upload manual, embedding, hỏi đáp có citations |
| 05 | Approval + Notification + Audit | Phê duyệt, n8n notification, audit log viewer |
| 06 | Nghiệm thu MVP | Chạy kịch bản demo cuối cùng |

## Luồng giá trị cần chứng minh

```text
Thang máy Calidas 1
  -> Cáp kéo còn 5 tháng
  -> Rule R-ELV-CABLE-001 được kích hoạt
  -> Tạo task kiểm tra
  -> Tồn kho cáp = 0
  -> Lead time = 7 tháng
  -> Tạo purchase request draft
  -> Người phê duyệt cuối = CEO
  -> Chat trả lời có căn cứ
```

## Deliverable cuối cùng

MVP được xem là đạt khi người dùng có thể:

1. Mở dashboard.
2. Xem Calidas 1 có rủi ro.
3. Chạy reasoning.
4. Xem task kiểm tra được tạo.
5. Xem purchase request draft.
6. Xem ontology map.
7. Hỏi bằng tiếng Việt và nhận câu trả lời có căn cứ.
8. Phê duyệt hoặc từ chối purchase request.
9. Xem audit log cho toàn bộ hành động.

