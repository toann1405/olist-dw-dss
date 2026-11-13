# PROGRESS LOG

## Hướng dẫn cho AI/người mới
1. Thứ tự đọc: `README.md` → `docs/SPEC.md` → `docs/PLAN.md` → **mục đầu tiên** của nhật ký bên dưới (mới nhất ở trên).
2. Sau **mỗi phiên làm việc**, cập nhật khối "Trạng thái hiện tại" và thêm một mục nhật ký mới **ở trên cùng**.
3. Không đổi quyết định đã chốt trong SPEC mà không ghi lý do ở đây và cập nhật SPEC §10.
4. Ghi rõ ai làm gì (phục vụ peer review — đề mục 1.3).

## Trạng thái hiện tại

| Mục | Nội dung |
|---|---|
| Phase hiện tại | Trước hạn 15/11: app Streamlit sáu trang (Home + bốn câu hỏi + Dữ liệu & phương pháp). Power BI là future work. T1 chốt 15/10/2026. X=10, N=40. Tháng chấm DSS 2018-08 |
| Đang làm | Branch `feat/policy-review`: siết hàng nút Áp dụng / Đặt lại trên tab Giả định. R09 vẫn ◐. Checkbox PLAN Phase 4/5 chưa tick |
| Blocker | Không |
| Việc tiếp theo | Chạy lại job DSS để tab Độ tin cậy có số của warehouse. Chưa mở PR. Báo cáo PDF và slide vẫn còn |
| Cập nhật | 13/11/2026 (nút form giả định sát nhau) |

---

## Nhật ký

### 13/11/2026 — Nút Áp dụng và Đặt lại sát nhau

- **Đã làm:** Tab Giả định bỏ hàng `st.columns([1.2, 2.2, 4.6])`. Hai nút nằm trong cột hẹp căn trái, rồi hai cột compact `gap="small"`. Giữ nhãn, `type="primary"` và `on_click=_reset_params`. Không đụng logic DSS. Giữ tooltip hover của tiêu đề khối. Không tick PLAN. R09 vẫn ◐. Không đổi SPEC §10.
- **Đã chạy:** Đã mở `http://localhost:8501/policy`, tab Giả định. Hai nút cùng hàng, cùng cao 40px; khoảng cách đo được 26px; không còn khoảng trống rộng giữa chúng.
- **Chưa làm:** không chạy pytest trong phiên này.

### 13/11/2026 — Badge sát title, bỏ nút ?

- **Đã làm:** `page_header` đặt nhãn Thực tế/Dự báo ngay sau câu hỏi, nút Làm mới vẫn bên phải. Tab Độ tin cậy dùng `help=` trên segmented control. Tiêu đề khối giả định dùng tooltip hover, không còn `st.popover("?")`. Không tick PLAN. R09 vẫn ◐. Không đổi SPEC §10.
- **Đã chạy:** Đã mở `http://localhost:8501/policy`. Badge «Dự báo» đứng sát «Chọn chính sách nào?». Tab Độ tin cậy không còn nút `?`. Tab Giả định còn dấu `?` nhỏ cạnh tiêu đề khối, hover chứ không phải button.
- **Chưa làm:** không chạy pytest trong phiên này.

### 13/11/2026 — Form giả định không ghi đè slider

- **Đã làm:** Nút Áp dụng trên tab Giả định chỉ ghi `applied` rồi `st.rerun()`. Không gán lại key `draft_*` sau khi slider đã được tạo. Nút Đặt lại về mặc định và Dùng ngưỡng gợi ý này vẫn ghi slider trong callback. Không tick PLAN. R09 vẫn ◐. Không đổi SPEC §10.
- **Đã chạy:** Đã mở `http://localhost:8501/policy`. Đưa số đơn tối thiểu lên 11 rồi bấm Áp dụng: caption thành «tùy chỉnh» và «≥ 11 đơn», không còn `StreamlitAPIException`. Bấm Đặt lại về mặc định: caption về «tham số mặc định» và «≥ 5 đơn».
- **Chưa làm:** không chạy pytest trong phiên này.

### 12/11/2026 — Ghi đánh giá M1 cho tab Độ tin cậy

- **Đã làm:** `train_and_score` trả thêm calibration (decile xác suất trên đơn test: `bin`, `mean_pred`, `observed_rate`, `n`) và đóng góp từng seller ở tháng chấm (`seller_id`, `feature`, `value`, `contribution`). `feature` ghi nhãn tiếng Việt từ `FEATURE_LABELS`; khóa huấn luyện không đổi. Nhánh baseline trả hai DataFrame rỗng. Job DSS `overwrite` `model_eval` (auc, brier, n_train_orders, n_test_orders, base_rate, kèm `test_month` = yyyyMM), `model_calibration` và `seller_risk_contrib`, `as_of_month` là tháng chấm. Tab Độ tin cậy đổi bảng metric thành 3 thẻ AUC, Brier, Tháng test. Không tick PLAN. R09 vẫn ◐. Không đổi SPEC §10.
- **Đã chạy:** `python -m pytest src/tests -q` → 38 passed in 17.39s. Khung giả: không quá 10 bin, tổng `n` bằng số đơn test, tổng contribution cộng intercept khớp logit.
- **Chưa làm:** không chạy job DSS trong phiên này, nên bảng Delta và tab live chưa có số mới.

### 12/11/2026 — Trang Cảnh báo seller khớp M2

- **Đã làm:** `min_orders` đọc từ session rồi `simulate(..., PolicyParams(min_orders=...))`. Thẻ và caption P2 lấy `n_sellers_flagged`, `gmv_affected_pct`, `meets_x` từ scenario; đơn xấu chưa can thiệp là `baseline_bad`. Help bốn thẻ từ params. Bộ lọc Danh sách dùng `st.selectbox`. `TIER_NAME` chuyển vào `recommend.py`. Pareto theo `baseline_bad`, scatter ngưỡng `THETA_1` nét `dot`. Caption Độ tin cậy đổi câu review nhiều seller. Không tick PLAN. R09 vẫn ◐.
- **Đã chạy:** `python -m pytest src/tests -q` → 36 passed in 13.68s. Test 3 seller: flagged 2, hạng 1 và 2 mỗi loại một, GMV thẻ = `simulate(...).gmv_affected_pct`. Đã mở `http://localhost:8502/risk`: 342 / 1.278; gắn cờ 7 (Theo dõi 7); GMV 0,3% Trần 10% Đạt; baseline 685,2 chiếm 1,9%; P2 còn 682,0 (giảm 0,5%). Bốn thẻ có dấu ?. Vùng/Hạng là selectbox. Caption Độ tin cậy: «Đơn có nhiều seller không được tính review cho từng seller.»

### 12/11/2026 — Câu kết luận trang Cảnh báo seller

- **Đã làm:** Câu dưới «Seller nào đáng lo nhất?» lấy tháng sau tháng chấm, số seller vượt ngưỡng P2 trên số seller đủ điều kiện, và phần đơn xấu dự kiến (`expected_bad` của P2) của nhóm đó. Hết câu chỉ ba mã seller. Không đổi mô hình, ngưỡng, hay SQL. Không tick PLAN. R09 vẫn ◐.
- **Đã chạy:** Hàm câu trên khung mẫu in «Tháng 2018-09 dự kiến có 2/4 seller… gom khoảng 18,0%…». Đã mở `http://localhost:8502/risk`: «Tháng 2018-09 dự kiến có 7/342 seller vượt ngưỡng rủi ro (chính sách P2), gom khoảng 1,4% đơn xấu dự kiến; xem danh sách bên dưới để chọn seller cần xử lý.» Tháng chấm 2018-08, 342/1.278 seller, thẻ đơn xấu dự kiến 682,0.

### 12/11/2026 — SQL Ad hoc dễ đọc

- **Đã làm:** `build_query` không thêm điều kiện người dùng khi lọc là Tất cả (`None`), nên hết dạng `(? IS NULL OR ...)`. Giữ sentinel `seller_key <> -1` (và khóa `-1` của tháng/ngày) vì bỏ chúng có thể đổi tổng. Câu chạy vẫn gắn `?` và tuple tham số, không ghép chữ người dùng vào SQL thực thi. Hộp SQL gọi `readable_sql`: `sqlparse` xuống dòng, từ khóa viết hoa, chuỗi trong nháy đơn; chuỗi đó không được chạy. Thêm `sqlparse` vào `src/frontend/requirements.txt`. Không tick PLAN. R09 vẫn ◐. Không đổi SPEC §10.
- **Đã chạy:** `python -m pytest src/tests -q` → 35 passed in 17.15s. GMV theo Vùng vẫn `13494400.74`. Norte bàn giao trễ vẫn 19,2%. Đã mở `http://localhost:8501/olap`, tab Tự khám phá: Tất cả thì SQL không có `IS NULL OR`, WHERE còn sentinel; Vùng = Sul có `s.region_name = 'Sul'`.

### 12/11/2026 — Caption cách đọc dưới biểu đồ

- **Đã làm:** `chart_card` và `chart_note` bỏ popover "Cách đọc". Nếu có câu đọc thì `st.caption` ngay dưới chart, trên dòng "Ẩn … nhóm" hoặc "Điểm mờ". Câu rỗng thì không render. Mỗi câu rút còn một câu: bản đồ, cột địa lý, scatter nhóm hàng, các chart Seller risk và tornado chính sách. Bản đồ bang: cao 640, title neo đáy vào mép trên của plot, margin trên 88, domain geo đầy vùng vẽ. Không đổi số liệu. Không tick PLAN. R09 vẫn ◐.
- **Đã chạy:** `python -m pytest src/tests -q` → 31 passed in 9.52s. Đã mở `http://localhost:8501/kpi`, tab Xảy ra ở đâu: không còn nút "Cách đọc". Caption dưới bản đồ là "Màu càng đậm, tỷ lệ càng cao; bang xám là bang có dưới 30 đơn." Khoảng từ đáy title tới bản đồ 26px, bản đồ cao 470px. Câu cột vùng đứng trên dòng "Ẩn 1 nhóm…".

### 12/11/2026 — Query khi bấm nút

