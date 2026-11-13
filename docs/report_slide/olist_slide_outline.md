# Outline SLIDE (high level): olist-dw-dss (CO4031 HK261)

> 3 người trình bày, tổng 15:00 + 5 phút Q&A. Không có demo; phần minh họa ứng dụng dùng screenshot.
> **Quy tắc mỗi slide:** 1 tiêu đề thông điệp + 1 visual + tối đa 3 bullet (≤10 từ, lời thường, không công thức, không tên cột/biến). Speaker note 1–2 câu. Mọi chi tiết kỹ thuật nằm trong report (cột "Report").
> **[CẦN SỐ] / [CẦN ẢNH]:** chỉ đánh dấu những gì hiện trên slide chính.

## Tổng quan 3 phase

| Phase               | Người       | Mạch kể                            | Slide        | Thời lượng |
| ------------------- | ----------- | ---------------------------------- | ------------ | ---------- |
| 1. Data engineering | **Người 1** | Vấn đề có thật, kho cho ra số đúng | 1–7          | 6:00       |
| 2. Dashboard/OLAP   | **Người 2** | Số liệu chỉ ra vấn đề ở đâu        | 8–11         | 4:00       |
| 3. DSS              | **Người 3** | Từ vấn đề đến chọn chính sách      | 12–16        | 5:00       |
|                     |             |                                    | **16 slide** | **15:00**  |

---

## Phase 1 · Người 1 (6:00)

| #   | Tiêu đề (thông điệp)                                               | Bullet (tối đa 3)                                                                                                             | Visual                                       | Thời lượng | Speaker note                                                                                                                    | Report        |
| --- | ------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------- | ---------- | ------------------------------------------------------------------------------------------------------------------------------- | ------------- |
| 1   | Olist Seller Performance: Kho dữ liệu và DSS hỗ trợ chọn seller cần can thiệp | • Môn: Kho dữ liệu và Hệ hỗ trợ quyết định (CO4031), HK261 • GVHD: [Tên GVHD] • Nhóm [số]: [Thành viên 1 – MSSV], [Thành viên 2 – MSSV], [Thành viên 3 – MSSV] | Bìa: logo trường, tên đề tài lớn, QR link app | 0:15 | "Chào thầy/cô, nhóm [số] xin trình bày đề tài Olist Seller Performance." | — |
| 2   | Bài trình bày gồm 3 phần, mỗi người một phần | • Phần 1 – Kho dữ liệu: bài toán, dữ liệu, kiến trúc, ETL ([Toàn]) • Phần 2 – Dashboard: vấn đề nằm ở đâu ([Người 2]) • Phần 3 – DSS: tháng tới xử lý seller nào ([Người 3]) | Agenda 3 khối màu kèm tên người trình bày | 0:20 | "Bài gồm 3 phần. Mình mở đầu với phần kho dữ liệu." | 1.4 |
| 3   | Mỗi tháng phải chọn can thiệp seller nào mà không mất quá nhiều doanh thu | • Vấn đề: 16,8% đơn là trải nghiệm xấu (review ≤ 2 hoặc giao trễ) • Theo dõi bằng KPI: GMV, tỷ lệ bàn giao trễ, review xấu, đơn xấu • Mục tiêu: giảm đơn xấu, ảnh hưởng tối đa 10% GMV và 40 seller | 1 big-number 16,8% + khung "Vấn đề → KPI → Quyết định" | 1:00 | "Project trả lời một câu hỏi lặp lại mỗi tháng: can thiệp ai để giảm đơn xấu mà vẫn giữ doanh thu. Mọi thứ phía sau đều phục vụ quyết định này." | 1.1–1.3 |
| 4   | Dữ liệu thật nhưng bẩn, nên cần một kiến trúc làm sạch theo tầng | • Dữ liệu: Olist Brazil, 99.441 đơn, 3.095 seller, 25 tháng, 11 file • Vấn đề: trùng lặp, thiếu, timestamp sai thứ tự, tháng thưa, đơn nhiều seller • Giải pháp: làm sạch và chuẩn hóa qua từng tầng trước khi phân tích | Bảng 3 cột "Dữ liệu → Vấn đề → Giải pháp" + biểu đồ số đơn/tháng nhỏ | 0:50 | "Dữ liệu không dùng thẳng được. Vì vậy nhóm thiết kế kiến trúc Medallion, làm sạch qua từng tầng, và đó là slide tiếp theo." | 3.1–3.2 |
| 5   | Kiến trúc Medallion: dữ liệu đi qua ba tầng rồi mới dùng           | • Thô → làm sạch → kho chuẩn (Gold) • Dashboard và mô hình chỉ đọc từ Gold • Chạy trên Databricks, giao diện Streamlit        | `high_level_architecture.drawio.png`         | 1:10       | "Gold là kho dữ liệu duy nhất. Không phân tích nào đọc file thô."                                                               | 2.1, 3.4, 3.5 |
| 6   | Star schema với ba góc nhìn: từng món, từng đơn, từng seller-tháng | • Ba bảng sự kiện dùng chung bảng chiều • Phân cấp thời gian, địa lý, danh mục • "Trễ" tách lỗi seller và lỗi vận chuyển      | ERD đơn giản hóa, tô màu theo 3 bảng sự kiện | 1:10       | "Mỗi câu hỏi cần một mức chi tiết riêng. Tách hai loại trễ để không phạt nhầm seller."                                          | 4.1–4.3       |
| 7   | ETL chạy lại bao nhiêu lần cũng ra cùng con số                     | • Một job tự động, sáu bước nối tiếp • Kho chỉ cập nhật hoặc thêm, không xóa • Mỗi lần nạp đều đếm và đối soát                | Screenshot Job DAG [CẦN ẢNH]                 | 1:00       | "Bằng chứng: tổng GMV cộng theo tháng, theo vùng hay toàn bộ đều ra R$ 13.494.400,74."                                          | 4.4, 4.5      |
| 8   | **Chuyển giao:** kho đã sẵn sàng, số liệu nói gì?                  | • Số đã đúng, giờ đọc ý nghĩa                                                                                                 | Sơ đồ kiến trúc, tô sáng khối dashboard      | 0:20       | "*Kho đã cho số đáng tin. [Người 2] sẽ cho thấy số liệu chỉ ra vấn đề ở đâu.*"                                                  | —             |

