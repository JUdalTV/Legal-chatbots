# Vector-only RAG Benchmark Score

- Vector answers: `benchmark/score_benchmark/vector`
- Groundtruth: `benchmark/score_benchmark/Evaluate/Dap_an_90_cau_hoi_groundtruth.md`
- Total rows: **90**
- Weights: semantic **50%**, citation **30%**, keyword **20%**

## Overview

| Scope | Questions | Semantic | Citation | Keyword | Overall | Grade |
|---|---:|---:|---:|---:|---:|---|
| Luật An ninh mạng 116/2025/QH15 | 30 | 0.881 | 0.967 | 0.917 | **0.914** | 🟢 Xuất sắc |
| Luật Viễn thông 24/2023/QH15 | 30 | 0.883 | 0.911 | 0.868 | **0.888** | 🟢 Xuất sắc |
| Luật Công nghệ thông tin 65/VBHN-VPQH | 30 | 0.844 | 0.917 | 0.880 | **0.873** | 🟢 Xuất sắc |
| **ALL** | **90** | **0.869** | **0.931** | **0.888** | **0.892** | **🟢 Xuất sắc** |

## By Difficulty

| Difficulty | Questions | Semantic | Citation | Keyword | Overall |
|---|---:|---:|---:|---:|---:|
| easy | 30 | 0.876 | 0.900 | 0.920 | **0.892** |
| medium | 30 | 0.848 | 0.978 | 0.897 | **0.896** |
| hard | 30 | 0.884 | 0.917 | 0.849 | **0.887** |

## Luật An ninh mạng 116/2025/QH15

| Difficulty | Questions | Semantic | Citation | Keyword | Overall |
|---|---:|---:|---:|---:|---:|
| easy | 10 | 0.864 | 0.900 | 0.915 | **0.885** |
| medium | 10 | 0.843 | 1.000 | 0.893 | **0.900** |
| hard | 10 | 0.936 | 1.000 | 0.941 | **0.956** |

### Details

