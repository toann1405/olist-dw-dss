# Outline BÁO CÁO: olist-dw-dss (CO4031 HK261)

> Nguồn: repo `toann1405/olist-dw-dss`, nhánh `main`, commit `ef1ae9c` (13/11/2026, UTC+7). **[CẦN SỐ]** đánh dấu chỗ repo chưa có số đo đã xác thực. Hạn nộp 23:59 15/11/2026.
> Báo cáo mẫu 49,8 MB chưa mở được trên box, nên outline này chỉ tham chiếu slide mẫu và `docs/assignment/DW_Assignment_Requirement.md`.
> Bản 10 chương cũ được lưu ở `/workspace/olist_outline_v1_backup.md`.

**Mạch kể:** bài toán (Ch1) → nền tảng (Ch2) → dữ liệu và kiến trúc (Ch3) → kho (Ch4) → khai thác và ra quyết định (Ch5) → bằng chứng và giới hạn (Ch6) → kết luận (Ch7).
**Thân bài: 33 trang**, không tính bìa, mục lục và phụ lục.

| Chương | Tên | Trang |
|---|---|---|
| 1 | Mở đầu và bài toán quyết định | 3,5 |
| 2 | Cơ sở lý thuyết | 4,5 |
| 3 | Dữ liệu nguồn và kiến trúc giải pháp | 4,5 |
| 4 | Thiết kế kho dữ liệu, ETL và chất lượng dữ liệu | 7,5 |
| 5 | Từ phân tích đến quyết định: OLAP, DSS và ứng dụng | 9 |
| 6 | Đánh giá, hạn chế và hướng phát triển | 3 |
| 7 | Kết luận | 1 |
| | **Tổng thân bài** | **33** |

---

## Phần mở đầu (không tính trang)
- **Bìa:** môn, GVHD, 3 thành viên và MSSV, link GitHub, link app https://olist-dw-dss.streamlit.app/, link video nếu có (R19).
- **Tóm tắt (½ trang):** bài toán, giải pháp và 3–4 con số chính: 99.441 đơn; GMV R$ 13.494.400,74; 16,8% đơn trải nghiệm xấu; AUC M1 [CẦN SỐ].
- Mục lục, danh mục hình và bảng, bảng viết tắt (`docs/glossary.md`).
- **Bảng phân công 3 thành viên:** vai trò và % đóng góp. Đề bắt buộc mục này (R14). Nguồn tham khảo: PROGRESS_LOG.

---

## Chương 1. Mở đầu và bài toán quyết định (3,5 tr)
| Mục | Nội dung | Nguồn repo | Hình/Bảng | Tr |
|---|---|---|---|---|
| 1.1 Bối cảnh | Seller tự bàn giao hàng cho đơn vị vận chuyển, nên seller kém kéo trải nghiệm của cả sàn đi xuống. Lý do chọn đề tài T1 | SPEC §1, TOPIC_EVALUATION §2–3 | — | 0,75 |
| 1.2 Bài toán quyết định | Decision maker; 4 hạng can thiệp; P0/P1/P2; principle of choice (tối thiểu đơn xấu dự kiến); X=10% GMV, N=40 seller | SPEC §1, `src/dss/params.py` | **Bảng 1.1** Thành phần bài toán quyết định | 1 |
| 1.3 Câu hỏi phân tích | 10 câu hỏi ↔ KPI ↔ dimension | SPEC §3 | **Bảng 1.2** Q1–Q10 | 1 |
| 1.4 Phạm vi, đóng góp, cấu trúc | Chỉ batch, cửa sổ 2016-09-04 → 2018-10-17; ngoài phạm vi; 3 đóng góp; bản đồ chương | SPEC §1 | Hình 1.1 story map (tùy chọn) | 0,75 |

