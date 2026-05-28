# BÁO CÁO ĐÁNH GIÁ SO SÁNH HAI PHIÊN BẢN RETRIEVAL

**Phiên bản 1:** Graph + Vector Reasoning  
**Phiên bản 2:** Vector Reasoning Only  
**Tổng số câu:** 30 câu (10 câu × 3 luật)

---

## TỔNG QUAN ĐIỂM SỐ

### Luật Viễn thông (Câu 1–10)

| Câu | Chủ đề | V1 (Graph+Vector) | V2 (Vector Only) | Chênh lệch |
|-----|--------|:-----------------:|:----------------:|:----------:|
| 1 | Cho thuê hạ tầng, bồi thường | 7 | 6 | +1 |
| 2 | Mạng viễn thông dùng riêng | 9 | 10 | -1 |
| 3 | Giám hộ — cập nhật thông tin thuê bao | 7 | 7 | 0 |
| 4 | Thu hồi giấy phép — bất khả kháng | 8 | 7 | +1 |
| 5 | OTT voice — loại giấy phép | 8 | 8 | 0 |
| 6 | Kết nối hạ tầng không được phép | 9 | 9 | 0 |
| 7 | Tranh chấp tên miền — dụng ý xấu | 9 | 9 | 0 |
| 8 | Bồi thường vi phạm tên miền | 10 | 10 | 0 |
| 9 | Khóa SIM — căn cứ tự ý | 8 | 7 | +1 |
| 10 | Thay đổi sở hữu — giấy phép | 8 | 8 | 0 |
| **Tổng** | | **83** | **81** | **+2** |
| **Trung bình** | | **8.3** | **8.1** | **+0.2** |

### Luật An ninh mạng (Câu 11–20, ghi theo Câu 1–10 trong tài liệu gốc)

| Câu | Chủ đề | V1 (Graph+Vector) | V2 (Vector Only) | Chênh lệch |
|-----|--------|:-----------------:|:----------------:|:----------:|
| 1 | Thời hạn yêu cầu — hiện diện pháp lý | 9 | 6* | +3 |
| 2 | Kiểm thử bảo mật — dữ liệu ra nước ngoài | 8 | 6 | +2 |
| 3 | AI sinh tin sai lệch kinh tế | 9 | 10 | -1 |
| 4 | SCADA — hệ thống năng lượng — báo cáo | 9 | 9 | 0 |
| 5 | Bí mật nhà nước vs bí mật công tác | 8 | 6 | +2 |
| 6 | Ngắt kết nối khẩn cấp — thẩm quyền | 9 | 6 | +3 |
| 7 | Deepfake nội bộ — nghĩa vụ nền tảng | 9 | 8 | +1 |
| 8 | Ransomware đại học — tiền mã hóa | 8 | 7 | +1 |
| 9 | Nền tảng nước ngoài — ba vi phạm | 8 | 9 | -1 |
| 10 | Hệ thống CSDL dân cư — thẩm định | 8 | 8 | 0 |
| **Tổng** | | **85** | **75** | **+10** |
| **Trung bình** | | **8.5** | **7.5** | **+1.0** |

*\*Câu 1 V2: lỗi pipeline — output là nội dung reasoning nội bộ thay vì câu trả lời. Điểm 6 phản ánh chất lượng reasoning được ghi nhận, không phải output thực tế.*

### Luật CNTT (Câu 21–30, ghi theo Câu 1–10 trong tài liệu gốc)

| Câu | Chủ đề | V1 (Graph+Vector) | V2 (Vector Only) | Chênh lệch |
|-----|--------|:-----------------:|:----------------:|:----------:|
| 1 | Trang bán hàng — trách nhiệm nội dung | 8 | 9 | -1 |
| 2 | Gián đoạn dịch vụ công — bất khả kháng | 9 | 9 | 0 |
| 3 | Nền tảng telemedicine — pháp lý y tế | 9 | 9 | 0 |
| 4 | Rò rỉ dữ liệu bệnh viện | 8 | 9 | -1 |
| 5 | Hủy đơn hàng nhập sai | 8 | 9 | -1 |
| 6 | Nhà cung cấp email tự xóa dữ liệu | 8 | 8 | 0 |
| 7 | Trích dẫn nguyên văn báo cáo nội bộ | 9 | 8 | +1 |
| 8 | CNTT giáo dục — quyền sở hữu | 7 | 7 | 0 |
| 9 | Mã nguồn — quyền tiếp cận | 7 | 8 | -1 |
| 10 | Server nước ngoài — hợp đồng VPĐD | 7 | 7 | 0 |
| **Tổng** | | **80** | **83** | **-3** |
| **Trung bình** | | **8.0** | **8.3** | **-0.3** |

