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

---

## PHẦN II: ĐÁNH GIÁ CÂU HỎI LIÊN LUẬT (20 câu — 3 Luật đồng thời)

**Phiên bản 3:** Graph + Vector Reasoning  
**Phiên bản 4:** Vector Reasoning Only (không thinking)  
**Cấu trúc:** 10 nhóm × 2 câu, mỗi nhóm một chủ đề pháp lý xuyên luật

---

### Bảng điểm tổng hợp — Liên luật

| Nhóm | Chủ đề | Câu | V3 (G+V) | V4 (V only) | Chênh |
|------|--------|-----|:--------:|:-----------:|:-----:|
| 1 | Bí mật thông tin vs. Yêu cầu nhà nước | 1 | 7.0 | 7.0 | 0 |
| 1 | | 2 | 8.0 | 6.0 | +2.0 |
| 2 | Ngừng dịch vụ | 3 | 7.5 | 7.0 | +0.5 |
| 2 | | 4 | 7.5 | 7.0 | +0.5 |
| 3 | Trách nhiệm trung gian | 5 | 8.5 | 8.5 | 0 |
| 3 | | 6 | 7.0 | 6.5 | +0.5 |
| 4 | Dữ liệu cá nhân | 7 | 9.0 | 7.5 | +1.5 |
| 4 | | 8 | 8.5 | 8.0 | +0.5 |
| 5 | SIM và danh tính | 9 | 8.0 | 7.5 | +0.5 |
| 5 | | 10 | 8.0 | 7.0 | +1.0 |
| 6 | Hạ tầng thiết yếu | 11 | 8.5 | 7.5 | +1.0 |
| 6 | | 12 | 8.5 | 8.0 | +0.5 |
| 7 | AI và công nghệ mới | 13 | 8.0 | 7.5 | +0.5 |
| 7 | | 14 | 7.0 | 7.0 | 0 |
| 8 | Phạm vi lãnh thổ | 15 | 8.0 | 7.5 | +0.5 |
| 8 | | 16 | 8.0 | 8.0 | 0 |
| 9 | Viễn thông công ích | 17 | 7.5 | 6.5 | +1.0 |
| 9 | | 18 | 7.5 | 7.0 | +0.5 |
| 10 | Xung đột thẩm quyền | 19 | 8.5 | 8.5 | 0 |
| 10 | | 20 | 7.5 | 6.5 | +1.0 |
| **Tổng** | | | **157.5** | **147.5** | **+10.0** |
| **Trung bình** | | | **7.88** | **7.38** | **+0.50** |

---

### Phân tích theo nhóm chủ đề

#### Nhóm 1 — Bí mật thông tin vs. Yêu cầu nhà nước

**Câu 1 (7.0 = 7.0):** Bằng nhau ở cả hai phiên bản. Điểm mấu chốt bị bỏ qua đồng đều — phân biệt công văn hành chính vs. quyết định tố tụng chưa được giải quyết tường minh. Đây là giới hạn của suy luận pháp lý, không phải giới hạn của retrieval.

**Câu 2 (8.0 vs 6.0 — chênh +2.0):** Chênh lệch lớn nhất nhóm này. V3 tìm được Điều 10 K5 ANM 2025 về nghĩa vụ thẩm định cấp độ 3 — căn cứ trực tiếp xác định tổ chức nước ngoài là chủ quản chịu trách nhiệm. V4 chỉ tiếp cận được Điều 5 VT và Điều 28 VT — các căn cứ chung, không chỉ định rõ chủ thể. Ngoài ra V3 bổ sung Điều 28 K2b VT làm cầu nối giữa vi phạm ANM và quyền chấm dứt hợp đồng VT — lập luận hai tầng mà V4 thiếu hoàn toàn.

---

#### Nhóm 2 — Ngừng dịch vụ

**Câu 3 (7.5 vs 7.0 — chênh +0.5):** V3 nhỉnh hơn do có Điều 25 K2 ANM về nghĩa vụ tuân thủ yêu cầu của Bộ CA — căn cứ để hiểu tại sao hai lệnh xung đột nhau. V4 suy luận Thủ tướng phân giải hợp lý nhưng không có anchor tường minh. Cả hai cùng nhận diện khoảng trống và gắn cờ low confidence đúng chỗ.