- **Đã làm:** Sidebar bọc trong `st.form("global_filters")`. Nút Áp dụng ghi `applied_filters`; `filters()` chỉ trả dict đã áp dụng. Nút Đặt lại về 2017-02 → 2018-08. Tab Ad hoc bọc trong `st.form("adhoc_form")`, nút Chạy truy vấn mới gọi `run_query`. Đổi Cột/Đường/Bảng không query lại. `run_query` cache 600 giây theo tuple tham số đã sort. Không đổi công thức và năm tab OLAP cũ. Không tick PLAN. R09 vẫn ◐.
- **Đã chạy:** `python -m pytest src/tests -q` → 31 passed in 38.73s. Cùng tham số chỉ gọi warehouse một lần. Đã mở `http://localhost:8501/olap`: trước khi bấm chỉ có câu "Chọn chỉ số, chiều rồi bấm Chạy truy vấn". Bấm một lần, GMV theo Vùng, Sudeste cao nhất R$ 10,57 tr.

### 12/11/2026 — Tab Ad hoc trên OLAP

- **Đã làm:** Tab thứ 6 `Tự khám phá (Ad hoc)` trên `fix/olap-page`. `src/frontend/lib/adhoc.py` có `MEASURES`, `DIMENSIONS` và `build_query`. Tỷ lệ là `SUM(tử)/SUM(mẫu)` đúng công thức trong `lib/queries.py` và roll-up item. Giá trị lọc đi theo tham số. `GROUP BY`, `ORDER BY`, `LIMIT 500`. GMV không gắn nhóm danh mục vì fact tháng không có product. Năm tab cũ, công thức KPI và `src/dss` không đổi. Không tick PLAN. R09 vẫn ◐. Chưa mở PR.
- **Đã chạy:** `python -m pytest src/tests -q` → 30 passed in 44.19s. GMV theo Vùng cộng lại `13494400.74`. Tỷ lệ bàn giao trễ Norte làm tròn 19,2%. Đã mở `http://localhost:8501/olap`: GMV × Vùng (Sudeste R$ 10,57 tr), tỷ lệ bàn giao trễ × Vùng (Nordeste 14,4%, n=1.670), GMV × Tháng (2017-11 R$ 1,00 tr). Có Tải CSV và Xem SQL.

### 12/11/2026 — Bỏ nhãn mẫu nhỏ khỏi legend

- **Đã làm:** Xóa mọi `add_legend_swatch` gọi `small_n_label()` trên KPI và OLAP, rồi xóa hàm đó trong `lib/ui.py`. Giữ `MIN_N_DISPLAY`. Chart xếp hạng (roll-up, slice, dice, cột top N, cột ad hoc) không vẽ nhóm có n dưới ngưỡng và có caption đếm số nhóm ẩn. Trend và scatter vẫn làm mờ điểm mẫu nhỏ, thêm câu "Điểm mờ: dưới 30 mẫu", không có mục legend. Heatmap pivot đổi phụ đề thành "ô trống khi dưới 30 mẫu", ô trống giữ nguyên. Cột bảng seller risk đổi thành "Ít đơn (<30)". Dòng "cao nhất" chỉ xét n ≥ `MIN_N_DISPLAY`. Không đổi loại chart, SQL, công thức KPI, `src/dss`. Không tick PLAN. R09 vẫn ◐.
- **Đã chạy:** `python -m pytest src/tests -q` → 30 passed in 37.70s. Đã mở `http://localhost:8501/kpi`, `/olap` và `/risk`. Legend không còn chữ "Mẫu nhỏ". KPI có caption điểm mờ và "Ẩn 1 nhóm có dưới 30 mẫu". OLAP roll-up "Ẩn 1 nhóm…", drill "Điểm mờ: dưới 30 mẫu", slice "Ẩn 201 nhóm…", dice "Ẩn 10 nhóm…", pivot có phụ đề ô trống. Bảng risk có cột "Ít đơn (<30)".

### 12/11/2026 — Title chart roll-up bị cắt

- **Đã làm:** Title roll-up không còn ghim `y=1` theo mép container, vì câu hỏi bị cắt ở cả Vùng, Bang và Thành phố. Title neo vào mép trên của plot, margin trên cố định, chú giải nằm dưới dòng phụ. Cùng một cách cho cả ba mức. Chưa commit.
- **Đã mở:** `http://localhost:8501/olap`, mức Vùng: câu "Bàn giao trễ là chuyện cả vùng hay một nơi?" và dòng "Mức Vùng…" hiện đủ, chú giải không đè câu hỏi.

### 12/11/2026 — Panel OLAP và nhãn tiếng Việt

- **Đã làm:** Branch `fix/olap-page` từ `fix/kpi-page`, chưa mở PR. Năm tab bỏ popover "Cách đọc". Dưới dòng cao nhất là 1–2 câu về phép OLAP và cách đọc chart. Câu hỏi chỉ còn ở title chart. Roll-up: nhãn Vùng/Bang/Thành phố, dòng cao nhất chỉ nhóm n ≥ `MIN_N_DISPLAY`, nhóm dưới ngưỡng vẫn vẽ nhưng mờ, margin top chart cố định. Slice và Pivot dùng chung bảng dịch nhóm danh mục, bỏ Unknown ở dropdown slice. Sidebar bỏ số thứ tự tên trang và caption "Đọc 1 → 4…". Không đổi loại chart, SQL, `src/dss`. Không tick PLAN. R09 vẫn ◐.
- **Đã chạy:** `python -m pytest src/tests -q` → 26 passed in 1.97s. Đã mở `http://localhost:8501/olap`. Năm tab không có popover "Cách đọc" và không lỗi. Roll-up hiện Vùng/Bang/Thành phố; khoảng từ nút Biểu đồ tới title chart là 0 px ở cả ba mức. Slice liệt kê tên nhóm tiếng Việt, không có Unknown. Pivot hiện "Dịch vụ và nhóm khác Q4 cao nhất". Menu không còn số thứ tự và caption "Đọc 1 → 4…".

### 12/11/2026 — Delta thẻ KPI và sparkline theo tháng

- **Đã làm:** Trên `fix/kpi-page`, chưa mở PR. Delta sáu thẻ đầu dùng dấu `-` ASCII để mũi tên và màu đúng hướng. Ẩn delta khi kỳ trước có dưới `MIN_ORDERS` đơn hợp lệ hoặc chứa tháng thưa. Help mỗi thẻ ghi kỳ so sánh, đơn vị (`%` hoặc điểm %), và xanh là tốt lên. Trang tách "Tổng quan kỳ" (sáu thẻ có delta và thẻ đơn trải nghiệm xấu) với "Xu hướng theo tháng" bằng `st.divider()`. Mỗi thẻ phần B nằm cùng sparkline trong một khung. Sparkline bỏ subtitle và legend, trục X chỉ tháng đầu và tháng cuối, tiêu đề "Theo tháng", điểm tháng cuối có giá trị. Thêm sparkline AOV = `gmv / n_orders_valid` từ `seller_month_series`. Không đổi loại chart, công thức KPI, `src/dss`. Không tick PLAN. R09 vẫn ◐.
- **Đã chạy:** `python -m pytest src/tests -q` → 26 passed in 1.63s. Kỳ 2015-07 → 2017-01 bị ẩn delta vì có tháng thưa; kỳ 2017-07 → 2018-01 đủ điều kiện. `signed_pct(-0.123)` ra `-12,3%`. Đã mở `http://localhost:8501/kpi` với 2017-02 → 2018-08: sáu thẻ không có delta, help ghi kỳ 2015-07 → 2017-01, phần B có caption một dòng và sparkline AOV, trục X hiện `2017-02` và `2018-08`.

### 12/11/2026 — Một bộ chọn thời gian ở sidebar KPI

- **Đã làm:** Bước 1 trên branch `fix/kpi-page`, chưa mở PR. Bỏ "Năm mua" và toggle "Chỉ giai đoạn đủ dữ liệu". Sidebar giữ Từ/Đến tháng, chỉ tháng có đơn, mặc định 2017-02 → 2018-08. Thêm preset Đủ dữ liệu / 2017 / 2018 / Toàn bộ. Query KPI đang lọc `year` chuyển sang khoảng tháng. Vùng, bang, nhóm hàng và funnel giữ. Delta so với khoảng liền trước cùng số tháng; không có đơn thì ẩn delta. Từ tháng sau Đến tháng thì `st.warning` và dừng trang KPI. Không đổi chart, công thức KPI, `src/dss`. Không tick PLAN. R09 vẫn ◐. PLAN chỉ đổi chữ "lọc năm mua" thành "lọc khoảng tháng".
- **Đã chạy:** `python -m pytest src/tests -q` → 26 passed in 2.37s. Tháng có đơn: 2016-09 → 2018-10, 25 tháng (không có 2016-11). GMV không lọc và GMV 2016-09 → 2018-10 đều `13494400.74`, app hiện `R$ 13,49 tr`. Khoảng liền trước của Toàn bộ là 2014-07 → 2016-08, `gmv` null, đơn hợp lệ 0. Đã mở `http://localhost:8501/kpi`: preset Toàn bộ đặt 2016-09 → 2018-10, GMV `R$ 13,49 tr`, không hiện delta.
### 11/11/2026 — Bố cục consumption layer trên Streamlit

- **Đã làm:** Theo spec đã chốt cùng ngày. `page_header(title, conclusion, kind)` và `chart_card` trong `src/frontend/lib/ui.py`. Nhãn Thực tế / Dự báo một lần ở đầu trang. Chú thích chart vào popover. Trang Chính sách mở bằng thẻ khuyến nghị và nút Chốt; lập luận M2 nằm trong tab. Home chỉ còn KPI, X/N, bốn lối vào và một dòng độ mới. Trang mới `pages/method.py` nhận bối cảnh, cách đọc, lineage, giới hạn và giả định M1/M2. Menu: bốn trang câu hỏi, rồi *Dữ liệu & phương pháp*. Không tick checkbox PLAN. R09 vẫn ◐. SPEC §10 giữ dòng năm trang và đánh dấu đã thay.
- **Không làm:** không đổi figure Plotly, không đổi `lib/queries.py`, không đổi công thức M1/M2, không đổi cách ghi `dss.decision_log`. Không đo lại SQL Warehouse trong phiên này.

