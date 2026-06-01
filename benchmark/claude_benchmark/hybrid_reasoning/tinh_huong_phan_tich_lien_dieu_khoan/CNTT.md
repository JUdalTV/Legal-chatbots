# LUẬT CÔNG NGHỆ THÔNG TIN (VĂN BẢN HỢP NHẤT 65/VBHN-VPQH)

## Câu 1 — Phân tầng trách nhiệm trong truyền đưa thông tin số

Điều 16 quy định tổ chức truyền đưa thông tin số của người khác KHÔNG phải chịu trách nhiệm về nội dung, trừ 3 trường hợp. Hãy phân tích: nếu nhà mạng A tự động định tuyến lại luồng dữ liệu của B sang C vì lý do kỹ thuật (mà không thay đổi nội dung), điều này có rơi vào ngoại lệ "lựa chọn người nhận" hay không? Phân tích từng yếu tố cấu thành của 3 ngoại lệ tại khoản 4.

### Trả lời

**1. Căn cứ pháp lý về ngoại lệ trách nhiệm**

[Luật Công nghệ thông tin (văn bản hợp nhất 2025)] Điều 16, Khoản 4:
> "Tổ chức, cá nhân truyền đưa thông tin số của tổ chức, cá nhân khác không phải chịu trách nhiệm về nội dung thông tin đó, trừ trường hợp thực hiện một trong các hành vi sau đây:
> a) Chính mình bắt đầu việc truyền đưa thông tin;
> b) Lựa chọn người nhận thông tin được truyền đưa;
> c) Lựa chọn và sửa đổi nội dung thông tin được truyền đưa."

**2. Phân tích hành vi định tuyến lại luồng dữ liệu**

Hành vi "định tuyến lại luồng dữ liệu của B sang C vì lý do kỹ thuật" cần đối chiếu với 3 ngoại lệ tại Khoản 4 Điều 16:

- **Ngoại lệ a) Chính mình bắt đầu việc truyền đưa thông tin:** Hành động định tuyến là tiếp nhận và chuyển tiếp, không phải khởi tạo luồng mới từ nguồn. → **KHÔNG thuộc**.
- **Ngoại lệ b) Lựa chọn người nhận thông tin được truyền đưa:** Cần xác định "lựa chọn" là hành vi chủ động xác định đích đến cụ thể dựa trên nội dung hay hành vi định tuyến tự động do cơ sở hạ tầng quy định → *Cần phân tích thêm* (xem mục 3).
- **Ngoại lệ c) Lựa chọn và sửa đổi nội dung thông tin được truyền đưa:** Hành động định tuyến kỹ thuật không thay đổi nội dung. → **KHÔNG thuộc**.

**3. Phân tích khoảng trống pháp lý (Trạng thái B)**

Luật quy định rõ 3 hành vi ngoại lệ. Tuy nhiên KHÔNG nêu định nghĩa cụ thể về "lựa chọn người nhận" trong bối cảnh định tuyến tự động (automatic routing) hay cân bằng tải (load balancing) của hạ tầng viễn thông.

*Suy luận bù khoảng trống:*
- **Nguyên tắc trung lập mạng (Network Neutrality) và tính kỹ thuật của hạ tầng:** Định tuyến là chức năng kỹ thuật của thiết bị mạng để tối ưu hóa đường truyền, không phải là hành vi "lựa chọn người nhận" nhằm mục đích phân phối nội dung.
- **Quan hệ ủy quyền:** Nhà mạng cung cấp dịch vụ kết nối, không phải là người phát tán nội dung.
- Mức độ chắc chắn: Đây là suy luận từ nguyên tắc kỹ thuật — luật chưa quy định tường minh về định nghĩa "lựa chọn người nhận" trong ngữ cảnh định tuyến tự động.

**Kết luận:** Hành động định tuyến lại luồng dữ liệu vì lý do kỹ thuật (không thay đổi nội dung) **KHÔNG RƠI VÀO** ngoại lệ "lựa chọn người nhận" theo tinh thần pháp lý (do thiếu tính chủ đích lựa chọn nội dung/đối tượng), nhưng luật chưa quy định tường minh để loại trừ trường hợp này khỏi Khoản 4 Điều 16. Do đó, nhà mạng vẫn được miễn trách nhiệm về nội dung (theo quy định chung của Khoản 4), nhưng rủi ro pháp lý tồn tại nếu không có văn bản hướng dẫn chi tiết về "hành vi định tuyến hợp pháp".

---

## Câu 2 — Sự bãi bỏ và tác động đến hệ thống pháp lý

Văn bản hợp nhất ghi rõ nhiều điều (ví dụ: Điều 10, khoản 9–12 Điều 4, Mục Chương V về công nghiệp CNTT) đã bị bãi bỏ theo Luật Công nghiệp công nghệ số 71/2025. Hãy phân tích: (a) khoảng trống pháp lý nào xuất hiện nếu Luật CNTS 71/2025 chưa có hiệu lực nhưng Luật CNTT đã bị bãi bỏ các điều đó? (b) nguyên tắc áp dụng Luật CNTT (Điều 3) xử lý xung đột với luật khác như thế nào khi chính luật đó bị sửa đổi?

### Trả lời