| No. | ID | Difficulty | Reference | Semantic | Citation | Keyword | Overall |
|---:|---|---|---|---:|---:|---:|---:|
| 1 | easy_01 | easy | Điều 44, khoản 1 | 0.393 | 1.000 | 1.000 | **0.697** |
| 2 | easy_02 | easy | Điều 2, khoản 1 | 0.990 | 1.000 | 1.000 | **0.995** |
| 3 | easy_03 | easy | Điều 8, khoản 1 | 0.667 | 1.000 | 0.500 | **0.734** |
| 4 | easy_04 | easy | Điều 39, khoản 2 | 0.978 | 1.000 | 0.917 | **0.972** |
| 5 | easy_05 | easy | Điều 2, khoản 13 | 0.954 | 1.000 | 1.000 | **0.977** |
| 6 | easy_06 | easy | Điều 2, khoản 9 | 0.972 | 0.000 | 1.000 | **0.686** |
| 7 | easy_07 | easy | Điều 44, khoản 2 | 0.895 | 1.000 | 0.737 | **0.895** |
| 8 | easy_08 | easy | Điều 30, khoản 1, điểm a | 0.925 | 1.000 | 1.000 | **0.963** |
| 9 | easy_09 | easy | Điều 2, khoản 5 | 0.926 | 1.000 | 1.000 | **0.963** |
| 10 | easy_10 | easy | Điều 29, khoản 1 | 0.935 | 1.000 | 1.000 | **0.967** |
| 11 | medium_01 | medium | Điều 8, khoản 1, điểm đ | 0.854 | 1.000 | 0.789 | **0.885** |
| 12 | medium_02 | medium | Điều 25, khoản 3 | 0.888 | 1.000 | 1.000 | **0.944** |
| 13 | medium_03 | medium | Điều 25, khoản 2, điểm a | 0.663 | 1.000 | 0.733 | **0.778** |
| 14 | medium_04 | medium | Điều 6, khoản 1 | 0.939 | 1.000 | 1.000 | **0.970** |
| 15 | medium_05 | medium | Điều 10, khoản 4 và 5 | 0.790 | 1.000 | 0.527 | **0.800** |
| 16 | medium_06 | medium | Điều 25, khoản 2, điểm b | 0.665 | 1.000 | 0.963 | **0.825** |
| 17 | medium_07 | medium | Điều 38, khoản 1 | 0.927 | 1.000 | 0.950 | **0.953** |
| 18 | medium_08 | medium | Điều 6, khoản 2 | 0.986 | 1.000 | 1.000 | **0.993** |
| 19 | medium_09 | medium | Điều 34, khoản 2 | 0.802 | 1.000 | 1.000 | **0.901** |
| 20 | medium_10 | medium | Điều 45, khoản 1 | 0.922 | 1.000 | 0.970 | **0.955** |
| 21 | hard_01 | hard | Điều 9, khoản 2 và khoản 4 | 0.932 | 1.000 | 0.985 | **0.963** |
| 22 | hard_02 | hard | Điều 39, khoản 2 | 0.934 | 1.000 | 0.957 | **0.958** |
| 23 | hard_03 | hard | Điều 7, khoản 1 | 0.953 | 1.000 | 0.956 | **0.968** |
| 24 | hard_04 | hard | Điều 5 | 0.962 | 1.000 | 0.963 | **0.974** |
| 25 | hard_05 | hard | Điều 41 | 0.925 | 1.000 | 1.000 | **0.962** |
| 26 | hard_06 | hard | Điều 26, khoản 2 | 0.936 | 1.000 | 1.000 | **0.968** |
| 27 | hard_07 | hard | Điều 37, khoản 2 và 3 | 0.933 | 1.000 | 0.990 | **0.964** |
| 28 | hard_08 | hard | Điều 21, khoản 2 và 3 | 0.942 | 1.000 | 0.968 | **0.964** |
| 29 | hard_09 | hard | Điều 2, khoản 14 và 15 | 0.920 | 1.000 | 0.618 | **0.884** |
| 30 | hard_10 | hard | Điều 40, khoản 1 và 2 | 0.926 | 1.000 | 0.979 | **0.959** |

### Lowest 5

- **6. easy_06** (easy): overall `0.686`, sem `0.972`, cit `0.000`, kw `1.000`. Question: ** 'Phần mềm độc hại' được định nghĩa như thế nào trong Luật An ninh mạng số 116/2025/QH15?
- **1. easy_01** (easy): overall `0.697`, sem `0.393`, cit `1.000`, kw `1.000`. Question: ** Luật An ninh mạng số 116/2025/QH15 có hiệu lực thi hành từ ngày nào?
- **3. easy_03** (easy): overall `0.734`, sem `0.667`, cit `1.000`, kw `0.500`. Question: ** Hệ thống thông tin được phân thành bao nhiêu cấp độ theo Luật An ninh mạng số 116/2025/QH15?
- **13. medium_03** (medium): overall `0.778`, sem `0.663`, cit `1.000`, kw `0.733`. Question: ** Theo Luật An ninh mạng số 116/2025/QH15, khi doanh nghiệp nhận được yêu cầu cung cấp thông tin người dùng từ lực lượng chuyên trách bảo vệ an ninh mạng thuộc Bộ Công an, thời hạn tối đa để thực hiện là bao lâu? Trường hợp khẩn cấp thì sa
- **15. medium_05** (medium): overall `0.800`, sem `0.790`, cit `1.000`, kw `0.527`. Question: ** Chủ quản hệ thống thông tin quan trọng về an ninh quốc gia có những nhiệm vụ và biện pháp bảo vệ an ninh mạng ở mức độ nào so với chủ quản hệ thống cấp độ 3, 4?

## Luật Viễn thông 24/2023/QH15

