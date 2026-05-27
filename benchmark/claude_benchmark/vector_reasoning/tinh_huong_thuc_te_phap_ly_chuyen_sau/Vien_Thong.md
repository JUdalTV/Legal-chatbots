# Vector reasoning — Luật Viễn thông 24/2023/QH15

- Task: `tinh_huong_thuc_te_phap_ly_chuyen_sau`
- Source: `Vien_Thong.docx`
- Time: 2026-05-27 17:12:07
- Pipeline: Vector RAG only (Qdrant + reranker + LLM)
- **Reasoning (enable_thinking): ON**
- Law filter: `LuatVienThong2023`
- Total questions: 10

## Câu 1

**Question:**

Công ty Viettel đang cho công ty VNPT thuê một phần hạ tầng cột ăng-ten. VNPT sau đó ký hợp đồng cho FPT Telecom thuê lại đúng phần hạ tầng đó mà không hỏi Viettel. FPT đã lắp đặt thiết bị và vận hành được 3 tháng thì Viettel phát hiện ra. Xác định: hành vi của VNPT có hợp pháp không; FPT có phải tháo dỡ thiết bị không; và nếu Viettel kiện đòi bồi thường thì căn cứ pháp lý nằm ở đâu.

- Elapsed: 105.5s
- Low confidence: True

**Answer:**
**1. Về tính hợp pháp của hành vi cho thuê lại hạ tầng của VNPT**
Trạng thái pháp lý: **B — Khoảng trống quy định**.
Luật Viễn thông 2023 không quy định cụ thể về cơ chế "cho thuê lại" hoặc "cho phép chuyển nhượng quyền sử dụng hạ tầng" giữa các doanh nghiệp viễn thông.
*   **Căn cứ:** [Luật Viễn thông 2023] Điều 5, Khoản 2 quy định trách nhiệm bảo vệ hạ tầng của "tổ chức, cá nhân sở hữu hạ tầng kỹ thuật viễn thông thụ động". [Luật Viễn thông 2023] Điều 9, Khoản 4 cấm "Thiết lập cơ sở hạ tầng viễn thông, cung cấp dịch vụ viễn thông khi chưa được phép thực hiện theo quy định của Luật này".
*   **Phân tích:** Hành vi của VNPT không bị cấm trực tiếp bởi văn bản, nhưng có thể vi phạm nghĩa vụ hợp đồng với Viettel (chủ sở hữu). Nếu VNPT cung cấp dịch vụ qua hạ tầng đó mà không có giấy phép (Điều 9, Khoản 4), hành vi này bị nghiêm cấm.
*   **Suy luận bù khoảng trống:**
    *   **Nguyên tắc:** Quyền sở hữu hạ tầng (Điều 5) ưu tiên quyền kiểm soát của chủ sở hữu (Viettel). Việc chuyển giao quyền sử dụng phải tuân thủ thỏa thuận ban đầu.
    *   **Phân công:** Viettel (chủ sở hữu) có quyền yêu cầu chấm dứt vi phạm. VNPT (người thuê) có nghĩa vụ tuân thủ hợp đồng với chủ sở hữu.
    *   **Mức độ chắc chắn:** Đây là suy luận từ nguyên tắc sở hữu và quản lý hạ tầng — luật chưa quy định tường minh về hợp đồng cho thuê lại hạ tầng.

**2. Về nghĩa vụ tháo dỡ thiết bị của FPT**
Trạng thái pháp lý: **A — Quy định rõ ràng** (nếu xét về tính hợp pháp của việc thiết lập).
*   **Căn cứ:** [Luật Viễn thông 2023] Điều 9, Khoản 4: "Thiết lập cơ sở hạ tầng viễn thông, cung cấp dịch vụ viễn thông khi chưa được phép thực hiện theo quy định của Luật này".
*   **Phân tích:** FPT đã lắp đặt và vận hành thiết bị trên hạ tầng của Viettel mà không có sự cho phép của chủ sở hữu (Viettel) và có thể thiếu giấy phép kinh doanh dịch vụ viễn thông (Điều 33, Khoản 2).
*   **Kết luận:** FPT có nghĩa vụ tháo dỡ thiết bị nếu hành vi này bị xác định là "chưa được phép" theo quy định của Luật.

**3. Về căn cứ pháp lý bồi thường**
Trạng thái pháp lý: **B — Khoảng trống quy định**.
*   **Căn cứ:** [Luật Viễn thông 2023] Điều 9, Khoản 3 cấm "gây hại đến hoạt động hợp pháp của cơ sở hạ tầng viễn thông của tổ chức, cá nhân khác".
*   **Phân tích:** Luật quy định hành vi bị cấm và trách nhiệm bảo đảm an toàn (Điều 5), nhưng không quy định cụ thể về mức bồi thường hay cơ chế khởi kiện dân sự giữa các doanh nghiệp.
*   **Suy luận bù khoảng trống:**
    *   **Nguyên tắc:** Vi phạm quy định về an toàn hạ tầng (Điều 5, Khoản 3) gây thiệt hại sẽ phát sinh trách nhiệm bồi thường theo nguyên tắc dân sự (khôi phục, bồi thường thiệt hại).
    *   **Phân công:** Viettel (bên bị thiệt hại) có quyền yêu cầu khắc phục hậu quả.
    *   **Mức độ chắc chắn:** Đây là khoảng trống thực sự — cần quy định chi tiết của pháp luật dân sự hoặc nghị định hướng dẫn cụ thể về bồi thường thiệt hại trong lĩnh vực viễn thông.