**(a) Khoảng trống pháp lý khi điều khoản bị bãi bỏ trước hiệu lực Luật mới**

**Căn cứ có:**
- [Luật Công nghệ thông tin (văn bản hợp nhất 2025)] Điều 4, Khoản 9, 10, 11, 12 ghi rõ: *"được bãi bỏ theo quy định tại khoản 1 Điều 49 của Luật Công nghiệp công nghệ số số 71/2025/QH15, có hiệu lực kể từ ngày 01 tháng 01 năm 2026."*
- [Luật Công nghệ thông tin (văn bản hợp nhất 2025)] Điều 10 ghi rõ: *"được bãi bỏ theo quy định tại điểm b khoản 1 Điều 62 của Luật Thanh tra số 84/2025/QH15, có hiệu lực kể từ ngày 01 tháng 7 năm 2025."*

**Khoảng trống xác định:**
Luật CNTT ghi nhận việc bãi bỏ các điều khoản với thời điểm hiệu lực tương lai (01/01/2026 hoặc 01/07/2025), TUY NHIÊN KHÔNG NÊU:
- Cơ chế chuyển tiếp khi điều khoản đã bị ghi "bãi bỏ" nhưng luật bãi bỏ chưa có hiệu lực
- Thời điểm chính xác khi điều khoản cũ mất hiệu lực pháp lý
- Nghĩa vụ của cơ quan quản lý trong giai đoạn chờ hiệu lực

*Suy luận bù khoảng trống:*
- **Nguyên tắc hiệu lực pháp luật:** Điều khoản bị bãi bỏ vẫn có hiệu lực cho đến khi luật bãi bỏ có hiệu lực thực tế. Văn bản ghi "bãi bỏ" là thông báo dự kiến, không phải hiệu lực ngay.
- **Phân công trách nhiệm:** Nhà nước xác định thời điểm chính xác; Doanh nghiệp tiếp tục tuân thủ điều khoản cũ cho đến khi có văn bản hướng dẫn chính thức từ cơ quan có thẩm quyền.
- Mức độ chắc chắn: Đây là suy luận từ nguyên tắc hiệu lực pháp luật — luật chưa quy định tường minh cơ chế chuyển tiếp cho trường hợp bãi bỏ có thời điểm hiệu lực tương lai.

**(b) Nguyên tắc áp dụng Luật CNTT (Điều 3) khi chính Luật đó bị sửa đổi**

**Căn cứ có:**

[Luật Công nghệ thông tin (văn bản hợp nhất 2025)] Điều 3, Khoản 1:
> "Trường hợp có sự khác nhau giữa quy định của Luật Công nghệ thông tin với quy định của luật khác về cùng một vấn đề liên quan đến hoạt động ứng dụng và phát triển công nghệ thông tin thì áp dụng quy định của Luật Công nghệ thông tin."

[Luật Công nghệ thông tin (văn bản hợp nhất 2025)] Điều 3, Khoản 2:
> "Trường hợp điều ước quốc tế mà Cộng hòa xã hội chủ nghĩa Việt Nam là thành viên có quy định khác với quy định của Luật này thì áp dụng quy định của điều ước quốc tế đó."

**Phân tích xung đột:**

- **Đối với xung đột với luật khác (Khoản 1):** Nguyên tắc: Luật CNTT có ưu tiên áp dụng. *Khoảng trống:* Khi chính Luật CNTT bị sửa đổi/bãi bỏ bởi luật khác (Luật Công nghiệp công nghệ số), nguyên tắc ưu tiên này trở nên vô nghĩa vì hai luật cùng điều chỉnh vấn đề. Không có quy định về thứ tự ưu tiên khi một luật là "luật chuyên ngành" và luật kia là "luật đặc thù".

- **Đối với xung đột với điều ước quốc tế (Khoản 2):** Điều ước quốc tế có ưu tiên. *Khoảng trống:* Không quy định cơ chế xem xét lại điều ước quốc tế khi luật trong nước bị sửa đổi.

*Suy luận bù khoảng trống:*
- **Nguyên tắc pháp chế:** Luật mới thay thế luật cũ. Khi Luật Công nghiệp công nghệ số có hiệu lực, các điều khoản bị bãi bỏ của Luật CNTT sẽ không còn giá trị pháp lý.
- **Nguyên tắc phân cấp quản lý:** Luật Công nghiệp công nghệ số (71/2025/QH15) là luật chuyên ngành mới hơn, có phạm vi điều chỉnh rộng hơn → có thể xem là luật đặc thù áp dụng ưu tiên.

**Kết luận:**
- Về khoảng trống (a): Suy luận từ nguyên tắc hiệu lực pháp luật — luật chưa quy định tường minh cơ chế chuyển tiếp.
- Về nguyên tắc (b): **Khoảng trống thực sự** — cần quy định chi tiết của Chính phủ về cơ chế chuyển tiếp và thứ tự ưu tiên khi luật chuyên ngành bị sửa đổi bởi luật đặc thù.

---

## Câu 3 — Đồng ý và không đồng ý trong thu thập thông tin cá nhân

