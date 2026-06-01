# Benchmark Report — Hybrid Legal RAG

- Trọng số: semantic **50%** · citation **30%** · keyword **20%**
- Semantic: cosine similarity (`truro7/vn-law-embedding`)
- Citation: recall trên (Điều, khoản) trong `reference`
- Keyword: recall trên content tokens (underthesea, sau khi lọc stopword)

## Tổng quan

| Luật | Câu | Semantic | Citation | Keyword | **Tổng** | Đánh giá |
|---|---:|---:|---:|---:|---:|---|
| Luật An ninh mạng 116/2025/QH15 | 30 | 0.863 | 0.967 | 0.940 | **0.909** | 🟢 Xuất sắc |
| Luật Viễn thông 24/2023/QH15 | 30 | 0.848 | 0.972 | 0.925 | **0.900** | 🟢 Xuất sắc |
| Luật Công nghệ thông tin 65/VBHN-VPQH | 30 | 0.796 | 0.950 | 0.931 | **0.869** | 🟢 Xuất sắc |
| **TOÀN BỘ** | **90** | **0.835** | **0.963** | **0.932** | **0.893** | **🟢 Xuất sắc** |

## Phân tích theo độ khó (toàn bộ)

| Độ khó | Câu | Semantic | Citation | Keyword | **Tổng** |
|---|---:|---:|---:|---:|---:|
| easy | 30 | 0.824 | 0.967 | 0.956 | **0.893** |
| medium | 30 | 0.819 | 1.000 | 0.957 | **0.901** |
| hard | 30 | 0.864 | 0.922 | 0.881 | **0.885** |

## Luật An ninh mạng 116/2025/QH15

### Tổng hợp theo độ khó

| Độ khó | Câu | Semantic | Citation | Keyword | **Tổng** |
|---|---:|---:|---:|---:|---:|
| easy | 10 | 0.815 | 1.000 | 0.911 | **0.890** |
| medium | 10 | 0.845 | 1.000 | 0.958 | **0.914** |
| hard | 10 | 0.929 | 0.900 | 0.950 | **0.925** |

### Chi tiết từng câu

