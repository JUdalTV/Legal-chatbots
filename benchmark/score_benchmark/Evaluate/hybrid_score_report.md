# Benchmark Report — Hybrid Legal RAG

- Trọng số: semantic **50%** · citation **30%** · keyword **20%**
- Semantic: cosine similarity (`truro7/vn-law-embedding`)
- Citation: recall trên (Điều, khoản) trong `reference`
- Keyword: recall trên content tokens (underthesea, sau khi lọc stopword)

## Tổng quan

| Luật | Câu | Semantic | Citation | Keyword | **Tổng** | Đánh giá |
|---|---:|---:|---:|---:|---:|---|
| Luật An ninh mạng 116/2025/QH15 | 30 | 0.913 | 0.933 | 0.922 | **0.921** | 🟢 Xuất sắc |
| Luật Viễn thông 24/2023/QH15 | 30 | 0.900 | 0.878 | 0.828 | **0.879** | 🟢 Xuất sắc |
| Luật Công nghệ thông tin 65/VBHN-VPQH | 30 | 0.811 | 0.933 | 0.891 | **0.864** | 🟢 Xuất sắc |
| **TOÀN BỘ** | **90** | **0.875** | **0.915** | **0.880** | **0.888** | **🟢 Xuất sắc** |

## Phân tích theo độ khó (toàn bộ)

| Độ khó | Câu | Semantic | Citation | Keyword | **Tổng** |
|---|---:|---:|---:|---:|---:|
| easy | 30 | 0.860 | 0.933 | 0.950 | **0.900** |
| medium | 30 | 0.888 | 0.978 | 0.884 | **0.914** |
| hard | 30 | 0.876 | 0.833 | 0.807 | **0.849** |

## Luật An ninh mạng 116/2025/QH15

### Tổng hợp theo độ khó

| Độ khó | Câu | Semantic | Citation | Keyword | **Tổng** |
|---|---:|---:|---:|---:|---:|
| easy | 10 | 0.909 | 1.000 | 0.977 | **0.950** |
| medium | 10 | 0.906 | 1.000 | 0.895 | **0.932** |
| hard | 10 | 0.923 | 0.800 | 0.892 | **0.880** |

### Chi tiết từng câu