### 11/11/2026 — Bộ lọc sidebar trở lại dropdown

- **Đã làm:** Bảy bộ lọc trong sidebar (`Năm mua`, `Vùng seller`, `Bang seller`, `Nhóm danh mục`, `Từ tháng`, `Đến tháng`, `Funnel`) dùng `st.selectbox`. Bỏ popover nút. Trang OLAP và Seller risk vẫn khóa bộ lọc. Không đổi bộ chọn dạng nút ở trong trang. Không tick PLAN. R09 vẫn ◐.
- **Đã mở:** `http://localhost:8501/kpi` có 7 combobox. Mở "Năm mua" thấy Tất cả, 2016, 2017, 2018, 2019, 2020. `http://localhost:8501/olap` vẫn có dòng "Trang này không dùng bộ lọc" và 7 dropdown bị khóa. Không đo lại SQL.

### 11/11/2026 — App đọc cấu hình kho theo secrets, môi trường, rồi .env

- **Đã làm:** `src/frontend/lib/db.py` lấy từng biến theo thứ tự `st.secrets` → `os.environ` → `.env`. `load_dotenv` chỉ đọc file khi file đó có mặt; không có `.env` thì bỏ qua. Host nhận `DATABRICKS_HOST` hoặc `DATABRICKS_SERVER_HOSTNAME`, bỏ tiền tố `https://` / `http://` và dấu `/` cuối. Không có `secrets.toml` thì nuốt lỗi, không làm app sập. Câu lỗi đổi thành `Thiếu cấu hình kết nối: <tên biến>`, không ghi giá trị token. `.streamlit/secrets.toml` được gitignore; `config.toml` vẫn được theo dõi. Không tick checkbox PLAN. R09 vẫn ◐. Không đổi SPEC §10.
- **Đã chạy:** `python -m pytest src/tests/test_db_settings.py -q` → 8 passed in 1.69s. Có ca chỉ `.env`, ca chỉ `.streamlit/secrets.toml` (secrets thắng biến môi trường và `.env`), ca `st.secrets` ném lỗi vẫn đọc được `.env`, và `git check-ignore` cho `secrets.toml`. Không mở SQL Warehouse. `settings()` trên máy này thấy host, http_path và token đều có; host không còn tiền tố `http`. Không in token.

### 11/11/2026 — Đồng bộ README và docs/ với trạng thái hiện tại

- **Đã làm:** Viết lại `README.md` (11 mục). Thêm `docs/glossary.md`. Cập nhật SPEC v0.10 §7 (năm trang), PLAN v0.7 (đổi phạm vi 10/11, không tick checkbox), `architecture.md` (Job DSS tách khỏi ETL), DESIGN §6.6 (tháng chấm 2018-08, không `MAX(month)`), `data/README.md` (cửa sổ Gold đã đo). Copy ba ảnh app vào `docs/images/app_*.png` từ `docs/report/screenshots/`. Không sửa `src/`. Không tick PLAN/RTM.
- **Không làm:** không bịa số mới. Không đổi SPEC §10 grain/X/N. Không viết lại nhật ký cũ.

### 11/11/2026 — Chú giải roll-up mức state không còn đè cột

- **Đã làm:** Ở tab Roll-up, khi mức là `state`, hai mục chú giải ("Cao nhất", "Các nhóm còn lại") chuyển sang lề phải của biểu đồ. Mức region và city vẫn để chú giải phía trên. `style_fig` nhận `legend_side`. Không đổi SQL hay công thức.
- **Chưa đo:** không chạy lại câu SQL. Không tick PLAN. R09 vẫn ◐.

### 11/11/2026 — Tiêu đề và chú giải trên mọi biểu đồ

- **Đã làm:** Thêm `style_fig(fig, title, subtitle=None, legend=True)` trong `src/frontend/lib/ui.py`. Helper gọi `apply_theme` rồi ghi đè `margin.t`, đặt tiêu đề câu hỏi (cỡ 16, đậm, x = 0) và phụ đề kỳ/bộ lọc. Chú giải nằm ngang phía trên đồ thị. Trục phần trăm dùng `tickformat` `.0%` khi tiêu đề trục có `%`. Chữ "Mẫu nhỏ" đọc `MIN_N_DISPLAY`, không chép số 30. Bản đồ giữ `fitbounds`, bang xám khi mẫu nhỏ, colorbar có đơn vị. Không tick checkbox PLAN. Không đổi RTM.
- **Grep `st.plotly_chart` dưới `src/frontend`:** `kpi.py` (3), `kpi_panels.py` (8, trong đó bản đồ gọi `style_fig` rồi truyền cùng `figure`), `olap.py` (5, roll-up qua `_hbar` đã gọi `style_fig`), `seller_risk.py` (7), `policy.py` (1). Home không có Plotly.
- **Đã mở app** trên `http://localhost:8501`. Home không có biểu đồ. KPI, OLAP (năm tab), Seller risk và Policy đều hiện tiêu đề và chú giải. Ảnh nằm ở `C:\Users\Administrator\AppData\Local\Temp\cursor\screenshots\` (`home-clean.png`, `kpi-sparks-titled.png`, `kpi-trend-titled.png`, `kpi-map.png`, `kpi-seller.png`, `kpi-trust.png`, `olap-rollup.png`, `olap-drill.png`, `olap-slice.png`, `olap-dice.png`, `olap-pivot.png`, `risk-hist.png`, `policy-tornado.png`).
- **Git:** `style_fig` và các biểu đồ trong `kpi_panels.py` đã vào commit bản đồ `42e6cdb` vì hai việc sửa cùng file. Commit phiên này chỉ các trang còn lại.
- **Không làm:** không commit `.env` hay `data/raw`. Không đổi SPEC §10.

### 11/11/2026 — Bản đồ bang trên tab Xảy ra ở đâu

- **Đã làm:** Tab KPI "Xảy ra ở đâu" thêm bản đồ choropleth Brazil, radio bang seller / bang khách (mặc định bang seller), và selectbox "Chỉ số" cùng hàng với "Mức địa lý". Chỉ số và mức địa lý áp cho cả bản đồ và cột. Tử và mẫu phía seller là `SUM` trên `fact_seller_monthly`, cùng định nghĩa `kpi_late_by_region` (bàn giao trễ) và `seller_month_series` (các tỷ lệ còn lại, GMV). Bang khách dựng lại từ cờ đơn và item, mỗi đơn một lần. GeoJSON 27 bang ở `src/frontend/assets/brazil_states.geojson`, nguồn click_that_hood, giấy phép MIT, khóa `sigla`. Không tick checkbox PLAN. R09 đã là ◐, không đổi.
- **Đối soát** bộ lọc năm 2018, vùng tất cả, bang tất cả, địa lý seller, chỉ số bàn giao trễ. Cột mức Bang và bản đồ dùng cùng một khung số: 21 bang có mẫu, chênh lệch tuyệt đối lớn nhất của tỷ lệ là 0. Roll-up theo vùng khớp `kpi_late_by_region`: Centro-Oeste 95/827, Nordeste 171/1121, Norte 2/5, Sudeste 4481/49754, Sul 808/7979. Tổng tử/mẫu 5557/59686. GeoJSON có 27 mã. Bản đồ gắn đủ 27 mã, không mã thừa và không mã thiếu. Năm 2018 không có seller ở AC, AL, AM, AP, RR, TO; sáu bang đó vẫn được vẽ với n = 0. Mọi năm có seller ở 23 bang (thiếu AL, AP, RR, TO). Câu bang khách năm 2018 trả 27 mã, không mã lạ.
- **Đã mở app:** tab hiện bản đồ, cột ngang và scatter. Không đo lại GMV toàn sàn trong phiên này.
- **Không làm:** không đổi SPEC §10. Không commit `.env`.

### 11/11/2026 — Home bổ sung bối cảnh, người dùng và nguồn dữ liệu

- **Đối chiếu trước khi sửa:** ① câu hỏi business, 3 KPI, hai badge X/N đã có; thiếu tên app, câu DSS và badge Thực tế. ② và ③ chưa có. ④ bốn thẻ điều hướng đã có; thiếu tiêu đề, sơ đồ bước, badge loại số và dòng bộ lọc. ⑤ expander giải thích đã có; thiếu cách đọc hai badge, glossary ngắn (kể cả P0/P1/P2) và hai dòng M1/M2. ⑥ một dòng freshness và expander một câu đã có; thiếu dòng tháng chấm + job, sơ đồ tầng, expander kỹ thuật và giới hạn. Dòng freshness chuyển xuống khối ⑥.
- **Đã làm:** `src/frontend/pages/home.py` chỉ thêm phần thiếu. Số lấy từ SQL Warehouse, X/N từ `src/dss/params.py`, ngày chốt và tháng chấm từ glossary và `AS_OF_MONTH`. Không tick checkbox PLAN. R09 chuyển ◐ vì trang Home đã chạy, DoD cả frontend chưa xong.
- **Đã đo, bộ lọc trống, cùng câu với app:**

  | Ô trên Home | SQL | Giá trị | App |
  |---|---|---:|---|
  | Tổng GMV | `kpi_seller_month` không lọc, cột `gmv` | 13494400.74 | R$ 13,49 tr |
  | % đơn trải nghiệm xấu | `story_by_region` dòng tổng, 16444 / 98079 | 0.16766 | 16,8% |
  | Seller đang hoạt động | `active_sellers` | 3053 | 3.053 |
  | Khoảng thời gian đơn | min/max `dim_date.full_date` của `fact_order.purchase_date_key` | 2016-09-04 → 2018-10-17 | cùng chữ |
  | Số đơn | `COUNT(*)` `fact_order` | 99441 | 99.441 |
  | Số seller | `dim_seller` trừ khóa −1 | 3095 | 3.095 |
  | Số khách | `dim_customer` trừ khóa −1 | 96096 | 96.096 |
  | Số danh mục | `COUNT(DISTINCT category_pt)` trừ Unknown | 73 | 73 |
  | Số bang | `COUNT(DISTINCT state_code)` seller, trừ Unknown | 23 | 23 |
  | Đơn nhiều seller | `fact_order.n_sellers > 1` | 1278 | 1.278 |
  | Tháng ít đơn | tháng có dưới 1000 đơn | 2016-09, 2016-10, 2016-12, 2017-01, 2018-09, 2018-10 | cùng danh sách |
  | Tháng không có đơn | lỗ giữa min và max | 2016-11 | cùng chữ |
  | Chiều / sự kiện | `information_schema` tiền tố `dim_` / `fact_` | 7 / 3 | 7 chiều và 3 bảng sự kiện |
  | Job lần cuối | `MAX(scored_at)` muộn hơn `MAX(etl_audit.loaded_at)` | 2026-11-11 09:00:12 UTC; Gold 2026-11-07 11:47:01 UTC | 2026-11-11 09:00 UTC |

- **Đã mở:** trang Home trên `http://localhost:8501/`. Hai link Kaggle (Brazilian E-Commerce và Marketing Funnel) mở được. Không commit `.env`.