### Tổng hợp toàn bộ

| Luật | V1 (Graph+Vector) | V2 (Vector Only) | Chênh lệch |
|------|:-----------------:|:----------------:|:----------:|
| Viễn thông | 83 / 100 | 81 / 100 | +2 |
| An ninh mạng | 85 / 100 | 75 / 100 | +10 |
| CNTT | 80 / 100 | 83 / 100 | -3 |
| **Tổng cộng** | **248 / 300** | **239 / 300** | **+9** |
| **Trung bình** | **8.27** | **7.97** | **+0.30** |

---

## PHÂN TÍCH CHI TIẾT THEO TỪNG LUẬT

### 1. Luật Viễn thông — V1 nhỉnh hơn nhẹ (+2 điểm)

**V1 làm tốt hơn ở:**

- **Câu 1 (+1):** V1 nhận ra Điều 13 khoản 4 điểm b (chỉ doanh nghiệp có hạ tầng mạng mới có quyền cho thuê), từ đó đặt vấn đề tư cách pháp lý của VNPT đúng hơn. V2 chỉ dùng Điều 9 khoản 3 (cấm gây hại hạ tầng) — sai chủ thể áp dụng, và Điều 62 khoản 3 thay vì căn cứ bồi thường đúng.
- **Câu 4 (+1):** V1 nhận ra Điều 40 khoản 1 điểm d (thời hạn 2 năm) rõ ràng hơn; phân tích bất khả kháng vs nguyên nhân khách quan sắc bén hơn.
- **Câu 9 (+1):** V1 nhận ra tension giữa Điều 5 khoản 6 và Luật An ninh mạng Điều 41 khoản 3 tốt hơn; tuy nhiên cả hai đều bỏ sót Điều 13 khoản 2 điểm m (tự khóa SIM khi vi phạm pháp luật viễn thông rõ ràng).

**V2 làm tốt hơn ở:**

- **Câu 2 (-1):** V2 đạt 10/10 hoàn hảo, V1 chỉ 9/10 vì chưa phân tích điểm tinh tế về pháp nhân độc lập.
- **Câu 3 (bằng nhau):** Cả hai cùng bỏ sót cơ chế Điều 6 khoản 4 điểm d — con đường pháp lý quan trọng nhất cho người giám hộ.

**Quan sát:** Với Luật Viễn thông, sự chênh lệch rất nhỏ. Graph reasoning giúp xác định đúng hơn chuỗi dẫn chiếu điều khoản (Điều 13 khoản 4 → tư cách pháp lý → Điều 62), nhưng không tạo ra lợi thế đáng kể trên các câu đã được index tốt.

---

### 2. Luật An ninh mạng — V1 vượt trội rõ (+10 điểm)

**V1 làm tốt hơn ở:**

- **Câu 1 (+3):** V2 gặp lỗi pipeline nghiêm trọng — output là nội dung reasoning nội bộ, không phải câu trả lời thực tế. V1 trả về output đúng định dạng với phân tích đầy đủ thời hạn (24h/3h/6h) và hiện diện pháp lý.
- **Câu 6 (+3):** V2 không tìm được Điều 20 khoản 4(b) — điều quan trọng nhất về thẩm quyền Thủ tướng/Bộ trưởng ra lệnh ngắt kết nối. V1 tìm được điều khoản cốt lõi này nhờ graph traversal từ nhánh "thẩm quyền khẩn cấp".
- **Câu 2 (+2):** V2 kết luận "không bị cấm trực tiếp" đối với việc mang dữ liệu ra nước ngoài — sai với trường hợp dữ liệu cá nhân. V1 nhận ra Điều 15 khoản 1 áp dụng đúng hơn.
- **Câu 5 (+2):** V2 không tìm được Điều 25 khoản 2 về thời hạn 24h của nền tảng — lỗi retrieval làm mất toàn bộ câu hỏi thứ ba. V1 nhờ graph có thể duyệt từ "nghĩa vụ nền tảng" sang "thời hạn xử lý yêu cầu".