**Tổng hợp:**
*   **VNPT:** Hành vi cho thuê lại không được luật cấm trực tiếp nhưng vi phạm nguyên tắc sở hữu hạ tầng (Điều 5) và có thể vi phạm điều kiện cung cấp dịch vụ (Điều 9, Khoản 4).
*   **FPT:** Phải tháo dỡ nếu không có phép (Điều 9, Khoản 4).
*   **Bồi thường:** Căn cứ vào hành vi gây hại (Điều 9, Khoản 3), nhưng cơ chế cụ thể không có trong văn bản.

## Câu 2

**Question:**

Một tổ chức phi lợi nhuận thiết lập mạng kết nối 12 văn phòng tại 4 tỉnh khác nhau, dùng đường truyền thuê từ VNPT, phục vụ liên lạc nội bộ hoàn toàn không thu phí. Tổ chức này không xin bất kỳ giấy phép nào. Cơ quan quản lý cho rằng đây là mạng viễn thông dùng riêng phải có phép. Tổ chức phản bác rằng họ chỉ thuê đường truyền nên được miễn. Xác định ai đúng, tại sao, và nếu phải xin phép thì điều kiện cụ thể là gì.

- Elapsed: 103.5s
- Low confidence: False

**Answer:**
**Kết luận:** Tổ chức phản bác đúng. Mạng này thuộc trường hợp miễn giấy phép.

**Căn cứ miễn giấy phép:**
[Luật Viễn thông 2023] Điều 42, khoản 4 quy định: "Mạng viễn thông dùng riêng mà các thành viên mạng trực thuộc cùng một tổ chức và không tự thiết lập đường truyền dẫn viễn thông."
*   **Phù hợp:** 12 văn phòng thuộc cùng một tổ chức ("trực thuộc cùng một tổ chức") và dùng đường truyền thuê từ VNPT ("không tự thiết lập đường truyền dẫn viễn thông").

**Căn cứ xác định là mạng viễn thông dùng riêng:**
[Luật Viễn thông 2023] Điều 3, khoản 16 định nghĩa: "Mạng viễn thông dùng riêng là mạng viễn thông do tổ chức hoạt động tại Việt Nam thiết lập để cung cấp dịch vụ viễn thông, dịch vụ ứng dụng viễn thông cho các thành viên của mạng không nhằm mục đích sinh lợi trực tiếp từ hoạt động của mạng."
*   **Phù hợp:** Tổ chức phi lợi nhuận, phục vụ nội bộ, không thu phí.

**Điều kiện cấp giấy phép (nếu không thuộc diện miễn):**
[Luật Viễn thông 2023] Điều 38, khoản 2 quy định giấy phép được cấp khi có đủ các điều kiện:
a) Cam kết thiết lập mạng viễn thông dùng riêng chỉ để cung cấp dịch vụ cho các thành viên của mạng, không vì mục đích sinh lợi;
b) Có phương án kỹ thuật, nghiệp vụ phù hợp với quy hoạch hạ tầng thông tin và truyền thông, các quy định của Luật này về tài nguyên viễn thông, kết nối, tiêu chuẩn, quy chuẩn kỹ thuật viễn thông;
c) Có biện pháp bảo đảm an toàn cơ sở hạ tầng viễn thông, an toàn thông tin mạng và an ninh mạng.

**Mức độ chắc chắn:** RÕ (Quy định miễn giấy phép trực tiếp tại [Luật Viễn thông 2023] Điều 42, khoản 4).

## Câu 3

**Question:**

Một khách hàng đăng ký SIM chính chủ với CCCD hợp lệ. Sau 2 năm, khách hàng này bị Tòa án tuyên bố mất năng lực hành vi dân sự. Người giám hộ muốn tiếp tục dùng SIM đó nhưng doanh nghiệp viễn thông từ chối vì thông tin hợp đồng không khớp với người giám hộ. Khách hàng còn một số dư tài khoản lớn. Xác định: doanh nghiệp xử lý SIM này thế nào là đúng luật; ai có quyền sử dụng số dư; và nếu doanh nghiệp tự ý khóa SIM thì có vi phạm không.

- Elapsed: 90.1s
- Low confidence: True