| ID | Độ khó | Reference | Semantic | Citation | Keyword | **Tổng** |
|---|---|---|---:|---:|---:|---:|
| easy_01 | easy | Điều 44, khoản 1 | 0.942 | 1.000 | 1.000 | **0.971** |
| easy_02 | easy | Điều 2, khoản 1 | 0.941 | 1.000 | 1.000 | **0.970** |
| easy_03 | easy | Điều 8, khoản 1 | 0.720 | 1.000 | 1.000 | **0.860** |
| easy_04 | easy | Điều 39, khoản 2 | 0.939 | 1.000 | 0.889 | **0.947** |
| easy_05 | easy | Điều 2, khoản 13 | 0.933 | 1.000 | 1.000 | **0.966** |
| easy_06 | easy | Điều 2, khoản 9 | 0.886 | 1.000 | 1.000 | **0.943** |
| easy_07 | easy | Điều 44, khoản 2 | 0.949 | 1.000 | 0.885 | **0.951** |
| easy_08 | easy | Điều 30, khoản 1, điểm a | 0.912 | 1.000 | 1.000 | **0.956** |
| easy_09 | easy | Điều 2, khoản 5 | 0.952 | 1.000 | 1.000 | **0.976** |
| easy_10 | easy | Điều 29, khoản 1 | 0.916 | 1.000 | 1.000 | **0.958** |
| medium_01 | medium | Điều 8, khoản 1, điểm đ | 0.904 | 1.000 | 0.625 | **0.877** |
| medium_02 | medium | Điều 25, khoản 3 | 0.816 | 1.000 | 1.000 | **0.908** |
| medium_03 | medium | Điều 25, khoản 2, điểm a | 0.851 | 1.000 | 0.969 | **0.919** |
| medium_04 | medium | Điều 6, khoản 1 | 0.923 | 1.000 | 1.000 | **0.961** |
| medium_05 | medium | Điều 10, khoản 4 và 5 | 0.911 | 1.000 | 0.960 | **0.948** |
| medium_06 | medium | Điều 25, khoản 2, điểm b | 0.946 | 1.000 | 1.000 | **0.973** |
| medium_07 | medium | Điều 38, khoản 1 | 0.925 | 1.000 | 1.000 | **0.963** |
| medium_08 | medium | Điều 6, khoản 2 | 0.964 | 1.000 | 0.981 | **0.978** |
| medium_09 | medium | Điều 34, khoản 2 | 0.918 | 1.000 | 0.955 | **0.950** |
| medium_10 | medium | Điều 45, khoản 1 | 0.901 | 1.000 | 0.464 | **0.843** |
| hard_01 | hard | Điều 9, khoản 2 và khoản 4 | 0.928 | 1.000 | 0.948 | **0.954** |
| hard_02 | hard | Điều 39, khoản 2 | 0.904 | 1.000 | 0.976 | **0.947** |
| hard_03 | hard | Điều 7, khoản 1 | 0.943 | 1.000 | 0.989 | **0.969** |
| hard_04 | hard | Điều 5 | 0.937 | 1.000 | 0.986 | **0.966** |
| hard_05 | hard | Điều 41 | 0.911 | 1.000 | 0.955 | **0.946** |
| hard_06 | hard | Điều 26, khoản 2 | 0.972 | 1.000 | 1.000 | **0.986** |
| hard_07 | hard | Điều 37, khoản 2 và 3 | 0.890 | 0.000 | 0.756 | **0.596** |
| hard_08 | hard | Điều 21, khoản 2 và 3 | 0.877 | 0.000 | 0.467 | **0.532** |
| hard_09 | hard | Điều 2, khoản 14 và 15 | 0.924 | 1.000 | 0.909 | **0.944** |
| hard_10 | hard | Điều 40, khoản 1 và 2 | 0.942 | 1.000 | 0.939 | **0.959** |

### 5 câu điểm thấp nhất (cần review)

- **hard_08** (hard) — tổng `0.532` · sem `0.877` · cit `0.000` · kw `0.467`
  > Câu hỏi: Theo Luật An ninh mạng số 116/2025/QH15, đấu tranh bảo vệ an ninh mạng được thực hiện trong những tình huống nào và ai có thẩm quyền chủ trì?
  > Citation thiếu: Điều 21 khoản 2
- **hard_07** (hard) — tổng `0.596` · sem `0.890` · cit `0.000` · kw `0.756`
  > Câu hỏi: Theo Luật An ninh mạng số 116/2025/QH15, việc nâng cao năng lực tự chủ về an ninh mạng được triển khai theo những biện pháp và cơ chế đầu tư cụ thể nào?
  > Citation thiếu: Điều 37 khoản 2
- **medium_10** (medium) — tổng `0.843` · sem `0.901` · cit `1.000` · kw `0.464`
  > Câu hỏi: Theo Luật An ninh mạng số 116/2025/QH15, hệ thống thông tin đã được xác định cấp độ theo Luật An toàn thông tin mạng cũ thì phải xử lý như thế nào trong giai đoạn chuyển tiếp?
- **easy_03** (easy) — tổng `0.860` · sem `0.720` · cit `1.000` · kw `1.000`
  > Câu hỏi: Hệ thống thông tin được phân thành bao nhiêu cấp độ theo Luật An ninh mạng số 116/2025/QH15?
- **medium_01** (medium) — tổng `0.877` · sem `0.904` · cit `1.000` · kw `0.625`
  > Câu hỏi: Hệ thống thông tin cấp độ 5 có đặc điểm gì theo Luật An ninh mạng số 116/2025/QH15?