### 11/11/2026 — Tháng chấm không còn là tháng lịch cuối

- **Đã làm:** `AS_OF_MONTH` = `2018-08` trong `src/dss/params.py`. Job DSS chấm đúng tháng đó, không dùng `MAX(month)`. UI Seller risk và Policy chỉ đọc điểm của tháng này. Kỳ không đủ seller thì ẩn thẻ phần trăm, Pareto và insight. Thêm nhãn dự báo/thực tế và khung bài toán 30 giây trên Policy.
- **Đã đo trên Gold, `n_orders_valid` cộng theo seller-tháng:**

  | Tháng | Seller | Đủ ≥ 5 đơn | Đơn hợp lệ |
  |---|---:|---:|---:|
  | 2018-06 | 1175 | 312 | 6259 |
  | 2018-07 | 1261 | 304 | 6334 |
  | 2018-08 | 1278 | 342 | 6540 |
  | 2018-09 | 1 | 0 | 1 |
  | 2018-10 | 0 | 0 | 0 |

- **Chưa chạy:** notebook `src/dss/dss_job.py` trên Databricks. Bảng điểm hiện vẫn là tháng 2018-09 với 1 seller. Trước khi chạy job, hai trang báo kỳ 2018-08 chưa đủ dữ liệu. Sau khi chạy, `sellers` trong log phải là số seller của 2018-08, không phải 1.
- **Không làm:** không đổi công thức M1/M2. Không commit `.env`.

### 11/11/2026 — Seller risk theo hướng intelligence

- **Đã làm:** trang Seller risk đọc `dss.seller_risk_score` và join `dim_seller` (vùng, bang, thành phố, business_segment, lead_type, won_date). Hạng và đơn xấu dự kiến lấy từ `simulate(..., "P2", PolicyParams())`, không viết lại ngưỡng. `min_orders` vẫn là `MIN_ORDERS` = 5. Tab đánh giá hiện câu chờ khi chưa có `dss.model_eval`. DDL ba bảng contrib/eval/calibration được thêm vào job DSS, job chưa chạy lại.
- **Đã chạy:** `python -m pytest src/tests/test_recommend.py src/tests/test_stats.py` — 6 passed. Bảng điểm: 1 seller `25be943a321c8938947bdaabca979a90`, `p_bad` 0.345639, `n_orders_valid` 1, `q_bar` 1.0, `gmv` 145.0. P0/P1/P2 `expected_bad_orders` đều 0.3456389245948667, 0 seller bị gắn cờ. Trang hiện 0 seller đủ điều kiện / 1 seller tổng với ngưỡng 5 đơn. `p_bad` không đổi so với bảng đã ghi.
- **Chưa làm:** không ghi `seller_risk_contrib` hay `model_eval` vì không chạy lại job (chạy lại sẽ ghi đè điểm). Không có 3 seller để đối soát contribution. Không commit `.env`.

### 11/11/2026 — KPI và OLAP analytic

- **Đã làm:** thêm Wilson interval, Pareto, từ điển tách review seller / review sàn và bàn giao trễ / giao trễ tới khách. Trang KPI giữ sáu công thức cũ khi không bật giai đoạn đủ dữ liệu, funnel hay khoảng tháng. Thêm dải ràng buộc, hero trải nghiệm xấu, tab xu hướng / nơi phát sinh / seller / độ tin cậy. OLAP đổi tên tab theo câu hỏi SPEC, kết luận từng tab, CSV, pivot loại Unknown và làm mờ n < 30.
- **Đã chạy:** `python -m pytest src/tests/test_stats.py src/tests/test_insights.py` — 15 passed. Tổng GMV theo tháng, bộ lọc trống: 13494400.74. `market_quality` bộ lọc trống: đơn 98666, đơn nhiều seller 1278, review loại khỏi measure seller 1943, bad_orders 16444, bad_eligible 98079, late_orders 6534, late_eligible 96447. App trang KPI hiện GMV R$ 13,49 tr, đơn 98.199, AOV R$ 137,42, bàn giao trễ 10,1%, review seller 13,7%, cancel 0,5%.
- **Chưa làm:** bản đồ Brazil, histogram nguyên nhân, treemap. Không đổi SQL của năm phép OLAP đã khóa. Không commit `.env`.

### 11/11/2026 — Policy scenario theo logic quyết định

- **Đã làm:** trang Policy xếp ① what-if, ② goal seeking, ③ sensitivity (biểu đồ tornado), ④ chốt. Tên hiển thị ở `lib/labels.py`. `recommend_policy` sinh câu từ kết quả. Giả định nằm trong form "Áp dụng". `decision_id` là UUID. X=10 và N=40 vẫn khóa, không đưa vào slider. Không sửa `compare_policies`, `goal_seek`, `tornado` hay giá trị mặc định trong `src/dss/params.py`.
- **Đã chạy:** `python -m pytest src/tests/test_insights.py` — 12 passed. Tham số mặc định trên bảng điểm hiện có (1 seller): P0, P1 và P2 đều `expected_bad_orders` 0.3456389245948667, GMV bị ảnh hưởng 0.0, 0 seller, đạt cả hai trần. Hàm M2 không đổi nên trước và sau refactor là cùng ba số này. App mở được. Bấm "Dùng ngưỡng gợi ý này" đổi dòng chốt thành "ngưỡng gợi ý".
- **Kho:** `dss.decision_log` có 0 dòng, `decision_id` đang BIGINT. Đã DROP và CREATE lại với `decision_id` STRING. Smoke insert UUID `c35eb05c-026b-4065-b475-c275ccfc7675` rồi DELETE, đếm lại còn 0. Không bấm ghi từ UI hai lần.
- **Không làm:** không đổi công thức M2. Không commit `.env`.

### 11/11/2026 — Streamlit: kể chuyện cho business

- **Đã làm:** điều hướng 0–4 theo câu hỏi. `lib/glossary.py` là một nguồn định nghĩa. Insight trang 1–4 sinh từ dữ liệu (`lib/insights.py`), chỉ so nhóm có n ≥ `min_orders` (5). Query mới `story_by_region` và `active_sellers` dùng tham số, không f-string. Sáu KPI giữ SQL và công thức cũ. Không tick PLAN hay RTM.
- **Đã chạy:** `python -m pytest src/tests/test_insights.py` — 8 passed. Bộ lọc tất cả, sáu KPI: GMV 13494400.74, đơn hợp lệ 98199, AOV 137.418922188617, bàn giao trễ 0.10069651741293532, review xấu 0.13692249984370766, cancel 0.004733140088784384. Khớp số đã ghi 10/11. App hiện GMV R$ 13,49 tr, trải nghiệm xấu 16,8%, 3.053 seller. Insight tất cả: Norte 26,9% (n=26). Năm 2018: 17,4%, Norte 20,0% (n=5); tổng GMV 7341182.41, tử 9315, mẫu 53514. Trang Seller risk: "Chưa đủ dữ liệu để kết luận" vì bảng điểm không có seller với `min_orders` 5. Policy mở được, tháng chấm 2018-09, insight P1 trên snapshot hiện có (một seller).
- **Không làm:** không đổi grain, không sửa ETL, không commit `.env`.

### 11/11/2026 — Xóa file Power BI

- **Đã làm:** xóa `src/frontend/dashboard.pbix`, `dashboard.pbip`, `dashboard.Report/`, `dashboard.SemanticModel/`, và hai thư mục backup `_backup_pbip_20261110_114343`, `_backup_pbip_20261110_120846`. App Streamlit giữ nguyên. Không tick checkbox PLAN hay cột TT của RTM. Quyết định SPEC §10 (Power BI là future work) không đổi.
- **Không làm:** không xóa `src/frontend/olist_seller_performance.lvdash.json` (file Lakeview / AI/BI, không phải Power BI). Không sửa ETL. Không commit.

### 10/11/2026 — UI Streamlit: theme, Home, KPI card, tab OLAP

- **Đã làm:** theme sáng, `lib/ui.py`, sidebar lọc dùng chung, trang Home, KPI thành card và chart, OLAP thành 5 tab. Không đổi công thức tử/mẫu. Không tick PLAN hay RTM.
- **Đối soát cùng filter “Tất cả” và “2018 / Sudeste”:** GMV, số đơn, bàn giao trễ, review, cancel khớp từng số đã đo trước refactor (GMV tất cả 13494400.74, đơn 98199, trễ 11132/110550, review 13141/95974, hủy 467/98666). Tổng GMV theo tháng và theo vùng cũng ra 13494400.74 và 11132/110550.
- **Đã mở app:** Home, KPI, OLAP, Seller risk, Policy đều load. Seller risk với `min_orders` 5 vẫn trống vì bảng điểm chỉ có 1 seller với 1 đơn.
- **Việc tiếp theo:** chạy `src/dss/dss_job.py` để có đủ điểm seller.

### 10/11/2026 — OLAP Explorer hiện năm phép trên một trang