**Answer:**
**1. Xử lý SIM và Khóa SIM**
*   **Quy định:** Doanh nghiệp viễn thông có nghĩa vụ cung cấp dịch vụ cho người sử dụng có thông tin thuê bao đầy đủ, trùng khớp với thông tin trên giấy tờ tùy thân đã xuất trình khi giao kết hợp đồng theo quy định của pháp luật [LuatVienThong2023] Điều 13, khoản 2, điểm i.
*   **Quyền khóa:** Doanh nghiệp viễn thông có nghĩa vụ ngừng cung cấp dịch vụ viễn thông đối với thuê bao viễn thông vi phạm pháp luật về viễn thông [LuatVienThong2023] Điều 13, khoản 2, điểm m.
*   **Thực hiện:** Khi khách hàng bị mất năng lực hành vi dân sự, thông tin hợp đồng không khớp với người giám hộ. Doanh nghiệp không được cung cấp dịch vụ cho người giám hộ thay thế trực tiếp mà không cập nhật hợp đồng. Việc tự ý khóa SIM không phải là vi phạm nếu không thuộc trường hợp vi phạm pháp luật, nhưng doanh nghiệp phải tuân thủ quy định về xác thực thông tin thuê bao.

**2. Quyền sử dụng số dư**
*   **Quy định:** Người sử dụng dịch vụ viễn thông là tổ chức, cá nhân giao kết hợp đồng cung cấp và sử dụng dịch vụ viễn thông với doanh nghiệp viễn thông hoặc đại lý dịch vụ viễn thông [LuatVienThong2023] Điều 3, khoản 31.
*   **Khoảng trống:** Luật Viễn thông không quy định cụ thể về quyền sở hữu số dư tài khoản khi người sử dụng mất năng lực hành vi dân sự.

**3. Phân tích khoảng trống (Trạng thái B)**
*   **Bước 1 — Nguyên tắc gần nhất:** Áp dụng nguyên tắc đại diện pháp lý. Người giám hộ đại diện cho người mất năng lực hành vi dân sự trong các giao dịch dân sự, bao gồm cả nghĩa vụ hợp đồng viễn thông.
*   **Bước 2 — Phân công trách nhiệm:**
    *   Doanh nghiệp viễn thông: Có trách nhiệm xác thực thông tin thuê bao đầy đủ, trùng khớp với giấy tờ tùy thân [LuatVienThong2023] Điều 13, khoản 2, điểm i; không được tiết lộ thông tin riêng [LuatVienThong2023] Điều 6, khoản 4.
    *   Người giám hộ: Có trách nhiệm quản lý tài sản (số dư) của người bị giám hộ và thực hiện thủ tục cập nhật hợp đồng với doanh nghiệp viễn thông.
*   **Bước 3 — Mức độ chắc chắn:** Đây là suy luận từ nguyên tắc đại diện pháp lý — luật chưa quy định tường minh.

**Kết luận:**
*   Doanh nghiệp xử lý đúng luật khi yêu cầu cập nhật thông tin hợp đồng cho phù hợp với người giám hộ trước khi cung cấp dịch vụ.
*   Số dư thuộc quyền quản lý của người giám hộ theo nguyên tắc đại diện.
*   Doanh nghiệp tự ý khóa SIM không vi phạm nếu không có căn cứ vi phạm pháp luật, nhưng có thể vi phạm nghĩa vụ cung cấp dịch vụ nếu không có cơ chế cập nhật hợp đồng hợp pháp.

## Câu 4

**Question:**

Sau đấu giá tần số, doanh nghiệp X được cấp giấy phép kinh doanh viễn thông có hạ tầng mạng. Sau 18 tháng, X mới triển khai được 30% cam kết vì lý do đất đai tại các tỉnh miền núi chưa được bàn giao. X gửi công văn giải trình và được UBND tỉnh xác nhận nguyên nhân khách quan. Bộ TT&TT vẫn ra quyết định thu hồi giấy phép vì vi phạm thời hạn 2 năm. Xác định quyết định thu hồi có đúng không; trường hợp bất khả kháng được hiểu thế nào trong tình huống này; và X có thể khiếu nại theo cơ chế nào.

- Elapsed: 55.5s
- Low confidence: True

**Answer:**
**1. Về tính đúng đắn của quyết định thu hồi**
Quyết định thu hồi **có thể sai** nếu nguyên nhân "đất đai chưa được bàn giao" được xác định là **trường hợp bất khả kháng**.
*   Căn cứ: [Luật Viễn thông 2023] Điều 40, khoản 1, điểm d: "Không triển khai đầy đủ trên thực tế cam kết triển khai mạng viễn thông... sau thời hạn 02 năm... **trừ trường hợp bất khả kháng**".
*   Phân tích: Bộ TT&TT ra quyết định thu hồi mặc dù X đã có xác nhận của UBND tỉnh về nguyên nhân khách quan. Việc xác định có phải là "bất khả kháng" hay không là yếu tố quyết định tính hợp pháp của quyết định thu hồi.