## Chương 2. Cơ sở lý thuyết (4,5 tr)
Mỗi mục kết thúc bằng một dòng "→ áp dụng ở mục …". Không chép định nghĩa dài.
| Mục | Nội dung | Nguồn | Hình/Bảng | Tr |
|---|---|---|---|---|
| 2.1 Data warehouse và lakehouse | 4 đặc tính Inmon; OLTP và OLAP; kiến trúc 3 tầng; data mart bottom-up; Medallion ↔ staging/integration/DW | `DW_Assignment_Requirement.md` §3.1, SPEC §4 | **Bảng 2.1** Ánh xạ Medallion ↔ khái niệm slide | 1,25 |
| 2.2 Mô hình đa chiều | Grain; 3 loại fact; surrogate key; SCD 1/2; role-playing; conformed dimension; constellation; bus matrix | Kimball [2] | — | 1 |
| 2.3 ETL và OLAP | Full load và incremental; MERGE/upsert; 5 phép OLAP; ROLAP/MOLAP/HOLAP | §3.2–3.3 file phân tích đề | — | 0,75 |
| 2.4 DSS và mô hình hóa | Simon: Intelligence → Design → Choice → Implementation; 3 subsystem; phân loại (compound); certainty/risk/uncertainty; influence diagram; what-if, goal seeking, sensitivity; logistic regression, AUC, Brier, calibration | §3.4–3.5 file phân tích đề | Hình 2.1 Ba pha Simon | 1,5 |

## Chương 3. Dữ liệu nguồn và kiến trúc giải pháp (4,5 tr)
| Mục | Nội dung | Nguồn repo | Hình/Bảng | Tr |
|---|---|---|---|---|
| 3.1 Bộ dữ liệu | 9 CSV Olist, 2 CSV Marketing Funnel, IBGE (27 dòng). License CC BY-NC-SA 4.0. Số dòng từng nguồn | DESIGN §5, `data/README.md` | **Bảng 3.1** Nguồn, số dòng, vai trò | 1 |
| 3.2 Profiling và vấn đề chất lượng | Các lỗi đã đo: geo trùng hoặc ngoài bbox, city sai dấu, category thiếu, timestamp đảo, review trùng, payment lạ, tháng thưa, đơn nhiều seller. Bảng đầy đủ đưa sang **PL-C** | SPEC §3, `src/notebooks/01_profiling.py` | **Bảng 3.2** 5 lỗi tiêu biểu; **Hình 3.1** số đơn/tháng, tô 6 tháng thưa | 1,25 |
| 3.3 Kiểm tra khả thi | G1–G6 (G1 = 173 seller; G6 = 380/3.095) → chốt T1 | TOPIC_EVALUATION §1.7, SPEC §10 | 1 đoạn | 0,25 |
| 3.4 Kiến trúc tổng thể | Volume → Bronze → Silver → Gold → Job DSS → `dss` → SQL Warehouse → Streamlit → `decision_log`. Hợp đồng từng lớp | `docs/images/high_level_architecture.drawio.png`, `docs/architecture.md` | **Hình 3.2** Kiến trúc; **Bảng 3.3** Hợp đồng lớp (bản rút gọn) | 1,25 |
| 3.5 Lựa chọn công nghệ | Databricks Free Edition + Delta + UC thay PostgreSQL; ROLAP; Streamlit thay Power BI (Power BI là future work); 2 Job tách riêng; DSS huấn luyện trên Gold (R31) | SPEC §4, §10 "Lịch sử quyết định" | **Bảng 3.4** Đã chọn / không chọn / lý do | 0,75 |