## Phase 2 · Người 2 (4:00)

| #   | Tiêu đề (thông điệp)                                          | Bullet (tối đa 3)                                                                                                                            | Visual                               | Thời lượng | Speaker note                                                                                          | Report |
| --- | ------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------ | ---------- | ----------------------------------------------------------------------------------------------------- | ------ |
| 9   | Một màn hình cho manager thấy sức khỏe cả sàn                 | • GMV R$ 13,49 triệu trong toàn giai đoạn • 10,1% món hàng bị seller bàn giao trễ • Theo dõi xu hướng từng tháng và từng bang                | Screenshot `docs/images/app_kpi.png` | 1:10       | "Mọi tỷ lệ tính trên tổng, nên nhóm nhỏ không làm méo số."                                            | 5.1    |
| 10   | Năm phép OLAP, mỗi phép trả lời một câu hỏi                   | • Gộp và tách theo vùng, thời gian • Lọc theo nhóm hàng, khu vực, quý • Xoay bảng để tìm nguồn gây trễ                                       | Lưới 5 screenshot OLAP [CẦN ẢNH]     | 1:20       | "Câu hỏi được đặt trước, phép OLAP được chọn sau để trả lời."                                         | 5.2    |
| 11  | Vấn đề tập trung theo vùng, không rải đều                     | • Norte bàn giao trễ 19,2%, gần gấp đôi toàn sàn • Hai phát hiện khác theo thời gian, nhóm hàng [CẦN SỐ] • Câu hỏi mới: dùng tab tự khám phá | Biểu đồ roll-up theo vùng [CẦN ẢNH]  | 1:00       | "Dashboard trả lời: chuyện gì đã xảy ra, ở đâu, khi nào. Số Norte cần kiểm lại theo bộ lọc mặc định." | 5.2    |
| 12  | **Chuyển giao:** biết vấn đề ở đâu, nhưng tháng tới xử lý ai? | • Nhìn quá khứ xong, giờ nhìn tháng tới                                                                                                      | Thanh 3 pha Simon, tô sáng pha đầu   | 0:30       | "*Dashboard nhìn về quá khứ. [Người 3] sẽ cho thấy cách dự báo và chọn chính sách.*"                  | —      |

## Phase 3 · Người 3 (5:00)

