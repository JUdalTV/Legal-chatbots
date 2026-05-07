"""Chạy 10 câu hard test ANM 2025 qua HybridRAGService."""
import sys, io, os, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.services.hybrid_rag_service import HybridRAGService

QUESTIONS = [
    ("1", "Phạm vi áp dụng với người gốc Việt chưa có căn cước",
     "Điều 1 khoản 2(b) áp dụng luật này với người gốc Việt Nam chưa xác định được quốc tịch đang sinh sống tại Việt Nam \"đã được cấp giấy chứng nhận căn cước.\" Điều này đặt ra câu hỏi: nếu một người gốc Việt chưa rõ quốc tịch chưa được cấp căn cước nhưng vẫn đang hoạt động trên không gian mạng tại Việt Nam, họ có bị điều chỉnh bởi luật này không? Khoảng trống pháp lý này được xử lý như thế nào?"),
    ("2", "Ranh giới đấu tranh bảo vệ vs tấn công mạng bị cấm",
     "Điều 21 khoản 2(đ) cho phép lực lượng chuyên trách \"chủ động tấn công vô hiệu hóa mục tiêu trên không gian mạng.\" Trong khi đó, Điều 7 khoản 3 nghiêm cấm hành vi \"tấn công mạng.\" Căn cứ pháp lý nào phân biệt hành vi tấn công hợp pháp (do lực lượng chuyên trách thực hiện) với hành vi bị nghiêm cấm? Liệu có rủi ro lạm dụng điều khoản này không?"),
    ("3", "Thời hạn cung cấp thông tin người dùng",
     "Điều 25 khoản 2(a) yêu cầu doanh nghiệp cung cấp thông tin người dùng trong vòng 24 giờ theo yêu cầu, và 3 giờ trong trường hợp khẩn cấp. Luật không quy định phải có lệnh của tòa án hay phán quyết độc lập nào trước khi yêu cầu này được thực hiện. Điều này có xung đột với các nguyên tắc bảo vệ dữ liệu cá nhân không? Cơ chế kiểm soát quyền lực nào tồn tại để ngăn việc yêu cầu thông tin tùy tiện?"),
    ("4", "Data localization với doanh nghiệp nước ngoài",
     "Điều 25 khoản 3 yêu cầu doanh nghiệp nước ngoài thu thập dữ liệu người dùng Việt Nam phải lưu trữ dữ liệu tại Việt Nam và đặt chi nhánh hoặc văn phòng đại diện tại Việt Nam. Nếu một doanh nghiệp nước ngoài từ chối tuân thủ nhưng vẫn tiếp cận thị trường Việt Nam qua kênh gián tiếp (VPN, bên thứ ba...), biện pháp cưỡng chế nào có thể được áp dụng? Luật có cơ chế thực thi thực chất không?"),
    ("5", "Định nghĩa tin giả và nguy cơ kiểm duyệt",
     "Điều 5 khoản 1(k) cho phép \"yêu cầu xóa bỏ thông tin sai sự thật, tin giả.\" Tuy nhiên, luật không định nghĩa tiêu chí cụ thể để xác định thế nào là \"tin giả.\" Ai có thẩm quyền kết luận một thông tin là sai sự thật trước khi ra lệnh xóa? Điều này tương tác như thế nào với quyền tự do ngôn luận và nghĩa vụ của doanh nghiệp phải xóa trong vòng 24 giờ (Điều 25) trước khi có xác minh độc lập?"),
    ("6", "Ngắt kết nối mạng quốc tế — ngưỡng và thiệt hại",
     "Điều 20 khoản 3(đ) cho phép \"ngừng cung cấp thông tin mạng tại khu vực cụ thể hoặc ngắt cổng kết nối mạng quốc tế\" như một biện pháp xử lý tình huống nguy hiểm. Thẩm quyền quyết định biện pháp này thuộc Thủ tướng hoặc Bộ trưởng Bộ Công an (khoản 4(b)). Luật có thiết lập điều kiện tối thiểu hay giới hạn thời gian nào cho biện pháp cực đoan này không? Trách nhiệm bồi thường thiệt hại kinh tế cho doanh nghiệp và người dân bị ảnh hưởng được quy định ở đâu?"),
    ("7", "Trách nhiệm cha mẹ và trẻ em",
     "Điều 16 khoản 2 quy định trẻ em sử dụng dịch vụ gia tăng trên không gian mạng phải đăng ký tài khoản bằng thông tin của cha, mẹ hoặc người giám hộ. Nếu trẻ tự đăng ký tài khoản bằng thông tin giả mạo người lớn và sau đó thực hiện hành vi vi phạm pháp luật, trách nhiệm pháp lý được phân bổ như thế nào giữa trẻ em, cha mẹ, và nền tảng cung cấp dịch vụ?"),
    ("8", "Tập huấn chứng nhận chỉ với DN nhà nước",
     "Điều 34 khoản 2 yêu cầu người trực tiếp quản trị, vận hành hệ thống thông tin cấp độ 3, 4, 5 trong cơ quan, tổ chức, doanh nghiệp nhà nước phải được tập huấn và cấp chứng nhận. Tại sao yêu cầu này chỉ áp dụng cho doanh nghiệp nhà nước mà không áp dụng cho doanh nghiệp tư nhân vận hành hệ thống cùng cấp độ? Sự phân biệt này có tạo ra khoảng trống an ninh mạng hay không?"),
    ("9", "Định nghĩa xung đột thông tin và phạm vi can thiệp",
     "Điều 22 khoản 1 định nghĩa \"xung đột thông tin\" là khi hai hoặc nhiều tổ chức trong nước và nước ngoài dùng biện pháp công nghệ gây tổn hại đến thông tin làm ảnh hưởng đến an ninh quốc gia, trật tự, an toàn xã hội. Liệu một cuộc tranh luận thông tin công khai giữa hai tổ chức phi chính phủ — ví dụ về chính sách — có thể bị diễn giải là \"xung đột thông tin\" và bị can thiệp theo Điều 22 không? Tiêu chí nào ngăn diễn giải mở rộng tùy tiện?"),
    ("10", "Ngân sách tối thiểu 15%",
     "Điều 38 khoản 1 bắt buộc cơ quan, tổ chức nhà nước phải bố trí tối thiểu 15% tổng kinh phí chương trình chuyển đổi số và ứng dụng CNTT cho bảo vệ an ninh mạng. Đây là con số cứng hay có thể linh hoạt? Nếu một cơ quan nhà nước không đủ ngân sách để đáp ứng ngưỡng này, trách nhiệm pháp lý của người đứng đầu cơ quan đó là gì? Cơ chế kiểm tra, thanh tra việc tuân thủ ngưỡng này được thực hiện như thế nào?"),
]


def main():
    svc = HybridRAGService()
    out_path = os.path.join(os.path.dirname(__file__), "anm_10_results_v2.json")
    results = []
    try:
        for idx, title, q in QUESTIONS:
            print(f"\n{'='*80}\n[{idx}] {title}\n{'='*80}")
            print(f"Q: {q[:200]}{'...' if len(q)>200 else ''}\n")
            try:
                r = svc.answer(q, law_id="LuatAnNinhMang2025")
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