- **Đã làm:** `src/frontend/pages/olap.py` bỏ ô chọn một phép. Cùng một trang có roll-up (cột ngang), drill-down (đường hoặc vùng), slice (cột ngang), dice (cột nhóm) và pivot (ô nhiệt). SQL và cách chia tử/mẫu không đổi. Không tick PLAN hay RTM.
- **Đã chạy:** mở Streamlit, trang `/olap` vẽ đủ năm phần trên SQL Warehouse. Không đo lại số KPI.
- **Việc tiếp theo:** vẫn là chạy `src/dss/dss_job.py` để bảng điểm đủ seller.

### 10/11/2026 — Phase 4–5 — Một app Streamlit, đã chạy KPI trên warehouse

- **Đã làm:** gộp dashboard và DSS vào `src/frontend/app.py`. Power BI chuyển thành future work trong SPEC §7, §10, architecture, PLAN, DESIGN, README và rule `00`, `02`, `08`, `09`. App đọc `gold.*` và `dss.*` qua SQL Warehouse. Không đọc Volume hay Silver. Không sửa `src/etl/`. Không tick checkbox PLAN hay cột TT của RTM.
- **Đã chạy, phiên này:** `SELECT 1` trên SQL Warehouse thành công. Câu KPI không lọc năm/vùng: `gmv` = `gmv_from_items` = 13494400.74; bàn giao trễ 11132 / 110550 = 0.10069651741293532; review seller 13141 / 95974 = 0.13692249984370766; AOV 13494400.74 / 98199 = 137.418922188617; cancel 467 / 98666 = 0.004733140088784384. Cùng bộ lọc năm 2018 và vùng seller Sudeste: `gmv` = `gmv_from_items` = 5771299.43; bàn giao trễ 4481 / 49754; review seller 6164 / 43641; AOV 5771299.43 / 44641; cancel 223 / 44864.
- **UI:** mở Streamlit local, trang Tổng quan KPI hiện đúng các số không lọc ở trên. Trang OLAP Explorer vẽ roll-up theo vùng. Trang Seller risk với `min_orders` = 5 báo chưa có dòng. Trang Policy mở được. Không bấm nút ghi quyết định.
- **DSS trên warehouse, đếm trong phiên này:** `dss.seller_risk_score` 1 dòng, `n_orders_valid` = 1; `dss.policy_scenario` 3 dòng; `dss.decision_log` 0 dòng. Một dòng điểm không phải kết quả chấm toàn bộ seller. Không ghi AUC hay Brier.
- **Không làm:** không chạy lại notebook DSS, không INSERT `decision_log`, không tick R09. Connector trên máy này nhận tham số bằng `?`.
- **Việc tiếp theo:** chạy `src/dss/dss_job.py` trên workspace, rồi đối soát trang Seller risk và Policy với SQL Editor.

### 10/11/2026 — Phase 5 — Mã DSS tối giản, chưa chạy trên warehouse

- **Đã làm:** thêm view `src/sql/views/v_seller_features.sql` chỉ từ `gold.*`. Thêm `src/dss/params.py`, `policy.py`, `train.py`, notebook `dss_job.py` và skeleton `dss_job.yml`. Streamlit `src/frontend/dss_app.py` có bốn trang DSS và một ô SELECT. Ghi cột `dss` vào DESIGN §6.6. Influence diagram SPEC §8 đánh dấu bản cuối. `00_setup.py` cho phép bốn object DSS đã đặt tên, vẫn chặn tên lạ. Không thêm task vào job ETL. Không làm R43. Không tạo `requirements.txt`.
- **Kiểm tra local:** gọi `train_and_score`, `compare_policies`, `goal_seek` và `tornado` trên DataFrame giả. Hàm chạy xong và trả ba phương án. Đây không phải số của Gold, không ghi AUC hay Brier vào SPEC.
- **Không làm:** không chạy notebook trên Databricks, không tạo view trên warehouse, không ghi `dss.seller_risk_score`. Không tick checkbox Phase 5 trong PLAN. Không nối Power BI. Không commit.
- **S2:** chưa gửi `SELECT 1`. File `.env` có mặt nhưng `DATABRICKS_HOST`, `DATABRICKS_HTTP_PATH` và `DATABRICKS_TOKEN` đang trống. `import databricks` lỗi `ModuleNotFoundError`. Streamlit đã có. Hai phương án, chưa chọn: (1) điền ba biến và cài `databricks-sql-connector` sau khi nhóm đồng ý, rồi chạy lại `SELECT 1`; (2) giữ app hiện tại và chỉ mở UI sau khi S2 nối được. Không chuyển UI sang đọc CSV.
- **RTM:** R10, R31, R32, R33, R34, R35 sang ◐. R36, R37, R38 sang ☑ vì sơ đồ, bảng biến, phân loại và ánh xạ pha trong SPEC §8 được chốt. R42 giữ ☐.
- **Việc tiếp theo:** người dùng điền `.env` và chạy job DSS trên workspace. Nếu job in được `model_name`, AUC hoặc Brier, và ba dòng P0/P1/P2, lúc đó mới tick PLAN.

### 07/11/2026 — Phase 4 — Năm câu OLAP trên SQL Warehouse

- **Đã làm:** thêm `src/sql/olap_queries/` với năm file, mỗi file một phép SPEC §7. Chạy trên warehouse `Serverless Starter Warehouse`, id `cfb33f9733d84eff`, catalog `olist_catalog`. Cả năm câu `SUCCEEDED`, kết quả không bị cắt. Số dòng: roll-up 665, drill-down 634, slice 612, dice 13, pivot 9. Mức tất cả của roll-up: `late_items` 11132, `eligible_items` 110550, `late_ship_rate` 0.10069651741293532. Slice lọc ví dụ `electronics_it_telephony`. Tick checkbox năm câu trong PLAN. R08 và R25 sang ☑. R42 và Power BI giữ ☐.
- **Không làm:** không tạo `src/sql/views/`. Không mở Power BI. Không xuất CSV. Không tick R09. Không đếm lại `gold.etl_audit` của Job ETL. Không commit.
- **Power BI, chưa nối:** hostname `dbc-6a3fb372-922e.cloud.databricks.com`, HTTP path `/sql/1.0/warehouses/cfb33f9733d84eff`. Token để trong `.env`, không ghi ở đây. License Pro: dựng bằng Power BI Desktop, DirectQuery, rồi Publish lên app.powerbi.com. Không dùng nút Publish trong Catalog.
- **File đã sửa:** `src/sql/olap_queries/`, `docs/PLAN.md`, `docs/SPEC.md`, `docs/PROGRESS_LOG.md`.
- **Việc tiếp theo:** người dùng nối Power BI Desktop. Nếu không nối được, ghi hai phương án và dừng.

### 07/11/2026 — Phase 3 — Notebook Databricks-only, DDL về notebook

- **Đã làm:** bỏ lớp `_spark()` / `SparkSession.getActiveSession()`. `00_setup` chỉ tạo 4 schema và `gold.etl_audit`, rồi kiểm tra Volume, không tạo lại Volume. DDL Gold chuyển vào notebook Gold, `CREATE TABLE IF NOT EXISTS` trước MERGE, giữ kiểu, `NOT NULL`, CHECK và comment. Silver giữ `NOT NULL` bằng DDL trong `02_silver.py` và overwrite không `overwriteSchema`. Bronze không có DDL riêng vì không có ràng buộc và ghi tạo bảng STRING. Xóa bản `src/sql/ddl/` đã có trong working tree, không khôi phục và không giữ hai bản. `olist_etl.job.yml` vẫn là skeleton, không phải file deploy. Giữ logic GMV status null, seller `-1` trên snapshot tháng, audit 10 cột và DQ grain.
- **Không làm:** không Run now. Không tick PLAN. Không đổi trạng thái R02, R06, R07, R40, R41, R47. Không đổi grain, KPI, surrogate key. Không commit.
- **File đã sửa:** `src/etl/`, `docs/PLAN.md`, `docs/DESIGN.md` §9, `docs/SPEC.md` (đường dẫn bằng chứng), `docs/architecture.md`, `README.md`, `docs/PROGRESS_LOG.md`.
- **Tự kiểm:** static checks only. Chưa chạy Databricks nên không kết luận pipeline chạy được.
- **Việc tiếp theo:** gắn Job trên workspace và Run now.

### 06/11/2026 — Phase 3 — Chốt GMV, seller -1, rows_loaded

- **Đã làm:** `fact_seller_monthly` vẫn loại seller `-1` và tháng mua thiếu, đếm `rows_rejected`, không tạo dòng tháng cho `-1`. Audit ghi `rows_unknown_fk=0`. `gmv`, `n_orders_valid` và `n_items_valid` giữ đơn có `order_status` null. `rows_loaded` vẫn là số dòng source của lần MERGE. Notebook in thêm grain before/source/after, số khóa Gold không có trong source, và tổng price/GMV của source batch so với tổng bảng.
- **Không làm:** không Run now. Không tick PLAN. Không đóng R07, R40, R47.
- **File đã sửa:** `src/etl/04_gold_facts.py`, `src/etl/05_gold_seller_monthly.py`, `src/etl/_dq.py`, `docs/PROGRESS_LOG.md`.
- **Việc tiếp theo:** gắn Job trên workspace và Run now.

### 05/11/2026 — Phase 3 — Scaffold ETL Cloud

- **Đã làm:** viết notebook `src/etl/` (`00_setup` đến `05_gold_seller_monthly`, `_audit`, `_dq`), DDL `src/sql/ddl/`, và skeleton `src/etl/olist_etl.job.yml`. Bronze/Silver FULL LOAD OVERWRITE. Gold MERGE chỉ `WHEN MATCHED THEN UPDATE` và `WHEN NOT MATCHED THEN INSERT`. Trong task facts: `fact_order_item` trước, `fact_order` sau; cờ trễ vẫn là cờ mức đơn tính từ Silver. `gmv` chỉ cộng `price`. Schema `dss` để trống. Không đường local.
- **Không làm:** không Run now trên workspace. Không đo số dòng mới. Không pytest. Không tick checkbox PLAN. Không đóng R07, R40, R47.
- **File đã sửa:** `src/etl/`, `src/sql/ddl/`, `docs/PLAN.md` (một câu thứ tự fact), `docs/DESIGN.md` §9, `docs/PROGRESS_LOG.md`.
- **RTM:** R07 giữ ☐, R40 giữ ◐, R47 giữ ☐. R27 giữ ◐. R46 giữ ☐.
- **Việc tiếp theo:** trên Databricks, kéo Git folder, tạo Job serverless `olist_etl` với 6 task theo `src/etl/olist_etl.job.yml`, `run_id={{job.run_id}}`, rồi Run now.