| ID | Độ khó | Reference | Semantic | Citation | Keyword | **Tổng** |
|---|---|---|---:|---:|---:|---:|
| easy_01 | easy | Điều 44, khoản 1 | 0.355 | 1.000 | 1.000 | **0.678** |
| easy_02 | easy | Điều 2, khoản 1 | 0.865 | 1.000 | 1.000 | **0.933** |
| easy_03 | easy | Điều 8, khoản 1 | 0.620 | 1.000 | 0.318 | **0.673** |
| easy_04 | easy | Điều 39, khoản 2 | 0.930 | 1.000 | 1.000 | **0.965** |
| easy_05 | easy | Điều 2, khoản 13 | 0.895 | 1.000 | 1.000 | **0.948** |
| easy_06 | easy | Điều 2, khoản 9 | 0.884 | 1.000 | 1.000 | **0.942** |
| easy_07 | easy | Điều 44, khoản 2 | 0.901 | 1.000 | 0.789 | **0.908** |
| easy_08 | easy | Điều 30, khoản 1, điểm a | 0.924 | 1.000 | 1.000 | **0.962** |
| easy_09 | easy | Điều 2, khoản 5 | 0.871 | 1.000 | 1.000 | **0.936** |
| easy_10 | easy | Điều 29, khoản 1 | 0.903 | 1.000 | 1.000 | **0.952** |
| medium_01 | medium | Điều 8, khoản 1, điểm đ | 0.845 | 1.000 | 0.842 | **0.891** |
| medium_02 | medium | Điều 25, khoản 3 | 0.866 | 1.000 | 1.000 | **0.933** |
| medium_03 | medium | Điều 25, khoản 2, điểm a | 0.726 | 1.000 | 0.967 | **0.856** |
| medium_04 | medium | Điều 6, khoản 1 | 0.920 | 1.000 | 1.000 | **0.960** |
| medium_05 | medium | Điều 10, khoản 4 và 5 | 0.794 | 1.000 | 0.836 | **0.864** |
| medium_06 | medium | Điều 25, khoản 2, điểm b | 0.706 | 1.000 | 0.963 | **0.846** |
| medium_07 | medium | Điều 38, khoản 1 | 0.894 | 1.000 | 1.000 | **0.947** |
| medium_08 | medium | Điều 6, khoản 2 | 0.973 | 1.000 | 1.000 | **0.986** |
| medium_09 | medium | Điều 34, khoản 2 | 0.855 | 1.000 | 1.000 | **0.928** |
| medium_10 | medium | Điều 45, khoản 1 | 0.874 | 1.000 | 0.970 | **0.931** |
| hard_01 | hard | Điều 9, khoản 2 và khoản 4 | 0.904 | 1.000 | 0.985 | **0.949** |
| hard_02 | hard | Điều 39, khoản 2 | 0.909 | 1.000 | 0.983 | **0.951** |
| hard_03 | hard | Điều 7, khoản 1 | 0.963 | 1.000 | 0.956 | **0.973** |
| hard_04 | hard | Điều 5 | 0.967 | 1.000 | 0.975 | **0.979** |
| hard_05 | hard | Điều 41 | 0.907 | 1.000 | 1.000 | **0.953** |
| hard_06 | hard | Điều 26, khoản 2 | 0.926 | 1.000 | 1.000 | **0.963** |
| hard_07 | hard | Điều 37, khoản 2 và 3 | 0.944 | 1.000 | 0.990 | **0.970** |
| hard_08 | hard | Điều 21, khoản 2 và 3 | 0.933 | 0.000 | 0.968 | **0.660** |
| hard_09 | hard | Điều 2, khoản 14 và 15 | 0.916 | 1.000 | 0.647 | **0.887** |
| hard_10 | hard | Điều 40, khoản 1 và 2 | 0.921 | 1.000 | 1.000 | **0.960** |

### 5 câu điểm thấp nhất (cần review)

- **hard_08** (hard) — tổng `0.660` · sem `0.933` · cit `0.000` · kw `0.968`
  > Câu hỏi: ** Theo Luật An ninh mạng số 116/2025/QH15, đấu tranh bảo vệ an ninh mạng được thực hiện trong những tình huống nào và ai có thẩm quyền chủ trì?
  > Citation thiếu: Điều 21 khoản 2
- **easy_03** (easy) — tổng `0.673` · sem `0.620` · cit `1.000` · kw `0.318`
  > Câu hỏi: ** Hệ thống thông tin được phân thành bao nhiêu cấp độ theo Luật An ninh mạng số 116/2025/QH15?
- **easy_01** (easy) — tổng `0.678` · sem `0.355` · cit `1.000` · kw `1.000`
  > Câu hỏi: ** Luật An ninh mạng số 116/2025/QH15 có hiệu lực thi hành từ ngày nào?
- **medium_06** (medium) — tổng `0.846` · sem `0.706` · cit `1.000` · kw `0.963`
  > Câu hỏi: ** Theo Luật An ninh mạng số 116/2025/QH15, doanh nghiệp yêu cầu phải ngăn chặn hoặc xóa thông tin vi phạm trong thời hạn bao lâu kể từ khi có yêu cầu? Trường hợp khẩn cấp thì sao?
- **medium_03** (medium) — tổng `0.856` · sem `0.726` · cit `1.000` · kw `0.967`
  > Câu hỏi: ** Theo Luật An ninh mạng số 116/2025/QH15, khi doanh nghiệp nhận được yêu cầu cung cấp thông tin người dùng từ lực lượng chuyên trách bảo vệ an ninh mạng thuộc Bộ Công an, thời hạn tối đa để thực hiệ

## Luật Viễn thông 24/2023/QH15

### Tổng hợp theo độ khó