## Chương 4. Thiết kế kho dữ liệu, ETL và chất lượng dữ liệu (7,5 tr)
| Mục | Nội dung | Nguồn repo | Hình/Bảng | Tr |
|---|---|---|---|---|
| 4.1 Fact constellation và grain | 3 fact: `fact_order_item` (transaction, 1 item), `fact_order` (accumulating snapshot, 1 đơn, 5 mốc), `fact_seller_monthly` (periodic snapshot, seller × tháng). Bus matrix | DESIGN §3.1, §4, §4.1; SPEC §5 | **Hình 4.1 ERD**; **Bảng 4.1** Fact, loại, grain; **Bảng 4.2** Bus matrix | 2 |
| 4.2 Dimension, khóa, SCD | 7 dimension và 3 hierarchy; `dim_date` role-playing, `dim_month` shrunken; surrogate key = max + row_number theo natural key; member −1; SCD1, `dim_seller` SCD2-ready. Chi tiết cột đưa sang **PL-A** | DESIGN §3.2–3.5, `src/etl/03_gold_dims.py` | **Bảng 4.3** Hierarchy | 1,25 |
| 4.3 Định nghĩa measure và KPI | GMV = SUM(price), loại canceled/unavailable; tỷ lệ = SUM/SUM; đơn xấu = review ≤2 OR giao trễ; bàn giao trễ ≠ giao trễ tới khách; luật đơn nhiều seller và `shared_review_type` | DESIGN §3.6, `docs/glossary.md` | **Bảng 4.4** KPI, công thức, mẫu, loại trừ | 1,25 |
| 4.4 Pipeline ETL | Job `olist_etl` gồm 6 task, chung `run_id`. Bronze: overwrite, STRING, có `_ingest_ts`/`_source_file`. Silver: cast, `city_norm`, IBGE, geo median, dedup review 2 tầng, timestamp đảo thành NULL. Gold: MERGE không DELETE, thứ tự nạp. Lý do chọn full refresh (R28). Mapping chi tiết đưa sang **PL-B** | `src/etl/*.py`, `olist_etl.job.yml`, SPEC §6 | **Hình 4.2** DAG Job (screenshot); đoạn code MERGE ~8 dòng | 1,75 |
| 4.5 Chất lượng dữ liệu và kiểm soát | Delta constraints; `gold.etl_audit` 10 cột; đối soát rows_read và Σprice; grain không trùng; không orphan; tự kiểm 4 đặc tính Inmon. Danh sách check đầy đủ đưa sang **PL-C** | `_audit.py`, `_dq.py`, DESIGN §7, §9 | **Bảng 4.5** etl_audit 1 run [CẦN SỐ]; **Bảng 4.6** 4 đặc tính Inmon ↔ bằng chứng | 1,25 |

## Chương 5. Từ phân tích đến quyết định: OLAP, DSS và ứng dụng (9 tr)
Chương đi theo trình tự Simon: Intelligence (5.1–5.2) → Design (5.3–5.5) → Choice/Implementation (5.6–5.7).
| Mục | Nội dung | Nguồn repo | Hình/Bảng | Tr |
|---|---|---|---|---|
| 5.1 Lớp phân tích ROLAP | SQL Warehouse; query có tham số `?`; cache; dashboard KPI (thẻ, sparkline, bản đồ bang, Wilson interval, ẩn nhóm n<30); tab ad hoc | `src/frontend/lib/db.py`, `queries.py`, `adhoc.py`, `pages/kpi*.py` | **Hình 5.1** `docs/images/app_kpi.png` | 1,25 |
| 5.2 Năm phép OLAP và phát hiện | Mỗi phép gồm câu hỏi, chart và 1 câu insight. Roll-up: bàn giao trễ theo Vùng → Bang → Thành phố. Drill-down: review theo Năm → Ngày. Slice: nhóm danh mục. Dice: Norte+Nordeste, Q1–Q2/2018, hàng bulky. Pivot: Bang×Quý → Nhóm×Quý. SQL đưa sang **PL-D** | `src/sql/olap_queries/01–05`, `pages/olap.py` | **Bảng 5.1** Phép, câu hỏi, insight [CẦN SỐ]; **Hình 5.2** lưới 4–5 chart | 1,5 |
| 5.3 Kiến trúc DSS | Compound DSS (data-driven + model-driven + luật nhẹ trong `recommend.py`); 3 subsystem; ánh xạ pha Simon ↔ trang app | SPEC §8, `src/frontend/app.py` | **Hình 5.3** 3 subsystem; **Bảng 5.2** Pha ↔ chức năng ↔ trang | 1 |
| 5.4 Influence diagram và biến | Biến quyết định (θ1–θ3, ngưỡng KPI, `min_orders`); không kiểm soát (e_k, r, s); trung gian (p_i, Q_i, hạng); kết quả (đơn xấu dự kiến, %GMV, số seller). Giá trị mặc định đưa sang **PL-F** | SPEC §8, `params.py` | **Hình 5.4** Influence diagram; **Bảng 5.3** Biến | 1 |
| 5.5 M1: dự báo rủi ro seller | Logistic regression trên panel seller × tháng; nhãn tháng t+1 mở rộng ra từng đơn; 5 biến số + one-hot nhóm hàng/vùng; tập train ≥10 item × ≥6 tháng; split theo thời gian (2 tháng cuối); AUC, Brier, calibration; contribution coef×(x−mean); chấm 2018-08 (342/1.278 seller ≥5 đơn). Loại mô hình: static, under risk | `src/dss/train.py`, `src/sql/views/v_seller_features.sql`, DESIGN §6.6 | **Bảng 5.4** Metric [CẦN SỐ]; **Hình 5.5** Calibration plot [CẦN SỐ] | 1,5 |
| 5.6 M2: mô phỏng chính sách | E[bad] = Σ p_i·Q_i·(1−e_k); GMV bị ảnh hưởng = Σ_flagged gmv·(1−r); P0/P1/P2 với trần X/N; goal seeking (bisection θ1); tornado ±20% cho e_k, r, s | `src/dss/policy.py` | **Bảng 5.5** P0/P1/P2 [CẦN SỐ P1]; **Hình 5.6** Tornado [CẦN SỐ] | 1,5 |
| 5.7 Ứng dụng và triển khai | 6 trang Streamlit; kịch bản 5 bước manager; nút Chốt ghi `dss.decision_log` (UUID); xuất CSV; config `st.secrets` → biến môi trường → `.env`; deploy Community Cloud; pytest 38 pass | `app.py`, `lib/ui.py`, `lib/db.py`, `src/tests/`, PROGRESS_LOG 11–12/11 | **Hình 5.7** `docs/images/app_policy.png`; screenshot các trang khác đưa sang **PL-H** | 1,25 |