### 05/11/2026 — Phase 3 — Plan ETL Cloud-only

- **Đã làm:** ghi plan Phase 3 chỉ trên Databricks. Job `olist_etl` có 6 task: setup → bronze → silver → gold dims → gold facts → `fact_seller_monthly`. Không task `dss`. Không `USE_SAMPLE`, không `data/sample/`, không pytest local. DQ Phase 3 là Delta constraints và cảnh báo in ở notebook. Trong task gold facts: `fact_order` trước, rồi copy `late_delivery_flag` sang `fact_order_item`.
- **Không làm:** không viết DDL, notebook, job, hay test. Không đo lại Volume. Không đóng R07, R27, R40, R46, R47. R27 giữ ◐. R46 giữ ☐ (S6, Phase 6, Phase 7). R41 giữ ☐.
- **File đã sửa:** `docs/PLAN.md` (v0.6), `docs/SPEC.md` (v0.9), `docs/DESIGN.md` §9, `docs/architecture.md`, `docs/PROGRESS_LOG.md`, `README.md`, `.env.example`, `.cursor/rules/` (`04-data-integrity`, `05-medallion-layers`, `07-spark-databricks`, `10-testing-dq`).
- **Quyết định:** SPEC §10, ngày 05/11/2026. ETL warehouse Phase 3 chỉ Databricks. Không sửa mục nhật ký cũ.
- **RTM:** không đổi trạng thái R07 ☐, R27 ◐, R40 ◐, R46 ☐, R47 ☐. R27 bỏ pytest khỏi sản phẩm Phase 3. R46 bỏ phase 3 khỏi cột phase.
- **Việc tiếp theo:** viết DDL và notebook theo checklist Phase 3. Checkbox vẫn trống vì load chưa chạy.

### 05/11/2026 — Phase 2 — Sửa hợp đồng trước khi sang Phase 3
- **Đã làm:** một luật hiện hành cho từng chủ đề. Gold `MERGE` chỉ `WHEN MATCHED THEN UPDATE` và `WHEN NOT MATCHED THEN INSERT`. Không `WHEN NOT MATCHED BY SOURCE THEN DELETE`. `dss.decision_log` do Streamlit append qua SQL Warehouse. Job ETL Gold không ghi bảng này. Job DSS vẫn ghi điểm và kịch bản. Bronze/Silver FULL LOAD OVERWRITE; Jobs setup → bronze → silver → gold dims → gold facts → `fact_seller_monthly` → dss; Power BI + Streamlit qua SQL Warehouse; `etl_audit` 10 cột; không `_batch_id`, không watermark trong hợp đồng hiện tại. `gmv` = `sum(price)`, freight là measure riêng. Review dùng chung là [GIẢ ĐỊNH]: grain (`review_id`, `order_id`), một review mới nhất mỗi `order_id`, cột `shared_review_type` (`none` / `same_seller` / `cross_seller`). Measure seller loại `cross_seller` và đơn nhiều seller. KPI sàn giữ `cross_seller`. Mẫu `COUNT(DISTINCT order_id)`. `late_flag` vẫn tính khi review bị loại. 789 `review_id` và 814 dòng thừa là số đã đo. Đỉnh tháng 3/2018 khoảng 1,6% vẫn là [GIẢ ĐỊNH]. Luật cuối chờ sensitivity top-40 sau Gold. X=10, N=40 giữ nguyên. Câu bị thay nằm ở SPEC §10, mục lịch sử.
- **Không làm:** không viết DDL, ETL, notebook, test. Không đo lại Volume.
- **File đã sửa:** `docs/DESIGN.md`, `docs/SPEC.md` (v0.8), `docs/PLAN.md`, `docs/architecture.md`, `docs/TOPIC_EVALUATION.md`, `docs/PROGRESS_LOG.md`, `README.md`, `data/README.md`, `.cursor/rules/` (`02-ambiguity-scope`, `05-medallion-layers`, `06-dw-modeling`, `07-spark-databricks`, `09-dss`).
- **Quyết định:** SPEC §10, ngày 05/11/2026. Dòng MERGE có nhánh xóa (26/10) và dòng review null trên fact (22/10, 26/10) đánh dấu superseded.
- **RTM:** không đổi mã. R28 giữ ⏸ deferred / future work.
- **Việc tiếp theo:** Phase 3, DDL và ETL theo hợp đồng đã sửa.

### 26/10/2026 — Tối: sửa nhận xét sau khi đơn giản hóa load
- **Đã làm:** review conflict in ở notebook, không ghi audit. `etl_audit` chỉ 10 cột đếm dòng. Đối soát `rows_read = rows_loaded + rows_dropped_by_dedup + rows_rejected` in trong cùng `run_id`. `rows_rejected` chỉ là dòng bỏ hẳn. Giá trị set null mà vẫn giữ dòng thì in DQ. `MERGE` Gold thêm `WHEN NOT MATCHED BY SOURCE THEN DELETE`, trừ member `-1`. Job DSS ghi điểm và kịch bản. Streamlit ghi thêm `dss.decision_log` qua SQL Warehouse. Sơ đồ: Gold → job DSS → `dss`; Gold và `dss` → SQL Warehouse → Power BI và Streamlit. R28 chuyển ⏸ deferred / future work vì đề cho phép incremental hoặc full refresh và dataset tĩnh. Tie-break thứ tự từ điển ghi vào quyết định 26/10.
- **Không làm:** không đổi grain, measure, SCD, surrogate key. Không viết DDL hay ETL. Không đánh dấu milestone Notion.
- **File đã sửa:** `docs/DESIGN.md`, `docs/SPEC.md`, `docs/PLAN.md`, `docs/architecture.md`, `docs/PROGRESS_LOG.md`, `README.md`, `.cursor/rules/` (`00-index`, `02-ambiguity-scope`, `03-docs-workflow`, `05-medallion-layers`, `06-dw-modeling`, `07-spark-databricks`, `09-dss`, `10-testing-dq`).
- **Quyết định:** bổ sung SPEC §10, cùng ngày 26/10/2026. Dòng lịch sử bị thay ngày 26/10 đánh dấu superseded. Dòng `snapshot_date` hằng số và ROLAP đánh dấu reinstated 26/10.
- **RTM:** R28 từ ☐ sang ⏸.
- **Việc tiếp theo:** Phase 3, DDL và ETL theo hợp đồng đã sửa.

### 26/10/2026 — Đơn giản hóa cách nạp
- **Đã làm:** ghi quyết định vì dataset tĩnh và ưu tiên tiến độ. Giữ star schema, `MERGE` theo grain, và DQ. Bronze và Silver là batch, FULL LOAD, OVERWRITE. Bronze thêm `_ingest_ts`, `_source_file`. Bỏ `_batch_id` và luật chọn bản giữa các lần nạp. Dedup trong file của review và geolocation giữ nguyên, cùng luật làm sạch §7. Gold là bảng Delta, `MERGE` idempotent, 7 dimension + 3 fact. `snapshot_date` = `DATE '2018-10-17'` trong config. `gold.etl_audit` còn 10 cột; cảnh báo geo, translation, conflict in ở notebook. Jobs: setup → bronze → silver → gold dims → gold facts → `fact_seller_monthly` → dss. Power BI là dashboard, Streamlit là truy vấn và DSS, OLAP là ROLAP qua SQL Warehouse. Incremental, append, CDF, Auto Loader ghi là future work (R28).
- **Không làm:** không đổi grain, measure, SCD, surrogate key. Không viết DDL, ETL, notebook, test. Không đánh dấu milestone Notion.
- **File đã sửa:** `docs/DESIGN.md`, `docs/SPEC.md` (v0.7), `docs/PLAN.md`, `docs/architecture.md`, `docs/PROGRESS_LOG.md`, `README.md`, `.cursor/rules/` (`00-index`, `02-ambiguity-scope`, `05-medallion-layers`, `07-spark-databricks`, `08-sql-olap`, `09-dss`).
- **Quyết định:** SPEC §10, ngày 26/10/2026. Dòng append-only, watermark, cửa sổ review theo cột ingest, audit nhiều cột, và frontend còn mở chuyển vào lịch sử.
- **RTM:** R26 sang ☑ vì đã chọn ROLAP. R28 giữ ☐ và ghi future work. R45 giữ ☑, sửa chữ hợp đồng layer.
- **Việc tiếp theo:** Phase 3, DDL và ETL theo hợp đồng mới.

### 22/10/2026 — Phase 2 — Chiều: tie-break, seller-tháng, geolocation, category
- **Đã làm:** cửa sổ review thêm `NULLS LAST` và tie-break `_ingest_ts`, `_batch_id`. Tháng seller-tháng theo `order_purchase_timestamp`. `min_orders` mặc định 5 là tham số DSS, không lọc Gold. Geolocation một dòng mỗi prefix, fallback theo thành phố, haversine bỏ null. Category fallback `'Unknown'`. `pc_gamer` là ví dụ minh họa, chưa đo trên Volume.
- **Không làm:** không viết DDL hay ETL.
- **File đã sửa:** `docs/DESIGN.md`, `docs/SPEC.md`, `docs/PROGRESS_LOG.md`.
- **Việc tiếp theo:** Phase 3, DDL và ETL.