**V2 làm tốt hơn ở:**

- **Câu 3 (-1):** V2 xuất sắc 10/10, sử dụng Điều 14 khoản 4 trực tiếp hơn V1 (dùng Điều 25 khoản 2). Đây là trường hợp vector search trả về điều khoản chính xác và súc tích hơn.
- **Câu 9 (-1):** V2 trình bày ba vi phạm rõ ràng hơn, lập luận logic hơn về mức độ nghiêm trọng.

**Quan sát:** Đây là luật Graph+Vector thể hiện ưu thế rõ nhất. Lý do: Luật An ninh mạng có nhiều mối quan hệ phức tạp giữa các khái niệm (thẩm quyền, phân loại hệ thống, thời hạn, tình huống khẩn cấp) đòi hỏi phải duyệt qua nhiều nút trong graph. Vector search đơn thuần bị thiếu hụt nghiêm trọng ở các câu yêu cầu truy ngược chuỗi thẩm quyền (Câu 6) hoặc xác định điều khoản ít xuất hiện (Câu 5 — Điều 25 khoản 2).

---

### 3. Luật CNTT — V2 nhỉnh hơn nhẹ (-3 điểm so với V1)

**V2 làm tốt hơn ở:**

- **Câu 1 (-1):** V2 tìm được Điều 20 khoản 2 và nhận ra tension với Điều 30, ghi nhận đây là khoảng trống pháp lý thú vị. V1 không phân tích xung đột này.
- **Câu 4 (-1):** V2 tìm được Điều 21 khoản 2 điểm a và b (nghĩa vụ thông báo và sử dụng đúng mục đích thông tin cá nhân) — căn cứ trực tiếp và mạnh nhất, không có trong V1.
- **Câu 5 (-1):** V2 kết luận dứt khoát hơn về quyền hủy; xác định điều khoản "không được hủy" vô hiệu rõ ràng hơn.
- **Câu 9 (-1):** V2 tìm được Điều 69 khoản 1 và 2 đầy đủ hơn, phân tích giới hạn của sao chép dự phòng chính xác hơn.

**V1 làm tốt hơn ở:**

- **Câu 7 (+1):** V1 phân tích khoảng trống về "lợi ích công cộng" tốt hơn; nhận ra song song với Luật An ninh mạng có căn cứ hơn.
- **Câu 8 (+0):** Cả hai cùng bỏ sót Điều 62 khoản 3 về quyền sở hữu từ ngân sách nhà nước, dù V2 tìm được điều khoản này.

**Quan sát:** Với Luật CNTT, vector search thuần túy hoạt động tốt tương đương hoặc tốt hơn. Lý do: Luật CNTT có cấu trúc tương đối phẳng, ít chuỗi dẫn chiếu chéo phức tạp. Nhiều điều khoản quan trọng (Điều 21, 30, 32) có nội dung đặc thù đủ để vector search tìm trực tiếp mà không cần graph traversal. Ngoài ra, V2 thực hiện tốt hơn ở các câu về dữ liệu cá nhân và thương mại điện tử — đây là lĩnh vực vector embedding hoạt động tốt do ngữ nghĩa rõ ràng.

---

## PHÂN TÍCH PATTERN LỖI

### Lỗi chung của cả hai phiên bản (không được giải quyết bởi graph)

| Pattern | Ví dụ cụ thể | Nguyên nhân |
|---------|-------------|-------------|
| Bỏ sót điều khoản "bẫy" | Điều 11 Luật VT (cổ phần chi phối DNNN) — cả 2 phiên bản, cả 2 lần | Điều khoản không được đề cập trong câu hỏi, không có anchor từ khóa để retrieval |
| Không xác định loại bí mật | "Bí mật nhà nước" vs "bí mật công tác" — Câu 5 ANM | Đòi hỏi suy luận pháp lý ngoài văn bản, không phải retrieval |
| Né kết luận dứt khoát | Nhiều câu dừng ở "suy luận" thay vì kết luận | Model tự giới hạn khi có khoảng trống pháp lý |
| Bỏ sót điều khoản xử phạt cụ thể | Điều 9 khoản 4 VT (thiết lập hạ tầng khi chưa được phép) | Câu hỏi hỏi "chế tài" nhưng retrieval ưu tiên "nội dung" hơn "thủ tục" |