## Luật Viễn thông 24/2023/QH15

### Tổng hợp theo độ khó

| Độ khó | Câu | Semantic | Citation | Keyword | **Tổng** |
|---|---:|---:|---:|---:|---:|
| easy | 10 | 0.898 | 0.900 | 0.921 | **0.903** |
| medium | 10 | 0.907 | 0.933 | 0.831 | **0.900** |
| hard | 10 | 0.896 | 0.800 | 0.732 | **0.834** |

### Chi tiết từng câu

| ID | Độ khó | Reference | Semantic | Citation | Keyword | **Tổng** |
|---|---|---|---:|---:|---:|---:|
| Q001 | easy | Điều 72 | 0.754 | 1.000 | 0.500 | **0.777** |
| Q002 | easy | Khoản 1 Điều 3 | 0.937 | 1.000 | 1.000 | **0.968** |
| Q003 | easy | Khoản 34 Điều 3 | 0.956 | 1.000 | 0.950 | **0.968** |
| Q004 | easy | Khoản 26 Điều 3 | 0.916 | 1.000 | 1.000 | **0.958** |
| Q005 | easy | Khoản 29 Điều 3 | 0.942 | 1.000 | 0.917 | **0.954** |
| Q006 | easy | Điều 2 | 0.684 | 0.000 | 0.917 | **0.525** |
| Q007 | easy | Khoản 15 Điều 3 | 0.950 | 1.000 | 1.000 | **0.975** |
| Q008 | easy | Điểm e Khoản 1 Điều 15 | 0.946 | 1.000 | 1.000 | **0.973** |
| Q009 | easy | Khoản 2 Điều 69 | 0.925 | 1.000 | 1.000 | **0.962** |
| Q010 | easy | Điều 7 | 0.966 | 1.000 | 0.923 | **0.968** |
| Q011 | medium | Khoản 7 Điều 3 | 0.943 | 1.000 | 0.903 | **0.952** |
| Q012 | medium | Khoản 1 Điều 22 | 0.926 | 1.000 | 1.000 | **0.963** |
| Q013 | medium | Khoản 4 Điều 6 | 0.909 | 1.000 | 0.898 | **0.934** |
| Q014 | medium | Điều 23 | 0.919 | 1.000 | 0.868 | **0.933** |
| Q015 | medium | Khoản 4 Điều 15 | 0.904 | 1.000 | 0.784 | **0.909** |
| Q016 | medium | Khoản 25 Điều 3, Điều 23 | 0.834 | 0.667 | 0.500 | **0.717** |
| Q017 | medium | Điều 57 | 0.909 | 1.000 | 0.974 | **0.950** |
| Q018 | medium | Khoản 10, 11 Điều 3 | 0.893 | 0.667 | 0.517 | **0.750** |
| Q019 | medium | Khoản 3 Điều 60 | 0.961 | 1.000 | 0.895 | **0.959** |
| Q020 | medium | Khoản 6, 7 Điều 5 | 0.874 | 1.000 | 0.971 | **0.931** |
| Q021 | hard | Điều 17 | 0.918 | 1.000 | 0.810 | **0.921** |
| Q022 | hard | Điều 21 | 0.817 | 1.000 | 0.525 | **0.814** |
| Q023 | hard | Điều 11 | 0.847 | 1.000 | 0.654 | **0.854** |
| Q024 | hard | Khoản 6, 7 Điều 65 | 0.925 | 0.667 | 0.881 | **0.838** |
| Q025 | hard | Điều 73 | 0.892 | 1.000 | 0.756 | **0.897** |
| Q026 | hard | Điều 16, Điều 17 | 0.982 | 0.500 | 0.968 | **0.835** |
| Q027 | hard | Điều 5 | 0.855 | 1.000 | 0.806 | **0.889** |
| Q028 | hard | Điểm h Khoản 2, Khoản 4 Điều 13 | 0.881 | 0.500 | 0.639 | **0.718** |
| Q029 | hard | Khoản 8, 12 Điều 3; Khoản 2 Điều 20; Điều 28 | 0.892 | 0.333 | 0.607 | **0.668** |
| Q030 | hard | Điều 62 | 0.948 | 1.000 | 0.676 | **0.909** |