## Chương 6. Đánh giá, hạn chế và hướng phát triển (3 tr)
| Mục | Nội dung | Nguồn repo | Hình/Bảng | Tr |
|---|---|---|---|---|
| 6.1 Đối chiếu yêu cầu đề | 6 mục tiêu của đề và các dòng RTM BB/BB*, đánh dấu đạt/chưa đạt (cập nhật trạng thái thật, xem E6). RTM đầy đủ đưa sang **PL-E** | SPEC §2 | **Bảng 6.1** Checklist | 0,75 |
| 6.2 Đánh giá kết quả | DW: GMV khớp 3 cách cộng (13.494.400,74), idempotency [CẦN SỐ]. M1 so với base rate [CẦN SỐ]. M2: P2 mặc định chỉ giảm ~0,5% đơn xấu (số tạm), thảo luận θ, phân phối p và goal seek | PROGRESS_LOG 10–12/11 | 1 bảng nhỏ | 1 |
| 6.3 Hạn chế và bài học | Dữ liệu 2016–2018; "tháng tới" là mô phỏng one-step-ahead; tháng thưa; e_k/r là giả định; tập train ≠ tập chấm; chưa backtest; Free Edition. Phát triển theo prototyping qua Phase 0–7 và các thay đổi quyết định (L.O.4.1) | SPEC §10, PLAN | — | 0,75 |
| 6.4 Hướng phát triển | Incremental/CDF/Auto Loader; SCD2 thật; A/B để đo e_k; backtest; Power BI; service principal thay PAT | README "Limits" | — | 0,5 |

## Chương 7. Kết luận (1 tr)
Trả lời lại bài toán ở 1.2 bằng 3 câu và 3 con số. Nêu điều làm được và điều còn mở.

## Tài liệu tham khảo
Inmon (2005); Kimball & Ross (2013); Golfarelli et al. (1998); Turban/Sharda (DSS); Simon (1960); tài liệu Databricks (Medallion, MERGE, Unity Catalog); scikit-learn; Olist/Kaggle; IBGE; click_that_hood (MIT).