| Difficulty | Questions | Semantic | Citation | Keyword | Overall |
|---|---:|---:|---:|---:|---:|
| easy | 10 | 0.905 | 1.000 | 0.932 | **0.939** |
| medium | 10 | 0.870 | 0.933 | 0.874 | **0.890** |
| hard | 10 | 0.872 | 0.800 | 0.798 | **0.836** |

### Details

| No. | ID | Difficulty | Reference | Semantic | Citation | Keyword | Overall |
|---:|---|---|---|---:|---:|---:|---:|
| 1 | Q001 | easy | Điều 72 | 0.739 | 1.000 | 0.864 | **0.842** |
| 2 | Q002 | easy | Khoản 1 Điều 3 | 0.976 | 1.000 | 1.000 | **0.988** |
| 3 | Q003 | easy | Khoản 34 Điều 3 | 0.925 | 1.000 | 0.913 | **0.945** |
| 4 | Q004 | easy | Khoản 26 Điều 3 | 0.939 | 1.000 | 1.000 | **0.969** |
| 5 | Q005 | easy | Khoản 29 Điều 3 | 0.981 | 1.000 | 1.000 | **0.990** |
| 6 | Q006 | easy | Điều 2 | 0.851 | 1.000 | 1.000 | **0.926** |
| 7 | Q007 | easy | Khoản 15 Điều 3 | 0.978 | 1.000 | 1.000 | **0.989** |
| 8 | Q008 | easy | Điểm e Khoản 1 Điều 15 | 0.902 | 1.000 | 0.545 | **0.860** |
| 9 | Q009 | easy | Khoản 2 Điều 69 | 0.983 | 1.000 | 1.000 | **0.992** |
| 10 | Q010 | easy | Điều 7 | 0.779 | 1.000 | 1.000 | **0.890** |
| 11 | Q011 | medium | Khoản 7 Điều 3 | 0.960 | 1.000 | 0.903 | **0.960** |
| 12 | Q012 | medium | Khoản 1 Điều 22 | 0.942 | 1.000 | 1.000 | **0.971** |
| 13 | Q013 | medium | Khoản 4 Điều 6 | 0.860 | 1.000 | 0.978 | **0.926** |
| 14 | Q014 | medium | Điều 23 | 0.700 | 1.000 | 0.951 | **0.840** |
| 15 | Q015 | medium | Khoản 4 Điều 15 | 0.897 | 1.000 | 0.981 | **0.945** |
| 16 | Q016 | medium | Khoản 25 Điều 3, Điều 23 | 0.880 | 0.667 | 0.500 | **0.740** |
| 17 | Q017 | medium | Điều 57 | 0.831 | 1.000 | 0.957 | **0.907** |
| 18 | Q018 | medium | Khoản 10, 11 Điều 3 | 0.970 | 0.667 | 0.545 | **0.794** |
| 19 | Q019 | medium | Khoản 3 Điều 60 | 0.836 | 1.000 | 1.000 | **0.918** |
| 20 | Q020 | medium | Khoản 6, 7 Điều 5 | 0.827 | 1.000 | 0.929 | **0.899** |
| 21 | Q021 | hard | Điều 17 | 0.613 | 1.000 | 0.841 | **0.775** |
| 22 | Q022 | hard | Điều 21 | 0.950 | 1.000 | 0.839 | **0.943** |
| 23 | Q023 | hard | Điều 11 | 0.884 | 1.000 | 0.746 | **0.891** |
| 24 | Q024 | hard | Khoản 6, 7 Điều 65 | 0.916 | 0.667 | 0.857 | **0.830** |
| 25 | Q025 | hard | Điều 73 | 0.865 | 1.000 | 0.759 | **0.884** |
| 26 | Q026 | hard | Điều 16, Điều 17 | 0.976 | 0.500 | 1.000 | **0.838** |
| 27 | Q027 | hard | Điều 5 | 0.908 | 1.000 | 0.893 | **0.933** |
| 28 | Q028 | hard | Điểm h Khoản 2, Khoản 4 Điều 13 | 0.830 | 0.500 | 0.750 | **0.715** |
| 29 | Q029 | hard | Khoản 8, 12 Điều 3; Khoản 2 Điều 20; Điều 28 | 0.857 | 0.333 | 0.580 | **0.645** |
| 30 | Q030 | hard | Điều 62 | 0.925 | 1.000 | 0.717 | **0.906** |