Điều 21 cho phép thu thập thông tin cá nhân mà không cần đồng ý trong 3 trường hợp (ký kết hợp đồng, tính cước, thực hiện nghĩa vụ pháp luật). Hãy phân tích: nếu doanh nghiệp thương mại điện tử thu thập thông tin cá nhân khi người dùng mua hàng (có hợp đồng), sau đó dùng thông tin đó để chạy quảng cáo cá nhân hóa — điều này có hợp pháp không theo Điều 21? Đối chiếu với yêu cầu "sử dụng đúng mục đích" tại khoản 2(b).

### Trả lời

**Kết luận:** Việc sử dụng thông tin cá nhân thu thập khi mua hàng để chạy quảng cáo cá nhân hóa **KHÔNG hợp pháp** nếu không có sự đồng ý riêng biệt của người dùng, trừ khi quảng cáo đó được coi là một phần của việc "thực hiện hợp đồng".

**Căn cứ pháp lý:**

**Về tính hợp pháp của việc thu thập ban đầu:**
Việc thu thập thông tin để giao kết và thực hiện hợp đồng mua hàng được phép không cần đồng ý theo [Luật Công nghệ thông tin (văn bản hợp nhất 2025)] Điều 21, Khoản 3, điểm a:
> "Ký kết, sửa đổi hoặc thực hiện hợp đồng sử dụng thông tin, sản phẩm, dịch vụ trên môi trường mạng"

Tuy nhiên, việc chạy **quảng cáo cá nhân hóa** là hoạt động tiếp thị, không nằm trong phạm vi "thực hiện hợp đồng" mua hàng.

**Về nghĩa vụ sử dụng đúng mục đích:**
Theo [Luật Công nghệ thông tin (văn bản hợp nhất 2025)] Điều 21, Khoản 2, điểm b: *"Sử dụng đúng mục đích thông tin cá nhân thu thập được."*

- Mục đích thu thập lúc mua hàng: "giao kết, thực hiện hợp đồng".
- Mục đích quảng cáo: "tiếp thị".
- **Hai mục đích này khác nhau** → việc chuyển đổi mục đích sử dụng vi phạm nguyên tắc sử dụng đúng mục đích.

**Về ngoại lệ không cần đồng ý:**

[Luật Công nghệ thông tin (văn bản hợp nhất 2025)] Điều 21, Khoản 3 chỉ liệt kê 3 trường hợp: (a) Hợp đồng, (b) Tính giá, (c) Nghĩa vụ pháp luật.

Hoạt động **quảng cáo cá nhân hóa không thuộc** bất kỳ trường hợp nào tại Khoản 3. Do đó, quay về Khoản 1: *"Tổ chức, cá nhân thu thập, xử lý và sử dụng thông tin cá nhân của người khác trên môi trường mạng phải được người đó đồng ý."*

**Khoảng trống pháp lý & Suy luận:**
Luật chưa định nghĩa rõ ràng ranh giới giữa "thực hiện hợp đồng" và "tiếp thị dựa trên dữ liệu khách hàng". Áp dụng nguyên tắc **giới hạn mục đích (Purpose Limitation):** Nếu mục đích thu thập ban đầu không bao gồm quảng cáo, việc sử dụng sau đó phải có sự đồng ý mới.

**Khuyến nghị:** Doanh nghiệp phải thu thập thêm sự đồng ý riêng biệt (opt-in) cho mục đích quảng cáo, hoặc thông báo rõ ràng tại thời điểm thu thập (Điều 21, Khoản 2, điểm a) về mục đích này.

---

## Câu 4 — Trách nhiệm của cơ quan nhà nước và ranh giới kiểm soát

Điều 20 quy định tổ chức, cá nhân KHÔNG phải tự giám sát thông tin của người khác, trừ khi cơ quan có thẩm quyền yêu cầu. Tuy nhiên, Điều 18(3b) yêu cầu doanh nghiệp cho thuê chỗ lưu trữ phải "kịp thời ngăn chặn thông tin trái pháp luật theo yêu cầu". Hỏi: liệu có mâu thuẫn giữa nghĩa vụ bị động (chỉ khi được yêu cầu) và nghĩa vụ chủ động (tự phát hiện, Điều 18(3c))? Luật phân biệt hai nghĩa vụ này như thế nào?

### Trả lời

**Kết luận: Không có mâu thuẫn.** Luật phân biệt rõ giữa nghĩa vụ giám sát chủ động (không bắt buộc) và nghĩa vụ hành động khi có tri thức (bắt buộc).

**Căn cứ pháp lý:**

[Luật Công nghệ thông tin (văn bản hợp nhất 2025)] Điều 20, khoản 2: *"Tổ chức, cá nhân tham gia ứng dụng công nghệ thông tin không phải chịu trách nhiệm theo dõi, giám sát thông tin số của tổ chức, cá nhân khác, trừ trường hợp cơ quan nhà nước có thẩm quyền yêu cầu."*

[Luật Công nghệ thông tin (văn bản hợp nhất 2025)] Điều 18, khoản 3: Tổ chức, cá nhân cho thuê chỗ lưu trữ thông tin số có trách nhiệm:
- *"b) Tiến hành kịp thời các biện pháp cần thiết để ngăn chặn việc truy nhập thông tin số hoặc loại bỏ thông tin số trái pháp luật theo yêu cầu của cơ quan nhà nước có thẩm quyền;"*
- *"c) Ngừng cho tổ chức, cá nhân khác thuê chỗ lưu trữ thông tin số trong trường hợp tự mình phát hiện hoặc được cơ quan nhà nước có thẩm quyền thông báo cho biết thông tin đang được lưu trữ là trái pháp luật;"*