### 5 câu điểm thấp nhất (cần review)

- **Q006** (easy) — tổng `0.525` · sem `0.684` · cit `0.000` · kw `0.917`
  > Câu hỏi: Luật Viễn thông 2023 áp dụng đối với những đối tượng nào?
  > Citation thiếu: Điều 2
- **Q029** (hard) — tổng `0.668` · sem `0.892` · cit `0.333` · kw `0.607`
  > Câu hỏi: Phân tích sự khác biệt giữa dịch vụ viễn thông cơ bản trên Internet và dịch vụ ứng dụng viễn thông. Tại sao sự phân biệt này quan trọng về mặt pháp lý?
  > Citation thiếu: Điều 20, Điều 20 khoản 2, Điều 3 khoản 12, Điều 3 khoản 2
- **Q016** (medium) — tổng `0.717` · sem `0.834` · cit `0.667` · kw `0.500`
  > Câu hỏi: Phương tiện thiết yếu trong viễn thông được hiểu như thế nào và tại sao nó quan trọng?
  > Citation thiếu: Điều 23
- **Q028** (hard) — tổng `0.718` · sem `0.881` · cit `0.500` · kw `0.639`
  > Câu hỏi: Luật Viễn thông 2023 quy định gì về việc thuê bao viễn thông được giữ nguyên số thuê bao khi đổi nhà mạng? Đây là nghĩa vụ của ai?
  > Citation thiếu: Điều 13 khoản 4
- **Q018** (medium) — tổng `0.750` · sem `0.893` · cit `0.667` · kw `0.517`
  > Câu hỏi: Dịch vụ điện toán đám mây được định nghĩa như thế nào trong Luật Viễn thông 2023?
  > Citation thiếu: Điều 3 khoản 10

## Luật Công nghệ thông tin 65/VBHN-VPQH

### Tổng hợp theo độ khó

| Độ khó | Câu | Semantic | Citation | Keyword | **Tổng** |
|---|---:|---:|---:|---:|---:|
| easy | 10 | 0.774 | 0.900 | 0.953 | **0.848** |
| medium | 10 | 0.850 | 1.000 | 0.924 | **0.910** |
| hard | 10 | 0.808 | 0.900 | 0.797 | **0.833** |

### Chi tiết từng câu