**Câu 4 (7.5 vs 7.0 — chênh +0.5):** V4 tìm được gợi ý thực tế "duy trì kênh tối thiểu cho cứu hộ" — điểm cộng thực tế tốt. Tuy nhiên thiếu Điều 25 K2b ANM về thời hạn 6 giờ khẩn cấp — căn cứ định lượng quan trọng mà V3 có.

---

#### Nhóm 3 — Trách nhiệm trung gian

**Câu 5 (8.5 = 8.5):** Kết quả đồng đều đáng chú ý. Cả hai đều tìm được Điều 18 K3c CNTT — căn cứ then chốt về nghĩa vụ chủ động ngừng cho thuê. V4 thậm chí bổ sung lập luận "luật chuyên ngành áp dụng trước luật chung" — điểm cộng về ưu tiên pháp lý mà V3 chưa có. Đây là trường hợp vector thuần tìm trực tiếp điều khoản đặc thù hiệu quả như graph.

**Câu 6 (7.0 vs 6.5 — chênh +0.5):** V3 nhờ graph tìm thêm được Điều 68 K8 (dù nguồn chưa xác minh nguyên văn); V4 tìm được Điều 14 K2 VT cho nghĩa vụ đại lý nhưng thiếu Điều 41 K3, K5 ANM 2025 để tạo đối trọng về trách nhiệm doanh nghiệp gốc.

---

#### Nhóm 4 — Dữ liệu cá nhân

**Câu 7 (9.0 vs 7.5 — chênh +1.5):** Chênh lệch rõ nhất nhóm này. V3 tìm được Điều 25 K2d ANM 2025 — quy định tường minh nghĩa vụ lưu trữ địa chỉ IP và thời gian sử dụng. V4 có suy luận tinh tế "cấm tiết lộ khác với cấm lưu trữ nội bộ" — điểm sáng về lập luận — nhưng thiếu căn cứ điều khoản cụ thể làm anchor. V3 cũng có bảng điều kiện hợp pháp rõ ràng hơn là điểm tổng hợp tốt nhất trong ba lần chấm.

**Câu 8 (8.5 vs 8.0 — chênh +0.5):** V3 tìm được Điều 22 K2 CNTT làm cầu nối ngoại lệ — lập luận hai tầng (CNTT → ANM) chặt hơn. V4 có Điều 25 K2a ANM với thời hạn 24 giờ — căn cứ chính xác — nhưng lập luận một tầng thay vì hai tầng.

---

#### Nhóm 5 — SIM và danh tính

**Câu 9 (8.0 vs 7.5 — chênh +0.5):** V3 có cấu trúc phân tích ba tầng đầy đủ hơn. V4 thiếu Điều 13 K2k, l, m VT — các căn cứ quan trọng về phạm vi trách nhiệm doanh nghiệp khi vi phạm xảy ra.

**Câu 10 (8.0 vs 7.0 — chênh +1.0):** V3 tìm được Điều 9 K2 CNTT làm anchor cho suy luận "giấy phép kinh doanh thay thế CCCD" và Điều 18 K2 ANM cho trách nhiệm chủ quản IoT — hai bước cụ thể hóa quan trọng. V4 suy luận hợp lý về tiêu chí IoT nhưng không có căn cứ tường minh.

---

#### Nhóm 6 — Hạ tầng thiết yếu

**Câu 11 (8.5 vs 7.5 — chênh +1.0):** Khác biệt chất lượng rõ. V3 tìm được Điều 39 K2g ANM — căn cứ tường minh rằng Bộ CA chỉ có quyền "tham mưu, đề xuất" Thủ tướng khi có tranh chấp liên Bộ, không có quyền ra lệnh đơn phương. V4 suy luận thứ bậc ưu tiên an ninh quốc gia hợp lý nhưng không thể kết luận dứt khoát nếu thiếu điều khoản này. V3 còn bổ sung Điều 47 K3 VT về thẩm quyền giải quyết tranh chấp chia sẻ.