**Phân tích sự khác biệt:**

**Về phạm vi hành vi (Giám sát vs. Phát hiện):**
- **Nghĩa vụ bị động (Điều 20):** "Không phải chịu trách nhiệm **theo dõi, giám sát** thông tin số". Đây là quy định chung cho tất cả tổ chức, cá nhân, **cấm chủ động quét, tìm kiếm** nội dung trái pháp luật của người khác.
- **Nghĩa vụ chủ động (Điều 18, khoản 3c):** "Trong trường hợp **tự mình phát hiện** hoặc được cơ quan nhà nước có thẩm quyền thông báo". Hành vi "tự mình phát hiện" không đồng nghĩa với "theo dõi, giám sát". Nó ám chỉ việc **trở nên biết đến** thông tin trái pháp luật thông qua các kênh thụ động (khiếu nại của khách hàng, báo cáo từ bên thứ ba, hoặc phát hiện ngẫu nhiên trong quá trình vận hành).

**Về loại hình biện pháp:**
- **Theo yêu cầu (Điều 18, khoản 3b):** "Ngăn chặn việc truy nhập thông tin số hoặc loại bỏ thông tin số" — đây là **biện pháp kỹ thuật** (xóa, chặn IP) thực hiện khi có lệnh của cơ quan nhà nước.
- **Khi tự phát hiện (Điều 18, khoản 3c):** "Ngừng cho tổ chức, cá nhân khác thuê chỗ lưu trữ thông tin số" — đây là **biện pháp hợp đồng** (hủy dịch vụ) thực hiện khi chủ thể biết rõ nội dung trái pháp luật.

**Nguyên tắc áp dụng:** Nghĩa vụ đặc thù (Điều 18) áp dụng bổ sung cho nghĩa vụ chung (Điều 20). Nhà nước có thẩm quyền yêu cầu xử lý (Điều 20, Điều 18b); Doanh nghiệp có trách nhiệm xử lý khi có tri thức (Điều 18c). Đây là quy định **tường minh** trong Luật Công nghệ thông tin (văn bản hợp nhất 2025).

---

## Câu 5 — Liên kết xuyên luật: CNTT, Viễn thông và An ninh mạng

Điều 13(3) Luật CNTT yêu cầu "tổ chức, cá nhân tiến hành hoạt động viễn thông trên môi trường mạng phải thực hiện các quy định của pháp luật về viễn thông". Sau khi Luật Viễn thông 24/2023 có hiệu lực (và sửa đổi Luật CNTT), nghĩa vụ này có còn hiệu lực không? Nếu một dịch vụ OTT (như Zalo) vừa bị điều chỉnh bởi Luật CNTT, Luật Viễn thông và Luật An ninh mạng, quy tắc nào xác định luật nào áp dụng ưu tiên?

### Trả lời

**1. Hiệu lực của Điều 13(3) Luật Công nghệ thông tin**

[Luật Công nghệ thông tin (văn bản hợp nhất 2025)] Điều 13, Khoản 3 quy định:
> "Tổ chức, cá nhân tiến hành hoạt động viễn thông, hoạt động phát thanh, truyền hình trên môi trường mạng phải thực hiện các quy định của pháp luật về viễn thông, báo chí và các quy định của Luật này."

Mặc dù Điều 76 Luật Công nghệ thông tin cũ đã bị bãi bỏ theo quy định tại khoản 4 Điều 71 của Luật Viễn thông số 24/2023/QH15, **Điều 13 vẫn được giữ lại** trong bản hợp nhất 2025.

→ **Nghĩa vụ tuân thủ pháp luật viễn thông theo Điều 13(3) hiện vẫn có hiệu lực** trong khung pháp lý hiện hành.

**2. Quy tắc ưu tiên áp dụng khi có nhiều luật**

Theo [Luật Công nghệ thông tin (văn bản hợp nhất 2025)] Điều 3(1):
> "Trường hợp có sự khác nhau giữa quy định của Luật Công nghệ thông tin với quy định của luật khác về cùng một vấn đề liên quan đến hoạt động ứng dụng và phát triển công nghệ thông tin thì áp dụng quy định của Luật Công nghệ thông tin."

**3. Phân tích khoảng trống**

Luật quy định nguyên tắc ưu tiên Luật Công nghệ thông tin tại Điều 3(1). Tuy nhiên KHÔNG nêu rõ mối quan hệ ưu tiên giữa Luật Viễn thông 2023 (luật chuyên ngành) và Luật CNTT 2025 (luật chung) đối với hoạt động viễn thông trên môi trường mạng.