| Độ khó | Câu | Semantic | Citation | Keyword | **Tổng** |
|---|---:|---:|---:|---:|---:|
| easy | 10 | 0.862 | 1.000 | 0.991 | **0.929** |
| medium | 10 | 0.823 | 1.000 | 0.946 | **0.900** |
| hard | 10 | 0.858 | 0.917 | 0.837 | **0.872** |

### Chi tiết từng câu

| ID | Độ khó | Reference | Semantic | Citation | Keyword | **Tổng** |
|---|---|---|---:|---:|---:|---:|
| Q001 | easy | Điều 72 | 0.684 | 1.000 | 0.955 | **0.833** |
| Q002 | easy | Khoản 1 Điều 3 | 0.856 | 1.000 | 1.000 | **0.928** |
| Q003 | easy | Khoản 34 Điều 3 | 0.905 | 1.000 | 0.957 | **0.944** |
| Q004 | easy | Khoản 26 Điều 3 | 0.906 | 1.000 | 1.000 | **0.953** |
| Q005 | easy | Khoản 29 Điều 3 | 0.893 | 1.000 | 1.000 | **0.946** |
| Q006 | easy | Điều 2 | 0.788 | 1.000 | 1.000 | **0.894** |
| Q007 | easy | Khoản 15 Điều 3 | 0.922 | 1.000 | 1.000 | **0.961** |
| Q008 | easy | Điểm e Khoản 1 Điều 15 | 0.920 | 1.000 | 1.000 | **0.960** |
| Q009 | easy | Khoản 2 Điều 69 | 0.923 | 1.000 | 1.000 | **0.961** |
| Q010 | easy | Điều 7 | 0.819 | 1.000 | 1.000 | **0.910** |
| Q011 | medium | Khoản 7 Điều 3 | 0.876 | 1.000 | 0.903 | **0.919** |
| Q012 | medium | Khoản 1 Điều 22 | 0.871 | 1.000 | 1.000 | **0.936** |
| Q013 | medium | Khoản 4 Điều 6 | 0.737 | 1.000 | 0.978 | **0.864** |
| Q014 | medium | Điều 23 | 0.660 | 1.000 | 0.951 | **0.820** |
| Q015 | medium | Khoản 4 Điều 15 | 0.841 | 1.000 | 0.962 | **0.913** |
| Q016 | medium | Khoản 25 Điều 3, Điều 23 | 0.775 | 1.000 | 0.783 | **0.844** |
| Q017 | medium | Điều 57 | 0.800 | 1.000 | 0.957 | **0.891** |
| Q018 | medium | Khoản 10, 11 Điều 3 | 0.930 | 1.000 | 0.970 | **0.959** |
| Q019 | medium | Khoản 3 Điều 60 | 0.844 | 1.000 | 1.000 | **0.922** |
| Q020 | medium | Khoản 6, 7 Điều 5 | 0.891 | 1.000 | 0.952 | **0.936** |
| Q021 | hard | Điều 17 | 0.628 | 1.000 | 0.841 | **0.782** |
| Q022 | hard | Điều 21 | 0.886 | 1.000 | 0.857 | **0.915** |
| Q023 | hard | Điều 11 | 0.857 | 1.000 | 0.794 | **0.887** |
| Q024 | hard | Khoản 6, 7 Điều 65 | 0.844 | 1.000 | 0.857 | **0.894** |
| Q025 | hard | Điều 73 | 0.898 | 1.000 | 0.776 | **0.904** |
| Q026 | hard | Điều 16, Điều 17 | 0.933 | 1.000 | 1.000 | **0.966** |
| Q027 | hard | Điều 5 | 0.824 | 1.000 | 0.987 | **0.909** |
| Q028 | hard | Điểm h Khoản 2, Khoản 4 Điều 13 | 0.869 | 0.500 | 0.875 | **0.760** |
| Q029 | hard | Khoản 8, 12 Điều 3; Khoản 2 Điều 20; Điều 28 | 0.892 | 0.667 | 0.670 | **0.780** |
| Q030 | hard | Điều 62 | 0.953 | 1.000 | 0.717 | **0.920** |