**2. Về khái niệm "bất khả kháng"**
*   Trích dẫn: Văn bản không định nghĩa cụ thể "bất khả kháng".
*   Khoảng trống: Luật quy định [trừ trường hợp bất khả kháng] tại [Điều 40, khoản 1, điểm d]. Tuy nhiên KHÔNG nêu định nghĩa hoặc tiêu chí cụ thể để xác định "bất khả kháng" trong tình huống chậm triển khai do đất đai.
*   Suy luận bù khoảng trống:
    *   **Bước 1 — Nguyên tắc:** Áp dụng nguyên tắc pháp luật hành chính về sự kiện bất khả kháng (sự kiện bất ngờ, không thể lường trước, không thể khắc phục được). Việc chậm bàn giao đất do nguyên nhân khách quan (như quy hoạch, giải phóng mặt bằng chậm) có thể được xem xét tùy thuộc vào tính chất "không thể khắc phục" của doanh nghiệp.
    *   **Bước 2 — Phân công:** Nhà nước (UBND tỉnh xác nhận) có trách nhiệm xác minh tính khách quan của nguyên nhân. Doanh nghiệp có trách nhiệm chứng minh nỗ lực triển khai.
    *   **Bước 3 — Mức độ chắc chắn:** Đây là suy luận từ nguyên tắc — luật chưa quy định tường minh.
*   Kết luận: Nếu "đất đai chưa bàn giao" thuộc sự kiện bất khả kháng theo nguyên tắc chung, quyết định thu hồi là **vi phạm**. Nếu thuộc lỗi doanh nghiệp hoặc rủi ro thương mại thông thường, quyết định là **đúng**.

**3. Cơ chế khiếu nại**
*   Căn cứ: [Luật Viễn thông 2023] Điều 68, khoản 8: "Giải quyết tranh chấp, khiếu nại, tố cáo, xử lý vi phạm pháp luật về viễn thông."
*   Hành động: X có quyền khiếu nại theo quy định chung về khiếu nại hành chính (liên quan đến quyết định thu hồi giấy phép) và giải quyết tranh chấp theo quy định tại Điều 68.

## Câu 5

**Question:**

Một công ty fintech cung cấp dịch vụ gọi điện qua app (OTT voice) cho 5 triệu người dùng tại Việt Nam, không dùng số thuê bao viễn thông, không có giấy phép viễn thông, chỉ đăng ký doanh nghiệp thông thường. Bộ TT&TT yêu cầu công ty phải xin giấy phép viễn thông hoặc ngừng dịch vụ. Công ty cho rằng họ chỉ cung cấp dịch vụ ứng dụng trên Internet, không phải dịch vụ viễn thông. Xác định dịch vụ này thuộc loại nào theo luật; công ty cần làm thủ tục gì; và nếu tiếp tục không xin phép thì bị xử lý ra sao.

- Elapsed: 120.4s
- Low confidence: True

**Answer:**
### 1. Phân loại dịch vụ
*   **Hành vi:** Cung cấp dịch vụ gọi điện qua app (gửi, truyền, nhận thông tin giữa người dùng qua mạng).
*   **Căn cứ:** [1] Luật Viễn thông 2023 Điều 3, Khoản 7, Điểm a: "Dịch vụ viễn thông cơ bản là dịch vụ gửi, truyền, nhận thông tin giữa hai người hoặc một nhóm người sử dụng dịch vụ viễn thông, giữa các thiết bị đầu cuối qua mạng viễn thông".
*   **Kết luận:** Thuộc **"Dịch vụ viễn thông"** (cụ thể là dịch vụ viễn thông cơ bản hoặc giá trị gia tăng).
*   **Phản bác:** Công ty cho là "dịch vụ ứng dụng". Tuy nhiên, [3] Luật Viễn thông 2023 Điều 3, Khoản 12 định nghĩa "Dịch vụ ứng dụng viễn thông" là "dịch vụ sử dụng mạng viễn thông để cung cấp dịch vụ ứng dụng trong lĩnh vực công nghệ thông tin...". Gọi điện thoại là truyền tải thông tin (khoản 7a), phù hợp hơn với định nghĩa dịch vụ viễn thông cơ bản/gia tăng.

### 2. Thủ tục pháp lý
*   **Yêu cầu:** Doanh nghiệp phải có giấy phép kinh doanh dịch vụ viễn thông hoặc thực hiện đăng ký, thông báo cung cấp dịch vụ viễn thông.
*   **Căn cứ:** [2] Luật Viễn thông 2023 Điều 20, Khoản 1: "Doanh nghiệp cung cấp dịch vụ viễn thông phải có giấy phép kinh doanh dịch vụ viễn thông hoặc thực hiện đăng ký, thông báo cung cấp dịch vụ viễn thông, trừ trường hợp quy định tại Điều 42 của Luật này."
*   **Thực hiện:** Công ty phải xin giấy phép hoặc đăng ký, thông báo theo quy định tại Điều 20.

### 3. Xử phạt vi phạm
*   **Hành vi:** Cung cấp dịch vụ viễn thông khi chưa được phép thực hiện theo quy định của Luật này.
*   **Căn cứ:** [7] Luật Viễn thông 2023 Điều 9, Khoản 4: "Thiết lập cơ sở hạ tầng viễn thông, cung cấp dịch vụ viễn thông khi chưa được phép thực hiện theo quy định của Luật này."
*   **Chế tài:** Văn bản không quy định cụ thể mức phạt tiền trong các đoạn trích cung cấp.
*   **Phân tích khoảng trống (Trạng thái B):**
    *   **Luật quy định:** Cấm hành vi cung cấp dịch vụ chưa được phép tại Điều 9, Khoản 4.
    *   **Khoảng trống:** KHÔNG nêu cụ thể mức phạt tiền hoặc biện pháp xử lý hành chính chi tiết trong văn bản.
    *   **Suy luận:**
        *   **Nguyên tắc:** Hành vi bị nghiêm cấm theo Điều 9 sẽ bị xử lý theo quy định của pháp luật về xử lý vi phạm hành chính hoặc hình sự tùy mức độ.
        *   **Phân công:** Nhà nước (Bộ TT&TT) có thẩm quyền yêu cầu khắc phục; Doanh nghiệp có nghĩa vụ tuân thủ và chấm dứt hành vi.
        *   **Mức độ chắc chắn:** Đây là suy luận từ nguyên tắc pháp luật hành chính — luật chuyên ngành chưa quy định tường minh mức phạt cụ thể trong văn bản.