*Suy luận bù khoảng trống:*
- **Bước 1:** Nguyên tắc luật đặc biệt áp dụng trước luật chung. Luật Viễn thông 2023 là luật chuyên ngành về viễn thông, Luật CNTT 2025 là luật chung về công nghệ thông tin. → Đối với các vấn đề viễn thông chuyên ngành: Luật Viễn thông ưu tiên.
- **Bước 2:** Đối với các vấn đề an ninh mạng: Luật An ninh mạng ưu tiên (theo nguyên tắc luật đặc biệt về an ninh).
- **Bước 3:** Luật CNTT đóng vai trò bổ sung cho các vấn đề ứng dụng CNTT không được điều chỉnh bởi hai luật kia.
- Mức độ chắc chắn: Đây là suy luận từ nguyên tắc — luật chưa quy định tường minh thứ tự ưu tiên này.

---

## Câu 6 — Yêu cầu trang thông tin điện tử và cấu trúc trách nhiệm

Theo Điều 23, tổ chức sử dụng tên miền ".vn" KHÔNG cần thông báo với Bộ Bưu chính Viễn thông, nhưng tổ chức dùng tên miền khác thì phải thông báo. Hỏi: (a) sau khi Bộ Bưu chính Viễn thông được tái cơ cấu thành Bộ Thông tin và Truyền thông (và nay có thể là tên khác), cơ quan nào tiếp nhận thông báo? (b) Nếu doanh nghiệp nước ngoài không có ".vn" mà cung cấp dịch vụ tại Việt Nam — nghĩa vụ thông báo có áp dụng không?

### Trả lời

**(a) Cơ quan tiếp nhận thông báo sau tái cơ cấu**

[Luật Công nghệ thông tin (văn bản hợp nhất 2025)] Điều 23, Khoản 2 quy định:
> "Tổ chức, cá nhân sử dụng tên miền quốc gia Việt Nam ".vn" khi thiết lập trang thông tin điện tử không cần thông báo với Bộ Bưu chính, Viễn thông. Tổ chức, cá nhân khi thiết lập trang thông tin điện tử không sử dụng tên miền quốc gia Việt Nam ".vn" phải thông báo trên môi trường mạng với Bộ Bưu chính, Viễn thông..."

Văn bản Luật CNTT (2025) vẫn ghi nhận tên "Bộ Bưu chính, Viễn thông". Tuy nhiên, [Luật Viễn thông 2023] quy định nghĩa vụ đăng ký, thông báo với **"Bộ trưởng Bộ Thông tin và Truyền thông"**.

*Suy luận bù khoảng trống:*
- **Nguyên tắc hành chính:** Khi hai Bộ xung đột về tên gọi trong cùng hệ thống pháp luật, nguyên tắc quản lý thống nhất cho thấy cơ quan quản lý nhà nước hiện hành là **Bộ Thông tin và Truyền thông** (hoặc tên gọi mới tương đương).
- Mức độ chắc chắn: Suy luận từ nguyên tắc quản lý nhà nước — luật chưa quy định tường minh việc cập nhật tên cơ quan trong Điều 23.

**(b) Nghĩa vụ thông báo của doanh nghiệp nước ngoài**

[Luật Công nghệ thông tin (văn bản hợp nhất 2025)] Điều 23, Khoản 2 quy định: *"Tổ chức, cá nhân khi thiết lập trang thông tin điện tử không sử dụng tên miền quốc gia Việt Nam ".vn" **phải** thông báo..."*

**Kết luận: Nghĩa vụ thông báo áp dụng cho doanh nghiệp nước ngoài cung cấp dịch vụ tại Việt Nam.**

- **Chủ thể:** "Tổ chức, cá nhân" bao gồm cả tổ chức nước ngoài hoạt động trên lãnh thổ Việt Nam.
- **Điều kiện:** Không sử dụng tên miền ".vn".
- Mức độ chắc chắn: **RÕ** (văn bản không loại trừ chủ thể nước ngoài).

---

## Câu 7 — Chuỗi trách nhiệm trong dịch vụ hosting và công cụ tìm kiếm

Doanh nghiệp hosting H phát hiện khách thuê T đang lưu trữ nội dung vi phạm pháp luật. Đồng thời, công cụ tìm kiếm S đang lập chỉ mục (index) nội dung đó. Hãy xác định đầy đủ chuỗi nghĩa vụ pháp lý: (a) H có nghĩa vụ gì theo Điều 18? (b) S có nghĩa vụ gì theo Điều 19? (c) H và S có thể bị xem là "hỗ trợ hoạt động bất hợp pháp" theo Điều 12(1) không? Ai phải hành động trước?

### Trả lời

**(a) Nghĩa vụ của Doanh nghiệp Hosting (H) theo Điều 18**

Theo [Luật Công nghệ thông tin (văn bản hợp nhất 2025)] Điều 18, Khoản 3, H có trách nhiệm:

- **(a)** Thực hiện yêu cầu của cơ quan nhà nước có thẩm quyền về việc xác định danh sách chủ sở hữu thuê chỗ lưu trữ thông tin số;
- **(b)** Tiến hành **kịp thời** các biện pháp cần thiết để ngăn chặn việc truy nhập thông tin số hoặc loại bỏ thông tin số trái pháp luật **theo yêu cầu** của cơ quan nhà nước có thẩm quyền;
- **(c)** **Ngừng cho tổ chức, cá nhân khác thuê chỗ lưu trữ thông tin số** trong trường hợp **tự mình phát hiện** hoặc được cơ quan nhà nước có thẩm quyền thông báo cho biết thông tin đang được lưu trữ là trái pháp luật;
- **(d)** Bảo đảm bí mật thông tin của tổ chức, cá nhân thuê chỗ lưu trữ thông tin.