### Lowest 5

- **29. Q029** (hard): overall `0.645`, sem `0.857`, cit `0.333`, kw `0.580`. Question: ** Phân tích sự khác biệt giữa dịch vụ viễn thông cơ bản trên Internet và dịch vụ ứng dụng viễn thông. Tại sao sự phân biệt này quan trọng về mặt pháp lý?
- **28. Q028** (hard): overall `0.715`, sem `0.830`, cit `0.500`, kw `0.750`. Question: ** Luật Viễn thông 2023 quy định gì về việc thuê bao viễn thông được giữ nguyên số thuê bao khi đổi nhà mạng? Đây là nghĩa vụ của ai?
- **16. Q016** (medium): overall `0.740`, sem `0.880`, cit `0.667`, kw `0.500`. Question: ** Phương tiện thiết yếu trong viễn thông được hiểu như thế nào và tại sao nó quan trọng?
- **21. Q021** (hard): overall `0.775`, sem `0.613`, cit `1.000`, kw `0.841`. Question: ** Phân tích các nghĩa vụ bổ sung của doanh nghiệp viễn thông có vị trí thống lĩnh thị trường so với doanh nghiệp viễn thông thông thường.
- **18. Q018** (medium): overall `0.794`, sem `0.970`, cit `0.667`, kw `0.545`. Question: ** Dịch vụ điện toán đám mây được định nghĩa như thế nào trong Luật Viễn thông 2023?

## Luật Công nghệ thông tin 65/VBHN-VPQH

| Difficulty | Questions | Semantic | Citation | Keyword | Overall |
|---|---:|---:|---:|---:|---:|
| easy | 10 | 0.859 | 0.800 | 0.912 | **0.852** |
| medium | 10 | 0.829 | 1.000 | 0.923 | **0.899** |
| hard | 10 | 0.843 | 0.950 | 0.806 | **0.868** |

### Details