## Câu 6

**Question:**

Hai mạng viễn thông dùng riêng thuộc hai tập đoàn nhà nước khác nhau muốn kết nối trực tiếp với nhau để tiết kiệm chi phí, không thông qua mạng công cộng nào. Cả hai đều cho rằng vì cùng là doanh nghiệp nhà nước thì được phép. Xác định việc kết nối này có hợp pháp không; điều kiện để được phép là gì; và nếu kết nối chui bị phát hiện thì hệ quả pháp lý với cả hai bên là gì.

- Elapsed: 78.1s
- Low confidence: False

**Answer:**
**1. Tính hợp pháp của việc kết nối**
Việc kết nối trực tiếp giữa hai mạng viễn thông dùng riêng là **không hợp pháp**, trừ khi có sự đồng ý bằng văn bản của Bộ Thông tin và Truyền thông.
*   **Căn cứ:** [1] LuatVienThong2023 | Điều 46. Kết nối mạng viễn thông dùng riêng — Khoản 3: "Các mạng viễn thông dùng riêng không được kết nối trực tiếp với nhau, trừ trường hợp có sự đồng ý bằng văn bản của Bộ Thông tin và Truyền thông."

**2. Điều kiện để được phép**
Để được phép kết nối trực tiếp, hai bên phải có **sự đồng ý bằng văn bản của Bộ Thông tin và Truyền thông**.
*   **Căn cứ:** [1] LuatVienThong2023 | Điều 46. Kết nối mạng viễn thông dùng riêng — Khoản 3: "trừ trường hợp có sự đồng ý bằng văn bản của Bộ Thông tin và Truyền thông."

**3. Về tư cách doanh nghiệp nhà nước**
Tư cách doanh nghiệp nhà nước **không tạo ra quyền miễn trừ** đối với quy định cấm kết nối trực tiếp. Quy định áp dụng cho "tổ chức hoạt động tại Việt Nam".
*   **Căn cứ:** [4] LuatVienThong2023 | Điều 3. Giải thích từ ngữ — Khoản 16: "Mạng viễn thông dùng riêng là mạng viễn thông do tổ chức hoạt động tại Việt Nam thiết lập để cung cấp dịch vụ viễn thông, dịch vụ ứng dụng viễn thông cho các thành viên của mạng không nhằm mục đích sinh lợi trực tiếp từ hoạt động của mạng."

**4. Hệ quả pháp lý nếu kết nối chui**
Hành vi kết nối trái quy định là vi phạm quy định bắt buộc của Luật Viễn thông. Tuy nhiên, các văn bản được cung cấp **không quy định cụ thể chế tài xử phạt** cho hành vi này.
*   **Phân tích:** [5] LuatVienThong2023 | Điều 9. Các hành vi bị nghiêm cấm trong hoạt động viễn thông quy định các hành vi bị cấm nhưng không liệt kê cụ thể hành vi kết nối mạng trái phép.
*   **Kết luận:** Hành vi vi phạm quy định tại Điều 46. Kết quả pháp lý cụ thể (phạt tiền, đình chỉ hoạt động...) phụ thuộc vào quy định xử phạt vi phạm hành chính trong lĩnh vực viễn thông (không nằm trong các văn bản được cung cấp).

## Câu 7

**Question:**

Một cá nhân sở hữu tên miền "vietcombank.vn" đã đăng ký từ 5 năm trước khi Vietcombank chưa đăng ký tên miền này. Vietcombank khởi kiện tranh chấp tên miền, lập luận rằng tên miền trùng với nhãn hiệu đã được bảo hộ của họ. Cá nhân phản bác rằng mình đăng ký trước và không có dụng ý xấu vì chỉ dùng làm trang blog cá nhân. Xác định ba yếu tố pháp lý cần chứng minh để Vietcombank thắng kiện; yếu tố nào khó chứng minh nhất trong tình huống này; và cơ quan nào có thẩm quyền giải quyết.

- Elapsed: 101.2s
- Low confidence: True