**(b) Nghĩa vụ của Công cụ tìm kiếm (S) theo Điều 19**

Theo [Luật Công nghệ thông tin (văn bản hợp nhất 2025)] Điều 19, Khoản 3:
> "Tổ chức, cá nhân có trách nhiệm **ngừng cung cấp cho tổ chức, cá nhân khác công cụ tìm kiếm** đến các nguồn thông tin số trong trường hợp **tự mình phát hiện** hoặc được cơ quan nhà nước có thẩm quyền thông báo cho biết thông tin đó là trái pháp luật."

**(c) Nguy cơ bị coi là "hỗ trợ hoạt động bất hợp pháp" theo Điều 12(1)**

Theo [Luật Công nghệ thông tin (văn bản hợp nhất 2025)] Điều 12, Khoản 1: *"Cản trở hoạt động hợp pháp hoặc hỗ trợ hoạt động bất hợp pháp về ứng dụng và phát triển công nghệ thông tin..."*

**Phân tích:**
- Nếu H và S **phát hiện nội dung vi phạm nhưng không thực hiện** nghĩa vụ ngừng cho thuê (Điều 18, Khoản 3, điểm c) hoặc ngừng cung cấp công cụ tìm kiếm (Điều 19, Khoản 3), hành vi tiếp tục lưu trữ hoặc chỉ mục nội dung đó **sẽ bị đánh giá là "hỗ trợ hoạt động bất hợp pháp"** theo Điều 12, Khoản 1.
- Việc không thực hiện nghĩa vụ "tiến hành kịp thời các biện pháp cần thiết" (Điều 18, Khoản 3, điểm b) khi có yêu cầu của cơ quan nhà nước cũng là hành vi vi phạm.

**Thứ tự hành động:**
- Cả H và S đều có **nghĩa vụ độc lập** khi "tự mình phát hiện" hoặc "được cơ quan nhà nước có thẩm quyền thông báo".
- Luật không quy định thứ tự ưu tiên giữa H và S khi cả hai cùng phát hiện. Tuy nhiên, về mặt kỹ thuật, **H có nghĩa vụ loại bỏ nguồn gốc lưu trữ** (Điều 18, Khoản 3, điểm c), còn **S có nghĩa vụ loại bỏ đường dẫn** (Điều 19, Khoản 3).

---

## Câu 8 — Ưu tiên ứng dụng CNTT trong khẩn cấp và giới hạn của ưu tiên

Điều 14 cho phép cơ quan có thẩm quyền "huy động một phần hoặc toàn bộ cơ sở hạ tầng thông tin" trong tình huống khẩn cấp. Hỏi: (a) "cơ sở hạ tầng thông tin" theo định nghĩa tại khoản 4 Điều 4 có bao gồm "mạng viễn thông" không? (b) Nếu có, điều này có mâu thuẫn với quyền kinh doanh của doanh nghiệp viễn thông không? (c) Cơ chế bồi thường, nếu có, được quy định ở đâu trong hệ thống pháp lý này?

### Trả lời

**(a) Định nghĩa "cơ sở hạ tầng thông tin"**

Theo [Luật Công nghệ thông tin (văn bản hợp nhất 2025)] Điều 4, Khoản 4:
> "Cơ sở hạ tầng thông tin là hệ thống trang thiết bị phục vụ cho việc sản xuất, truyền đưa, thu thập, xử lý, lưu trữ và trao đổi thông tin số, **bao gồm mạng viễn thông, mạng Internet, mạng máy tính và cơ sở dữ liệu**."

→ **Kết luận: Định nghĩa này bao gồm "mạng viễn thông".**

**(b) Xung đột quyền kinh doanh**

- **Quyền huy động:** [Luật Công nghệ thông tin (văn bản hợp nhất 2025)] Điều 14, Khoản 1 quy định: *"Cơ quan nhà nước có thẩm quyền quyết định huy động một phần hoặc toàn bộ cơ sở hạ tầng thông tin để ưu tiên phục vụ cho việc ứng dụng công nghệ thông tin khi có một trong các trường hợp khẩn cấp..."*

- **Nghĩa vụ tuân thủ:** [Luật Viễn thông 2023] Điều 5, Khoản 6 quy định: *"Doanh nghiệp viễn thông có trách nhiệm ngừng khẩn cấp việc cung cấp dịch vụ viễn thông trong trường hợp có bạo loạn... theo yêu cầu của cơ quan nhà nước có thẩm quyền..."*

**Phân tích:** Luật quy định quyền huy động và nghĩa vụ ngừng cung cấp dịch vụ trong tình huống khẩn cấp. Điều này tạo ra **sự hạn chế tạm thời** đối với quyền kinh doanh bình thường của doanh nghiệp viễn thông để phục vụ mục đích quốc phòng, an ninh hoặc cứu hộ. Khoảng trống: Luật không quy định cụ thể cơ chế giải quyết xung đột giữa quyền sở hữu/hợp đồng kinh doanh và lệnh huy động khẩn cấp.

**(c) Cơ chế bồi thường**