| ID | Độ khó | Reference | Semantic | Citation | Keyword | **Tổng** |
|---|---|---|---:|---:|---:|---:|
| Q001 | easy | Điều 78 | 0.588 | 1.000 | 0.917 | **0.777** |
| Q002 | easy | Điều 4, khoản 2 | 0.856 | 1.000 | 0.857 | **0.899** |
| Q003 | easy | Điều 4, khoản 15 | 0.830 | 1.000 | 1.000 | **0.915** |
| Q004 | easy | Điều 7, khoản 1 | 0.846 | 1.000 | 1.000 | **0.923** |
| Q005 | easy | Điều 4, khoản 16 | 0.852 | 1.000 | 1.000 | **0.926** |
| Q006 | easy | Điều 2 | 0.737 | 0.000 | 0.917 | **0.552** |
| Q007 | easy | Điều 4, khoản 17 | 0.881 | 1.000 | 1.000 | **0.941** |
| Q008 | easy | Điều 4, khoản 18 | 0.826 | 1.000 | 1.000 | **0.913** |
| Q009 | easy | Điều 75, khoản 2 | 0.487 | 1.000 | 0.909 | **0.725** |
| Q010 | easy | Điều 4, khoản 7 | 0.841 | 1.000 | 0.929 | **0.906** |
| Q011 | medium | Điều 16, khoản 4 | 0.855 | 1.000 | 1.000 | **0.927** |
| Q012 | medium | Điều 9, khoản 2 | 0.943 | 1.000 | 1.000 | **0.972** |
| Q013 | medium | Điều 55, khoản 2 | 0.919 | 1.000 | 1.000 | **0.960** |
| Q014 | medium | Điều 14, khoản 1 | 0.636 | 1.000 | 0.958 | **0.810** |
| Q015 | medium | Điều 71 | 0.810 | 1.000 | 0.625 | **0.830** |
| Q016 | medium | Điều 9, khoản 4 | 0.847 | 1.000 | 1.000 | **0.924** |
| Q017 | medium | Điều 69, khoản 2 | 0.901 | 1.000 | 0.941 | **0.939** |
| Q018 | medium | Điều 41, khoản 3 | 0.954 | 1.000 | 1.000 | **0.977** |
| Q019 | medium | Điều 17, khoản 2 | 0.825 | 1.000 | 0.739 | **0.860** |
| Q020 | medium | Điều 63, khoản 1 | 0.810 | 1.000 | 0.977 | **0.900** |
| Q021 | hard | Điều 3 | 0.756 | 1.000 | 0.905 | **0.859** |
| Q022 | hard | Điều 12, khoản 2 | 0.846 | 1.000 | 0.970 | **0.917** |
| Q023 | hard | Phần đầu văn bản hợp nhất | 0.453 | 1.000 | 0.375 | **0.601** |
| Q024 | hard | Điều 68 | 0.898 | 1.000 | 0.771 | **0.903** |
| Q025 | hard | Điều 42, khoản 4-5; Điều 43 | 0.749 | 0.000 | 0.525 | **0.480** |
| Q026 | hard | Điều 61, khoản 3 | 0.832 | 1.000 | 0.929 | **0.902** |
| Q027 | hard | Điều 73 | 0.922 | 1.000 | 0.820 | **0.925** |
| Q028 | hard | Điều 72, khoản 2 | 0.886 | 1.000 | 0.976 | **0.938** |
| Q029 | hard | Điều 74 | 0.886 | 1.000 | 0.882 | **0.919** |
| Q030 | hard | Điều 15, khoản 4-5; Điều 12 | 0.852 | 1.000 | 0.816 | **0.889** |

### 5 câu điểm thấp nhất (cần review)

- **Q025** (hard) — tổng `0.480` · sem `0.749` · cit `0.000` · kw `0.525`
  > Câu hỏi: Theo Luật CNTT, cơ sở đào tạo nhân lực CNTT được hưởng những ưu đãi gì? Nhà nước có chính sách hỗ trợ gì đối với giáo viên, sinh viên, học sinh trong vấn đề tiếp cận CNTT?
  > Citation thiếu: Điều 42 khoản 4, Điều 43
- **Q006** (easy) — tổng `0.552` · sem `0.737` · cit `0.000` · kw `0.917`
  > Câu hỏi: Luật CNTT áp dụng đối với những đối tượng nào?
  > Citation thiếu: Điều 2
- **Q023** (hard) — tổng `0.601` · sem `0.453` · cit `1.000` · kw `0.375`
  > Câu hỏi: Luật CNTT gốc (67/2006/QH11) đã được sửa đổi, bổ sung bởi những luật nào? Hãy liệt kê đầy đủ tên luật, số hiệu, ngày ban hành và ngày có hiệu lực.
- **Q009** (easy) — tổng `0.725` · sem `0.487` · cit `1.000` · kw `0.909`
  > Câu hỏi: Theo Luật CNTT, tranh chấp về công nghệ thông tin được giải quyết như thế nào?
- **Q001** (easy) — tổng `0.777` · sem `0.588` · cit `1.000` · kw `0.917`
  > Câu hỏi: Luật Công nghệ thông tin số 67/2006/QH11 có hiệu lực thi hành từ ngày nào?