**Answer:**
**1. Ba yếu tố pháp lý cần chứng minh**
Theo [Luật Viễn thông 2023] Điều 52, Khoản 2, nguyên đơn phải chứng minh các yếu tố sau:
a) "Tên miền trùng hoặc tương tự gây nhầm lẫn với tên, nhãn hiệu, chỉ dẫn địa lý, tên thương mại mà bên nguyên đơn có quyền, lợi ích hợp pháp";
b) "Quyền, lợi ích hợp pháp liên quan đến tên miền của các bên tranh chấp";
c) "Bị đơn đã sử dụng tên miền với dụng ý xấu, lợi dụng uy tín, danh tiếng của nhãn hiệu, tên thương mại, chỉ dẫn địa lý mà bên nguyên đơn có quyền, lợi ích hợp pháp nhằm thu lợi bất chính".

**2. Yếu tố khó chứng minh nhất**
Luật không quy định thứ tự độ khó của các yếu tố. Tuy nhiên, căn cứ Khoản 2, điểm c, yếu tố "dụng ý xấu" là khó chứng minh nhất trong tình huống này. Lý do:
*   Yếu tố "trùng hoặc tương tự" (điểm a) là khách quan, dễ xác định so với nhãn hiệu Vietcombank.
*   Yếu tố "dụng ý xấu" (điểm c) là chủ quan, phụ thuộc vào nhận định về tâm trạng bị đơn (cá nhân). Trong tình huống, bị đơn lập luận "chỉ dùng làm trang blog cá nhân" để bác bỏ dụng ý xấu, đòi hỏi nguyên đơn phải cung cấp chứng cứ chứng minh mục đích lợi dụng uy tín (Khoản 3).
*   Đây là suy luận từ bản chất của "dụng ý xấu" — luật chưa quy định tiêu chí định lượng cụ thể để phân biệt "dụng ý xấu" và "sử dụng hợp pháp".

**3. Cơ quan có thẩm quyền giải quyết**
Thẩm quyền giải quyết bao gồm hòa giải, trọng tài, tòa án theo quy định của pháp luật. [Luật Viễn thông 2023] Điều 52, Khoản 1.

## Câu 8

**Question:**

Nhà nước cần thu hồi một dải số thuê bao di động H2H để tái phân bổ phục vụ quốc phòng. Dải số này hiện đang được một doanh nghiệp sử dụng thông qua đấu giá cách đây 3 năm với giá 20 tỷ đồng. Doanh nghiệp yêu cầu bồi thường 30 tỷ (20 tỷ gốc + 10 tỷ lợi nhuận kỳ vọng). Xác định: Nhà nước có quyền thu hồi không và theo điều kiện nào; mức bồi thường tối đa theo luật là bao nhiêu; và yêu cầu 10 tỷ lợi nhuận kỳ vọng có được chấp nhận không.

- Elapsed: 35.2s
- Low confidence: True

**Answer:**
**1. Quyền thu hồi**
Nhà nước có quyền thu hồi. Căn cứ:
[Tổng hợp luật: Luật Viễn thông 2023 Điều 53, Khoản 2, Điểm a quy định thu hồi để sử dụng mã, số viễn thông, tài nguyên Internet Việt Nam phục vụ lợi ích công cộng, quốc phòng, an ninh.]

**2. Mức bồi thường tối đa**
Mức bồi thường tối đa là 20 tỷ đồng (số tiền trúng đấu giá). Căn cứ:
[Luật Viễn thông 2023 Điều 53, Khoản 4, Điểm b quy định: Đối với mã, số viễn thông, tài nguyên Internet được phân bổ, cấp theo phương thức đấu giá quyền sử dụng, mức bồi thường được xác định bằng số tiền trúng đấu giá.]

**3. Yêu cầu 10 tỷ lợi nhuận kỳ vọng**
Không được chấp nhận. Căn cứ:
[Luật Viễn thông 2023 Điều 53, Khoản 4, Điểm b chỉ quy định mức bồi thường bằng "số tiền trúng đấu giá", không quy định khoản bồi thêm cho lợi nhuận kỳ vọng.]

## Câu 9

**Question:**

Doanh nghiệp viễn thông A phát hiện thuê bao B đang dùng thiết bị phát sóng giả mạo BTS (IMSI catcher) để nghe lén cuộc gọi của người khác. A lập tức khóa SIM của B và báo cáo cơ quan công an. B kiện A vì khóa SIM không có lý do và yêu cầu bồi thường. Xác định: A có quyền tự ý khóa SIM mà không cần lệnh cơ quan nhà nước không; hành vi của B vi phạm những quy định nào cụ thể trong luật; và trách nhiệm của A với người bị nghe lén nếu không phát hiện sớm hơn.

- Elapsed: 109.2s
- Low confidence: True