### 22/10/2026 — Phase 2 — Khóa grain review và review dùng chung
- **Đã làm:** `silver.order_reviews` giữ một dòng mỗi (`review_id`, `order_id`) bằng `ROW_NUMBER`, không chỉ bỏ dòng trùng y hệt. Thêm `silver.order_reviews_dedup`, một dòng mỗi `order_id`. `fact_order` chỉ đọc bảng dedupe. Review dùng chung nhiều seller vào cùng điều kiện loại review với đơn nhiều seller. Nhánh `late_flag` của trải nghiệm xấu vẫn tính. Mẫu tỷ lệ review là số `order_id` phân biệt.
- **Quyết định trong ngày, đã ghi SPEC §10:** GMV loại đơn `canceled` và `unavailable`; `n_orders_placed` / `n_orders_valid`, `n_items_placed` / `n_items_valid`, `aov`; `seller_ship_late_flag` null khi hủy và bằng 1 khi quá hạn chưa bàn giao; `snapshot_date` = `TO_DATE(watermark_cutoff_ts)`; luật review ở mục này.
- **Không làm:** không viết DDL, ETL, notebook, test. Không sửa `TOPIC_EVALUATION.md`. Không đo số đơn có seller_set nhiều seller. Câu 1,6% tháng 3/2018 ghi là [GIẢ ĐỊNH].
- **File đã sửa:** `docs/DESIGN.md`, `docs/SPEC.md`, `docs/PROGRESS_LOG.md`.
- **Việc tiếp theo:** Phase 3, DDL và ETL. Sau Gold, sensitivity check top-40 cho review dùng chung.

### 22/10/2026 — Phase 2 — Chốt snapshot, volume M1 và cờ giao trễ
- **Đã làm:** đóng ba điểm còn mở sau lần chỉnh GMV. `snapshot_date` lấy từ `watermark_cutoff_ts`; mỗi lần nạp tính lại `seller_ship_late_flag` khi cờ còn null hoặc đơn chưa có carrier. M1 dùng `n_orders_valid`. Đơn hủy ra khỏi `late_flag` và mẫu `late_delivery_*`. Thêm callout ở mục G3, không sửa câu kết quả cũ.
- **Không làm:** không viết DDL, ETL, notebook, test. Không đo lại.
- **File đã sửa:** `docs/DESIGN.md`, `docs/SPEC.md`, `docs/TOPIC_EVALUATION.md`, `docs/PROGRESS_LOG.md`.
- **Quyết định:** SPEC §10, ngày 22/10/2026. Dòng tách `snapshot_date` khỏi watermark được đánh dấu thay thế cùng ngày.
- **Việc tiếp theo:** Phase 3, DDL và ETL.

### 22/10/2026 — Phase 2 — Bổ sung luật đơn nhiều seller, cờ trễ, SCD và địa chỉ
- **Đã làm:** đối chiếu bốn quyết định với SPEC, DESIGN, TOPIC_EVALUATION. Chỗ đã khớp thì giữ. Bổ sung chỗ còn lệch: review của đơn nhiều seller để null trên `fact_order` (không chỉ ở snapshot tháng); `seller_ship_late_flag` khi thiếu carrier sau ngày chốt và khi đơn hủy; `dim_seller` SCD2-ready; địa chỉ khách chuyển từ `dim_customer` sang `fact_order`.
- **Không làm:** không viết DDL, ETL, notebook, test. Không chạy profiling. Không đo thêm số đơn thiếu carrier hay số đơn hủy.
- **File đã sửa:** `docs/DESIGN.md`, `docs/SPEC.md` (v0.6), `docs/TOPIC_EVALUATION.md`, `docs/PLAN.md` (một câu ở mục Phase 1: đơn nhiều seller để null, không xóa), `docs/PROGRESS_LOG.md`.
- **Quyết định:** ghi thêm SPEC §10. Dòng địa chỉ 15/10 đánh dấu thay thế. Dòng SCD1 15/10 giữ vì vẫn đúng. R41 vẫn là điểm cộng, chưa làm.
- **RTM:** R04, R23, R24, R29 giữ ☑ (phần thiết kế). R41 giữ ☐.
- **Việc tiếp theo:** Phase 3, DDL và ETL.

### 15/10/2026 — Phase 2 — Khóa thiết kế DW
- **Đã làm:** viết lại `docs/DESIGN.md` thành hợp đồng Phase 3. Sửa các lỗi thiết kế đã rà (cờ bàn giao có đủ 0/1/null, mốc đảo thành null kèm `raw_*` và `ts_inversion_flag`, grain review `(order_id, review_id)`, từ điển từng cột, Bronze giữ chuỗi gốc, nhãn `'Unknown'`, audit tách dedupe và reject, CHECK miền giá trị, 99.224 − 814 = 98.410, 547 là số đơn nhiều dòng review trên file thô). Khóa luật nhóm: 8 `category_group` (thêm `eletroportateis`), `size_band`, địa chỉ khách, một deal, thanh toán chính, SCD Type 1, cờ trải nghiệm xấu, so sánh ngày và timestamp, incremental theo `watermark_cutoff_ts` không sửa `order_status`.
- **Không làm:** không viết DDL, ETL, notebook, test. Không chạy profiling. Không đọc lại Volume nên không ghi số dòng IBGE mới.
- **Số giữ pending:** khóa trùng, số dòng review theo grain mới, số zip sau bbox, số seller-tháng, max của các mốc ngoài ngày mua.
- **File đã sửa:** `docs/DESIGN.md`, `docs/SPEC.md` (v0.5), `docs/PLAN.md` (10 mục Phase 2), `docs/PROGRESS_LOG.md`.
- **Quyết định:** ghi thêm ở SPEC §10. Dòng quyết định cũ giữ nguyên. R41 SCD2 vẫn là điểm cộng, chưa làm.
- **RTM:** R04, R05, R22, R23, R24, R29, R45 sang đã xong phần thiết kế. R02 và R36 giữ đang làm (DDL thuộc Phase 3; influence diagram vẫn là bản nháp).
- **Việc tiếp theo:** Phase 3, DDL và ETL.

### 15/10/2026 — Phase 1 — Ghi số đo Volume và chốt T1, X, N
- **Đã làm:** ghi kết quả `01_profiling.py` Run All trên Databricks (`SOURCE=volume`, `NOT_OFFICIAL=no`). Không viết ETL. Không upload Volume.
- **Cổng:** G1 pass 173/3.095; G2 pass 96.469/96.478; G3 pass 1.278/98.666; G4 pass 14.575/99.224; G5 pass 19/25 tháng; G6 record 380/3.095 (12,3%), `funnel_as_attribute_only=no`.
- **Quyết định nhóm:** giữ T1; trải nghiệm xấu = review ≤ 2 hoặc giao trễ hẹn; loại 1.278 đơn nhiều seller khỏi measure đó; giữ cửa sổ 2016-09-04 → 2018-10-17 (tháng thưa ghi hạn chế); X=10% GMV; N=40 seller/tháng.
- **File đã sửa:** `docs/SPEC.md` (v0.4), `docs/TOPIC_EVALUATION.md`, `docs/PLAN.md`, `docs/DESIGN.md` §7, `docs/PROGRESS_LOG.md`.
- **Còn mở:** đọc slide Ch6–7; upload IBGE vào `ref/`; S2, S3, S6; frontend OLAP; loại OLAP; thuyết trình; phân vai.
- **Việc tiếp theo:** Phase 2 thiết kế DW.

### 15/10/2026 — Phase 1 — Bỏ ngày lễ; snapshot bang → vùng IBGE
- **Đã làm:** nhóm bỏ lịch ngày lễ Brazil. Tạo `data/external/ibge_state_region.csv` từ API https://servicodados.ibge.gov.br/api/v1/localidades/estados (tải 15/10/2026). Không gọi API trong ETL. Không upload Volume. Không chạy profiling.
- **Số liệu (đếm file vừa ghi):** 27 dòng dữ liệu, 28 dòng kể header, 863 byte, 27 `state_code` phân biệt, 5 `region_name` (Norte, Nordeste, Sudeste, Sul, Centro-Oeste).
- **Lý do bỏ ngày lễ:** không có file 2016–2018 được phép đưa vào repo. `dim_date` chỉ dùng timestamp của đơn (ngày, thứ, cuối tuần).
- **File đã sửa:** `data/external/ibge_state_region.csv`, `data/README.md`, `docs/SPEC.md`, `docs/PLAN.md`, `docs/DESIGN.md`, `docs/TOPIC_EVALUATION.md`, `docs/PROGRESS_LOG.md`.
- **Quyết định:** ghi SPEC §10. Upload sau này vào `/Volumes/olist_catalog/bronze/raw/ref/`, không vào `funnel/` (thư mục đó chỉ có 2 CSV Marketing Funnel).
- **Việc tiếp theo:** upload file IBGE vào `ref/`, rồi Run `01_profiling.py` trên Databricks.

### 13/10/2026 — Phase 0 — S1, S4, S5 đạt
- **Đã làm:** ghi kết quả spike Cloud. Không viết ETL, không profiling.
- **S1 đạt:** catalog `olist_catalog`; schema `bronze`, `silver`, `gold`, `dss`; Volume `/Volumes/olist_catalog/bronze/raw/` với `olist/` (9 CSV) và `funnel/` (2 CSV). Dung lượng file trên Volume khớp `data/README.md` §3. `spark.read` `olist_orders_dataset.csv`: 99,441 dòng, mọi cột `string`.
- **S4 đạt:** job `s4_smoke`, compute Serverless, hai lần Run now thành công; lịch `11:04 PM` Asia/Saigon đã lưu và đang Paused. R40 chuyển ◐ vì Job ETL thật chưa gắn.
- **S5 đạt:** Git folder `olist-dw-dss`, nhánh `main`, repo `https://github.com/toann1405/olist-dw-dss.git`. Workspace thấy `README.md`, `docs/`, `src/`, `data/`.
- **File đã sửa:** `docs/PLAN.md`, `docs/SPEC.md` (v0.3), `docs/PROGRESS_LOG.md`, `README.md`, `data/README.md`, `.env.example`. `UC_CATALOG=olist_catalog` đã có trong `.env` (không commit).
- **Quyết định:** catalog và Volume khóa theo S1. Jobs và Git folder dùng được trên Free Edition. Không đổi kiến trúc SPEC §10 ngày 10/10/2026.
- **Còn mở:** S2, S3, S6; frontend OLAP; loại OLAP; AI/BI trên Free Edition.
- **Việc tiếp theo:** S2 (SQL warehouse từ Python local), rồi S3. S6 không chặn ETL Cloud.