| No. | ID | Difficulty | Reference | Semantic | Citation | Keyword | Overall |
|---:|---|---|---|---:|---:|---:|---:|
| 1 | Q001 | easy | Điều 78 | 0.341 | 1.000 | 1.000 | **0.670** |
| 2 | Q002 | easy | Điều 4, khoản 2 | 0.979 | 1.000 | 1.000 | **0.989** |
| 3 | Q003 | easy | Điều 4, khoản 15 | 0.985 | 1.000 | 1.000 | **0.993** |
| 4 | Q004 | easy | Điều 7, khoản 1 | 0.920 | 1.000 | 0.333 | **0.827** |
| 5 | Q005 | easy | Điều 4, khoản 16 | 0.990 | 0.000 | 0.947 | **0.685** |
| 6 | Q006 | easy | Điều 2 | 0.870 | 1.000 | 1.000 | **0.935** |
| 7 | Q007 | easy | Điều 4, khoản 17 | 0.955 | 1.000 | 1.000 | **0.977** |
| 8 | Q008 | easy | Điều 4, khoản 18 | 0.845 | 1.000 | 1.000 | **0.923** |
| 9 | Q009 | easy | Điều 75, khoản 2 | 0.717 | 0.000 | 0.842 | **0.527** |
| 10 | Q010 | easy | Điều 4, khoản 7 | 0.987 | 1.000 | 1.000 | **0.993** |
| 11 | Q011 | medium | Điều 16, khoản 4 | 0.974 | 1.000 | 1.000 | **0.987** |
| 12 | Q012 | medium | Điều 9, khoản 2 | 0.813 | 1.000 | 1.000 | **0.907** |
| 13 | Q013 | medium | Điều 55, khoản 2 | 0.942 | 1.000 | 0.839 | **0.939** |
| 14 | Q014 | medium | Điều 14, khoản 1 | 0.570 | 1.000 | 1.000 | **0.785** |
| 15 | Q015 | medium | Điều 71 | 0.858 | 1.000 | 0.605 | **0.850** |
| 16 | Q016 | medium | Điều 9, khoản 4 | 0.927 | 1.000 | 1.000 | **0.964** |
| 17 | Q017 | medium | Điều 69, khoản 2 | 0.933 | 1.000 | 0.800 | **0.927** |
| 18 | Q018 | medium | Điều 41, khoản 3 | 0.667 | 1.000 | 1.000 | **0.833** |
| 19 | Q019 | medium | Điều 17, khoản 2 | 0.867 | 1.000 | 1.000 | **0.934** |
| 20 | Q020 | medium | Điều 63, khoản 1 | 0.737 | 1.000 | 0.982 | **0.865** |
| 21 | Q021 | hard | Điều 3 | 0.828 | 1.000 | 0.917 | **0.898** |
| 22 | Q022 | hard | Điều 12, khoản 2 | 0.869 | 1.000 | 0.970 | **0.929** |
| 23 | Q023 | hard | Phần đầu văn bản hợp nhất | 0.567 | 1.000 | 0.267 | **0.637** |
| 24 | Q024 | hard | Điều 68 | 0.964 | 1.000 | 0.948 | **0.971** |
| 25 | Q025 | hard | Điều 42, khoản 4-5; Điều 43 | 0.942 | 0.500 | 0.750 | **0.771** |
| 26 | Q026 | hard | Điều 61, khoản 3 | 0.866 | 1.000 | 0.867 | **0.906** |
| 27 | Q027 | hard | Điều 73 | 0.899 | 1.000 | 0.980 | **0.946** |
| 28 | Q028 | hard | Điều 72, khoản 2 | 0.794 | 1.000 | 0.976 | **0.892** |
| 29 | Q029 | hard | Điều 74 | 0.887 | 1.000 | 0.765 | **0.897** |
| 30 | Q030 | hard | Điều 15, khoản 4-5; Điều 12 | 0.813 | 1.000 | 0.620 | **0.831** |

### Lowest 5

- **9. Q009** (easy): overall `0.527`, sem `0.717`, cit `0.000`, kw `0.842`. Question: ** Theo Luật CNTT, tranh chấp về công nghệ thông tin được giải quyết như thế nào?
- **23. Q023** (hard): overall `0.637`, sem `0.567`, cit `1.000`, kw `0.267`. Question: ** Luật CNTT gốc (67/2006/QH11) đã được sửa đổi, bổ sung bởi những luật nào? Hãy liệt kê đầy đủ tên luật, số hiệu, ngày ban hành và ngày có hiệu lực.
- **1. Q001** (easy): overall `0.670`, sem `0.341`, cit `1.000`, kw `1.000`. Question: ** Luật Công nghệ thông tin số 67/2006/QH11 có hiệu lực thi hành từ ngày nào?
- **5. Q005** (easy): overall `0.685`, sem `0.990`, cit `0.000`, kw `0.947`. Question: ** Theo Luật CNTT, 'vi rút máy tính' được định nghĩa là gì?
- **25. Q025** (hard): overall `0.771`, sem `0.942`, cit `0.500`, kw `0.750`. Question: ** Theo Luật CNTT, cơ sở đào tạo nhân lực CNTT được hưởng những ưu đãi gì? Nhà nước có chính sách hỗ trợ gì đối với giáo viên, sinh viên, học sinh trong vấn đề tiếp cận CNTT?