**Answer:**
**1. Về quyền tự ý khóa SIM của Doanh nghiệp A**
Trạng thái: **B — Luật có quy định + có khoảng trống**.
Luật Viễn thông 2023 quy định trách nhiệm bảo đảm an toàn thông tin tại [Luật Viễn thông 2023] Điều 5, khoản 2 nhưng KHÔNG quy định cụ thể về quyền tự chủ của doanh nghiệp viễn thông trong việc khóa thuê bao khi phát hiện hành vi vi phạm an ninh mà không cần lệnh cơ quan nhà nước.
<suy_luận_bù_khoảng_trống>
BƯỚC 1 — XÁC ĐỊNH NGUYÊN TẮC GẦN NHẤT: Áp dụng nguyên tắc bảo đảm an toàn thông tin mạng và an ninh quốc gia. Hành vi sử dụng thiết bị IMSI catcher thuộc hành vi bị nghiêm cấm tại [Luật Viễn thông 2023] Điều 9, khoản 2 (nghe trộm) và khoản 1 (xâm phạm an ninh quốc gia). Để thực hiện trách nhiệm bảo vệ mạng viễn thông tại [Luật Viễn thông 2023] Điều 5, khoản 2, doanh nghiệp có quyền áp dụng biện pháp kỹ thuật ngăn chặn rủi ro.
BƯỚC 2 — PHÂN CÔNG TRÁCH NHIỆM: Doanh nghiệp viễn thông có trách nhiệm phát hiện và xử lý sự cố an ninh mạng trên mạng của mình. Cơ quan nhà nước có thẩm quyền (Công an) có trách nhiệm điều tra, truy tố.
BƯỚC 3 — MỨC ĐỘ CHẮC CHẮN: Đây là suy luận từ nguyên tắc bảo đảm an toàn thông tin — luật chưa quy định tường minh về thủ tục cấp phép cho hành vi khóa SIM.
</suy_luận_bù_khoảng_trống>

**2. Về hành vi vi phạm của Thuê bao B**
Trạng thái: **A — Luật RÕ + ĐỦ**.
Hành vi của B vi phạm các quy định sau:
- [Luật Viễn thông 2023] Điều 9, khoản 2: "Thu trộm, nghe trộm, xem trộm thông tin trên mạng viễn thông".
- [Luật Viễn thông 2023] Điều 9, khoản 1: "Lợi dụng hoạt động viễn thông nhằm... xâm phạm an ninh quốc gia".
- [Luật Viễn thông 2023] Điều 15, khoản 4, điểm e: "Bảo vệ mật khẩu, khóa mật mã và thiết bị đầu cuối của mình".

**3. Về trách nhiệm của Doanh nghiệp A với người bị nghe lén**
Trạng thái: **B — Luật có quy định + có khoảng trống**.
Luật Viễn thông 2023 quy định trách nhiệm bồi thường của doanh nghiệp tại [Luật Viễn thông 2023] Điều 15, khoản 1, điểm e: "được hoàn trả tiền sử dụng dịch vụ và bồi thường thiệt hại trực tiếp khác do lỗi của doanh nghiệp viễn thông... gây ra". Tuy nhiên, luật KHÔNG quy định cụ thể về mức độ giám sát hay thời hạn phát hiện sự cố để xác định "lỗi" của doanh nghiệp.
<suy_luận_bù_khoảng_trống>
BƯỚC 1 — XÁC ĐỊNH NGUYÊN TẮC GẦN NHẤT: Nguyên tắc trách nhiệm bảo đảm an toàn cơ sở hạ tầng viễn thông. Doanh nghiệp có nghĩa vụ bảo vệ mạng viễn thông tại [Luật Viễn thông 2023] Điều 5, khoản 2.
BƯỚC 2 — PHÂN CÔNG TRÁCH NHIỆM: Doanh nghiệp có trách nhiệm ứng cứu sự cố an ninh mạng. Người bị hại có quyền yêu cầu bồi thường nếu chứng minh được lỗi của doanh nghiệp (ví dụ: chậm trễ phát hiện do thiếu biện pháp kỹ thuật).
BƯỚC 3 — MỨC ĐỘ CHẮC CHẮN: Đây là suy luận từ nguyên tắc trách nhiệm bảo đảm an toàn — luật chưa quy định tường minh về tiêu chí xác định lỗi trong việc phát hiện sớm hành vi vi phạm của thuê bao.
</suy_luận_bù_khoảng_trống>

## Câu 10

**Question:**

Một tập đoàn nước ngoài mua lại 100% cổ phần của một doanh nghiệp viễn thông Việt Nam không có hạ tầng mạng, đang cung cấp dịch vụ bán lại. Sau thâu tóm, tập đoàn nước ngoài muốn chuyển doanh nghiệp này thành doanh nghiệp có hạ tầng mạng bằng cách tự đầu tư xây dựng. Bộ TT&TT yêu cầu doanh nghiệp xin cấp phép mới. Doanh nghiệp cho rằng giấy phép cũ vẫn còn hiệu lực. Xác định: việc thay đổi 100% sở hữu nước ngoài có ảnh hưởng đến tính hợp lệ của giấy phép cũ không; khi chuyển sang có hạ tầng thì giấy phép cũ có tự động mở rộng phạm vi không; và điều kiện nào doanh nghiệp phải đáp ứng thêm.

- Elapsed: 118.7s
- Low confidence: True

**Answer:**
### 1. Về ảnh hưởng của thay đổi sở hữu nước ngoài đến tính hợp lệ giấy phép cũ
**Trạng thái:** B (Luật có quy định về chủ thể nhưng có khoảng trống về cơ chế chuyển nhượng).