Trong các văn bản được cung cấp, **không có quy định cụ thể** về cơ chế bồi thường thiệt hại cho doanh nghiệp viễn thông khi bị huy động cơ sở hạ tầng trong tình huống khẩn cấp.

*Suy luận bù khoảng trống:*
- **Nguyên tắc:** Theo nguyên tắc quản lý hành chính, khi cơ quan nhà nước có thẩm quyền ra quyết định huy động tài sản hợp pháp gây thiệt hại cho chủ sở hữu, nguyên tắc chung của pháp luật hành chính là **nhà nước có nghĩa vụ bồi thường thiệt hại hợp pháp**.
- **Phân công:** Nhà nước (cơ quan có thẩm quyền) chịu trách nhiệm chi trả hoặc phê duyệt ngân sách cho việc bồi thường; Doanh nghiệp viễn thông có trách nhiệm phối hợp cung cấp thông tin thiệt hại và khôi phục hệ thống sau khi lệnh huy động kết thúc.
- Mức độ chắc chắn: **Suy luận từ nguyên tắc pháp luật hành chính** — luật chuyên ngành viễn thông/công nghệ thông tin chưa quy định tường minh về bồi thường cho trường hợp huy động khẩn cấp.

---

## Câu 9 — Quyền yêu cầu đính chính thông tin và giới hạn của quyền

Điều 22 cho phép cá nhân yêu cầu "kiểm tra, đính chính hoặc hủy bỏ" thông tin cá nhân. Tuy nhiên, Điều 21(3) cho phép thu thập thông tin mà không cần đồng ý để thực hiện "nghĩa vụ pháp luật". Hỏi: nếu thông tin cá nhân được thu thập theo nghĩa vụ pháp luật (ví dụ: dữ liệu thuế), người dùng có quyền yêu cầu hủy bỏ không? Luật CNTT giải quyết xung đột này như thế nào, và Luật An ninh mạng 116/2025 có quy định nào bổ sung không?

### Trả lời

**1. Quy định của Luật Công nghệ thông tin 2025**

- **Điều 21, Khoản 1:** Thu thập, xử lý và sử dụng thông tin cá nhân của người khác trên môi trường mạng phải được người đó đồng ý, **trừ trường hợp pháp luật có quy định khác**.
- **Điều 21, Khoản 3, điểm c:** Có quyền thu thập, xử lý và sử dụng thông tin cá nhân của người khác mà không cần sự đồng ý trong trường hợp: *"Thực hiện nghĩa vụ khác theo quy định của pháp luật."*
- **Điều 22, Khoản 1:** *"Cá nhân có quyền yêu cầu tổ chức, cá nhân lưu trữ thông tin cá nhân của mình trên môi trường mạng thực hiện việc kiểm tra, đính chính hoặc hủy bỏ thông tin đó."*

**2. Phân tích xung đột và khoảng trống pháp lý**

Trạng thái B — Luật có quy định + có khoảng trống:

Khoảng trống xác định: Luật quy định [Điều 21, Khoản 3] cho phép thu thập thông tin cá nhân mà không cần đồng ý để thực hiện nghĩa vụ pháp luật. Tuy nhiên KHÔNG nêu rõ liệu quyền yêu cầu hủy bỏ tại [Điều 22, Khoản 1] có áp dụng cho trường hợp dữ liệu được thu thập theo ngoại lệ này hay không.

*Suy luận bù khoảng trống:*
- **Nguyên tắc ưu tiên:** Điều 21(3)(c) là ngoại lệ cho yêu cầu đồng ý, không phải là quy định về quyền hạn chế quyền yêu cầu hủy bỏ.
- **Suy luận:** Quyền yêu cầu hủy bỏ tại Điều 22(1) vẫn tồn tại độc lập với cơ sở thu thập tại Điều 21(3), vì Điều 22 không phân biệt nguồn gốc thu thập thông tin.
- Tuy nhiên, đối với dữ liệu thuế hoặc dữ liệu thu thập theo nghĩa vụ pháp luật, tổ chức lưu trữ **có thể từ chối hủy bỏ** nếu việc hủy bỏ sẽ vi phạm chính nghĩa vụ pháp luật yêu cầu lưu trữ đó.

**3. Về Luật An ninh mạng 2025**

Trong phạm vi văn bản được cung cấp, **không tìm thấy quy định nào** của Luật An ninh mạng 2025 trực tiếp giải quyết vấn đề quyền yêu cầu hủy bỏ thông tin cá nhân khi dữ liệu được thu thập để thực hiện nghĩa vụ pháp luật.

**Kết luận:**
- **Luật Công nghệ thông tin 2025:** Có quy định về quyền yêu cầu hủy bỏ (Điều 22, Khoản 1) nhưng không giải quyết rõ ràng xung đột với ngoại lệ thu thập theo nghĩa vụ pháp luật (Điều 21, Khoản 3).
- **Luật An ninh mạng 2025:** Không có quy định bổ sung trực tiếp về vấn đề này.
- **Khuyến nghị:** Cần xem xét quy định chi tiết của Chính phủ hoặc hướng dẫn của Bộ Thông tin và Truyền thông để làm rõ điều kiện áp dụng quyền hủy bỏ đối với dữ liệu thu thập theo cơ sở pháp lý đặc thù.

