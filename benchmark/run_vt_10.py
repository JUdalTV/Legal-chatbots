"""Chạy 10 câu hard test Luật Viễn thông 2023."""
import sys, io, os, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.services.hybrid_rag_service import HybridRAGService

QUESTIONS = [
    ("1", "Ranh giới dịch vụ VT cơ bản trên Internet vs ứng dụng VT",
     "Điều 3 định nghĩa dịch vụ viễn thông cơ bản trên Internet là dịch vụ có \"tính năng chính là gửi, truyền, nhận thông tin giữa hai người hoặc một nhóm người.\" Trong khi đó dịch vụ ứng dụng viễn thông là dịch vụ \"sử dụng mạng viễn thông để cung cấp ứng dụng trong lĩnh vực tài chính, ngân hàng...\" Một ứng dụng nhắn tin tích hợp thanh toán (như Zalo Pay, WeChat) thuộc loại hình nào? Việc phân loại sai dẫn đến những hệ quả pháp lý gì về giấy phép và nghĩa vụ?"),
    ("2", "Nghĩa vụ bán buôn và giới hạn từ chối",
     "Điều 17 khoản 3(a) buộc doanh nghiệp thống lĩnh thị trường phải thực hiện hoạt động bán buôn \"khi có yêu cầu từ doanh nghiệp viễn thông khác.\" Điều 16 khoản 2(a) yêu cầu giá cả phải \"công bằng, hợp lý, không phân biệt đối xử.\" Tuy nhiên, không có cơ chế trọng tài độc lập nào được quy định trong luật để xác định mức giá bán buôn \"hợp lý\" khi có tranh chấp. Khi hai bên không đồng thuận về giá, cơ chế giải quyết cụ thể là gì và ai có thẩm quyền phán quyết cuối cùng?"),
    ("3", "Bảo mật thông tin và ngoại lệ tiết lộ",
     "Điều 6 khoản 4 cấm doanh nghiệp tiết lộ thông tin người dùng, nhưng có ngoại lệ tại điểm (d): \"khi có yêu cầu của cơ quan nhà nước có thẩm quyền theo quy định của pháp luật.\" Ngoại lệ này không giới hạn phạm vi thông tin có thể yêu cầu, không yêu cầu hình thức văn bản hay phán quyết độc lập. Điều này tương tác như thế nào với quyền bảo mật thông tin của người dùng tại Điều 15 khoản 1(đ)? Liệu có mâu thuẫn nội tại trong luật không?"),
    ("4", "Từ chối giao kết hợp đồng và danh sách đen",
     "Điều 22 khoản 1(c) cho phép doanh nghiệp từ chối cung cấp dịch vụ với người dùng đã bị một doanh nghiệp khác liệt vào danh sách \"trốn tránh nghĩa vụ thanh toán\" — chỉ cần có \"thỏa thuận bằng văn bản\" giữa các doanh nghiệp. Cơ chế chia sẻ danh sách đen này có bị điều chỉnh bởi nguyên tắc bảo vệ dữ liệu cá nhân không? Nếu một người dùng bị liệt vào danh sách sai, họ có cơ chế khiếu nại và đòi quyền tiếp cận dịch vụ như thế nào?"),
    ("5", "Miễn trách nhiệm nội dung của điện toán đám mây",
     "Điều 29 khoản 1(c) quy định doanh nghiệp cung cấp dịch vụ điện toán đám mây \"không phải chịu trách nhiệm về nội dung thông tin của người sử dụng dịch vụ trong quá trình xử lý, lưu trữ và truy xuất thông tin, trừ trường hợp luật khác có quy định.\" Ngoại lệ \"luật khác\" này mở ra phạm vi rất rộng — bao gồm Luật An ninh mạng, Luật CNTT, Luật Báo chí. Trong thực tế, khi nội dung vi phạm được lưu trên hạ tầng đám mây nước ngoài đặt tại Việt Nam, ranh giới chịu trách nhiệm của nhà cung cấp hạ tầng và người đăng nội dung được xác định như thế nào?"),
    ("6", "Cung cấp dịch vụ qua biên giới và WTO",
     "Điều 21 khoản 2 yêu cầu tổ chức nước ngoài cung cấp dịch vụ qua biên giới phải tuân thủ các yêu cầu \"quốc phòng, an ninh, chính sách công cộng\" ngoài cam kết WTO. Khái niệm \"chính sách công cộng\" không được định nghĩa trong luật. Điều này có tạo ra rủi ro vi phạm cam kết WTO nếu Việt Nam sử dụng điều khoản này như rào cản thương mại trá hình không? Cơ chế nào ngăn sự lạm dụng điều khoản mở này?"),
    ("7", "Giấy phép thử nghiệm và thương mại hóa",
     "Điều 38 khoản 3 cấp giấy phép thử nghiệm tối đa 2 năm cho dịch vụ \"chưa được quy định trong giấy phép\" và yêu cầu \"phạm vi và quy mô thử nghiệm được giới hạn để đánh giá công nghệ, thị trường.\" Luật không định nghĩa ngưỡng quy mô cụ thể. Một dịch vụ 5G thử nghiệm đang phục vụ hàng triệu người dùng tại các thành phố lớn có còn là \"thử nghiệm giới hạn\" không? Ai có thẩm quyền kết luận doanh nghiệp đã vượt ngưỡng thử nghiệm và cần giấy phép chính thức?"),
    ("8", "Quyền giữ số khi chuyển mạng",
     "Điều 13 khoản 2(h) buộc doanh nghiệp phải \"bảo đảm cho thuê bao được giữ nguyên số thuê bao khi thay đổi doanh nghiệp cung cấp dịch vụ trong cùng một loại hình dịch vụ.\" Cụm từ \"cùng một loại hình dịch vụ\" đặt ra câu hỏi: nếu người dùng muốn chuyển từ dịch vụ di động 4G của nhà mạng A sang dịch vụ di động 5G của nhà mạng B, đây có phải \"cùng loại hình\" hay không? Khi nhà mạng mới chưa phủ sóng địa bàn người dùng, họ có thể từ chối chuyển số theo Điều 22 khoản 1(b) về \"không khả thi kỹ thuật\" không?"),
    ("9", "Huy động cơ sở hạ tầng và bồi thường",
     "Điều 13 khoản 2(g) buộc doanh nghiệp phải thực hiện yêu cầu huy động \"một phần hoặc toàn bộ cơ sở hạ tầng viễn thông, dịch vụ viễn thông trong trường hợp khẩn cấp theo quy định của pháp luật về quốc phòng, an ninh quốc gia.\" Luật Viễn thông không quy định cơ chế bồi thường. Quyền lợi kinh tế của doanh nghiệp tư nhân bị huy động toàn bộ hạ tầng được bảo vệ theo cơ chế pháp lý nào? Ai có thẩm quyền quyết định mức bồi thường và trong thời hạn bao lâu?"),
    ("10", "Ngừng cung cấp khẩn cấp và trách nhiệm dân sự",
     "Điều 5 khoản 6 buộc doanh nghiệp phải \"ngừng khẩn cấp việc cung cấp dịch vụ viễn thông\" khi có yêu cầu của cơ quan nhà nước trong trường hợp có bạo loạn hoặc xâm phạm an ninh quốc gia. Nếu việc ngừng dịch vụ gây thiệt hại trực tiếp cho người dùng đang thực hiện giao dịch tài chính, y tế khẩn cấp, hoặc hợp đồng kinh tế — Điều 15 khoản 1(e) cho phép người dùng \"được bồi thường thiệt hại trực tiếp do lỗi của doanh nghiệp.\" Doanh nghiệp tuân lệnh nhà nước có bị coi là có \"lỗi\" không? Và nếu không, người dùng bị thiệt hại có thể kiện ai?"),
]


def main():
    svc = HybridRAGService()
    out_path = os.path.join(os.path.dirname(__file__), "vt_10_results_v2.json")
    results = []
    try:
        for idx, title, q in QUESTIONS:
            print(f"\n{'='*80}\n[{idx}] {title}\n{'='*80}")
            print(f"Q: {q[:200]}{'...' if len(q)>200 else ''}\n")
            try:
                r = svc.answer(q, law_id="LuatVienThong2023")
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