## Phụ lục (không tính trang). Phần chi tiết bị cắt khỏi thân bài được đưa về đây
- **PL-A Data dictionary** Gold và `dss`: DESIGN §6.3–6.6.
- **PL-B Source-to-target mapping** Bronze → Silver → Gold: DESIGN §6.1–6.4; bảng ước lượng số dòng: DESIGN §5.
- **PL-C Quy tắc làm sạch và DQ:** bảng profiling đầy đủ (SPEC §3); quy tắc DESIGN §7; CHECK constraints DESIGN §9; `_dq.py`; etl_audit mọi bảng [CẦN SỐ].
- **PL-D SQL 5 phép OLAP** và view `v_seller_features`: `src/sql/`.
- **PL-E RTM đầy đủ** (đã cập nhật): SPEC §2.
- **PL-F Tham số DSS** (`params.py`), công thức M2 đầy đủ, schema `decision_log`.
- **PL-G Hướng dẫn chạy lại:** README "How to run".
- **PL-H Screenshot** tất cả trang và tab (danh sách ở PROGRESS_LOG 11/11).
- **PL-I Lịch sử quyết định và timeline Phase:** SPEC §10, PLAN.

---

## C. Số liệu

### C1. Đã đo, có nguồn trong repo
| Số | Giá trị | Nguồn |
|---|---|---|
| Đơn (`fact_order`) | 99.441 | README, PROGRESS_LOG 11/11 |
| Cửa sổ mua | 2016-09-04 → 2018-10-17; 25 tháng có đơn, thiếu 2016-11 | PROGRESS_LOG 11–12/11 |
| Tháng thưa | 2016-09, 2016-10, 2016-12, 2017-01, 2018-09, 2018-10 | SPEC §3 |
| GMV | R$ 13.494.400,74 | README |
| Đơn trải nghiệm xấu | 16,8% (16.444 / 98.079) | README |
| Seller hoạt động / seller trong dim / khách / danh mục / bang seller | 3.053 / 3.095 / 96.096 / 73 / 23 | PROGRESS_LOG 11/11 |
| Đơn nhiều seller | 1.278 (1,2953% của 98.666 đơn có item) | SPEC §3 |
| Đơn hợp lệ, AOV | 98.199; R$ 137,42 | PROGRESS_LOG 11/11 |
| Bàn giao trễ / review xấu seller / cancel | 10,07% (11.132/110.550) / 13,69% (13.141/95.974) / 0,47% (467/98.666) | PROGRESS_LOG 10/11 |
| Số dòng nguồn | items 112.650; reviews 99.224; payments 103.886; products 32.951; geo 1.000.163; deals 842; MQL 8.000 | DESIGN §5 |
| Profiling | 19.015 zip; 31 điểm ngoài bbox; 610 product thiếu category; 789 review_id gắn nhiều đơn / 814 dòng thừa; timestamp đảo 1.359/166/23; 387 đơn lệch payment | SPEC §3 |
| Số dòng kết quả OLAP | 665 / 634 / 612 / 13 / 9 | PROGRESS_LOG 07/11 |
| Ví dụ theo vùng | Norte bàn giao trễ 19,2%; Sudeste GMV R$ 10,57 tr; Nordeste 14,4% (n=1.670) | PROGRESS_LOG 12/11 (kiểm lại bộ lọc trước khi trích) |
| Tháng chấm 2018-08 | 1.278 seller; 342 seller ≥5 đơn; 6.540 đơn hợp lệ | PROGRESS_LOG 11/11 |
| P2 mặc định (số tạm 12/11) | 7 seller (hạng Theo dõi); GMV ảnh hưởng 0,3%; đơn xấu P0 685,2 → P2 682,0 (−0,5%) | PROGRESS_LOG 12/11 |
| G1, G6, pytest | 173 seller; 380/3.095 (12,3%); 38 passed | SPEC §10, PROGRESS_LOG 12/11 |