**Câu 12 (8.5 vs 8.0 — chênh +0.5):** V3 tìm được Điều 26 K2b ANM — căn cứ xác định doanh nghiệp chỉ bị xử lý nếu vi phạm quy chuẩn kỹ thuật, không bị xử lý chỉ vì lỗ hổng vô tình chưa thành sự cố. V4 có Điều 11 K2d ANM và Điều 15 K4 ANM tốt nhưng thiếu điều khoản phân biệt mức xử phạt này.

---

#### Nhóm 7 — AI và công nghệ mới

**Câu 13 (8.0 vs 7.5 — chênh +0.5):** V3 trình bày bảng kết luận rõ hơn, phân biệt thiệt hại trực tiếp vs. gián tiếp tường minh hơn. Cả hai đều bỏ sót cơ chế xác định lỗi khi AI chặn nhầm.

**Câu 14 (7.0 = 7.0):** Bằng nhau. Cả hai tìm được các điều khoản tương đương (Điều 7 K2g ANM, Điều 13 K2l VT). Cả hai cùng nhận ra khoảng trống về Luật Giao dịch điện tử và xử lý trung thực. Đây là câu mà nội dung suy luận quyết định chất lượng hơn là retrieval.

---

#### Nhóm 8 — Phạm vi lãnh thổ

**Câu 15 (8.0 vs 7.5 — chênh +0.5):** V3 tìm được Điều 25 K2c ANM về quyền "không cung cấp hoặc ngừng cung cấp dịch vụ" — cơ chế cưỡng chế thực tế khả thi nhất. V4 cũng tìm được điều khoản này nhưng không khai thác sâu bằng; ngoài ra V4 đưa thêm nguyên tắc "bồi hoàn công" không liên quan vào phần suy luận — nhiễu logic.

**Câu 16 (8.0 = 8.0):** Bằng nhau — một trong số ít câu vector thuần đạt ngang graph. V4 tìm được Điều 13 K2đ VT và Điều 15 K4 ANM đầy đủ, bảng kết luận theo tiêu chí rõ, phân loại đúng khoảng trống thực sự vs. suy luận từ nguyên tắc.

---

#### Nhóm 9 — Viễn thông công ích

**Câu 17 (7.5 vs 6.5 — chênh +1.0):** V4 gặp lỗi kỹ thuật nghiêm trọng — nội dung thinking lẫn vào phần answer, làm giảm chất lượng trình bày. V3 tìm được Điều 18 K2 ANM về nghĩa vụ áp dụng biện pháp kỹ thuật phòng ngừa — căn cứ cho lập luận "thiếu dự phòng có thể bị xem là chưa tuân thủ". V4 thiếu cả Điều 30 K4 VT về Quỹ công ích.

**Câu 18 (7.5 vs 7.0 — chênh +0.5):** V3 tìm được Điều 31 K3a VT về nghĩa vụ "hỗ trợ bù đắp chi phí" của Quỹ — căn cứ cụ thể. V4 tìm được Điều 30 K4 và Điều 31 K3a VT — tương đương — nhưng kết luận "doanh nghiệp không được từ chối" thiếu căn cứ trực tiếp hơn (chỉ dựa suy luận nguyên tắc).

---

#### Nhóm 10 — Xung đột thẩm quyền

**Câu 19 (8.5 = 8.5):** Đồng đều xuất sắc — cả hai đều tìm được Điều 39 K2g ANM (quy trình tham mưu → Thủ tướng quyết định) và Điều 69 K1-3 VT. Đây là trường hợp điều khoản cốt lõi được index đủ tốt để vector thuần tìm chính xác không cần graph.

**Câu 20 (7.5 vs 6.5 — chênh +1.0):** V3 tìm được Điều 40 K1 ANM về nghĩa vụ báo cáo sự cố của chủ quản — căn cứ phù hợp hơn Điều 12 K3 (vốn áp dụng cho hệ thống không thuộc danh mục ANQG). V4 chỉ dừng ở Điều 6 K4 và Điều 13 K2d VT — thiếu Điều 41 K3 ANM và Điều 7 K5 ANM về hành vi xâm nhập trái phép, kết luận mỏng hơn hẳn.

---

### Tổng kết so sánh — Phần II Liên luật

#### Phân phối chênh lệch điểm