### 13/10/2026 — Phase 0 — PLAN tách Cloud và Local
- **Đã làm:** viết lại `docs/PLAN.md` v0.3. Mỗi phase có mục **Cloud**, **Local → Cloud**, **Local**. Thứ tự hiện thực: Databricks trước; pyspark + delta-spark trên `data/sample/` (R46) làm sau khi phần Cloud tương ứng đã chạy.
- **Lý do:** nhóm cần biết việc nào làm trên workspace và việc nào làm trên máy. Không đổi kiến trúc SPEC §10, không thêm hoặc bỏ mã R-xx, không viết ETL.
- **File đã sửa:** `docs/PLAN.md`, `docs/PROGRESS_LOG.md`.
- **Quyết định:** không có quyết định kiến trúc mới. Chỉ thứ tự làm: Cloud trước, local sau.
- **Việc tiếp theo:** S1 trên Databricks (catalog, Volume, `spark.read`).

### 10/10/2026 — Phase 0 (sửa kiến trúc) — Đổi sang Databricks medallion; spike chưa bắt đầu
- **Đã làm:** cập nhật tài liệu từ stack PostgreSQL (đã khóa trong SPEC v0.1) sang medallion Databricks. Không viết ETL/DSS, không tạo file mới, không commit.
- **Lý do:** giảng viên cho phép cloud/Databricks và Power BI. Nhóm muốn lakehouse. Gold vẫn là star-schema DW (data mart Kimball bottom-up) nên vẫn đáp ứng mục tiêu 2–4 và điều kiện 3.1(a). Bỏ PostgreSQL, psycopg và schema `staging` / `dw` để không giữ hai kho. Quyết định PostgreSQL **thay thế ngày 10/10/2026** (giữ dòng cũ trong SPEC §10, không xóa).
- **File đã sửa:** `docs/SPEC.md` (v0.2), `docs/PLAN.md` (v0.2), `docs/DESIGN.md` (chỉ câu kiến trúc và nguồn DSS), `README.md`, `data/README.md`, `.env.example`, `.gitignore`, `docs/PROGRESS_LOG.md`. `docs/TOPIC_EVALUATION.md` không sửa vì không có câu nào nêu PostgreSQL, psycopg, DuckDB hay schema `staging`/`dw` là stack đã chọn.
- **Quyết định đã chốt (nhóm xác nhận 10/10/2026):** Bronze = staging (raw, append-only); Silver = làm sạch/conform; Gold = DW / data mart; `dss` = đầu ra DSS. Chỉ batch. PySpark + Spark SQL, notebook `.py`, Delta `MERGE`. DSS Python đọc chỉ từ Gold, ghi `dss.*`, huấn luyện trên Gold (lệch có chủ đích so với Silver, để đáp ứng mục tiêu 4). Audit: `gold.etl_audit`. Thêm R45 (BB\*), R46 (NC), R47 (ĐC). Đề tài T1, decision maker, alternatives, principle of choice, 3 fact, hierarchy, M1/M2 giữ nguyên.
- **[GIẢ ĐỊNH] chưa kiểm:** tên catalog và Volume (S1); Unity Catalog trên Free Edition (S1); SQL warehouse từ máy local (S2); Jobs (S4); Git folder (S5); AI/BI Dashboard trên Free Edition (quan sát lúc chốt frontend); pyspark + delta-spark local (S6).
- **Câu hỏi còn mở:**
  1. S1–S6 đạt hay không? Nếu không đạt: 2 phương án, chờ nhóm, không tự chọn.
  2. Frontend OLAP: Power BI Desktop, Databricks AI/BI Dashboard, hay Streamlit?
  3. Loại OLAP: ROLAP hay HOLAP? Chốt cùng frontend.
  4. Tên catalog Unity Catalog?
  5. Các mục Phase 1 vẫn mở: G1–G6, X, N, định nghĩa trải nghiệm xấu, thuyết trình, thành viên, ngày lễ / bảng IBGE.
- **Việc tiếp theo:** spike S1–S6 (hạn 13/10). Chưa bắt đầu.

### 10/10/2026 — Phase 0 — Finalize topic, stack, data, sample
- **Đã làm:** kiểm tra `data/raw/` đã có đủ 9 CSV Olist (nhóm tải tay) và `data/external/` đã có Marketing Funnel; chạy `python src/notebooks/00_verify_and_sample.py`; điền số liệu vào `data/README.md`; cập nhật README, SPEC, PLAN, TOPIC_EVALUATION; `git init` + 1 commit local (không push).
- **Script:** Missing/Extra vs expected = none. Integrity asserts: passed. Sample: 5,000 orders, seed 42. Thêm in nhẹ vào script có sẵn: `order_purchase_timestamp` min/max và bảng file `data/external/` (không tạo script mới).
- **Số liệu (từ output script, không profiling):**
  - orders 99,441 × 8 · items 112,650 × 7 · payments 103,886 × 5 · reviews 99,224 × 7 · customers 99,441 × 5 · sellers 3,095 × 4 · products 32,951 × 9 · geolocation 1,000,163 × 5 · translation 71 × 2
  - `order_purchase_timestamp`: min=2016-09-04 21:15:19, max=2018-10-17 17:30:18 (non-null=99,441/99,441)
  - Funnel: closed_deals 842 × 14 (0.16 MB); marketing_qualified_leads 8,000 × 4 (0.67 MB)
- **File đã sửa:** `README.md`, `data/README.md`, `docs/SPEC.md`, `docs/PLAN.md`, `docs/TOPIC_EVALUATION.md`, `docs/PROGRESS_LOG.md`, `src/notebooks/00_verify_and_sample.py`. `.gitignore` đã đúng (`docs/report/*.aux`, `dist/`, `*.egg-info/`, `*.zip`); không đổi. `data/sample/*.csv` sinh bởi script.
- **Quyết định đã chốt (nhóm xác nhận 10/10/2026):** T1 Seller Performance (có điều kiện G1–G6; dự phòng T2 cùng DW); stack PostgreSQL + Python 3.11+ (pandas, SQLAlchemy, psycopg) + Streamlit + scikit-learn/statsmodels + pytest; bottom-up data mart, fact constellation, ROLAP; Marketing Funnel dùng chắc chắn. Decision maker / quyết định / alternatives / principle of choice giữ SPEC §1.
- **Vấn đề phát sinh:** repo chưa có `.git/` khi bắt đầu phiên (PROGRESS_LOG phiên khởi tạo ghi đã `git init`) → `git init` lại rồi commit. Không tạo file tài liệu/code mới.
- **Câu hỏi còn mở (chuyển Phase 1 / nhóm tự làm):**
  1. G1–G6 đạt? Chốt cuối T1 hay chuyển T2?
  2. Giá trị X, N; định nghĩa "trải nghiệm xấu"?
  3. Thuyết trình trực tiếp hay video?
  4. Thành viên, MSSV, phân vai? (nhóm tự điền README)
  5. License ngày lễ Brazil và bảng bang→vùng IBGE?
- **Việc tiếp theo:** Phase 1 profiling + G1–G6. Nhóm tự làm: tạo GitHub và push; mỗi người cài PostgreSQL; điền bảng thành viên.

### 10/10/2026 — Phase 0 — Phiên khởi tạo
- **Đã làm:** đọc đề `CO4031_Assignment_HK261.pdf` và file phân tích; dựng repo `olist-dw-dss/` theo cấu trúc chuẩn; `git init` (nhánh `main`, chưa commit, chưa push); viết TOPIC_EVALUATION, SPEC, PLAN, DESIGN (khung), README, data/README; viết script kiểm tra + tạo mẫu.
- **Tải dữ liệu: CHƯA THÀNH CÔNG.** Kaggle CLI và `kagglehub` không có sẵn và không cài được; mọi kết nối ra ngoài lỗi phân giải tên miền (Kaggle, PyPI); không có `~/.kaggle/kaggle.json`. Không tạo dữ liệu giả. License đã đọc trực tiếp trên trang Kaggle: **CC BY-NC-SA 4.0** (cả dataset chính và Marketing Funnel).
- **Cách khắc phục cho nhóm:** làm theo `data/README.md` §2 (Kaggle CLI / kagglehub / tải bằng trình duyệt) → giải nén 9 CSV vào `data/raw/` → chạy `python src/notebooks/00_verify_and_sample.py` → dán bảng thống kê vào `data/README.md` §3.
- **File tạo:** `README.md`, `.gitignore`, `.env.example`, `docs/{TOPIC_EVALUATION,SPEC,PLAN,DESIGN,PROGRESS_LOG}.md`, `docs/assignment/*`, `data/README.md`, `src/notebooks/00_verify_and_sample.py`, `.gitkeep` ở thư mục rỗng.
- **Quyết định (đề xuất, chờ nhóm xác nhận):** đề tài **T1 – Seller Performance Management**; dự phòng T2 Delivery Promise (dùng lại cùng DW); stack PostgreSQL + Python + Streamlit + scikit-learn/statsmodels; bottom-up data mart, fact constellation, ROLAP.
- **Vấn đề phát sinh:** mục 4 (feasibility) chỉ làm được ở mức schema → "chờ dữ liệu", gom thành cổng G1–G6.
- **Câu hỏi mở:**
  1. Nhóm xác nhận T1 hay chọn T2?
  2. Thuyết trình trực tiếp hay video (đăng ký với giảng viên)?
  3. Thành viên, MSSV, phân vai?
  4. Giá trị mặc định X (% GMV bị ảnh hưởng), N (số seller xử lý/tháng), định nghĩa "trải nghiệm xấu"?
  5. Tuần 8 nhóm làm được bao nhiêu (PLAN giả định ~50%)?
  6. Dùng PostgreSQL hay DuckDB? Có cần Power BI không?
- **Việc tiếp theo:** tải dữ liệu; xác nhận đề tài/stack/vai trò; tạo repo GitHub; bắt đầu Phase 1.