| #   | Tiêu đề (thông điệp)                                    | Bullet (tối đa 3)                                                                                                                        | Visual                                                                                    | Thời lượng | Speaker note                                                                                                                           | Report        |
| --- | ------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- | ---------- | -------------------------------------------------------------------------------------------------------------------------------------- | ------------- |
| 13  | DSS đi theo ba bước: tìm vấn đề, thiết kế, lựa chọn     | • Dữ liệu từ kho, hai mô hình, giao diện • Người dùng chỉnh ngưỡng can thiệp • Hiệu quả can thiệp là giả định cần kiểm                   | Influence diagram rút gọn                                                                 | 1:00       | "Dashboard là bước tìm vấn đề. Phần này là thiết kế và lựa chọn."                                                                      | 2.4, 5.3, 5.4 |
| 14  | Mô hình dự báo seller nào dễ có đơn xấu tháng tới       | • Logistic regression học từ lịch sử seller • Kiểm tra trên các tháng sau cùng [CẦN SỐ] • Chấm điểm 342 seller đủ đơn tháng 8/2018       | Calibration plot [CẦN SỐ]                                                                 | 1:00       | "Mô hình chỉ học từ quá khứ và được kiểm trên tháng nó chưa thấy."                                                                     | 5.5           |
| 15  | So ba chính sách, chỉ giữ chính sách nằm trong giới hạn | • Không làm, theo ngưỡng, theo dự báo • So số đơn xấu dự kiến còn lại [CẦN SỐ] • Loại nếu vượt 10% GMV hoặc 40 seller                    | Bảng 3 chính sách tô màu đạt/không đạt [CẦN SỐ] + screenshot `docs/images/app_policy.png` | 1:10       | "Mỗi chính sách được chấm cùng một thước đo, rồi lọc theo giới hạn."                                                                   | 5.6           |
| 16  | Kết luận có còn đứng vững khi giả định lệch?            | • Tự tìm ngưỡng vừa đủ giới hạn [CẦN SỐ] • Thử giả định lệch 20% hai chiều • Quyết định cuối được lưu lại để đối chiếu                   | Tornado chart [CẦN ẢNH]                                                                   | 0:50       | "Quyết định được lưu lại, tháng sau so được với kết quả thật."                                                                         | 5.6, 5.7      |
| 17  | Đạt yêu cầu đề; bước tiếp theo là đo hiệu quả thật      | • Đủ kho, dashboard và hỗ trợ quyết định • Giới hạn: dữ liệu cũ, hiệu quả còn giả định • Tiếp theo: thử nghiệm A/B, nạp dữ liệu tăng dần | Checklist ✓/✗ + roadmap 3 mốc                                                             | 1:00       | "Kho đáng tin, DSS chọn được chính sách trong giới hạn. Điểm yếu lớn nhất là hiệu quả can thiệp chưa đo được. Cảm ơn thầy và các bạn." | 6.1–6.4, Ch7  |



---

## [CẦN SỐ] / [CẦN ẢNH] trên slide chính

| Slide | Cần lấy | Lấy từ |
|---|---|---|
| 6 | Screenshot Job DAG | Databricks Jobs UI, job `olist_etl` |
| 9 | 5 screenshot OLAP | App, trang Phân tích đa chiều |
| 10 | Screenshot roll-up theo vùng; 2 phát hiện có số; kiểm lại Norte 19,2% với bộ lọc mặc định | App, trang Phân tích đa chiều |
| 13 | Kết quả kiểm tra mô hình (AUC/Brier, đọc thành lời); calibration plot | `dss.model_eval`, `dss.model_calibration` (chạy lại Job DSS) |
| 14 | Số đơn xấu dự kiến, %GMV, số seller cho 3 chính sách (P1 chưa có; P0/P2 số tạm 685,2 → 682,0, 7 seller, 0,3% GMV cần xác nhận) | App, trang Chọn chính sách |
| 15 | Ngưỡng goal seek tìm được; screenshot tornado | App, trang Chọn chính sách |

**Số đã xác thực dùng trên slide** (nguồn: README, PROGRESS_LOG 10–12/11): 16,8% đơn xấu; 99.441 đơn; 3.095 seller; 25 tháng; GMV R$ 13.494.400,74 (R$ 13,49 triệu); bàn giao trễ 10,1%; Norte 19,2% (cần kiểm bộ lọc); 342 seller tại 2018-08.