**Phân tích:**
*   **Quy định hiện hành:** Luật Viễn thông 2023 không quy định cụ thể về việc thay đổi tỷ lệ sở hữu (bao gồm 100% nước ngoài) có làm mất hiệu lực giấy phép hay không.
*   **Khoảng trống:** Luật không nêu cơ chế xử lý khi chủ sở hữu thay đổi dẫn đến thay đổi bản chất pháp lý của doanh nghiệp (ví dụ: từ doanh nghiệp trong nước sang có vốn đầu tư nước ngoài 100%).
*   **Suy luận bù khoảng trống:**
    *   **Bước 1 — Nguyên tắc gần nhất:** Theo nguyên tắc quản lý thống nhất, khi hai Bộ (Thông tin và Truyền thông, Kế hoạch và Đầu tư) xung đột về thẩm quyền cấp phép sau chuyển nhượng, Thủ tướng Chính phủ là cơ quan phân giải. Tuy nhiên, Luật Viễn thông 2023 không quy định tường minh cơ chế này.
    *   **Bước 2 — Phân công trách nhiệm:**
        *   **Nhà nước:** Bộ TT&TT có thẩm quyền yêu cầu doanh nghiệp làm rõ nguồn gốc vốn và tuân thủ pháp luật đầu tư nước ngoài.
        *   **Doanh nghiệp:** Phải chứng minh năng lực pháp lý và tuân thủ điều kiện cấp phép mới nếu thay đổi mô hình kinh doanh.
    *   **Bước 3 — Mức độ chắc chắn:** Đây là suy luận từ nguyên tắc quản lý nhà nước — luật chưa quy định tường minh về tác động của chuyển nhượng cổ phần lên hiệu lực giấy phép.

**Căn cứ:**
*   [LuatVienThong2023] Điều 3, Khoản 29: "Doanh nghiệp viễn thông là doanh nghiệp được thành lập theo pháp luật Việt Nam và được phép kinh doanh dịch vụ viễn thông theo quy định của Luật này."
*   [LuatVienThong2023] Điều 73, Khoản 2: "Doanh nghiệp được tiếp tục thực hiện kinh doanh dịch vụ viễn thông theo thời hạn của giấy phép kinh doanh dịch vụ viễn thông..." (Chỉ áp dụng cho trường hợp tiếp tục hoạt động, không nêu rõ khi thay đổi bản chất doanh nghiệp).

### 2. Về việc mở rộng phạm vi giấy phép khi chuyển sang có hạ tầng
**Trạng thái:** A (Luật quy định rõ ràng).

**Phân tích:**
Giấy phép cũ (không có hạ tầng) và giấy phép mới (có hạ tầng) là hai loại giấy phép khác nhau, không tự động chuyển đổi.

**Căn cứ:**
*   [LuatVienThong2023] Điều 33, Khoản 2: "Giấy phép kinh doanh dịch vụ viễn thông bao gồm: a) Giấy phép cung cấp dịch vụ viễn thông có hạ tầng mạng có thời hạn không quá 15 năm được cấp cho doanh nghiệp cung cấp dịch vụ có hạ tầng mạng; b) Giấy phép cung cấp dịch vụ viễn thông không có hạ tầng mạng có thời hạn không quá 10 năm được cấp cho doanh nghiệp cung cấp dịch vụ không có hạ tầng mạng."
*   **Kết luận:** Việc chuyển từ "không có hạ tầng mạng" sang "có hạ tầng mạng" là thay đổi loại hình dịch vụ. Giấy phép cũ (loại b) **không tự động mở rộng** sang loại a. Doanh nghiệp phải xin cấp giấy phép mới tương ứng với loại hình có hạ tầng mạng.

### 3. Về điều kiện doanh nghiệp phải đáp ứng thêm
**Trạng thái:** A (Luật quy định rõ ràng).

**Phân tích:**
Khi xin cấp giấy phép cho doanh nghiệp có hạ tầng mạng, doanh nghiệp phải đáp ứng các điều kiện riêng biệt tại Điều 36, Khoản 2, khác với Điều kiện tại Khoản 1 (cho doanh nghiệp không có hạ tầng).

**Căn cứ:**
*   [LuatVienThong2023] Điều 36, Khoản 2: "Giấy phép viễn thông quy định tại điểm a khoản 2 Điều 35 của Luật này được cấp cho doanh nghiệp khi có đủ các điều kiện sau đây: a) Các điều kiện quy định tại các điểm a, b, c và d khoản 1 Điều này; b) Điều kiện về triển khai mạng viễn thông theo quy định của Chính phủ."
*   **Điều kiện bổ sung:** Doanh nghiệp phải đáp ứng thêm "Điều kiện về triển khai mạng viễn thông theo quy định của Chính phủ" (điểm b Khoản 2 Điều 36).

**Tổng hợp luật:**
[Tổng hợp luật: [LuatVienThong2023] Điều 33, Khoản 2 quy định phân biệt giấy phép có hạ tầng và không có hạ tầng; [LuatVienThong2023] Điều 36, Khoản 2 quy định điều kiện cấp phép cho doanh nghiệp có hạ tầng — kết hợp xác định: Doanh nghiệp phải xin cấp giấy phép mới loại có hạ tầng và đáp ứng điều kiện triển khai mạng.]

