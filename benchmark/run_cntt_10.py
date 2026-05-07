"""Chạy 10 câu hard test CNTT qua HybridRAGService và in kết quả."""
import sys, io, os, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.services.hybrid_rag_service import HybridRAGService

QUESTIONS = [
    ("1", "Xung đột luật và ưu tiên áp dụng",
     "Theo Điều 3, khi có sự khác nhau giữa Luật CNTT và một luật chuyên ngành khác về cùng một vấn đề ứng dụng CNTT, luật nào được áp dụng? Nguyên tắc này có bị phá vỡ trong trường hợp nào không?"),
    ("2", "Giới hạn miễn trách nhiệm khi truyền đưa thông tin",
     "Điều 16 quy định tổ chức/cá nhân truyền đưa thông tin của người khác không phải chịu trách nhiệm về nội dung, nhưng có 3 trường hợp ngoại lệ. Nếu một nhà mạng chỉ \"lựa chọn người nhận\" mà không sửa nội dung, họ có bị truy cứu trách nhiệm hay không? Phân tích ranh giới pháp lý."),
    ("3", "Thu thập thông tin cá nhân không cần đồng ý",
     "Điều 21 khoản 3 cho phép thu thập thông tin cá nhân mà không cần đồng ý trong một số trường hợp. Một doanh nghiệp viễn thông có thể viện dẫn điểm nào trong khoản này để sử dụng dữ liệu hành vi người dùng cho mục đích quảng cáo mà không cần xin phép? Lập luận này có hợp lệ không?"),
    ("4", "Trách nhiệm của nhà cung cấp dịch vụ lưu trữ",
     "Theo Điều 18, nhà cung cấp dịch vụ cho thuê chỗ lưu trữ chỉ cần xóa nội dung trái pháp luật khi \"tự mình phát hiện hoặc được cơ quan nhà nước thông báo.\" Điều này có mâu thuẫn với Điều 20 khoản 2 — vốn miễn trừ nghĩa vụ theo dõi, giám sát cho tư nhân — hay không? Phân tích sự khác biệt."),
    ("5", "Quyền đơn phương chấm dứt hợp đồng điện tử",
     "Điều 32 cho phép người mua đơn phương chấm dứt hợp đồng nếu nhập sai thông tin và hệ thống không có chức năng sửa. Điều kiện \"chưa sử dụng hoặc hưởng bất kỳ lợi ích nào\" được hiểu như thế nào đối với hàng hóa kỹ thuật số (phần mềm, nội dung số) vốn \"sử dụng\" ngay khi tải về?"),
    ("6", "Tên miền và sở hữu trí tuệ",
     "Điều 68 khoản 3 yêu cầu việc đăng ký tên miền \".vn\" không xâm phạm quyền lợi hợp pháp của tổ chức, cá nhân khác \"có trước ngày đăng ký.\" Nếu một nhãn hiệu được đăng ký sau khi tên miền đã được cấp phép, bên nào có quyền ưu tiên theo Luật CNTT? Luật này tương tác như thế nào với Luật Sở hữu trí tuệ?"),
    ("7", "Bản sao phần mềm dự phòng và giới hạn quyền",
     "Điều 69 khoản 2 cho phép người dùng hợp pháp sao chép phần mềm để \"lưu trữ dự phòng và thay thế phần mềm bị phá hỏng.\" Việc sao chép một phần mềm đang hoạt động bình thường để chuyển sang máy tính khác có được coi là \"dự phòng\" theo luật này không? Ai có thẩm quyền xác định giới hạn này?"),
    ("8", "Huy động cơ sở hạ tầng trong trường hợp khẩn cấp",
     "Điều 14 cho phép cơ quan nhà nước huy động \"một phần hoặc toàn bộ\" cơ sở hạ tầng thông tin trong trường hợp khẩn cấp. Luật không quy định cơ chế bồi thường cho doanh nghiệp tư nhân bị huy động. Quyền lợi của họ được bảo vệ theo cơ chế pháp lý nào?"),
    ("9", "Nguyên tắc người đứng đầu chịu trách nhiệm và phạm vi",
     "Điều 24 khoản 7 quy định người đứng đầu cơ quan nhà nước phải chịu trách nhiệm về ứng dụng CNTT. Trong khi đó, Điều 77 chỉ quy định xử lý vi phạm đối với \"cá nhân\" và \"tổ chức\" theo cách chung. Vậy khi một cơ quan nhà nước để xảy ra sự cố lộ lọt dữ liệu, trách nhiệm pháp lý cá nhân của người đứng đầu được xác lập như thế nào theo luật này?"),
    ("10", "Phạm vi điều chỉnh sau các lần sửa đổi",
     "Nhiều điều khoản quan trọng đã bị bãi bỏ bởi Luật Công nghiệp Công nghệ số (71/2025/QH15) có hiệu lực từ 01/01/2026, gồm cả các mục về phát triển công nghiệp CNTT (Mục 3, 4 của Chương III). Điều này đặt ra câu hỏi: sau ngày 01/01/2026, phạm vi thực tế của Luật CNTT còn lại là gì, và liệu luật này có còn đủ tính toàn vẹn để điều chỉnh \"phát triển công nghệ thông tin\" như tên gọi hay không?"),
]


def main():
    svc = HybridRAGService()
    out_path = os.path.join(os.path.dirname(__file__), "cntt_10_results_v2.json")
    results = []
    try:
        for idx, title, q in QUESTIONS:
            print(f"\n{'='*80}\n[{idx}] {title}\n{'='*80}")
            print(f"Q: {q[:200]}{'...' if len(q)>200 else ''}\n")
            try:
                r = svc.answer(q, law_id="LuatCNTT2025")
            except Exception as ex:
                print(f"[ERROR] {ex}")
                results.append({"id": idx, "error": str(ex)})
                continue
            print(f"\n--- ANSWER ---\n{r.answer}\n")
            f = r.faithfulness or {}
            cit_match = sum(1 for c in r.citations if c.get('matched'))
            print(f"  citations: {cit_match}/{len(r.citations)} | faith score={f.get('score')}")
            results.append({
                "id": idx, "title": title, "question": q,
                "refined": r.refined.get("refined", ""),
                "answer": r.answer,
                "citations_matched": f"{cit_match}/{len(r.citations)}",
                "faithfulness_score": f.get("score"),
            })
        with open(out_path, "w", encoding="utf-8") as fp:
            json.dump(results, fp, ensure_ascii=False, indent=2)
        print(f"\n→ Saved {out_path}")
    finally:
        svc.close()


if __name__ == "__main__":
    main()
