# DW Assignment Requirement

**Nhãn dùng trong bài:****[ĐỀ]** = ghi trực tiếp trong đề ·**[SUY RA]** = suy ra từ L.O. hoặc slide ·**[KN]** = khuyến nghị của em. Số trang là số trang PDF, cũng là số in trên slide.

**Phạm vi đã đọc và lưu ý trước khi làm**

- **Trang chủ yếu là hình:** Em đã xem ảnh các hình quan trọng: kiến trúc DW/DSS, granularity, Batch ETL, metadata, star schema, fact constellation, các phép OLAP, influence diagram, thành phần mô hình, SDLC, model management.
- **Chưa đọc chi tiết:** Các hình công thức và ví dụ tính toán của decision tree, Naive Bayes, k-means và neural network (Ch5 bản đầu, khoảng tr.7–15 và 22–34), cùng một số hình data cube 3D/4D (Ch3 tr.23, 29, 30). Với các trang này em chỉ đọc tiêu đề.
- **Slide thiếu mục:** Ch2 tr.19 nhảy thẳng sang mục "5. Data Vault", tức mục 3–4 của phần kiến trúc không có trong file. [[Chapter_2_...ousing.pdf | PDF]](https://softwareone-my.sharepoint.com/personal/toan_nguyen1_softwareone_com/Documents/Documents/Personal/DW/Chapter_2_Basic%20issues%20in%20data%20warehousing.pdf)
- **Lịch không thống nhất:** Ch0 (bản 2025) và slide Introduction ghi mốc khác với đề, ví dụ dự án làm tuần 2–10 và thuyết trình tuần 11–15. Em **theo file đề** vì đó là bản mới nhất, ban hành 10/09/2026. [[Introducti...-HK261.pdf | PDF]](https://softwareone-my.sharepoint.com/personal/toan_nguyen1_softwareone_com/Documents/Documents/Personal/DW/Introduction-CO4031-HK261.pdf), [[Chapter_0_...erview.pdf | PDF]](https://softwareone-my.sharepoint.com/personal/toan_nguyen1_softwareone_com/Documents/Documents/Personal/DW/Chapter_0_Overview.pdf) [[CO4031_Ass..._HK261.pdf | PDF]](https://softwareone-my.sharepoint.com/personal/toan_nguyen1_softwareone_com/Documents/Documents/Personal/DW/CO4031_Assignment_HK261.pdf)
- **Thời gian còn lại:** Hôm nay là tuần 7, còn khoảng 5 tuần đến hạn 15/11. Chương 6–8 (DSS) được giảng sau giữa kỳ, nên nhóm cần đọc trước để kịp làm phần DSS**[KN]**.

---

## Phần 1. Yêu cầu ghi rõ trong đề [ĐỀ]

| Mục | Nội dung |
| --- | --- |
| Tỷ trọng | 35% điểm môn [[CO4031_Ass..._HK261.pdf | PDF]](https://softwareone-my.sharepoint.com/personal/toan_nguyen1_softwareone_com/Documents/Documents/Personal/DW/CO4031_Assignment_HK261.pdf) |
| Nhóm | 2–3 sinh viên. Mỗi người phải có vai trò rõ ràng. Điểm cá nhân có thể cộng hoặc trừ qua peer review và đánh giá khi thuyết trình [[CO4031_Ass..._HK261.pdf | PDF]](https://softwareone-my.sharepoint.com/personal/toan_nguyen1_softwareone_com/Documents/Documents/Personal/DW/CO4031_Assignment_HK261.pdf) |
| 6 mục tiêu | (1) Phân tích nghiệp vụ; (2) Thiết kế DW đa chiều (star/snowflake) kèm ETL; (3) Backend (cơ sở dữ liệu, ETL, OLAP) và frontend (dashboard hoặc giao diện truy vấn); (4) Thành phần DSS dựa trên DW; (5) Đánh giá, hạn chế, hướng phát triển; (6) Thuyết trình [[CO4031_Ass..._HK261.pdf | PDF]](https://softwareone-my.sharepoint.com/personal/toan_nguyen1_softwareone_com/Documents/Documents/Personal/DW/CO4031_Assignment_HK261.pdf) |
| **Điều kiện đề tài** | (a) DW phải là **cốt lõi**, phục vụ phân tích và ra quyết định; (b) Nguồn dữ liệu: open data, Kaggle, UCI, hoặc dữ liệu doanh nghiệp **có sự đồng ý của chủ dữ liệu**, với **quy mô đủ lớn**; (c) Có **ý nghĩa thực tế**: giải một bài toán phân tích hoặc ra quyết định cụ thể [[CO4031_Ass..._HK261.pdf | PDF]](https://softwareone-my.sharepoint.com/personal/toan_nguyen1_softwareone_com/Documents/Documents/Personal/DW/CO4031_Assignment_HK261.pdf) |
| Lĩnh vực gợi ý | Bán lẻ, ngân hàng, y tế, giáo dục, logistics, thương mại điện tử, nông nghiệp, viễn thông, giao thông. Không bắt buộc chọn trong danh sách này [[CO4031_Ass..._HK261.pdf | PDF]](https://softwareone-my.sharepoint.com/personal/toan_nguyen1_softwareone_com/Documents/Documents/Personal/DW/CO4031_Assignment_HK261.pdf) |
| Thuyết trình trực tiếp | 15 phút trình bày + 5 phút Q&A, tất cả thành viên phải nói. Các buổi vào 19/11, 26/11, 03/12 [[CO4031_Ass..._HK261.pdf | PDF]](https://softwareone-my.sharepoint.com/personal/toan_nguyen1_softwareone_com/Documents/Documents/Personal/DW/CO4031_Assignment_HK261.pdf) |
| Video (nhóm không thuyết trình trực tiếp) | 10–15 phút, mọi thành viên phải xuất hiện, hình và tiếng rõ. Đăng YouTube unlisted hoặc Google Drive, gắn link lên trang bìa báo cáo [[CO4031_Ass..._HK261.pdf | PDF]](https://softwareone-my.sharepoint.com/personal/toan_nguyen1_softwareone_com/Documents/Documents/Personal/DW/CO4031_Assignment_HK261.pdf) |
| Nộp bài | 1 file ZIP gồm: báo cáo PDF; `src/` (SQL, Python/R, frontend, ETL, ưu tiên link GitHub truy cập được); `data/` (GitHub hoặc Drive); slide PDF; link video trên bìa. Nộp qua LMS, **hạn 23:59 ngày 15/11/2026** [[CO4031_Ass..._HK261.pdf | PDF]](https://softwareone-my.sharepoint.com/personal/toan_nguyen1_softwareone_com/Documents/Documents/Personal/DW/CO4031_Assignment_HK261.pdf) |

**Đề không quy định:** rubric hoặc thang điểm thành phần, số trang báo cáo, ngôn ngữ, công cụ hay DBMS, ngưỡng định lượng cho "đủ lớn", loại mô hình DSS cụ thể. **Giả định an toàn ** chọn công cụ tự do nhưng phải giải thích lý do; tự đặt và nêu rõ ngưỡng dữ liệu (xem Phần 5).

---

## Phần 2. Ánh xạ đề bài ↔ chuẩn đầu ra ↔ slide

| L.O. | Mục tiêu trong đề | Yêu cầu cụ thể (đề + suy ra) | Slide liên quan | Sản phẩm chứng minh |
| --- | --- | --- | --- | --- |
| **1.1** Khái niệm DW/DSS | 1, 2 | [SUY RA] Báo cáo dùng đúng khái niệm: 4 đặc tính của Inmon, OLTP và OLAP, ETL, staging, data mart, DSS | Ch1 tr.3–20; Ch2 tr.6–13; Ch2-cont tr.3; Ch3 tr.3 [[Chapter_1_...System.pdf | PDF]](https://softwareone-my.sharepoint.com/personal/toan_nguyen1_softwareone_com/Documents/Documents/Personal/DW/Chapter_1_Introduction%20of%20Datawarehouse%20and%20Decision%20Support%20System.pdf), [[Chapter_2_...ousing.pdf | PDF]](https://softwareone-my.sharepoint.com/personal/toan_nguyen1_softwareone_com/Documents/Documents/Personal/DW/Chapter_2_Basic%20issues%20in%20data%20warehousing.pdf), [[Chapter_2_...ntinue.pdf | PDF]](https://softwareone-my.sharepoint.com/personal/toan_nguyen1_softwareone_com/Documents/Documents/Personal/DW/Chapter_2_Basic%20issues%20in%20data%20warehousing%20-%20continue.pdf), [[Chapter_3_...ehouse.pdf | PDF]](https://softwareone-my.sharepoint.com/personal/toan_nguyen1_softwareone_com/Documents/Documents/Personal/DW/Chapter_3_Designing%20a%20Data%20warehouse.pdf) | Chương cơ sở lý thuyết, có liên hệ trực tiếp với đề tài |
| **1.2** Vai trò DW trong DSS | 3, 4 | [ĐỀ] DSS phải được xây "dựa trên kho dữ liệu đã xây dựng" | Ch1 tr.21–25, 31–38; Ch6 tr.13, 21 [[Chapter_1_...System.pdf | PDF]](https://softwareone-my.sharepoint.com/personal/toan_nguyen1_softwareone_com/Documents/Documents/Personal/DW/Chapter_1_Introduction%20of%20Datawarehouse%20and%20Decision%20Support%20System.pdf), [[Chapter_6_...ersion.pdf | PDF]](https://softwareone-my.sharepoint.com/personal/toan_nguyen1_softwareone_com/Documents/Documents/Personal/DW/Chapter_6_Details%20of%20decision%20support%20systems%20-%20new%20version.pdf) | Sơ đồ kiến trúc tổng thể cho thấy luồng DW → DSS và vòng phản hồi |
| **1.3** Ví dụ thực tế | 1 | [ĐỀ] Đề tài có ý nghĩa thực tế | Ch1 tr.39–41 (ngân hàng, siêu thị) [[Chapter_1_...System.pdf | PDF]](https://softwareone-my.sharepoint.com/personal/toan_nguyen1_softwareone_com/Documents/Documents/Personal/DW/Chapter_1_Introduction%20of%20Datawarehouse%20and%20Decision%20Support%20System.pdf) | Bối cảnh nghiệp vụ, người dùng, quyết định cụ thể |
| **2.1** Quy trình, nguyên lý thiết kế DW | 2 | [ĐỀ] Star hoặc snowflake schema + ETL | Ch3 tr.5–21 (3-tier, EDW/data mart, top-down/bottom-up/hybrid), tr.31–37, 39 [[Chapter_3_...ehouse.pdf | PDF]](https://softwareone-my.sharepoint.com/personal/toan_nguyen1_softwareone_com/Documents/Documents/Personal/DW/Chapter_3_Designing%20a%20Data%20warehouse.pdf) | Nêu cách tiếp cận đã chọn (vd. bottom-up/data mart) có lý do; mô hình conceptual → logical → physical |
| **2.2** Vấn đề thiết kế DW | 2, 5 | [SUY RA] Thảo luận granularity, tích hợp, metadata, nạp và làm mới dữ liệu, partition, bảo mật, scalability | Ch2 tr.3; Ch2-cont tr.5–9, 14–17; Ch1 tr.12–13 [[Chapter_2_...ousing.pdf | PDF]](https://softwareone-my.sharepoint.com/personal/toan_nguyen1_softwareone_com/Documents/Documents/Personal/DW/Chapter_2_Basic%20issues%20in%20data%20warehousing.pdf), [[Chapter_2_...ntinue.pdf | PDF]](https://softwareone-my.sharepoint.com/personal/toan_nguyen1_softwareone_com/Documents/Documents/Personal/DW/Chapter_2_Basic%20issues%20in%20data%20warehousing%20-%20continue.pdf), [[Chapter_1_...System.pdf | PDF]](https://softwareone-my.sharepoint.com/personal/toan_nguyen1_softwareone_com/Documents/Documents/Personal/DW/Chapter_1_Introduction%20of%20Datawarehouse%20and%20Decision%20Support%20System.pdf) | Mục "Design decisions & issues" trong báo cáo |
| **2.3** Thiết kế và hiện thực DW | 2, 3 | [ĐỀ] Backend gồm cơ sở dữ liệu, ETL, OLAP | Ch3 tr.22–30, 38, 41–44; Ch2 tr.8–10, 14–16, 21–24 [[Chapter_3_...ehouse.pdf | PDF]](https://softwareone-my.sharepoint.com/personal/toan_nguyen1_softwareone_com/Documents/Documents/Personal/DW/Chapter_3_Designing%20a%20Data%20warehouse.pdf), [[Chapter_2_...ousing.pdf | PDF]](https://softwareone-my.sharepoint.com/personal/toan_nguyen1_softwareone_com/Documents/Documents/Personal/DW/Chapter_2_Basic%20issues%20in%20data%20warehousing.pdf) | DDL, ETL chạy được, DW đã nạp dữ liệu, truy vấn OLAP |
| **3.1** MSS/DSS | 4 | [SUY RA] Phân loại DSS của nhóm thuộc loại nào | Ch4 tr.17–26; Ch6 tr.4–8, 32–35 [[CHAPTER_4_...pdated.pdf | PDF]](https://softwareone-my.sharepoint.com/personal/toan_nguyen1_softwareone_com/Documents/Documents/Personal/DW/CHAPTER_4_Management%20Support%20Systems_Updated.pdf), [[Chapter_6_...ersion.pdf | PDF]](https://softwareone-my.sharepoint.com/personal/toan_nguyen1_softwareone_com/Documents/Documents/Personal/DW/Chapter_6_Details%20of%20decision%20support%20systems%20-%20new%20version.pdf) | Một đoạn phân loại, ví dụ "data-driven + model-driven = compound DSS" |
| **3.2** Giai đoạn ra quyết định | 1, 4 | [SUY RA] Gắn các chức năng DSS với intelligence → design → choice (→ implementation) | Ch5-cont tr.2, 11–17; Ch4 tr.21 [[CHAPTER_5_...- cont.pdf | PDF]](https://softwareone-my.sharepoint.com/personal/toan_nguyen1_softwareone_com/Documents/Documents/Personal/DW/CHAPTER_5_Decision%20support%20systems,%20modeling%20and%20support%20-%20cont.pdf), [[CHAPTER_4_...pdated.pdf | PDF]](https://softwareone-my.sharepoint.com/personal/toan_nguyen1_softwareone_com/Documents/Documents/Personal/DW/CHAPTER_4_Management%20Support%20Systems_Updated.pdf) | Bảng ánh xạ giai đoạn ↔ màn hình hoặc chức năng |
| **3.3** Mô hình hóa trong DSS | 4 | [SUY RA] Có ít nhất 1 mô hình (slide nói DSS phải chứa ít nhất một model) | Ch5-cont tr.9; Ch7 toàn chương; Ch5 tr.3–34 [[CHAPTER_5_...- cont.pdf | PDF]](https://softwareone-my.sharepoint.com/personal/toan_nguyen1_softwareone_com/Documents/Documents/Personal/DW/CHAPTER_5_Decision%20support%20systems,%20modeling%20and%20support%20-%20cont.pdf), [[Chapter_7...alysis.pdf | PDF]](https://softwareone-my.sharepoint.com/personal/toan_nguyen1_softwareone_com/Documents/Documents/Personal/DW/Chapter_7%20Modeling%20and%20analysis.pdf), [[CHAPTER_5_...upport.pdf | PDF]](https://softwareone-my.sharepoint.com/personal/toan_nguyen1_softwareone_com/Documents/Documents/Personal/DW/CHAPTER_5_Decision%20support%20systems,%20modeling%20and%20support.pdf) | Influence diagram; mô tả decision, uncontrollable và result variables; mô hình chạy được |
| **4.1** Nguyên tắc phân tích, thiết kế DSS | 4, 5 | [SUY RA] Trình bày quy trình phát triển DSS | Ch8 tr.5–7 (SDLC), 14–15, 20–23, 30 (prototyping) [[Chapter_8...opment.pdf | PDF]](https://softwareone-my.sharepoint.com/personal/toan_nguyen1_softwareone_com/Documents/Documents/Personal/DW/Chapter_8%20Decision%20support%20system%20development.pdf) | Mục phương pháp phát triển, rủi ro và cách giảm thiểu |
| **4.2** Hiện thực DSS đơn giản | 3, 4 | [ĐỀ] Phát triển thành phần DSS | Ch6 tr.10–16, 18, 24–28 [[Chapter_6_...ersion.pdf | PDF]](https://softwareone-my.sharepoint.com/personal/toan_nguyen1_softwareone_com/Documents/Documents/Personal/DW/Chapter_6_Details%20of%20decision%20support%20systems%20-%20new%20version.pdf) | DSS có data, model và UI subsystem chạy được, demo được |
| — | 6 | [ĐỀ] Thuyết trình hoặc video | — (slide không đề cập) | Slide PDF + buổi trình bày hoặc video |

---

## Phần 3. Kiến thức từ slide chuyển thành tiêu chí bài làm

### 3.1 Thiết kế DW

| Tiêu chí | Nguồn | Vì sao giúp đáp ứng đề |
| --- | --- | --- |
| 4 đặc tính subject-oriented, integrated, time-variant, non-volatile | Ch1 tr.4–8; Ch2-cont tr.3; Ch3 tr.3 | Dùng làm tiêu chí tự kiểm thiết kế. Ví dụ: có chiều thời gian, fact không bị cập nhật đè [[Chapter_1_...System.pdf | PDF]](https://softwareone-my.sharepoint.com/personal/toan_nguyen1_softwareone_com/Documents/Documents/Personal/DW/Chapter_1_Introduction%20of%20Datawarehouse%20and%20Decision%20Support%20System.pdf), [[Chapter_3_...ehouse.pdf | PDF]](https://softwareone-my.sharepoint.com/personal/toan_nguyen1_softwareone_com/Documents/Documents/Personal/DW/Chapter_3_Designing%20a%20Data%20warehouse.pdf) |
| Kiến trúc 3 tầng: source → staging/ETL → DW → presentation | Ch2 tr.13, 18; Ch3 tr.5–9 | Khớp trực tiếp yêu cầu backend + frontend [[Chapter_2_...ousing.pdf | PDF]](https://softwareone-my.sharepoint.com/personal/toan_nguyen1_softwareone_com/Documents/Documents/Personal/DW/Chapter_2_Basic%20issues%20in%20data%20warehousing.pdf), [[Chapter_3_...ehouse.pdf | PDF]](https://softwareone-my.sharepoint.com/personal/toan_nguyen1_softwareone_com/Documents/Documents/Personal/DW/Chapter_3_Designing%20a%20Data%20warehouse.pdf) |
| Chọn EDW, data mart hay virtual DW; top-down, bottom-up hay hybrid | Ch3 tr.10–21, 39 | Phục vụ L.O.2.1. Với nhóm 2–3 người, data mart/bottom-up dễ lập luận nhất [KN] [[Chapter_3_...ehouse.pdf | PDF]](https://softwareone-my.sharepoint.com/personal/toan_nguyen1_softwareone_com/Documents/Documents/Personal/DW/Chapter_3_Designing%20a%20Data%20warehouse.pdf) |
| Fact, dimension, measure, cell, data cube | Ch2 tr.11, 15; Ch3 tr.22–30 | Là lõi của "mô hình đa chiều" [[Chapter_2_...ousing.pdf | PDF]](https://softwareone-my.sharepoint.com/personal/toan_nguyen1_softwareone_com/Documents/Documents/Personal/DW/Chapter_2_Basic%20issues%20in%20data%20warehousing.pdf), [[Chapter_3_...ehouse.pdf | PDF]](https://softwareone-my.sharepoint.com/personal/toan_nguyen1_softwareone_com/Documents/Documents/Personal/DW/Chapter_3_Designing%20a%20Data%20warehouse.pdf) |
| Star, snowflake, fact constellation (galaxy) | Ch3 tr.31–37 | Đề yêu cầu star/snowflake. Fact constellation phù hợp khi có từ 2 fact trở lên dùng chung dimension [[Chapter_3_...ehouse.pdf | PDF]](https://softwareone-my.sharepoint.com/personal/toan_nguyen1_softwareone_com/Documents/Documents/Personal/DW/Chapter_3_Designing%20a%20Data%20warehouse.pdf) |
| **Granularity** (slide dùng "granularity", không dùng chữ "grain"): chọn mức chi tiết vừa phải, ước lượng số dòng/dung lượng, cân nhắc dual levels (chi tiết + tổng hợp) | Ch2 tr.3, 13; Ch2-cont tr.5–9, 18 | Slide gọi đây là một trong hai quyết định thiết kế quan trọng nhất [[Chapter_2_...ousing.pdf | PDF]](https://softwareone-my.sharepoint.com/personal/toan_nguyen1_softwareone_com/Documents/Documents/Personal/DW/Chapter_2_Basic%20issues%20in%20data%20warehousing.pdf), [[Chapter_2_...ntinue.pdf | PDF]](https://softwareone-my.sharepoint.com/personal/toan_nguyen1_softwareone_com/Documents/Documents/Personal/DW/Chapter_2_Basic%20issues%20in%20data%20warehousing%20-%20continue.pdf) |
| Hierarchy (năm > quý > tháng > ngày; quốc gia > tỉnh > thành phố), concept hierarchy | Ch2 tr.15; Ch2-cont tr.11 | Điều kiện để drill-down và roll-up có ý nghĩa [[Chapter_2_...ousing.pdf | PDF]](https://softwareone-my.sharepoint.com/personal/toan_nguyen1_softwareone_com/Documents/Documents/Personal/DW/Chapter_2_Basic%20issues%20in%20data%20warehousing.pdf), [[Chapter_2_...ntinue.pdf | PDF]](https://softwareone-my.sharepoint.com/personal/toan_nguyen1_softwareone_com/Documents/Documents/Personal/DW/Chapter_2_Basic%20issues%20in%20data%20warehousing%20-%20continue.pdf) |
| Aggregate/summary data, partition theo thời gian, index, bitmap index, materialized view | Ch1 tr.12; Ch2 tr.16; Ch3 tr.7 | Thể hiện mặt hiệu năng của L.O.2.2 [[Chapter_1_...System.pdf | PDF]](https://softwareone-my.sharepoint.com/personal/toan_nguyen1_softwareone_com/Documents/Documents/Personal/DW/Chapter_1_Introduction%20of%20Datawarehouse%20and%20Decision%20Support%20System.pdf), [[Chapter_2_...ousing.pdf | PDF]](https://softwareone-my.sharepoint.com/personal/toan_nguyen1_softwareone_com/Documents/Documents/Personal/DW/Chapter_2_Basic%20issues%20in%20data%20warehousing.pdf), [[Chapter_3_...ehouse.pdf | PDF]](https://softwareone-my.sharepoint.com/personal/toan_nguyen1_softwareone_com/Documents/Documents/Personal/DW/Chapter_3_Designing%20a%20Data%20warehouse.pdf) |
| Metadata: cấu trúc, nguồn, phép biến đổi, data model, lịch sử extract; phân biệt technical và business metadata | Ch1 tr.9; Ch2-cont tr.14–15; Ch6 tr.22 | Làm nền cho data dictionary và data lineage [[Chapter_1_...System.pdf | PDF]](https://softwareone-my.sharepoint.com/personal/toan_nguyen1_softwareone_com/Documents/Documents/Personal/DW/Chapter_1_Introduction%20of%20Datawarehouse%20and%20Decision%20Support%20System.pdf), [[Chapter_2_...ntinue.pdf | PDF]](https://softwareone-my.sharepoint.com/personal/toan_nguyen1_softwareone_com/Documents/Documents/Personal/DW/Chapter_2_Basic%20issues%20in%20data%20warehousing%20-%20continue.pdf), [[Chapter_6_...ersion.pdf | PDF]](https://softwareone-my.sharepoint.com/personal/toan_nguyen1_softwareone_com/Documents/Documents/Personal/DW/Chapter_6_Details%20of%20decision%20support%20systems%20-%20new%20version.pdf) |
| Derived data | Ch2-cont tr.13 | Dùng cho các measure phái sinh như tỷ lệ hay biên lợi nhuận [[Chapter_2_...ntinue.pdf | PDF]](https://softwareone-my.sharepoint.com/personal/toan_nguyen1_softwareone_com/Documents/Documents/Personal/DW/Chapter_2_Basic%20issues%20in%20data%20warehousing%20-%20continue.pdf) |
| Data quality, governance, security, maintenance (refresh, đồng bộ nguồn, quản lý tăng trưởng dữ liệu) | Ch1 tr.13; Ch2-cont tr.16–17; Ch3 tr.41; Ch6 tr.23 | Dùng cho phần đánh giá và hạn chế [[Chapter_1_...System.pdf | PDF]](https://softwareone-my.sharepoint.com/personal/toan_nguyen1_softwareone_com/Documents/Documents/Personal/DW/Chapter_1_Introduction%20of%20Datawarehouse%20and%20Decision%20Support%20System.pdf), [[Chapter_2_...ntinue.pdf | PDF]](https://softwareone-my.sharepoint.com/personal/toan_nguyen1_softwareone_com/Documents/Documents/Personal/DW/Chapter_2_Basic%20issues%20in%20data%20warehousing%20-%20continue.pdf), [[Chapter_3_...ehouse.pdf | PDF]](https://softwareone-my.sharepoint.com/personal/toan_nguyen1_softwareone_com/Documents/Documents/Personal/DW/Chapter_3_Designing%20a%20Data%20warehouse.pdf), [[Chapter_6_...ersion.pdf | PDF]](https://softwareone-my.sharepoint.com/personal/toan_nguyen1_softwareone_com/Documents/Documents/Personal/DW/Chapter_6_Details%20of%20decision%20support%20systems%20-%20new%20version.pdf) |
| **Slide không đề cập:** SCD, surrogate key, conformed dimension, bus matrix, quy trình 4 bước của Kimball, data dictionary theo dạng chuẩn | — | Có thể dùng như điểm cộng, lấy từ sách Kimball (tài liệu tham khảo [2] trong đề) [KN] |

### 3.2 ETL

| Tiêu chí | Nguồn | Vì sao |
| --- | --- | --- |
| Extract không làm gián đoạn nguồn; Transform gồm cleansing, mapping, áp dụng business rules; Load gồm **incremental** hoặc full refresh | Ch2 tr.8 | Khung chuẩn để trình bày pipeline [[Chapter_2_...ousing.pdf | PDF]](https://softwareone-my.sharepoint.com/personal/toan_nguyen1_softwareone_com/Documents/Documents/Personal/DW/Chapter_2_Basic%20issues%20in%20data%20warehousing.pdf) |
| Staging area nằm giữa nguồn và DW | Ch1 tr.16; Ch3 tr.6 | Nên có schema staging tách riêng [[Chapter_1_...System.pdf | PDF]](https://softwareone-my.sharepoint.com/personal/toan_nguyen1_softwareone_com/Documents/Documents/Personal/DW/Chapter_1_Introduction%20of%20Datawarehouse%20and%20Decision%20Support%20System.pdf), [[Chapter_3_...ehouse.pdf | PDF]](https://softwareone-my.sharepoint.com/personal/toan_nguyen1_softwareone_com/Documents/Documents/Personal/DW/Chapter_3_Designing%20a%20Data%20warehouse.pdf) |
| ETL và ELT (rủi ro của ELT nếu quản lý không tốt), công cụ code-producing và parameterized | Ch2 tr.9 | Giải thích lý do chọn công cụ hoặc cách làm [[Chapter_2_...ousing.pdf | PDF]](https://softwareone-my.sharepoint.com/personal/toan_nguyen1_softwareone_com/Documents/Documents/Personal/DW/Chapter_2_Basic%20issues%20in%20data%20warehousing.pdf) |
| **Batch ETL**: chạy tay và chạy theo lịch (scheduled/unattended), có khoảng thời gian dữ liệu bao phủ | Ch2 tr.10 (hình) | Đây là căn cứ trên slide cho phần lịch chạy ETL [[Chapter_2_...ousing.pdf | PDF]](https://softwareone-my.sharepoint.com/personal/toan_nguyen1_softwareone_com/Documents/Documents/Personal/DW/Chapter_2_Basic%20issues%20in%20data%20warehousing.pdf) |
| Các phép biến đổi: smoothing, attribute construction, aggregation, normalization, discretization | Ch2-cont tr.10–11 | Nguồn ý tưởng cho bước transform, ví dụ chia nhóm tuổi [[Chapter_2_...ntinue.pdf | PDF]](https://softwareone-my.sharepoint.com/personal/toan_nguyen1_softwareone_com/Documents/Documents/Personal/DW/Chapter_2_Basic%20issues%20in%20data%20warehousing%20-%20continue.pdf) |
| Làm sạch: chống trùng lặp, đảm bảo referential integrity, thống nhất định dạng | Ch1 tr.6 | Là bằng chứng cho đặc tính "integrated" [[Chapter_1_...System.pdf | PDF]](https://softwareone-my.sharepoint.com/personal/toan_nguyen1_softwareone_com/Documents/Documents/Personal/DW/Chapter_1_Introduction%20of%20Datawarehouse%20and%20Decision%20Support%20System.pdf) |
| Kiến trúc real-time hoặc streaming | Ch2 tr.20 | Có thể nêu ở mục hướng phát triển [[Chapter_2_...ousing.pdf | PDF]](https://softwareone-my.sharepoint.com/personal/toan_nguyen1_softwareone_com/Documents/Documents/Personal/DW/Chapter_2_Basic%20issues%20in%20data%20warehousing.pdf) |

### 3.3 OLAP

| Tiêu chí | Nguồn | Vì sao |
| --- | --- | --- |
| 5 phép **slice, dice, drill-down, roll-up, pivot** | Ch2 tr.16, 23; Ch3 tr.26, 38 | Nên demo đủ cả 5 phép [[Chapter_2_...ousing.pdf | PDF]](https://softwareone-my.sharepoint.com/personal/toan_nguyen1_softwareone_com/Documents/Documents/Personal/DW/Chapter_2_Basic%20issues%20in%20data%20warehousing.pdf), [[Chapter_3_...ehouse.pdf | PDF]](https://softwareone-my.sharepoint.com/personal/toan_nguyen1_softwareone_com/Documents/Documents/Personal/DW/Chapter_3_Designing%20a%20Data%20warehouse.pdf) |
| ROLAP, MOLAP, HOLAP | Ch2 tr.24; Ch3 tr.44 | Phải nêu nhóm dùng loại nào. SQL trên star schema là ROLAP [SUY RA] [[Chapter_2_...ousing.pdf | PDF]](https://softwareone-my.sharepoint.com/personal/toan_nguyen1_softwareone_com/Documents/Documents/Personal/DW/Chapter_2_Basic%20issues%20in%20data%20warehousing.pdf), [[Chapter_3_...ehouse.pdf | PDF]](https://softwareone-my.sharepoint.com/personal/toan_nguyen1_softwareone_com/Documents/Documents/Personal/DW/Chapter_3_Designing%20a%20Data%20warehouse.pdf) |
| Ad-hoc query, tổng hợp đa mức, pre-aggregation | Ch2 tr.22, 26 | Dùng để thiết kế giao diện truy vấn [[Chapter_2_...ousing.pdf | PDF]](https://softwareone-my.sharepoint.com/personal/toan_nguyen1_softwareone_com/Documents/Documents/Personal/DW/Chapter_2_Basic%20issues%20in%20data%20warehousing.pdf) |
| Kết hợp OLAP với data mining (classification, prediction, clustering) | Ch3 tr.42, 45 | Cầu nối sang mô hình của DSS [[Chapter_3_...ehouse.pdf | PDF]](https://softwareone-my.sharepoint.com/personal/toan_nguyen1_softwareone_com/Documents/Documents/Personal/DW/Chapter_3_Designing%20a%20Data%20warehouse.pdf) |

### 3.4 DSS

| Tiêu chí | Nguồn | Vì sao |
| --- | --- | --- |
| Các pha **intelligence, design, choice** (mục lục có thêm implementation, evaluation); phân loại vấn đề programmed/nonprogrammed; problem decomposition; problem ownership | Ch5-cont tr.2, 11–16; Ch4 tr.21 | Phục vụ L.O.3.2. Mỗi chức năng DSS nên gắn với một pha [[CHAPTER_5_...- cont.pdf | PDF]](https://softwareone-my.sharepoint.com/personal/toan_nguyen1_softwareone_com/Documents/Documents/Personal/DW/CHAPTER_5_Decision%20support%20systems,%20modeling%20and%20support%20-%20cont.pdf), [[CHAPTER_4_...pdated.pdf | PDF]](https://softwareone-my.sharepoint.com/personal/toan_nguyen1_softwareone_com/Documents/Documents/Personal/DW/CHAPTER_4_Management%20Support%20Systems_Updated.pdf) |
| Principle of choice: tiêu chí chọn phương án, chính là result variable | Ch5-cont tr.17 | DSS phải có KPI mục tiêu rõ ràng [[CHAPTER_5_...- cont.pdf | PDF]](https://softwareone-my.sharepoint.com/personal/toan_nguyen1_softwareone_com/Documents/Documents/Personal/DW/CHAPTER_5_Decision%20support%20systems,%20modeling%20and%20support%20-%20cont.pdf) |
| Thành phần: data, model, user interface subsystem, knowledge-based subsystem (tùy chọn); thêm lớp integration/communication | Ch1 tr.20; Ch4 tr.23; Ch6 tr.6, 10–16, 24–28 | Kiến trúc DSS phải thể hiện đủ 3 subsystem bắt buộc [[Chapter_1_...System.pdf | PDF]](https://softwareone-my.sharepoint.com/personal/toan_nguyen1_softwareone_com/Documents/Documents/Personal/DW/Chapter_1_Introduction%20of%20Datawarehouse%20and%20Decision%20Support%20System.pdf), [[CHAPTER_4_...pdated.pdf | PDF]](https://softwareone-my.sharepoint.com/personal/toan_nguyen1_softwareone_com/Documents/Documents/Personal/DW/CHAPTER_4_Management%20Support%20Systems_Updated.pdf), [[Chapter_6_...ersion.pdf | PDF]](https://softwareone-my.sharepoint.com/personal/toan_nguyen1_softwareone_com/Documents/Documents/Personal/DW/Chapter_6_Details%20of%20decision%20support%20systems%20-%20new%20version.pdf) |
| Loại DSS: data-, model-, knowledge-, document-, communication-driven, intelligent, hybrid; Holsapple & Whinston (database-, spreadsheet-, solver-, rule-oriented, compound) | Ch4 tr.24–26; Ch6 tr.32–35 | Dùng để tự phân loại DSS của nhóm [[CHAPTER_4_...pdated.pdf | PDF]](https://softwareone-my.sharepoint.com/personal/toan_nguyen1_softwareone_com/Documents/Documents/Personal/DW/CHAPTER_4_Management%20Support%20Systems_Updated.pdf), [[Chapter_6_...ersion.pdf | PDF]](https://softwareone-my.sharepoint.com/personal/toan_nguyen1_softwareone_com/Documents/Documents/Personal/DW/Chapter_6_Details%20of%20decision%20support%20systems%20-%20new%20version.pdf) |
| Mô hình: **what-if, sensitivity, optimization** (Ch6 tr.14); **goal seeking**, optimization, simulation trên spreadsheet (Ch7 tr.20); **forecasting** (Ch6 tr.18; Ch7 tr.4); simulation (Ch7 tr.17–18); heuristic search (Ch7 tr.15–16) | Ch6, Ch7 | Đây là "modeling" của L.O.3.3 [[Chapter_6_...ersion.pdf | PDF]](https://softwareone-my.sharepoint.com/personal/toan_nguyen1_softwareone_com/Documents/Documents/Personal/DW/Chapter_6_Details%20of%20decision%20support%20systems%20-%20new%20version.pdf), [[Chapter_7...alysis.pdf | PDF]](https://softwareone-my.sharepoint.com/personal/toan_nguyen1_softwareone_com/Documents/Documents/Personal/DW/Chapter_7%20Modeling%20and%20analysis.pdf) |
| Static và dynamic model; certainty, risk, uncertainty | Ch7 tr.5–9 | Cần nêu mô hình của nhóm thuộc loại nào [[Chapter_7...alysis.pdf | PDF]](https://softwareone-my.sharepoint.com/personal/toan_nguyen1_softwareone_com/Documents/Documents/Personal/DW/Chapter_7%20Modeling%20and%20analysis.pdf) |
| **Influence diagram**; 3 thành phần decision, uncontrollable và result variables | Ch7 tr.10–12 | Cách trình bày mô hình mà slide hướng tới [[Chapter_7...alysis.pdf | PDF]](https://softwareone-my.sharepoint.com/personal/toan_nguyen1_softwareone_com/Documents/Documents/Personal/DW/Chapter_7%20Modeling%20and%20analysis.pdf) |
| Thuật toán: decision tree, Naive Bayes, k-means, neural network; công cụ Tableau, Power BI | Ch5 tr.3–34 | Có thể dùng cho predictive model trong DSS [[CHAPTER_5_...upport.pdf | PDF]](https://softwareone-my.sharepoint.com/personal/toan_nguyen1_softwareone_com/Documents/Documents/Personal/DW/CHAPTER_5_Decision%20support%20systems,%20modeling%20and%20support.pdf) |
| MBMS: control, flexibility, interface, giảm dư thừa, tăng nhất quán | Ch7 tr.19; Ch6 tr.29 | Lý do để tách module mô hình riêng [[Chapter_7...alysis.pdf | PDF]](https://softwareone-my.sharepoint.com/personal/toan_nguyen1_softwareone_com/Documents/Documents/Personal/DW/Chapter_7%20Modeling%20and%20analysis.pdf), [[Chapter_6_...ersion.pdf | PDF]](https://softwareone-my.sharepoint.com/personal/toan_nguyen1_softwareone_com/Documents/Documents/Personal/DW/Chapter_6_Details%20of%20decision%20support%20systems%20-%20new%20version.pdf) |
| Ví dụ mẫu: dashboard KPI, công cụ what-if, dự báo bán hàng, tối ưu tồn kho, luật phân khúc khách hàng | Ch6 tr.18 | Gần như một bản thiết kế mẫu cho DSS [[Chapter_6_...ersion.pdf | PDF]](https://softwareone-my.sharepoint.com/personal/toan_nguyen1_softwareone_com/Documents/Documents/Personal/DW/Chapter_6_Details%20of%20decision%20support%20systems%20-%20new%20version.pdf) |

### 3.5 Phát triển DSS

| Tiêu chí | Nguồn | Vì sao |
| --- | --- | --- |
| SDLC: planning → analysis → design → implementation; DSS thường làm theo **prototyping** (iterative, RAD) | Ch8 tr.5–7, 30 | Phục vụ L.O.4.1 [[Chapter_8...opment.pdf | PDF]](https://softwareone-my.sharepoint.com/personal/toan_nguyen1_softwareone_com/Documents/Documents/Personal/DW/Chapter_8%20Decision%20support%20system%20development.pdf) |
| Yếu tố thành công: mục tiêu rõ, scope tối thiểu, yêu cầu cố định, có sự tham gia của người dùng | Ch8 tr.14–15 | Giúp giới hạn phạm vi đề tài [[Chapter_8...opment.pdf | PDF]](https://softwareone-my.sharepoint.com/personal/toan_nguyen1_softwareone_com/Documents/Documents/Personal/DW/Chapter_8%20Decision%20support%20system%20development.pdf) |
| Rủi ro: hiểu sai yêu cầu, scope thay đổi, công nghệ mới | Ch8 tr.20–23 | Dùng cho mục hạn chế và rủi ro [[Chapter_8...opment.pdf | PDF]](https://softwareone-my.sharepoint.com/personal/toan_nguyen1_softwareone_com/Documents/Documents/Personal/DW/Chapter_8%20Decision%20support%20system%20development.pdf) |
| Tool và generator: Excel, OLAP là integrated tool; web là giao diện chuẩn của DSS | Ch8 tr.24–26; Ch6 tr.38, 40 | Giải thích lựa chọn công nghệ [[Chapter_8...opment.pdf | PDF]](https://softwareone-my.sharepoint.com/personal/toan_nguyen1_softwareone_com/Documents/Documents/Personal/DW/Chapter_8%20Decision%20support%20system%20development.pdf), [[Chapter_6_...ersion.pdf | PDF]](https://softwareone-my.sharepoint.com/personal/toan_nguyen1_softwareone_com/Documents/Documents/Personal/DW/Chapter_6_Details%20of%20decision%20support%20systems%20-%20new%20version.pdf) |

---

## Phần 4. Danh sách feature và deliverable

Ký hiệu ưu tiên: 🔴 cao · 🟡 trung bình · 🟢 thấp

### (a) Phân tích nghiệp vụ và chọn đề tài

| Feature | Mức | Đầu ra | Ưu tiên |
| --- | --- | --- | --- |
| Bối cảnh, người ra quyết định, bài toán quyết định cụ thể | BẮT BUỘC [ĐỀ 1, 3.1c] | 1–2 trang mô tả | 🔴 |
| Danh sách câu hỏi phân tích (khoảng 8–15 câu) và KPI | NÊN CÓ [KN] | Bảng câu hỏi ↔ KPI ↔ dimension | 🔴 |
| Mô tả nguồn dữ liệu (nguồn, license, quy mô, giai đoạn thời gian) | BẮT BUỘC [ĐỀ 3.1b] | Bảng data profiling | 🔴 |
| Phân loại vấn đề (programmed/nonprogrammed), problem decomposition | NÊN CÓ [Ch5-cont tr.13–15] | 1 đoạn + cây phân rã | 🟡 |
| Bảng phân công vai trò | BẮT BUỘC [ĐỀ 1.3] | Bảng thành viên ↔ vai trò ↔ % đóng góp | 🔴 |

### (b) Thiết kế DW

| Feature | Mức | Đầu ra | Ưu tiên |
| --- | --- | --- | --- |
| Sơ đồ kiến trúc 3 tầng DW + DSS | BẮT BUỘC [SUY RA L.O.1.2, 2.1] | Diagram | 🔴 |
| Chọn cách tiếp cận (data mart/bottom-up…) có lý do | BẮT BUỘC [SUY RA L.O.2.1] | 1 đoạn | 🟡 |
| Star hoặc snowflake schema (ERD), khai báo granularity cho từng fact | BẮT BUỘC [ĐỀ 2] | ERD + câu khai báo granularity | 🔴 |
| Từ 2 fact trở lên dùng chung dimension (fact constellation) | NÊN CÓ [Ch3 tr.35–36] | ERD | 🟡 |
| Hierarchy cho mỗi dimension chính, đặc biệt Date | NÊN CÓ (gần như bắt buộc để drill-down) [Ch2 tr.15] | Bảng hierarchy | 🔴 |
| Data dictionary / metadata (bảng, cột, kiểu, nguồn, quy tắc biến đổi) | NÊN CÓ [Ch2-cont tr.14; Ch6 tr.22] | Bảng hoặc file | 🔴 |
| Ước lượng số dòng và dung lượng | NÊN CÓ [Ch2-cont tr.7] | Bảng ước lượng | 🟢 |
| Surrogate key, SCD Type 2 cho 1 dimension | ĐIỂM CỘNG — **slide không đề cập** [KN, Kimball] | DDL + ví dụ | 🟡 |
| Bus matrix (nếu có ≥ 2 fact) | ĐIỂM CỘNG — **slide không đề cập** [KN] | Ma trận | 🟢 |
| Aggregate table / materialized view, index, partition | NÊN CÓ [Ch1 tr.12] | DDL + so sánh thời gian truy vấn | 🟡 |
| DDL scripts | BẮT BUỘC [ĐỀ 5.1] | `src/sql/` | 🔴 |

### (c) ETL pipeline

| Feature | Mức | Đầu ra | Ưu tiên |
| --- | --- | --- | --- |
| Extract → staging → transform → load chạy được từ đầu đến cuối | BẮT BUỘC [ĐỀ 2, 3] | Script + log | 🔴 |
| Làm sạch: thiếu dữ liệu, trùng lặp, chuẩn hóa định dạng, referential integrity | BẮT BUỘC [SUY RA, Ch1 tr.6; Ch2 tr.8] | Bảng quy tắc + số dòng trước/sau | 🔴 |
| Mapping nguồn → đích (source-to-target) | NÊN CÓ [Ch2 tr.8] | Bảng | 🟡 |
| Incremental load (watermark) bên cạnh full load | NÊN CÓ [Ch2 tr.3, 8] | Demo nạp thêm batch mới | 🟡 |
| Lịch chạy (cron, Airflow…) | ĐIỂM CỘNG [Ch2 tr.10] | Config + screenshot | 🟢 |
| Kiểm tra data quality sau khi load (đối soát số dòng và tổng) | NÊN CÓ [Ch1 tr.13] | Báo cáo kiểm tra | 🟡 |

### (d) OLAP và truy vấn

| Feature | Mức | Đầu ra | Ưu tiên |
| --- | --- | --- | --- |
| Lớp OLAP (ROLAP bằng SQL GROUP BY ROLLUP/CUBE, hoặc cube engine) | BẮT BUỘC [ĐỀ 3] | `src/olap/` | 🔴 |
| Demo đủ 5 phép slice, dice, drill-down, roll-up, pivot, mỗi phép trả lời một câu hỏi nghiệp vụ | NÊN CÓ (gần như bắt buộc) [Ch2 tr.23; Ch3 tr.26] | Truy vấn + kết quả | 🔴 |
| Nêu loại ROLAP/MOLAP/HOLAP đã dùng | NÊN CÓ [Ch2 tr.24] | 1 đoạn | 🟡 |
| Benchmark truy vấn có và không có aggregate | ĐIỂM CỘNG [KN] | Bảng thời gian | 🟢 |

### (e) Frontend / dashboard

| Feature | Mức | Đầu ra | Ưu tiên |
| --- | --- | --- | --- |
| Dashboard hoặc giao diện truy vấn kết nối DW | BẮT BUỘC [ĐỀ 3] | App (Power BI, Superset, Streamlit…) | 🔴 |
| Bộ lọc và drill-down tương tác trên dashboard | NÊN CÓ [Ch3 tr.8] | Màn hình | 🔴 |
| Thẻ KPI, xu hướng theo thời gian | NÊN CÓ [Ch6 tr.18] | Màn hình | 🟡 |
| Trang ad-hoc query | ĐIỂM CỘNG [Ch2 tr.22] | Màn hình | 🟢 |

### (f) Thành phần DSS

| Feature | Mức | Đầu ra | Ưu tiên |
| --- | --- | --- | --- |
| DSS dùng dữ liệu **từ DW** (không đọc file CSV thô) | BẮT BUỘC [ĐỀ 4] | Code + sơ đồ luồng dữ liệu | 🔴 |
| Đủ 3 subsystem: data, model, UI | BẮT BUỘC [SUY RA L.O.4.2; Ch6 tr.6] | Sơ đồ + code | 🔴 |
| Ít nhất 1 mô hình định lượng (forecasting/classification + what-if) | BẮT BUỘC [SUY RA L.O.3.3; Ch5-cont tr.9] | Module model | 🔴 |
| What-if / sensitivity analysis (người dùng chỉnh tham số, thấy result variable thay đổi) | NÊN CÓ (rất nên) [Ch6 tr.14] | Màn hình kịch bản | 🔴 |
| Goal seeking hoặc optimization | ĐIỂM CỘNG [Ch7 tr.20] | Chức năng | 🟡 |
| Influence diagram + bảng decision/uncontrollable/result variables | NÊN CÓ [Ch7 tr.10–12] | Hình trong báo cáo | 🔴 |
| Ánh xạ chức năng ↔ pha intelligence/design/choice/implementation | NÊN CÓ [Ch5-cont tr.11–12] | Bảng | 🔴 |
| Knowledge subsystem (luật/khuyến nghị dạng rule) | ĐIỂM CỘNG [Ch6 tr.16] | Rule base | 🟢 |
| Đánh giá mô hình (MAE/MAPE, accuracy…) và nêu loại certainty/risk | NÊN CÓ [Ch7 tr.7–8] | Bảng metric | 🟡 |

### (g) Đánh giá, hạn chế, hướng phát triển

| Feature | Mức | Đầu ra | Ưu tiên |
| --- | --- | --- | --- |
| Đánh giá kết quả so với câu hỏi và mục tiêu ban đầu | BẮT BUỘC [ĐỀ 5] | Bảng đạt/chưa đạt | 🔴 |
| Hạn chế: dữ liệu, granularity, data quality, mô hình | BẮT BUỘC [ĐỀ 5] | Mục báo cáo | 🔴 |
| Hướng phát triển: real-time, cloud, Data Vault, AI | BẮT BUỘC [ĐỀ 5] gắn [Ch2 tr.19–20; Ch8 tr.30] | Mục báo cáo | 🟡 |
| Rủi ro dự án và bài học (đối chiếu Ch8) | ĐIỂM CỘNG [Ch8 tr.20–23] | Mục báo cáo | 🟢 |

### (h) Báo cáo PDF — mục lục đề xuất [KN, dựa trên đề và L.O.]

1. Trang bìa: nhóm, MSSV, vai trò, **link video** (nếu thuyết trình bằng video) [ĐỀ], link GitHub
2. Giới thiệu: bối cảnh, bài toán quyết định, mục tiêu, phạm vi
3. Cơ sở lý thuyết: DW, DSS, vai trò DW trong DSS, ví dụ thực tế (L.O.1.x, 3.1)
4. Phân tích nghiệp vụ và dữ liệu nguồn: câu hỏi phân tích, KPI, data profiling
5. Thiết kế DW: kiến trúc, cách tiếp cận, schema, granularity, hierarchy, data dictionary, các vấn đề thiết kế (L.O.2.1–2.2)
6. ETL: luồng xử lý, quy tắc làm sạch, incremental, data quality
7. OLAP và dashboard: 5 phép OLAP, các màn hình
8. DSS: phân loại, kiến trúc, mô hình (influence diagram), ánh xạ các pha quyết định, demo kịch bản (L.O.3.2–4.2)
9. Phương pháp phát triển (SDLC/prototyping) và phân công
10. Đánh giá, hạn chế, hướng phát triển
11. Tài liệu tham khảo (dùng danh mục [1]–[8] trong đề) + phụ lục

### (i) Slide và thuyết trình

| Feature | Mức | Ưu tiên |
| --- | --- | --- |
| Slide PDF; mọi thành viên trình bày; 15 + 5 phút (trực tiếp) hoặc video 10–15 phút | BẮT BUỘC [ĐỀ 4] | 🔴 |
| Demo trực tiếp ETL → dashboard → kịch bản what-if của DSS | NÊN CÓ [KN] | 🔴 |
| Chuẩn bị Q&A: lý do chọn granularity, schema, mô hình | NÊN CÓ [KN] | 🟡 |

### (j) Cấu trúc ZIP [ĐỀ 5.1 + KN]

```
CO4031_GroupXX.zip
├── Report_GroupXX.pdf        # bìa có link video + link GitHub/Drive
├── Slides_GroupXX.pdf
├── src/                      # hoặc README chứa link GitHub truy cập được
│   ├── README.md             # cách cài đặt và chạy
│   ├── sql/ (ddl/, olap_queries/)
│   ├── etl/
│   ├── dss/ (models/)
│   └── frontend/
└── data/
    ├── sample/               # dữ liệu mẫu nhỏ
    └── README.md             # nguồn, license, link dữ liệu đầy đủ (Drive/GitHub)
```

**Giả định an toàn:** đề vừa yêu cầu thư mục `src/` và `data/` vừa ưu tiên link. Vì vậy nhóm nên **có cả thư mục lẫn link**.

---

## Phần 5. Tiêu chí chọn đề tài và dữ liệu

### Checklist (tất cả là [KN], trừ chỗ ghi khác)

- [ ]  Nguồn hợp lệ: open data, Kaggle hoặc UCI; dữ liệu doanh nghiệp phải có đồng ý bằng văn bản**[ĐỀ]**
- [ ]  Có **một quyết định cụ thể** và người ra quyết định cụ thể**[ĐỀ 3.1c]**, ví dụ "nên nhập bao nhiêu hàng cho mỗi cửa hàng mỗi tuần"
- [ ]  Có **chiều thời gian** đủ dài, nên từ 1 năm trở lên, để làm xu hướng và forecasting (đặc tính time-variant, Ch1 tr.7)
- [ ]  Có ít nhất 3–4 dimension có nghĩa, trong đó ít nhất 2 dimension có **hierarchy** để drill-down
- [ ]  Có measure dạng số cộng dồn được (doanh thu, số lượng, chi phí)
- [ ]  Có thể tạo ít nhất 1 fact (nên 2 fact dùng chung dimension)
- [ ]  Quy mô "đủ lớn" (đề không định lượng): nên có fact từ khoảng 100 nghìn đến vài triệu dòng, và **nhiều bảng hoặc file nguồn** để ETL có việc tích hợp thật
- [ ]  Dữ liệu có lỗi thật (thiếu, trùng, lệch định dạng) để phần làm sạch có ý nghĩa
- [ ]  Có thể làm mô hình what-if: xác định được decision variables (giá, ngân sách, số lượng…) và result variable
- [ ]  Vừa sức nhóm 2–3 người trong 5 tuần ("minimized scope", Ch8 tr.14)

### Lỗi thường gặp khiến đề tài yếu

1. **Một file CSV phẳng** tách thành star schema một cách gượng ép: ETL không có tích hợp thật, khó bảo vệ L.O.2.3.
2. **Không có chiều thời gian**, hoặc chỉ là snapshot tại một thời điểm: mất đặc tính time-variant, không làm được forecasting.
3. **"Dashboard = DSS"**: chỉ có báo cáo mô tả, không có model và what-if, nên hụt L.O.3.3 và L.O.4.2.
4. **DSS không đọc từ DW** (mô hình ML huấn luyện trên file gốc), vi phạm mục tiêu 4 của đề.
5. **Không khai báo granularity**, hoặc chọn mức quá thô làm mất khả năng drill-down.
6. **Câu hỏi quyết định mơ hồ** (chẳng hạn "phân tích doanh số"), không có principle of choice hay KPI mục tiêu.
7. Dataset đã được tổng hợp sẵn (đã aggregate), không còn dữ liệu cấp giao dịch.
8. Dữ liệu doanh nghiệp không có sự đồng ý, hoặc dataset Kaggle không rõ license.
9. Scope quá rộng (cả một EDW), không kịp hoàn thiện. Slide Ch8 xếp scope thay đổi và yêu cầu không cố định vào nhóm rủi ro hàng đầu.