| Mức chênh | Số câu | Tỷ lệ |
|-----------|--------|-------|
| V3 hơn ≥ 1.5 điểm | 2 câu | 10% |
| V3 hơn 1.0 điểm | 5 câu | 25% |
| V3 hơn 0.5 điểm | 8 câu | 40% |
| Bằng nhau | 5 câu | 25% |
| V4 hơn | 0 câu | 0% |

#### Lỗi đặc trưng phân theo phiên bản

| Pattern lỗi | V3 (Graph+Vector) | V4 (Vector Only) |
|-------------|:-----------------:|:----------------:|
| Trích dẫn graph chưa xác minh nguyên văn | 3 câu | — |
| Bỏ sót điều khoản thẩm quyền phân cấp | — | 4 câu |
| Lỗi pipeline (thinking lẫn output) | — | 2 câu |
| Thiếu cầu nối liên luật (điều khoản dẫn chiếu chéo) | 0 câu | 5 câu |
| Kết luận dứt khoát thái quá thiếu căn cứ | 1 câu | 2 câu |

#### Câu vector thuần đạt ngang hoặc vượt graph

| Câu | Điểm V4 | Lý do V4 không thua |
|-----|---------|---------------------|
| Câu 1 | 7.0 = 7.0 | Giới hạn suy luận, không phải retrieval |
| Câu 5 | 8.5 = 8.5 | Điều khoản đặc thù, index rõ |
| Câu 14 | 7.0 = 7.0 | Khoảng trống thực sự, suy luận quyết định |
| Câu 16 | 8.0 = 8.0 | Câu có anchor từ khóa rõ ràng |
| Câu 19 | 8.5 = 8.5 | Điều khoản cốt lõi được index đủ tốt |

---

## TỔNG KẾT TOÀN BỘ HAI PHẦN

| Phần | V1/V3 (Graph+Vector) | V2/V4 (Vector Only) | Chênh lệch |
|------|:--------------------:|:-------------------:|:----------:|
| Phần I — Đơn luật (30 câu) | 248.0 / 300 | 239.0 / 300 | +9.0 |
| Phần II — Liên luật (20 câu) | 157.5 / 200 | 147.5 / 200 | +10.0 |
| **Tổng cộng (50 câu)** | **405.5 / 500** | **386.5 / 500** | **+19.0** |
| **Trung bình / câu** | **8.11** | **7.73** | **+0.38** |

### Kết luận tổng hợp

**Graph+Vector duy trì ưu thế ổn định +0.38 điểm/câu trên toàn bộ 50 câu.** Ưu thế này không đồng đều — tập trung ở hai loại câu hỏi cụ thể:

**Loại câu hỏi Graph+Vector vượt trội rõ (chênh ≥ 1.0):**
- Xác định thẩm quyền phân cấp đa cơ quan (ai có quyền gì trong chuỗi Thủ tướng → Bộ trưởng → cơ quan chuyên trách)
- Dẫn chiếu chéo liên luật đòi hỏi cầu nối trung gian (CNTT → ANM qua Điều 22 K2)
- Điều khoản xác định chủ thể chịu trách nhiệm khi có nhiều chủ thể tham gia

**Loại câu hỏi Vector Only đủ tốt (chênh 0):**
- Điều khoản cốt lõi được index rõ ràng (Điều 39 K2g ANM — Câu 19)
- Câu hỏi có khoảng trống pháp lý thực sự — chất lượng phụ thuộc suy luận, không phải retrieval
- Điều khoản đặc thù nội dung (Điều 18 K3c CNTT — Câu 5)

**Rủi ro đặc thù của từng phương pháp:**
- **Graph+Vector:** Đôi khi trích dẫn điều khoản từ graph chưa xác minh nguyên văn — cần cơ chế kiểm tra lại.
- **Vector Only:** Lỗi pipeline (thinking lẫn output) xuất hiện 2/20 câu liên luật — cần xử lý ở tầng kỹ thuật. Retrieval miss điều khoản thẩm quyền phân cấp là điểm yếu cấu trúc.

---

*Báo cáo tổng hợp: 50 câu — Phần I (30 câu đơn luật) + Phần II (20 câu liên luật)*  
*V1/V3: Graph + Vector Reasoning | V2/V4: Vector Reasoning Only*