### Lỗi đặc trưng của V2 (Vector Only)

| Pattern | Ví dụ cụ thể | Tần suất |
|---------|-------------|---------|
| **Retrieval miss điều khoản thẩm quyền** | Điều 20 khoản 4(b) ANM — Câu 6 | 2/10 câu ANM |
| **Nhầm chủ thể điều khoản** | Điều 15 khoản 2 (trách nhiệm Bộ CA) thay vì Điều 25 khoản 2 (nghĩa vụ nền tảng) | 1/10 câu ANM |
| **Lỗi pipeline output** | Reasoning nội bộ lộ ra thay vì câu trả lời | 1/10 câu ANM |
| **Kết luận sai hướng** | "Không bị cấm trực tiếp" với dữ liệu cá nhân ra nước ngoài | 1/10 câu ANM |

### Lỗi đặc trưng của V1 (Graph+Vector)

| Pattern | Ví dụ cụ thể | Tần suất |
|---------|-------------|---------|
| **Graph traversal quá rộng** | Điều 9 khoản 1 "xâm phạm ANQG" dùng cho kết nối tiết kiệm chi phí — Câu 6 VT | 1/10 câu VT |
| **Thiếu phân tích ranh giới tinh tế** | Ranh giới pháp nhân độc lập vs nhánh trực thuộc — Câu 2 VT | 2/30 câu |
| **Không khai thác hết chain dẫn chiếu** | Bỏ Điều 6 khoản 4 điểm d — con đường qua cơ quan nhà nước cho người giám hộ | 1/10 câu VT |

---

## KẾT LUẬN VÀ KHUYẾN NGHỊ

### Kết luận chính

**1. Graph+Vector vượt trội rõ ràng với Luật An ninh mạng (+10 điểm / 100)**

Graph reasoning đặc biệt hiệu quả khi câu hỏi đòi hỏi duyệt chuỗi thẩm quyền (ai → có quyền gì → điều kiện nào → ngoại lệ nào) và xác định điều khoản ít xuất hiện trong corpus nhưng có quan hệ logic rõ với các điều khoản khác. Điều 20 khoản 4(b) ANM (thẩm quyền ngắt kết nối khẩn cấp) là ví dụ điển hình.

**2. Vector Only đủ tốt hoặc nhỉnh hơn với Luật CNTT (-3 điểm / 100)**

Khi luật có cấu trúc tương đối phẳng và các điều khoản có nội dung đặc thù, vector search tìm trực tiếp hiệu quả hơn. Graph có thể gây nhiễu khi traversal ra các nút không liên quan (Điều 9 khoản 1 về ANQG cho câu hỏi thương mại).

**3. Cả hai phương pháp có ceiling tương đương**

Điểm trừ chung lớn nhất không đến từ retrieval mà từ: (a) điều khoản "bẫy" không có anchor từ khóa, (b) yêu cầu suy luận pháp lý ngoài văn bản (phân biệt bí mật nhà nước vs bí mật công tác), và (c) xu hướng né kết luận dứt khoát khi có khoảng trống pháp lý.

### Khuyến nghị

| Loại câu hỏi | Phương pháp nên dùng | Lý do |
|-------------|---------------------|-------|
| Chuỗi thẩm quyền đa cơ quan | Graph + Vector | Cần duyệt quan hệ phân cấp |
| Thời hạn & thủ tục khẩn cấp | Graph + Vector | Điều khoản liên quan nằm rải rác |
| Điều khoản đơn lẻ, nội dung đặc thù | Vector Only | Embedding trực tiếp hiệu quả hơn |
| Xung đột giữa hai điều khoản | Graph + Vector | Cần biết quan hệ lex specialis |
| Thương mại điện tử / dữ liệu cá nhân | Vector Only | Ngữ nghĩa rõ, ít chain dẫn chiếu |

---

*Báo cáo dựa trên 30 câu đánh giá — 10 câu mỗi luật, mỗi câu chấm thang 10 điểm.*  
*V1: Graph + Vector Reasoning | V2: Vector Reasoning Only*