### C2. [CẦN SỐ]: phải lấy từ lần chạy thật
1. M1 (`dss.model_eval`): AUC, Brier, base_rate, n_train/n_test orders, tháng test.
2. 10 bin calibration (`dss.model_calibration`).
3. Hệ số logistic và contribution của 1–2 seller mẫu (`dss.seller_risk_contrib`).
4. Phân phối p_bad tháng 2018-08 và số seller theo hạng 1/2/3.
5. Kết quả P1, xác nhận lại P0/P2 sau lần chạy Job DSS cuối.
6. Goal seek: θ1, %GMV, số seller. Budget seek: k và ràng buộc binding.
7. Tornado low/high cho e_k, r, s.
8. `etl_audit` của 1 run hoàn chỉnh và `rows_dropped_by_dedup`.
9. Số dòng còn Pending (DESIGN §5): silver reviews, reviews_dedup, geolocation_zip, fact_seller_monthly, dim_date/dim_month.
10. Thời gian chạy Job ETL và Job DSS; latency một truy vấn OLAP.
11. Idempotency: số dòng Gold sau 2 lần chạy liên tiếp.
12. Insight có số cho 5 phép OLAP (bộ lọc mặc định 2017-02 → 2018-08).
13. Số dòng `dss.decision_log` sau demo.
14. Test khả dụng: thời gian và số click cho 3 câu hỏi của manager.

## D. Câu hỏi hội đồng có thể hỏi
| # | Câu hỏi | Mục trả lời |
|---|---|---|
| 1 | Lakehouse có phải DW không? Gold thỏa 4 đặc tính Inmon thế nào? | 2.1, 3.4, 4.5 |
| 2 | Vì sao 3 fact? Grain của seller-tháng là gì, và vì sao không cộng `n_orders` qua seller? | 4.1, 4.3 |
| 3 | Bronze/Silver overwrite mà Gold MERGE, có mâu thuẫn không? Sao không làm incremental? | 4.4 |
| 4 | Vì sao chọn logistic regression? Tránh leakage thế nào? Mô hình calibrate tốt không? | 5.5, 6.2 |
| 5 | e_k, r là giả định, vậy khuyến nghị có đáng tin không? | 5.4, 5.6, 6.3 |
| 6 | P2 chỉ giảm ~0,5% đơn xấu, DSS có giá trị gì? | 6.2 |
| 7 | Bàn giao trễ khác giao trễ ở đâu? Xử lý đơn nhiều seller và review dùng chung ra sao? | 4.3 |
| 8 | DSS khác dashboard ở đâu? Bằng chứng DSS đọc từ DW? | 3.5, 5.3 |

## E. Mâu thuẫn giữa docs và code
1. App có **6 trang**, không phải 5. Tên trên menu trong `app.py` (Tổng quan kinh doanh / Phân tích đa chiều / Cảnh báo seller / Chọn chính sách) khác README và SPEC §7 (Sức khỏe marketplace…). SPEC §9 vẫn ghi "năm trang".
2. Docs vẫn ghi "app **local**" dù app đã deploy. S2 vẫn ghi "chưa chạy".
3. **GMV bị ảnh hưởng:** SPEC §8 ghi chỉ tính seller *bị tạm ngưng*, nhưng `policy.simulate` tính `gmv·(1−r)` cho **mọi** seller bị gắn cờ, kể cả hạng Theo dõi. Cần chọn sửa code hoặc viết đúng theo code.
4. Tập train M1 (≥10 item × ≥6 tháng) khác tập chấm (≥5 đơn tại 2018-08), tức có distribution shift.
5. Đặc trưng M1 chưa chuẩn hóa trong khi dùng L2 mặc định, nên không so sánh trực tiếp được độ lớn hệ số.
6. RTM trong SPEC đã cũ: R06/R07 vẫn ☐, R44 ☐ dù code eval đã có, R40 và SPEC §5 vẫn ghi "Bảng chưa tạo".
7. SPEC §8 ghi DSS có phần knowledge-driven, nhưng R43 ghi "không làm", trong khi `recommend.py` có luật đơn giản.
8. SPEC nhắc backtest nhưng repo không có code backtest.
9. `olist_seller_performance.lvdash.json` (AI/BI) vẫn nằm trong repo dù SPEC ghi "không chọn".
10. `docs/report/` được nhắc trong SPEC nhưng chưa tồn tại.
11. `overwrite()` trong `dss_job.py` thực chất là DELETE rồi append.
12. Số P0/P2 là số tạm ngày 12/11, phải xác nhận lại sau lần chạy Job DSS cuối.