### 5 câu điểm thấp nhất (cần review)

- **Q028** (hard) — tổng `0.760` · sem `0.869` · cit `0.500` · kw `0.875`
  > Câu hỏi: ** Luật Viễn thông 2023 quy định gì về việc thuê bao viễn thông được giữ nguyên số thuê bao khi đổi nhà mạng? Đây là nghĩa vụ của ai?
  > Citation thiếu: Điều 13 khoản 4
- **Q029** (hard) — tổng `0.780` · sem `0.892` · cit `0.667` · kw `0.670`
  > Câu hỏi: ** Phân tích sự khác biệt giữa dịch vụ viễn thông cơ bản trên Internet và dịch vụ ứng dụng viễn thông. Tại sao sự phân biệt này quan trọng về mặt pháp lý?
  > Citation thiếu: Điều 28, Điều 3 khoản 2
- **Q021** (hard) — tổng `0.782` · sem `0.628` · cit `1.000` · kw `0.841`
  > Câu hỏi: ** Phân tích các nghĩa vụ bổ sung của doanh nghiệp viễn thông có vị trí thống lĩnh thị trường so với doanh nghiệp viễn thông thông thường.
- **Q014** (medium) — tổng `0.820` · sem `0.660` · cit `1.000` · kw `0.951`
  > Câu hỏi: ** Điều kiện để doanh nghiệp viễn thông ngừng kinh doanh một phần hoặc toàn bộ dịch vụ là gì?
- **Q001** (easy) — tổng `0.833` · sem `0.684` · cit `1.000` · kw `0.955`
  > Câu hỏi: ** Luật Viễn thông số 24/2023/QH15 có hiệu lực thi hành từ ngày nào?

## Luật Công nghệ thông tin 65/VBHN-VPQH

### Tổng hợp theo độ khó

| Độ khó | Câu | Semantic | Citation | Keyword | **Tổng** |
|---|---:|---:|---:|---:|---:|
| easy | 10 | 0.795 | 0.900 | 0.968 | **0.861** |
| medium | 10 | 0.788 | 1.000 | 0.969 | **0.888** |
| hard | 10 | 0.803 | 0.950 | 0.857 | **0.858** |

### Chi tiết từng câu