---

## Câu 10 — Tích hợp ba luật: tình huống thực tế đa chiều

Một doanh nghiệp viễn thông Việt Nam (có hạ tầng, thống lĩnh thị trường) vận hành cả: (1) mạng viễn thông công cộng, (2) dịch vụ trung tâm dữ liệu, (3) dịch vụ điện toán đám mây, và (4) nền tảng OTT nhắn tin. Khi bị tấn công mạng làm gián đoạn cả 4 dịch vụ trên, hãy xác định: (a) theo Luật An ninh mạng, hệ thống nào được ưu tiên ứng phó trước nếu đây là hệ thống thông tin quan trọng về an ninh quốc gia? (b) theo Luật Viễn thông, nghĩa vụ "ngừng khẩn cấp" và "cung cấp điểm truy nhập" có mâu thuẫn với nhau trong tình huống tấn công không? (c) theo Luật CNTT, trách nhiệm thông báo và khắc phục của doanh nghiệp là gì?

### Trả lời

**(a) Ưu tiên ứng phó hệ thống thông tin quan trọng về an ninh quốc gia (Luật An ninh mạng)**

Theo [Luật An ninh mạng 2025] Điều 9, Khoản 1: *"Hệ thống thông tin quan trọng về an ninh quốc gia là hệ thống thông tin có vai trò chiến lược, đặc biệt quan trọng đối với chính trị, quốc phòng, an ninh quốc gia."*

**Phân tích ưu tiên:** Văn bản không quy định cụ thể thứ tự ưu tiên giữa các loại hình dịch vụ (mạng viễn thông, trung tâm dữ liệu, điện toán đám mây, OTT) khi cùng thuộc một doanh nghiệp bị tấn công. Tuy nhiên, nếu hệ thống được xếp vào danh mục "quan trọng về an ninh quốc gia", nó sẽ được ưu tiên bảo vệ theo nguyên tắc bảo vệ an ninh mạng.

*Suy luận:* Khi có sự cố ảnh hưởng đến nhiều dịch vụ, **hệ thống được xác định là "quan trọng về an ninh quốc gia"** (theo Điều 9) sẽ được ưu tiên xử lý trước các hệ thống thông tin thông thường để đảm bảo an ninh quốc gia. Mức độ chắc chắn: Suy luận từ nguyên tắc bảo vệ an ninh quốc gia — luật chưa quy định tường minh thứ tự ưu tiên giữa các loại hình dịch vụ cụ thể.

**(b) Mâu thuẫn giữa "ngừng khẩn cấp" và "cung cấp điểm truy nhập" (Luật Viễn thông)**

Luật Viễn thông 2023 Điều 5, Khoản 6 (ngừng khẩn cấp) và Khoản 7 (cung cấp điểm truy nhập) quy định hai nghĩa vụ riêng biệt. Tuy nhiên, luật **không nêu rõ nghĩa vụ** đối với tình huống cụ thể là bị tấn công mạng.

*Suy luận bù khoảng trống:*
- Khi có yêu cầu của cơ quan nhà nước có thẩm quyền (theo Điều 7 Luật An ninh mạng về hành vi bị cấm cản trở hoạt động bảo vệ an ninh mạng), doanh nghiệp có thể bị yêu cầu ngừng cung cấp dịch vụ để ngăn chặn rủi ro.
- Nhà nước (cơ quan quản lý) ra quyết định ngừng khẩn cấp; Doanh nghiệp (chủ quản hệ thống) thực hiện phối hợp.
- Mức độ chắc chắn: **Khoảng trống thực sự** — cần quy định chi tiết của Chính phủ về cơ chế cân bằng giữa an ninh và tiếp cận dịch vụ.

**Kết luận:** Không thể khẳng định mâu thuẫn dựa trên văn bản hiện có.

**(c) Trách nhiệm thông báo và khắc phục theo Luật CNTT**

Theo [Luật Công nghệ thông tin (văn bản hợp nhất 2025)] Điều 9, Khoản 2: Doanh nghiệp khi hoạt động kinh doanh trên môi trường mạng phải thông báo công khai những thông tin có liên quan, bao gồm: (a) Tên, địa chỉ địa lý, số điện thoại, địa chỉ thư điện tử; (b) Thông tin về quyết định thành lập, giấy phép hoạt động...

**Về khắc phục sự cố:** Văn bản không quy định cụ thể nghĩa vụ "khắc phục sự cố" hay "thời hạn thông báo sự cố" trong Điều 9.

**Tổng hợp:** Doanh nghiệp có nghĩa vụ:
1. Thông báo thông tin kinh doanh theo Luật CNTT (Điều 9).
2. Áp dụng biện pháp kỹ thuật để phòng ngừa, ngăn chặn tấn công theo Luật An ninh mạng (Điều 18).
3. Nghĩa vụ thông báo sự cố cụ thể (nếu có) cần căn cứ thêm quy định chi tiết của Chính phủ hoặc Luật An ninh mạng (Điều 20 về tình huống nguy hiểm).

Mức độ chắc chắn: Quy định thông báo kinh doanh là **tường minh**; quy định khắc phục sự cố tấn công mạng cần **kết hợp với Luật An ninh mạng**.