| ID | Độ khó | Reference | Semantic | Citation | Keyword | **Tổng** |
|---|---|---|---:|---:|---:|---:|
| Q001 | easy | Điều 78 | 0.289 | 1.000 | 1.000 | **0.644** |
| Q002 | easy | Điều 4, khoản 2 | 0.878 | 1.000 | 1.000 | **0.939** |
| Q003 | easy | Điều 4, khoản 15 | 0.874 | 1.000 | 1.000 | **0.937** |
| Q004 | easy | Điều 7, khoản 1 | 0.941 | 1.000 | 0.833 | **0.937** |
| Q005 | easy | Điều 4, khoản 16 | 0.936 | 1.000 | 1.000 | **0.968** |
| Q006 | easy | Điều 2 | 0.855 | 1.000 | 1.000 | **0.927** |
| Q007 | easy | Điều 4, khoản 17 | 0.897 | 1.000 | 1.000 | **0.949** |
| Q008 | easy | Điều 4, khoản 18 | 0.793 | 1.000 | 1.000 | **0.896** |
| Q009 | easy | Điều 75, khoản 2 | 0.693 | 0.000 | 0.842 | **0.515** |
| Q010 | easy | Điều 4, khoản 7 | 0.798 | 1.000 | 1.000 | **0.899** |
| Q011 | medium | Điều 16, khoản 4 | 0.785 | 1.000 | 1.000 | **0.892** |
| Q012 | medium | Điều 9, khoản 2 | 0.699 | 1.000 | 1.000 | **0.849** |
| Q013 | medium | Điều 55, khoản 2 | 0.940 | 1.000 | 1.000 | **0.970** |
| Q014 | medium | Điều 14, khoản 1 | 0.678 | 1.000 | 1.000 | **0.839** |
| Q015 | medium | Điều 71 | 0.805 | 1.000 | 0.860 | **0.875** |
| Q016 | medium | Điều 9, khoản 4 | 0.905 | 1.000 | 1.000 | **0.953** |
| Q017 | medium | Điều 69, khoản 2 | 0.874 | 1.000 | 0.880 | **0.913** |
| Q018 | medium | Điều 41, khoản 3 | 0.561 | 1.000 | 1.000 | **0.780** |
| Q019 | medium | Điều 17, khoản 2 | 0.885 | 1.000 | 0.963 | **0.935** |
| Q020 | medium | Điều 63, khoản 1 | 0.748 | 1.000 | 0.982 | **0.870** |
| Q021 | hard | Điều 3 | 0.609 | 1.000 | 0.875 | **0.780** |
| Q022 | hard | Điều 12, khoản 2 | 0.837 | 1.000 | 0.970 | **0.913** |
| Q023 | hard | Phần đầu văn bản hợp nhất | 0.710 | 1.000 | 0.378 | **0.731** |
| Q024 | hard | Điều 68 | 0.961 | 1.000 | 0.966 | **0.974** |
| Q025 | hard | Điều 42, khoản 4-5; Điều 43 | 0.834 | 0.500 | 0.750 | **0.717** |
| Q026 | hard | Điều 61, khoản 3 | 0.800 | 1.000 | 0.933 | **0.887** |
| Q027 | hard | Điều 73 | 0.895 | 1.000 | 0.980 | **0.944** |
| Q028 | hard | Điều 72, khoản 2 | 0.612 | 1.000 | 1.000 | **0.806** |
| Q029 | hard | Điều 74 | 0.851 | 1.000 | 0.980 | **0.922** |
| Q030 | hard | Điều 15, khoản 4-5; Điều 12 | 0.923 | 1.000 | 0.734 | **0.908** |

### 5 câu điểm thấp nhất (cần review)

- **Q009** (easy) — tổng `0.515` · sem `0.693` · cit `0.000` · kw `0.842`
  > Câu hỏi: ** Theo Luật CNTT, tranh chấp về công nghệ thông tin được giải quyết như thế nào?
  > Citation thiếu: Điều 75 khoản 2
- **Q001** (easy) — tổng `0.644` · sem `0.289` · cit `1.000` · kw `1.000`
  > Câu hỏi: ** Luật Công nghệ thông tin số 67/2006/QH11 có hiệu lực thi hành từ ngày nào?
- **Q025** (hard) — tổng `0.717` · sem `0.834` · cit `0.500` · kw `0.750`
  > Câu hỏi: ** Theo Luật CNTT, cơ sở đào tạo nhân lực CNTT được hưởng những ưu đãi gì? Nhà nước có chính sách hỗ trợ gì đối với giáo viên, sinh viên, học sinh trong vấn đề tiếp cận CNTT?
  > Citation thiếu: Điều 43
- **Q023** (hard) — tổng `0.731` · sem `0.710` · cit `1.000` · kw `0.378`
  > Câu hỏi: ** Luật CNTT gốc (67/2006/QH11) đã được sửa đổi, bổ sung bởi những luật nào? Hãy liệt kê đầy đủ tên luật, số hiệu, ngày ban hành và ngày có hiệu lực.
- **Q021** (hard) — tổng `0.780` · sem `0.609` · cit `1.000` · kw `0.875`
  > Câu hỏi: ** Trong trường hợp có sự khác nhau giữa Luật CNTT với quy định của luật khác về cùng một vấn đề liên quan đến hoạt động ứng dụng và phát triển CNTT, thì áp dụng quy định nào? Quy tắc này có ngoại lệ 
