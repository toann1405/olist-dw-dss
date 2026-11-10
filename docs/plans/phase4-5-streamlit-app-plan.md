# Phase 4–5 Streamlit app — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Gộp dashboard Phase 4 và DSS Phase 5 thành một app Streamlit local. App đọc `gold.*` và `dss.*` qua Databricks SQL Warehouse, và chỉ append `dss.decision_log`.

**Architecture:** SQL nằm trong file `.sql`. `lib/queries.py` nạp file và gắn tham số. `lib/db.py` mở SQL Warehouse, cache câu đọc, và không cache câu ghi. Bốn trang chỉ gọi hai module đó. Job DSS hiện có (`src/dss/dss_job.py`) vẫn là chỗ ghi `dss.seller_risk_score` và `dss.policy_scenario`. App không huấn luyện lại và không ghi hai bảng đó.

**Tech Stack:** Python, Streamlit (`st.navigation` khi bản cài có API này), `databricks-sql-connector`, pandas, numpy (vì `src/dss/policy.py` dùng numpy). SQL Warehouse trên Databricks Free Edition, catalog `olist_catalog`.

**Trạng thái file này:** Bước 1, chờ duyệt. Chưa sửa SPEC, PLAN, code, và chưa commit.

## Global Constraints

- Quyết định 10/11/2026: một app Streamlit. Power BI ra khỏi scope hiện tại và ghi là future work. ROLAP qua SQL Warehouse giữ nguyên.
- App chạy local. Đọc `gold.*` và `dss.*` qua SQL Warehouse. Không đọc Volume, Bronze, Silver, `data/raw/`, `data/sample/`.
- Không đổi grain, measure, hay KPI đã khóa của Gold. `gmv` = `SUM(price)` của item thuộc đơn không `canceled` và không `unavailable`. Không cộng `freight_value`.
- Tỷ lệ trên app = tử / mẫu. Không `AVG` và không `SUM` cột `*_rate` hay `aov`. Dòng có cờ null không vào mẫu.
- Member `-1` không xuất hiện trong slicer vùng, bang, thành phố, hay `category_group`.
- `X = 10` (% GMV) và `N = 40` (seller/tháng) khóa từ 15/10/2026. `min_orders` mặc định 5 trên `n_orders_valid`.
- Streamlit chỉ `INSERT` vào `dss.decision_log`. Không `DELETE`, `UPDATE`, `MERGE`, hay overwrite bảng đó. Không `CREATE` schema.
- Job ETL Phase 3 (`src/etl/`) không sửa, trừ khi bước đối soát phát hiện conflict. Conflict thì dừng và báo, không vá ETL trong cùng PR.
- Không tick checkbox PLAN và không đổi cột TT trong RTM ở bước thực hiện, dù câu chữ SPEC có sửa.
- Không commit `.env`, token, hay `DATABRICKS_TOKEN`.
- Chat và `docs/` tiếng Việt. `README.md`, code, SQL, tên cột, commit: tiếng Anh.
- Số dòng, byte, và kết quả query chỉ ghi khi đã chạy trong phiên đó. Phiên viết plan này không đo warehouse.

## Cách đọc cần duyệt trước khi code

Những mục dưới đây là cách đọc tài liệu cho app. Duyệt plan tức là duyệt các cách đọc này.

1. **Vùng trên trang KPI** là `dim_seller.region_name` (vùng seller). Năm là năm của tháng mua (`dim_month.year`). Dice OLAP vẫn dùng vùng khách, đúng SPEC §7, và không lấy slicer của trang KPI.
2. **Thẻ “tỷ lệ review xấu”** dùng measure seller: `negative_review_count / negative_review_eligible`. Tập này đã loại đơn `n_sellers > 1` và `shared_review_type = cross_seller`. KPI sàn (giữ `cross_seller`, grain đơn trên `fact_order`) nằm ở phép drill-down, không nằm trên thẻ này.
3. **AOV và cancel rate khi gộp nhiều seller** không cộng `n_orders_valid`, `n_orders_placed`, hay `cancel_count`. Mẫu là `COUNT(DISTINCT order_id)`. SPEC định nghĩa `aov` và `cancel_rate` ở grain seller-tháng. Cách gộp này là cách đọc luật “không cộng đếm đơn qua seller” (DESIGN §3.6). Chưa có câu SPEC nào đặt tên cho AOV đã gộp.
4. **Năm trang 5–7 của SPEC §7** gộp vào hai trang DSS. Goal seeking và sensitivity ±20% nằm trên trang Policy, vì R34 và R35 đã có hàm trong `src/dss/policy.py`. Không cắt hai hàm đó.
5. **Ô SELECT tự do** trong `src/frontend/dss_app.py` không mang sang app mới. Đối soát làm trên SQL Editor.
6. **M1/M2 không viết lại.** App đọc bảng `dss` và gọi `policy.py` cho what-if. Các số θ, `e_k`, ngưỡng KPI cứng, `r`, `s`, khoảng cách hạng, và logic OR của P1 là quy ước trong `params.py`. SPEC chỉ đặt tên, không đặt các số đó. Danh sách nằm ở mục 4.
7. **File kèm quyết định đã chốt.** Ngoài SPEC §7, `architecture.md`, PLAN Phase 4/5 và README, bước 2 còn sửa SPEC §1, §4, §5, §9, §10, DESIGN (câu frontend), và rule `.cursor/rules/` `00-index`, `08-sql-olap`, `09-dss`. Không sửa thì phiên sau sẽ dựng lại Power BI.

---

## 1. Thay đổi docs — câu cũ → câu mới

Bước 2 sửa câu. Giữ nguyên cột TT của RTM và checkbox đã tick. Checkbox Power BI chưa tick thì đổi chữ việc, vẫn để trống.

### 1.1 `docs/SPEC.md` §7 — màn hình

Cũ:

> Truy vấn viết bằng Spark SQL trên Gold. OLAP là ROLAP qua Databricks SQL Warehouse. Dashboard là Power BI. Giao diện truy vấn và DSS là Streamlit. Kết nối từ máy local vẫn chờ S2 và S3.

Mới:

> Truy vấn viết bằng Spark SQL trên Gold. OLAP là ROLAP qua Databricks SQL Warehouse. Một app Streamlit local là dashboard KPI, OLAP Explorer và DSS. App đọc `gold.*` và `dss.*`. Không đọc Volume hay Silver. Power BI là future work, không thuộc scope hiện tại. Kết nối từ máy local vẫn là [GIẢ ĐỊNH] cho đến S2.

Cũ:

> **Danh sách màn hình.** Power BI: (1) Tổng quan KPI · (2) OLAP Explorer (5 phép) · (3) Hồ sơ seller (drill tới seller). Streamlit đọc Gold và `dss` qua SQL Warehouse (kết nối là **[GIẢ ĐỊNH]**, S2): (4) DSS – Điểm rủi ro · (5) DSS – What-if chính sách · (6) DSS – Goal seeking & sensitivity · (7) Quyết định & xuất danh sách. Mục 7 ghi thêm một dòng `dss.decision_log` qua SQL Warehouse. Streamlit không ghi `dss.seller_risk_score` hay `dss.policy_scenario`. Streamlit cũng là chỗ truy vấn ad-hoc trên Gold.

Mới:

> **Danh sách màn hình.** Một app Streamlit, bốn trang. (1) Tổng quan KPI: GMV, tỷ lệ bàn giao trễ, tỷ lệ review xấu theo measure seller, AOV, cancel rate, lọc năm mua và vùng seller. (2) OLAP Explorer: năm phép SPEC, mỗi phép một visual, SQL ở `src/sql/olap_queries/`. (3) Seller risk: đọc `dss.seller_risk_score`, lọc `min_orders` mặc định 5, xem một seller. (4) Policy scenario: chỉnh tham số, xem P0/P1/P2, goal seeking, sensitivity ±20%, xuất CSV seller bị gắn cờ, nút ghi quyết định append `dss.decision_log`. Trang 4 không ghi `dss.seller_risk_score` hay `dss.policy_scenario`. Không có ô SQL tự do. Power BI là future work.

Năm phép trong bảng §7 giữ nguyên câu hỏi và bảng nguồn. Không đổi chữ Roll-up, Drill-down, Slice, Dice, Pivot.

### 1.2 `docs/SPEC.md` — các câu Power BI còn lại

| Vị trí | Cũ | Mới |
|---|---|---|
| Khối trạng thái đầu file | `ROLAP, Power BI + Streamlit` | `ROLAP, một app Streamlit. Power BI là future work` |
| §1 Phạm vi | `OLAP ROLAP qua SQL Warehouse, dashboard Power BI; DSS mô hình rủi ro + mô phỏng chính sách, đọc Gold và ghi dss.*, giao diện Streamlit` | `OLAP ROLAP qua SQL Warehouse; một app Streamlit local làm dashboard và DSS, đọc Gold và dss, ghi thêm dss.decision_log. Power BI là future work` |
| §1 Ngoài phạm vi | câu hướng phát triển hiện tại, chưa có Power BI | thêm `Power BI` vào cuối danh sách hướng phát triển |
| §4 sơ đồ mermaid, nút `WH --> OL[Power BI dashboard]` và `WH --> ST[Streamlit]` | hai nút | một nút `WH --> ST[Streamlit dashboard va DSS]`. Giữ `ST -->|append decision_log| DL` |
| §4 hợp đồng layer | `Power BI và Streamlit đọc Gold và dss qua SQL Warehouse` | `Streamlit đọc Gold và dss qua SQL Warehouse` |
| §4 bảng Presentation | `Power BI dashboard đọc Gold qua SQL Warehouse (ROLAP); Streamlit đọc Gold và dss` | `Streamlit đọc Gold và dss qua SQL Warehouse (ROLAP). Power BI là future work` |
| §4 bảng Công nghệ, dòng OLAP frontend | `Power BI: dashboard... Streamlit: giao diện truy vấn và DSS, không phải dashboard OLAP` và cột còn mở `Kết nối Power BI tới SQL Warehouse ([GIẢ ĐỊNH], S3)` | `Streamlit: một app local, dashboard KPI + 5 phép OLAP + DSS, đọc Gold và dss qua SQL Warehouse`. Cột còn mở: `Kết nối Streamlit ([GIẢ ĐỊNH], S2)`. Cột không dùng: thêm `Power BI: future work từ 10/11/2026` |
| §5 câu loại OLAP | `Power BI là dashboard` | `Streamlit là lớp trình bày. Power BI là future work` |
| §8 UI | `Trang 4–7: Streamlit local...` | `Bốn trang Streamlit ở §7. Trang Policy append dss.decision_log. Kết nối vẫn [GIẢ ĐỊNH], S2` |
| §8 Implementation | giữ CSV và `decision_log` | không đổi nghĩa. Chỉ bỏ chữ “mục 7” nếu còn trỏ số màn hình cũ, thay bằng “trang Policy” |
| §9 dòng `src/frontend/` | `Power BI (dashboard, chưa nối) và Streamlit dss_app.py (truy vấn / DSS). S2 chưa đạt` | `Một app Streamlit (app.py). Power BI là future work. S2 chưa đạt` |
| R09 cột sản phẩm | `src/frontend/` | giữ đường dẫn. Không đổi ô TT `☐` |
| R26 nội dung | `ROLAP qua Databricks SQL Warehouse. Power BI đọc Gold. Streamlit là giao diện truy vấn và DSS. HOLAP và MOLAP không dùng` | `ROLAP qua Databricks SQL Warehouse. Một app Streamlit đọc Gold và dss. Power BI là future work. HOLAP và MOLAP không dùng` |

R26 giữ `☑`. Lý do: ô này đóng vì đã chọn ROLAP (26/10) và năm câu SQL đã chạy (07/11), không phải vì Power BI đã nối. Nếu nhóm muốn `☑` có nghĩa “Power BI đã nối”, hạ R26 về `◐` — đó là việc khác, không làm trong bước 2 trừ khi duyệt thêm.

R09, R10, R25, R31–R35, R42 giữ nguyên dấu TT hiện tại.

### 1.3 `docs/SPEC.md` §10 — quyết định mới, giữ dòng cũ

Thêm một dòng vào bảng **Quyết định hiện hành**:

> Một app Streamlit local cho KPI, năm phép OLAP và DSS. Đọc `gold.*` và `dss.*` qua Databricks SQL Warehouse (`databricks-sql-connector`). Không đọc Volume, Bronze, hay Silver. Streamlit append `dss.decision_log`. Job DSS vẫn ghi `dss.seller_risk_score` và `dss.policy_scenario`. Power BI là future work. ROLAP giữ nguyên. Grain Gold, GMV, X=10, N=40 không đổi.

Ngày: 10/11/2026.

Thêm một dòng vào **Lịch sử quyết định**:

| Quyết định đã bị thay | Ngày gốc | Thay ngày |
|---|---|---|
| Power BI là dashboard OLAP; Streamlit chỉ là truy vấn và DSS | 26/10/2026, nhắc lại trong dòng load 05/11/2026 | 10/11/2026 |

Dòng load 05/11/2026 trong bảng hiện hành giữ nguyên phần MERGE, `decision_log`, và GMV. Không viết lại cả đoạn. Câu “Power BI là dashboard” trong dòng đó được coi là đã thay bởi dòng 10/11/2026.

Sửa hàng rủi ro “Công cụ đã chốt: Power BI và Streamlit, ROLAP”:

Mới: `Công cụ trình bày đã chốt 10/11/2026: một app Streamlit. Power BI là future work. ROLAP giữ. S2 vẫn chưa chạy.`

Sửa hàng “Kết nối từ ngoài vào Free Edition (Python local, Power BI, Streamlit)”:

Mới: `Kết nối từ ngoài vào Free Edition (Streamlit qua SQL Warehouse). S2 chưa chạy. Nếu fail thì ghi 2 phương án và chờ, không chuyển app sang đọc CSV.`

### 1.4 `docs/architecture.md`

Sửa câu mở: thêm “Quyết định trình bày 10/11/2026: Consumption chỉ còn Streamlit. Power BI là future work.”

Trong sơ đồ `flowchart TB`, xóa nút `pbi["Power BI<br/>dashboard"]` và cạnh `wh --> pbi`. Giữ `wh --> st`. Đổi nhãn `st` thành `Streamlit<br/>dashboard va DSS`.

| Vị trí | Cũ | Mới |
|---|---|---|
| Bảng lớp Power BI | cả hàng Power BI | xóa hàng. Thêm một câu dưới bảng: `Power BI là future work (10/11/2026), không có object trong luồng hiện tại.` |
| Hàng Streamlit, cột Transformations | `Truy vấn, what-if, goal seek, xuất quyết định` | `KPI, 5 phép OLAP, điểm rủi ro, what-if, goal seek, sensitivity, xuất quyết định` |
| Legend `-->` | `SQL Warehouse → Power BI và Streamlit` | `SQL Warehouse → Streamlit` |
| Câu cuối file | `Kết nối Power BI (S3) và Streamlit (S2) từ máy local tới SQL Warehouse chưa chạy. Công cụ đã chốt; hai spike chỉ kiểm kết nối.` | `Kết nối Streamlit từ máy local tới SQL Warehouse chưa chạy (S2). Power BI (S3) là future work, không chặn app.` |

Job ETL vẫn dừng ở `fact_seller_monthly`. Mũi tên `dss job` vẫn là Phase 5.

### 1.5 `docs/PLAN.md`

**Nhãn Local**, cũ: `repo, tài liệu, pytest, Power BI Desktop, Streamlit, pyspark + delta-spark trên data/sample/`.

Mới: `repo, tài liệu, pytest, Streamlit, pyspark + delta-spark trên data/sample/. Power BI Desktop là future work`.

**S3**, cũ: `Thử kết nối Power BI Desktop tới SQL warehouse. Chỉ kiểm tra kết nối, chưa làm dashboard (R09)`.

Mới: `S3 Power BI — future work từ 10/11/2026. Không chặn Streamlit. Không làm trong phase này (R09)`. Checkbox vẫn trống.

**DoD spike**, cũ: `Frontend và ROLAP đã chốt 26/10/2026 (Power BI dashboard, Streamlit truy vấn/DSS). S2–S3 sau khi có SQL warehouse; S2–S3 chỉ kiểm kết nối.`

Mới: `ROLAP đã chốt 26/10/2026. Trình bày đã chốt 10/11/2026: một app Streamlit. S2 vẫn là kiểm kết nối Streamlit. S3 là future work.`

**Phase 4**, thay hai checkbox Local → Cloud:

Cũ:

- `Power BI Desktop: dashboard ROLAP, đọc Gold qua SQL Warehouse. Kết nối kiểm ở S3 (R09, R26)`
- `Bộ lọc tương tác + drill theo hierarchy trên Power BI (R09, R24)`

Mới (checkbox trống):

- `Streamlit, trang Tổng quan KPI: năm chỉ số mục 3 của plan app, lọc năm mua và vùng seller, đọc Gold qua SQL Warehouse (R09)`
- `Streamlit, trang OLAP Explorer: đủ 5 phép, mỗi phép một visual, SQL lấy từ src/sql/olap_queries/ (R09, R24, R25)`

Sản phẩm cũ: `src/sql/olap_queries/, src/sql/views/, dashboard Power BI`.

Sản phẩm mới: `src/sql/olap_queries/, src/frontend/ (app KPI và OLAP). View DSS nằm ở Phase 5. Power BI là future work`.

DoD cũ: `Công cụ đã chốt 26/10/2026: Power BI cho dashboard, ROLAP qua SQL Warehouse. Streamlit thuộc Phase 5`.

DoD mới: `Năm câu SQL trên Gold đã chạy 07/11/2026. App Streamlit gọi lại đúng các file đó. Một KPI trên app khớp một câu SQL Editor cùng bộ lọc, khi S2 chạy được. Chưa có số đối soát thì không ghi là đã khớp. Power BI không thuộc DoD.`

Checkbox năm câu SQL giữ `[x]`. Không tick hai checkbox Streamlit cho đến khi có bằng chứng chạy.

**Phase 5**, checkbox UI cũ: bốn trang Điểm rủi ro, What-if, Goal seek, Quyết định trong Streamlit.

Mới: `Hai trang còn lại của cùng app: Seller risk đọc dss.seller_risk_score; Policy scenario gọi policy.py trên điểm đã ghi, rồi append dss.decision_log (R32, R34, R35). Nếu S2 không đạt: ghi 2 phương án, chờ, không đọc CSV.`

Sản phẩm mới: `src/dss/ (giữ notebook hiện có), hai trang DSS trong src/frontend/app.py`.

DoD Phase 5 giữ câu “không có read_csv trong src/dss/”. Thêm: `Trang Policy không ghi đè dss.policy_scenario.`

Không tick checkbox Cloud của Phase 5. `PROGRESS_LOG` 10/11/2026 ghi job DSS chưa chạy trên workspace. Phiên plan không đo lại.

### 1.6 `README.md` (tiếng Anh)

Cũ, đoạn Stack:

> The OLAP dashboard is Power BI (ROLAP through a Databricks SQL Warehouse).

Mới:

> One local Streamlit app is the OLAP dashboard and the DSS UI. It reads `gold` and `dss` through a Databricks SQL Warehouse. Power BI is future work.

Cũ, cây thư mục:

> `frontend/          # Power BI dashboard; Streamlit query and DSS UI`

Mới:

> `frontend/          # one Streamlit app: KPI, OLAP, and DSS UI`

Câu Status: thêm một câu “On 10/11/2026 the UI decision changed to a single Streamlit app. Power BI is future work. S2 is still open.” Giữ nguyên các câu Phase 3 và S6.

### 1.7 `docs/DESIGN.md` — chỉ câu frontend

Không đổi grain, §3.6, hay §6.6.

| Vị trí | Cũ | Mới |
|---|---|---|
| Decision update, hàng Frontend | `Power BI: dashboard... Streamlit: giao diện truy vấn và DSS` | `Một app Streamlit: dashboard, OLAP và DSS, đọc Gold và dss qua SQL Warehouse. Power BI là future work. decision_log do Streamlit append` |
| §1 hàng `gold`, câu cuối | `Power BI và Streamlit đọc Gold qua SQL Warehouse` | `Streamlit đọc Gold qua SQL Warehouse` |
| §8 đoạn Power BI | `Power BI dựng dashboard và đọc Gold qua SQL Warehouse. Streamlit là giao diện truy vấn và DSS... S2 (Streamlit) và S3 (Power BI)` | `Streamlit dựng dashboard, OLAP và DSS, đọc Gold và dss qua SQL Warehouse. Kết nối vẫn [GIẢ ĐỊNH] đến S2. Power BI là future work. S3 không còn là cổng của app` |

### 1.8 Rule cho phiên sau

| File | Cũ | Mới |
|---|---|---|
| `.cursor/rules/00-index.mdc` | `OLAP is ROLAP in Power BI through a SQL Warehouse. Streamlit is the query and DSS UI.` | `OLAP is ROLAP through a Databricks SQL Warehouse. One local Streamlit app is the dashboard and the DSS UI. Power BI is future work.` |
| `.cursor/rules/08-sql-olap.mdc` | `The dashboard is Power BI. Streamlit is the query and DSS UI, not a second OLAP dashboard.` | `One local Streamlit app is the dashboard and the DSS UI. Power BI is future work.` Giữ câu cấm cube, HOLAP, AI/BI |
| `.cursor/rules/09-dss.mdc` | `DSS screens are SPEC §7 items 4–7. ... The OLAP dashboard is Power BI, not Streamlit.` | `The Streamlit app has the four pages in SPEC §7. The policy page appends dss.decision_log. Power BI is future work.` |

`05-medallion-layers.mdc` đã nói OLAP và DSS không đọc Bronze/Silver. Giữ nguyên.

---

## 2. Cấu trúc app

```
src/frontend/
  app.py                 # entry, st.navigation
  requirements.txt
  lib/db.py              # warehouse, cache, insert
  lib/queries.py         # load .sql, bind catalog and parameters
  pages/kpi.py
  pages/olap.py
  pages/seller_risk.py
  pages/policy.py
src/sql/olap_queries/    # SQL của KPI và 5 phép, đã có 01–05
src/frontend/dss_app.py  # còn lại thành launcher gọi app.main
```

Một trang một file. Trang không chứa chuỗi `SELECT`. `grep` trên `src/frontend/pages/` không được thấy `SELECT`, `bronze`, hay `silver`.

`app.py` gọi `st.navigation` với bốn `st.Page` trỏ tới hàm `render` của từng module. Nếu bản Streamlit đang cài không có `st.navigation`, `app.py` dùng `st.sidebar.radio` như `dss_app.py` hiện tại. Cả hai đường đều mở cùng bốn hàm `render`.

### 2.1 `lib/db.py`

Đọc `.env` ở root repo. `Path(__file__).resolve().parents[3]` là root, vì file nằm ở `src/frontend/lib/`.

Biến:

| Biến | Việc dùng |
|---|---|
| `DATABRICKS_SERVER_HOSTNAME` | `server_hostname`. Nếu trống, lấy `DATABRICKS_HOST` (tên cũ trong `.env.example`) |
| `DATABRICKS_HTTP_PATH` | `http_path` |
| `DATABRICKS_TOKEN` | `access_token`. Không log, không ghi vào exception do app tự dựng |
| `UC_CATALOG` | mặc định `olist_catalog`. Chỉ chấp nhận `^[A-Za-z_][A-Za-z0-9_]*$` |
| `GOLD_SCHEMA` | mặc định `gold` |
| `DSS_SCHEMA` | mặc định `dss` |

Ba hàm:

```python
def settings() -> dict[str, str]: ...

@st.cache_data(ttl=600, show_spinner=False)
def query(sql: str, params: tuple = ()) -> pd.DataFrame: ...

def execute(sql: str, params: tuple) -> None: ...
```

`query` mở connection, chạy, đóng, trả DataFrame. Cache theo `(sql, params)` trong 600 giây. `execute` không đi qua cache. `execute` chỉ được gọi với câu bắt đầu bằng `INSERT INTO` và tên bảng kết thúc bằng `decision_log`. Câu khác thì ném `ValueError` trước khi gửi warehouse.

Thiếu host, path, hoặc token: ném `RuntimeError` với tên biến còn trống. Trang bắt lỗi và hiện đúng hai phương án: (1) điền `.env` rồi bấm lại; (2) dừng, ghi vào PROGRESS_LOG khi đến lúc, không đọc CSV.

`databricks.sql.paramstyle` quyết định dấu tham số (`qmark` → `?`, còn lại → `%s`). `queries.py` nhận dấu đó. Phiên này chưa chạy connector. Cách chọn dấu là [GIẢ ĐỊNH] đến khi S2 gửi được `SELECT 1`.

### 2.2 `lib/queries.py`

SQL nằm trong `src/sql/`. Hàm `load(filename)` đọc file, thay `{catalog}`, `{gold}`, `{dss}` từ `settings()`, thay `{p}` bằng dấu tham số. Giá trị lọc của người dùng chỉ đi qua tuple tham số, không đi qua `str.format`.

Hàm trang được phép gọi:

| Hàm | File SQL | Tham số |
|---|---|---|
| `years()` | `kpi_years.sql` | không |
| `regions()` | `kpi_regions.sql` | không |
| `kpi_seller_month(year, region)` | `kpi_seller_month.sql` | năm, vùng, mỗi giá trị lặp hai lần vì `{p} IS NULL OR col = {p}` |
| `kpi_orders(year, region)` | `kpi_orders.sql` | cùng kiểu |
| `category_groups()` | `olap_categories.sql` | không |
| `rollup()` | `01_rollup_seller_late_handoff.sql` | không |
| `drilldown()` | `02_drilldown_negative_review.sql` | không |
| `slice(category_group)` | `03_slice_category_late_sellers.sql` | một `category_group` đã có trong `category_groups()` |
| `dice()` | `04_dice_north_bulky.sql` | không |
| `pivot()` | `05_pivot_category_quarter_late.sql` | không |
| `risk_scores(min_orders)` | `risk_scores.sql` | `min_orders` |
| `seller_profile(seller_id)` | `seller_profile.sql` | `seller_id` |
| `policy_snapshot()` | `policy_scenario.sql` | không |
| `insert_decision()` | `insert_decision.sql` | đúng 21 giá trị ở mục 5 |

Năm file `01`–`05` đã có và đã chạy trên warehouse ngày 07/11/2026. Loader chỉ thêm tên catalog đầy đủ: thay token `gold.` trong thân câu bằng `` `{catalog}`.`gold`. `` sau khi catalog đã qua regex. Không đổi công thức bên trong năm file đó.

File `03` hiện gắn cứng `'electronics_it_telephony'`. Bước 2 đổi literal đó thành `{p}`, sau khi danh sách `category_group` lấy từ `dim_product` với `product_key <> -1`. Giá trị không có trong danh sách thì không gửi query. Câu đã chạy ngày 07/11 với nhóm `electronics_it_telephony` vẫn là mốc đối soát khi chọn đúng nhóm đó.

`{p}` với năm hoặc vùng: truyền `None` khi người dùng chọn “Tất cả”. `None` làm nhánh `{p} IS NULL` đúng và không lọc.

### 2.3 Bốn trang

**a. Tổng quan KPI** — `pages/kpi.py`

- Selectbox năm: “Tất cả” cộng `years()`. Selectbox vùng seller: “Tất cả” cộng `regions()`.
- Năm thẻ: GMV, tỷ lệ bàn giao trễ, tỷ lệ review xấu (measure seller), AOV, cancel rate. Công thức ở mục 3.
- `st.spinner` trong lúc `query`. Caption: warehouse Free Edition có thể mất vài phút cho câu đầu.
- Nút “Làm mới” gọi `st.cache_data.clear()`.

**b. OLAP Explorer** — `pages/olap.py`

Mỗi phép một visual. Không tính lại tỷ lệ bằng trung bình các tỷ lệ con.

| Phép | Visual | Cách hiện |
|---|---|---|
| Roll-up | `st.bar_chart` của `late_ship_rate` | Chọn mức `region` / `state` / `city` từ cột `rollup_level`. Mức `city`: chart lấy 20 dòng `eligible_items` lớn nhất. Bảng đầy đủ nằm dưới chart |
| Drill-down | `st.line_chart` của `negative_review_rate` | Chọn mức năm, quý, tháng, hoặc ngày. App `groupby` rồi cộng `negative_orders` và `reviewed_orders`, sau đó chia. Không `.mean()` trên cột rate |
| Slice | `st.bar_chart` top 20 `late_delivery_rate` | Selectbox `category_group`. Bảng đầy đủ phía dưới |
| Dice | `st.dataframe` | Hai tỷ lệ theo `state_code`. Bộ lọc Norte/Nordeste, Q1–Q2/2018, `size_band = bulky` nằm trong SQL, không thành slicer |
| Pivot | `st.dataframe` | `category_group` × `q1`–`q4`. File 05 gộp mọi năm vào cùng một quý. SPEC §7 không tách năm. Giữ nguyên |

Nhãn vùng null trên roll-up hiện là `(không map được vùng)`. Không ghi chữ `Unknown` cho null đó, vì `Unknown` là nhãn member `-1`.

**c. Seller risk** — `pages/seller_risk.py`

- Đọc `dss.seller_risk_score`. Number input `min_orders`, mặc định 5, lọc `n_orders_valid >= min_orders`. Đây là lọc hiển thị, không ghi lại bảng điểm.
- Bảng các seller qua lọc, sắp `p_bad` giảm.
- Selectbox một `seller_id`. Hồ sơ: cột điểm ở DESIGN §6.6 cộng `city_name`, `state_code`, `region_name` từ `gold.dim_seller`.
- Bảng trống hoặc bảng chưa có: câu “Chạy `src/dss/dss_job.py` trên workspace trước.” App không tạo bảng.

**d. Policy scenario** — `pages/policy.py`

- Đọc `dss.seller_risk_score` (không lọc `min_orders` ở SQL; `policy.py` tự áp `min_orders`).
- Hiện ba dòng `dss.policy_scenario` như kết quả lần job gần nhất, với tham số mặc định của job. Slider không ghi đè bảng này.
- Slider và number input cho θ₁–θ₃, e₁, e₂, e₃, e_P1, ngưỡng `late_ship_rate`, ngưỡng `avg_review`, `r`, `s`, `min_orders`. `X` và `N` chỉ hiện chữ `10` và `40`, không có ô sửa.
- Bảng P0/P1/P2 từ `compare_policies`.
- Một mục Goal seeking gọi `goal_seek`. Một mục Sensitivity gọi `tornado`.
- Radio P0/P1/P2, bảng seller `flagged`, nút tải CSV (SPEC §8, pha Implementation).
- Ô ghi chú. Nút “Ghi quyết định” gọi `insert_decision()` một lần. Thành công thì hiện `decision_id`.

Trang Policy import `src.dss.policy` và `src.dss.params`. Không import `src.dss.train`.

### 2.4 Launcher cũ

`src/frontend/dss_app.py` còn file để đường cũ không mở một app thứ hai. Nội dung mới chỉ gọi `app.main`. Xóa trang, ô SQL, và connection riêng trong file đó.

---

## 3. KPI — tử, mẫu, nguồn, grain

Bộ lọc chung của trang KPI:

- Năm: `dim_month.year` (GMV, bàn giao trễ, review) hoặc `dim_date.year` của `purchase_date_key` (AOV, cancel). Cùng một năm mua.
- Vùng: `dim_seller.region_name`.
- “Tất cả” không thêm vị từ năm hoặc vùng.
- Mọi câu đều có `seller_key <> -1` trên fact và trên `dim_seller`, và `month_key <> -1` hoặc `date_key <> -1`.

Slicer vùng lấy từ `dim_seller` với `seller_key <> -1`, `region_name` không null và khác `'Unknown'`. Slicer danh mục của trang OLAP lấy `dim_product.category_group` với `product_key <> -1`. Sản phẩm thật thiếu tên category vẫn có `category_group = 'Unknown'` và khóa dương. Nhóm đó được phép nằm trong slicer. Dòng `-1` không thêm một nhóm mới vì đã bị `product_key <> -1` loại trước `DISTINCT`.

### 3.1 GMV

| | |
|---|---|
| Tử | `SUM(fact_seller_monthly.gmv)` |
| Mẫu | không có. Đây là tổng tiền |
| Nguồn | `gold.fact_seller_monthly`, `gold.dim_month`, `gold.dim_seller` |
| Grain hiển thị | một số cho bộ lọc năm × vùng seller |
| Grain đã khóa | seller-tháng. `gmv` cộng được qua seller vì `price` nằm trên từng item, mỗi item một seller |

`gmv` trên fact đã là `SUM(price)` sau khi loại `canceled` và `unavailable`, không gồm freight. App không cộng `freight_value`.

### 3.2 Tỷ lệ bàn giao trễ

| | |
|---|---|
| Tử | `SUM(late_ship_count)` — item có `seller_ship_late_flag = 1` |
| Mẫu | `SUM(late_ship_eligible)` — item có cờ khác null |
| Tỷ lệ | tử / mẫu khi mẫu > 0, else null |
| Nguồn | cùng ba bảng với GMV |
| Grain | item, đã cộng lên seller-tháng. Hai cột đếm này cộng được qua seller |

Cột `late_ship_rate` không đi vào `AVG` hay `SUM`. Cờ null không nằm trong `late_ship_eligible`. Đơn `canceled` / `unavailable` có cờ null nên không vào mẫu. Chúng đi vào cancel rate.

### 3.3 Tỷ lệ review xấu (thẻ KPI)

| | |
|---|---|
| Tử | `SUM(negative_review_count)` |
| Mẫu | `SUM(negative_review_eligible)` |
| Tỷ lệ | tử / mẫu khi mẫu > 0, else null |
| Nguồn | `gold.fact_seller_monthly` và hai dimension ở trên |
| Grain | đơn đã được ETL đếm trên seller-tháng |

Tập đo, đã khóa ở DESIGN §3.6: đơn có điểm, `n_sellers = 1`, `shared_review_type` thuộc `none` hoặc `same_seller`. Vì mỗi đơn trong tập này có một seller và một tháng mua, cộng qua seller trong một vùng không đếm đơn hai lần.

Không dùng thẻ này cho KPI sàn. KPI sàn giữ `cross_seller`, grain một đơn, nguồn `fact_order.negative_review_flag`, và không có vùng seller. Phép drill-down hiện KPI sàn. Hai số không cần bằng nhau.

### 3.4 AOV

| | |
|---|---|
| Tử | `SUM(price)` của item thuộc seller trong bộ lọc, đơn có `order_status` null hoặc không thuộc `canceled` / `unavailable` |
| Mẫu | `COUNT(DISTINCT order_id)` của cùng tập item đó |
| Tỷ lệ | tử / mẫu khi mẫu > 0, else null |
| Nguồn | `gold.fact_order_item`, `gold.fact_order`, `gold.dim_order_status`, `gold.dim_seller`, `gold.dim_date` |
| Grain của thương số | một số cho bộ lọc. Mẫu là đơn phân biệt, không phải tổng `n_orders_valid` |

Khi chọn một vùng, tử chỉ gồm `price` của seller trong vùng đó. Mẫu gồm mọi đơn có ít nhất một item của các seller đó. Đơn có seller ở hai vùng được đếm một lần trong mỗi vùng, với phần `price` của vùng đó ở tử số.

`SUM(gmv)` ở mục 3.1 và tử AOV phải bằng nhau trên cùng bộ lọc. Lệch thì dừng, ghi conflict, không sửa ETL trong PR này.

### 3.5 Cancel rate

| | |
|---|---|
| Tử | `COUNT(DISTINCT order_id)` có `order_status` thuộc `canceled` hoặc `unavailable`, trong các đơn chạm seller của bộ lọc |
| Mẫu | `COUNT(DISTINCT order_id)` mọi status, cùng tập đơn |
| Tỷ lệ | tử / mẫu khi mẫu > 0, else null |
| Nguồn | cùng các bảng với AOV |
| Grain | đơn. Không cộng `cancel_count` hay `n_orders_placed` qua seller |

Status null và status `'Unknown'` (khóa `-1`) nằm ở mẫu, không nằm ở tử. ETL đã giữ đơn status null trong `n_orders_valid` và trong `gmv` (PROGRESS_LOG 06/11/2026).

---

## 4. DSS — dùng code hiện có, không bịa công thức mới

`PROGRESS_LOG` 10/11/2026: notebook `src/dss/dss_job.py` đã có trong repo, chưa chạy trên workspace, chưa ghi `dss.seller_risk_score`. Phiên plan không `SHOW TABLES`, nên không ghi là bảng đang có hay đang thiếu trên catalog.

### 4.1 Chỗ đã có

| Việc | File | Hành vi đã viết |
|---|---|---|
| Feature view, chỉ `gold.*` | `src/sql/views/v_seller_features.sql` | Bỏ `seller_key = -1`. `min_orders` không lọc view |
| M1 | `src/dss/train.py` | Logistic regression, `random_state = 42`. Hết điều kiện thì `baseline_rate` |
| M2 | `src/dss/policy.py` | P0, P1, P2, `goal_seek`, `tornado` ±20% trên `e_k`, `r`, `s` |
| Tham số một chỗ | `src/dss/params.py` | `X = 10`, `N = 40`, `MIN_ORDERS = 5` |
| Job, tách khỏi ETL | `src/dss/dss_job.py`, `src/dss/dss_job.yml` | `CREATE TABLE IF NOT EXISTS` ba bảng. `DELETE` rồi append hai bảng điểm và kịch bản. In câu `decision_log was not modified` |
| DDL `decision_log` | cùng notebook | Khớp DESIGN §6.6 |

Bước 2 không thêm task `dss` vào `src/etl/olist_etl.job.yml`. Không sửa `train.py` hay `policy.py` chỉ để gắn UI.

Việc trên workspace, khi có người chạy notebook, vẫn là một Job DSS riêng: tạo view, ghi hai bảng, tạo `decision_log` nếu chưa có, không xóa log. App chỉ làm được trang 3 và 4 sau lần chạy đó. Trang 1 và 2 chỉ cần Gold.

`dss_job.py` đang `DELETE FROM` cả bảng điểm rồi insert lại tháng chấm mới nhất. DESIGN §6.6 nói ghi đè kết quả của tháng chấm. Hành vi này xóa luôn tháng đã chấm ở lần chạy trước. Không phải conflict với grain Gold. Không sửa trong PR app. App đọc bảng như một snapshot hiện tại.

### 4.2 Chỗ SPEC chưa cho số — giữ nguyên trong `params.py`, ghi trên UI là quy ước

| Việc trong code | SPEC / DESIGN nói gì |
|---|---|
| `THETA_1 = 0.20`, `THETA_2 = 0.35`, `THETA_3 = 0.50` | SPEC chỉ nói ba ngưỡng là biến quyết định, người dùng chỉnh được. Không có số mặc định |
| `TIER_GAP_2 = 0.15`, `TIER_GAP_3 = 0.30`, `THETA_HI = 0.70` | Goal seeking dịch θ₂ và θ₃ theo θ₁ bằng hai khoảng này. SPEC không định nghĩa khoảng |
| `E1 = 0.25`, `E2 = 0.50`, `E3 = 0.75`, `E_P1 = 0.50` | `e_k` là biến không kiểm soát. Không có số đã đo |
| `LATE_SHIP_THRESHOLD = 0.15`, `AVG_REVIEW_THRESHOLD = 3.5` | SPEC nói có ngưỡng KPI cứng, không nói 0,15 hay 3,5 |
| `R = 0.5`, `S = 1.0` | SPEC đặt tên `r` và `s`. Không khóa số |
| P1 gắn cờ khi `late_ship_rate >= ngưỡng` **hoặc** `avg_review <= ngưỡng` | SPEC không nói AND hay OR, và không nói chiều so sánh |
| `late_ship_rate` null hoặc `avg_review` null thì nhánh đó không gắn cờ | SPEC không nói |
| Seller dưới `min_orders` vẫn nằm trong tổng `expected_bad_orders`, với `e_k = 0` | SPEC không nói họ có ra khỏi tổng hay không |
| Nhãn M1 là tháng lịch kế tiếp (`month_key` + 1), inner join. Tháng seller không bán thì mất dòng train | SPEC nói “tháng t+1”, không nói tháng lịch hay tháng seller-tháng kế tiếp có dữ liệu |
| Tập train M1: seller có ≥ 6 tháng với `n_items_valid >= 10` | Khớp câu G1 trong SPEC §10. Ngưỡng này khác `min_orders` |
| Test = 2 giá trị `year_month` cuối | SPEC chỉ nói chia theo thời gian, không nói hai tháng |
| Điền median cho feature số, điền `'Unknown'` cho category null trước khi one-hot | SPEC không mô tả bước này |
| `late_ship_rate_3m` là trung bình các `late_ship_rate` của tối đa ba dòng seller-tháng | DESIGN §6.6 cho phép trung bình này trên feature. Trang KPI không được làm vậy với thẻ tỷ lệ |

Công thức đã có chữ, app và job phải giữ:

- `expected_bad_orders = Σ p_i · Q_i · (1 − e_k(i))` với `Q_i = q_bar · s` và `q_bar = n_orders_valid` (SPEC §8, DESIGN §6.6).
- `gmv_affected_pct = 100 · Σ gmv · (1 − r)` của seller bị gắn cờ, chia tổng GMV tháng chấm. Null khi tổng GMV = 0 (DESIGN §6.6).
- Sau khi gắn cờ, cắt còn tối đa `N` seller. P1 giữ seller `late_ship_rate` cao hơn. P2 giữ seller `p_bad` cao hơn (`policy.py`).

Trang Policy hiện các số quy ước bằng giá trị khởi tạo của slider và một caption: “Số khởi tạo là quy ước trong `src/dss/params.py`. SPEC không khóa các số này. X=10 và N=40 là số đã khóa.”

---

## 5. `dss.decision_log`

DDL dưới đây là bản Spark SQL của DESIGN §6.6. Notebook `dss_job.py` đã tạo bảng bằng `CREATE TABLE IF NOT EXISTS` với cùng cột. Bước 2 không thêm bản DDL thứ hai trong `src/sql/ddl/` và không gọi `CREATE` từ Streamlit.

```sql
CREATE TABLE IF NOT EXISTS olist_catalog.dss.decision_log (
  decision_id BIGINT NOT NULL,
  decided_at TIMESTAMP NOT NULL,
  as_of_month STRING NOT NULL,
  policy_code STRING NOT NULL,
  theta_1 DOUBLE NOT NULL,
  theta_2 DOUBLE NOT NULL,
  theta_3 DOUBLE NOT NULL,
  e1 DOUBLE NOT NULL,
  e2 DOUBLE NOT NULL,
  e3 DOUBLE NOT NULL,
  e_p1 DOUBLE NOT NULL,
  late_ship_threshold DOUBLE NOT NULL,
  avg_review_threshold DOUBLE NOT NULL,
  r DOUBLE NOT NULL,
  s DOUBLE NOT NULL,
  min_orders INT NOT NULL,
  x_limit DOUBLE NOT NULL,
  n_limit INT NOT NULL,
  expected_bad_orders DOUBLE NOT NULL,
  gmv_affected_pct DOUBLE,
  n_sellers_flagged INT NOT NULL,
  note STRING
) USING DELTA
```

Catalog trong notebook lấy từ widget, không gắn cứng khi chạy job. Khối trên dùng `olist_catalog` để người đối soát dán vào SQL Editor.

App chỉ gửi:

```sql
INSERT INTO {catalog}.{dss}.decision_log (
  decision_id, decided_at, as_of_month, policy_code,
  theta_1, theta_2, theta_3, e1, e2, e3, e_p1,
  late_ship_threshold, avg_review_threshold, r, s, min_orders,
  x_limit, n_limit, expected_bad_orders, gmv_affected_pct,
  n_sellers_flagged, note
) VALUES ({p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p})
```

`decision_id = COALESCE(MAX(decision_id), 0) + 1` bằng một `SELECT` ngay trước `INSERT`. `decided_at` là giờ UTC lúc bấm nút, bỏ tzinfo. `policy_code` chỉ nhận từ radio `P0`, `P1`, `P2`. `x_limit = 10`, `n_limit = 40`. `note` rỗng thì ghi null.

Hai phiên bấm cùng lúc có thể lấy cùng `MAX`. App là một người dùng local, chấp nhận theo đúng chữ “max + 1” của DESIGN. Không đổi sang identity trong PR này.

Đối soát sau một lần bấm: `SELECT COUNT(*) FROM olist_catalog.dss.decision_log` tăng 1, và dòng mới có `policy_code` vừa chọn. Không có câu `DELETE` nào trong `src/frontend/` nhằm vào bảng này.

---

## 6. Checklist đối soát

Mỗi câu dưới đây là câu người chạy dán vào SQL Editor sau `USE CATALOG olist_catalog`, hoặc chạy với tên catalog đầy đủ. App phải ra cùng tử, cùng mẫu, và cùng thương số với câu tương ứng, trên cùng năm và cùng vùng, trong cùng một lần mở warehouse.

Phiên viết plan không chạy các câu này. Không điền số kỳ vọng. Số roll-up ngày 07/11/2026 (`late_items` 11132, `eligible_items` 110550, rate `0.10069651741293532` ở mức `all`) là số đã ghi trong PROGRESS_LOG. Chỉ dùng làm ký ức. Nếu Gold nạp lại sau ngày đó, số sẽ khác. Mốc đúng là câu SQL Editor chạy cùng ngày với app.

Quy ước tham số trong các câu mẫu bên dưới: `CAST(NULL AS INT)` và `CAST(NULL AS STRING)` nghĩa là “Tất cả”. Khi thử năm 2018 và vùng `Sudeste`, thay bằng `2018` và `'Sudeste'`.

### 6.1 Slicer

`src/sql/olap_queries/kpi_years.sql`

```sql
SELECT DISTINCT m.year
FROM {catalog}.{gold}.dim_month AS m
WHERE m.month_key <> -1
  AND m.year IS NOT NULL
ORDER BY m.year
```

`src/sql/olap_queries/kpi_regions.sql`

```sql
SELECT DISTINCT s.region_name
FROM {catalog}.{gold}.dim_seller AS s
WHERE s.seller_key <> -1
  AND s.region_name IS NOT NULL
  AND s.region_name <> 'Unknown'
ORDER BY s.region_name
```

`src/sql/olap_queries/olap_categories.sql`

```sql
SELECT DISTINCT p.category_group
FROM {catalog}.{gold}.dim_product AS p
WHERE p.product_key <> -1
  AND p.category_group IS NOT NULL
ORDER BY p.category_group
```

Kỳ vọng slicer: không có dòng `-1`, không có nhãn vùng `'Unknown'` lấy từ member `-1`.

### 6.2 Thẻ GMV, bàn giao trễ, review seller

`src/sql/olap_queries/kpi_seller_month.sql`

```sql
SELECT
  SUM(f.gmv) AS gmv,
  SUM(f.late_ship_count) AS late_ship_count,
  SUM(f.late_ship_eligible) AS late_ship_eligible,
  CASE
    WHEN SUM(f.late_ship_eligible) > 0
      THEN SUM(f.late_ship_count) / SUM(f.late_ship_eligible)
  END AS late_ship_rate,
  SUM(f.negative_review_count) AS negative_review_count,
  SUM(f.negative_review_eligible) AS negative_review_eligible,
  CASE
    WHEN SUM(f.negative_review_eligible) > 0
      THEN SUM(f.negative_review_count) / SUM(f.negative_review_eligible)
  END AS negative_review_rate
FROM {catalog}.{gold}.fact_seller_monthly AS f
INNER JOIN {catalog}.{gold}.dim_month AS m
  ON f.month_key = m.month_key
INNER JOIN {catalog}.{gold}.dim_seller AS s
  ON f.seller_key = s.seller_key
WHERE f.seller_key <> -1
  AND m.month_key <> -1
  AND s.seller_key <> -1
  AND ({p} IS NULL OR m.year = {p})
  AND ({p} IS NULL OR s.region_name = {p})
```

Đối soát thêm, cùng bộ lọc, từ item. Hai tổng item phải bằng `late_ship_count` và `late_ship_eligible` của câu trên. Lệch thì dừng.

```sql
SELECT
  SUM(CASE WHEN i.seller_ship_late_flag = 1 THEN 1 ELSE 0 END) AS late_items,
  SUM(CASE WHEN i.seller_ship_late_flag IS NOT NULL THEN 1 ELSE 0 END) AS eligible_items
FROM {catalog}.{gold}.fact_order_item AS i
INNER JOIN {catalog}.{gold}.dim_seller AS s
  ON i.seller_key = s.seller_key
INNER JOIN {catalog}.{gold}.dim_date AS d
  ON i.purchase_date_key = d.date_key
WHERE i.seller_key <> -1
  AND s.seller_key <> -1
  AND d.date_key <> -1
  AND ({p} IS NULL OR d.year = {p})
  AND ({p} IS NULL OR s.region_name = {p})
```

Khi “Tất cả” năm và “Tất cả” vùng, `late_items / eligible_items` là cùng định nghĩa với dòng `rollup_level = 'all'` của `01_rollup_seller_late_handoff.sql`. So với lần chạy SQL Editor hôm đối soát, không so với số nhớ 07/11 nếu chưa chạy lại file 01.

### 6.3 Thẻ AOV và cancel rate

`src/sql/olap_queries/kpi_orders.sql`

```sql
WITH touched AS (
  SELECT
    i.order_id,
    i.price,
    st.order_status
  FROM {catalog}.{gold}.fact_order_item AS i
  INNER JOIN {catalog}.{gold}.fact_order AS o
    ON i.order_id = o.order_id
  INNER JOIN {catalog}.{gold}.dim_order_status AS st
    ON o.order_status_key = st.order_status_key
  INNER JOIN {catalog}.{gold}.dim_seller AS s
    ON i.seller_key = s.seller_key
  INNER JOIN {catalog}.{gold}.dim_date AS d
    ON i.purchase_date_key = d.date_key
  WHERE i.seller_key <> -1
    AND s.seller_key <> -1
    AND d.date_key <> -1
    AND ({p} IS NULL OR d.year = {p})
    AND ({p} IS NULL OR s.region_name = {p})
)
SELECT
  SUM(
    CASE
      WHEN order_status IS NULL OR order_status NOT IN ('canceled', 'unavailable')
        THEN price
    END
  ) AS gmv_from_items,
  COUNT(DISTINCT
    CASE
      WHEN order_status IS NULL OR order_status NOT IN ('canceled', 'unavailable')
        THEN order_id
    END
  ) AS valid_orders,
  CASE
    WHEN COUNT(DISTINCT
      CASE
        WHEN order_status IS NULL OR order_status NOT IN ('canceled', 'unavailable')
          THEN order_id
      END
    ) > 0
      THEN SUM(
        CASE
          WHEN order_status IS NULL OR order_status NOT IN ('canceled', 'unavailable')
            THEN price
        END
      ) / COUNT(DISTINCT
        CASE
          WHEN order_status IS NULL OR order_status NOT IN ('canceled', 'unavailable')
            THEN order_id
        END
      )
  END AS aov,
  COUNT(DISTINCT CASE WHEN order_status IN ('canceled', 'unavailable') THEN order_id END) AS cancel_orders,
  COUNT(DISTINCT order_id) AS placed_orders,
  CASE
    WHEN COUNT(DISTINCT order_id) > 0
      THEN COUNT(DISTINCT CASE WHEN order_status IN ('canceled', 'unavailable') THEN order_id END)
        / COUNT(DISTINCT order_id)
  END AS cancel_rate
FROM touched
```

`gmv_from_items` phải bằng `gmv` của mục 6.2 trên cùng bộ lọc.

### 6.4 KPI sàn — không phải số trên thẻ review

Chạy để chắc người đối soát không lấy nhầm. Không yêu cầu bằng thẻ “tỷ lệ review xấu”.

```sql
SELECT
  SUM(CASE WHEN o.negative_review_flag = 1 THEN 1 ELSE 0 END) AS negative_orders,
  SUM(CASE WHEN o.negative_review_flag IS NOT NULL THEN 1 ELSE 0 END) AS reviewed_orders,
  CASE
    WHEN SUM(CASE WHEN o.negative_review_flag IS NOT NULL THEN 1 ELSE 0 END) > 0
      THEN SUM(CASE WHEN o.negative_review_flag = 1 THEN 1 ELSE 0 END)
        / SUM(CASE WHEN o.negative_review_flag IS NOT NULL THEN 1 ELSE 0 END)
  END AS marketplace_negative_review_rate
FROM {catalog}.{gold}.fact_order AS o
INNER JOIN {catalog}.{gold}.dim_date AS d
  ON o.purchase_date_key = d.date_key
WHERE d.date_key <> -1
  AND ({p} IS NULL OR d.year = {p})
```

Câu này không lọc vùng seller. Drill-down của app, khi chọn mức năm và cùng một năm, phải ra cùng tử và mẫu sau khi cộng các ngày trong năm đó.

### 6.5 Năm phép OLAP

| Phép | File app gọi | Đối soát |
|---|---|---|
| Roll-up | `01_rollup_seller_late_handoff.sql` | Cùng số dòng và cùng `late_items`, `eligible_items` với SQL Editor. Rate trên chart là cột `late_ship_rate` của file, không phải trung bình các dòng con |
| Drill-down | `02_drilldown_negative_review.sql` | Ở mức ngày, khớp file. Ở mức năm/quý/tháng, tử và mẫu là tổng các dòng ngày, rate tính lại |
| Slice | `03_slice_category_late_sellers.sql` với `{p}` | Chọn `electronics_it_telephony`. Khớp file đã chạy 07/11 nếu Gold không đổi. Nhóm khác: chạy cùng câu với literal đó trong SQL Editor |
| Dice | `04_dice_north_bulky.sql` | Khớp nguyên file. Không thêm slicer |
| Pivot | `05_pivot_category_quarter_late.sql` | Khớp nguyên file, gồm việc gộp mọi năm vào một quý |

### 6.6 DSS

`src/sql/olap_queries/risk_scores.sql`

```sql
SELECT
  seller_key,
  seller_id,
  as_of_month,
  p_bad,
  q_bar,
  gmv,
  late_ship_rate,
  avg_review,
  n_orders_valid,
  model_name,
  trained_through_month
FROM {catalog}.{dss}.seller_risk_score
WHERE n_orders_valid >= {p}
ORDER BY p_bad DESC
```

`src/sql/olap_queries/seller_profile.sql`

```sql
SELECT
  r.seller_id,
  r.as_of_month,
  r.p_bad,
  r.q_bar,
  r.gmv,
  r.late_ship_rate,
  r.avg_review,
  r.n_orders_valid,
  r.model_name,
  r.trained_through_month,
  s.city_name,
  s.state_code,
  s.region_name
FROM {catalog}.{dss}.seller_risk_score AS r
LEFT JOIN {catalog}.{gold}.dim_seller AS s
  ON r.seller_key = s.seller_key
WHERE r.seller_id = {p}
```

`src/sql/olap_queries/policy_scenario.sql`

```sql
SELECT
  as_of_month,
  policy_code,
  expected_bad_orders,
  gmv_affected_pct,
  n_sellers_flagged,
  meets_x,
  meets_n,
  theta_1,
  theta_2,
  theta_3,
  min_orders,
  x_limit,
  n_limit
FROM {catalog}.{dss}.policy_scenario
ORDER BY policy_code
```

Đối soát what-if: với slider để đúng số trong `params.py` và `min_orders = 5`, ba số `expected_bad_orders`, `gmv_affected_pct`, `n_sellers_flagged` trên trang phải trùng ba dòng `dss.policy_scenario` của lần job vừa ghi. Slider lệch khỏi mặc định thì bảng job và bảng trang được phép khác nhau. Trang không được `UPDATE` bảng job.

Đối soát nút ghi: đếm dòng `decision_log` trước và sau là +1. Không có dòng nào bị sửa `decision_id` cũ.

---

## 7. Rủi ro

| Rủi ro | Việc làm trong app |
|---|---|
| SQL Warehouse Free Edition khởi động chậm | `st.spinner`. Cache `query` 600 giây. Không mở nhiều connection song song ở lần tải đầu. Không tự chạy lại năm lần |
| Hết quota hoặc warehouse tắt | Hiện message của connector. Hai phương án: đợi rồi bấm “Làm mới”, hoặc ghi PROGRESS_LOG và dừng. Không đọc CSV, không đọc Volume |
| Token | Chỉ trong `.env`. `.env` đã bị gitignore. `.env.example` để trống token. `execute` và `query` không in `settings()` |
| `?` hay `%s` | Đọc `databricks.sql.paramstyle` lúc chạy. Chưa kiểm trên warehouse này |
| `COALESCE(NULL, region)` sẽ loại seller có `region_name` null khi chọn “Tất cả” | Không dùng `COALESCE`. Dùng `{p} IS NULL OR col = {p}` |
| Cache giữ số cũ sau khi job DSS chạy lại | Nút “Làm mới” xóa `st.cache_data` |
| `decision_id = max + 1` đụng nhau | Chấp nhận với một người dùng. Không đổi kiểu khóa trong PR này |
| Bảng `dss` chưa có vì job chưa chạy | Trang 3 và 4 báo chạy notebook. Trang 1 và 2 vẫn đọc Gold |
| Nhầm KPI sàn với measure seller | Checklist 6.4. Caption trên thẻ review: “Measure seller, loại đơn nhiều seller và cross_seller” |
| AOV gộp chưa có tên trong SPEC | Caption trên thẻ: “GMV trong bộ lọc / số đơn phân biệt” |
| Sửa nhầm ETL khi đối soát lệch | Dừng, ghi lệch, không vá `src/etl/` trong PR này |

---

## 8. Thứ tự làm và DoD

Làm sau khi plan được duyệt. Nhánh: `feat/phase4-5-streamlit-app`.

### Task 1: Sửa docs và rule

**Files:** `docs/SPEC.md`, `docs/architecture.md`, `docs/PLAN.md`, `docs/DESIGN.md`, `README.md`, `.cursor/rules/00-index.mdc`, `.cursor/rules/08-sql-olap.mdc`, `.cursor/rules/09-dss.mdc`.

- [ ] Sửa đúng các cặp câu ở mục 1. Không đổi cột TT. Không tick checkbox PLAN mới.
- [ ] Thêm dòng SPEC §10 ngày 10/11/2026 và dòng lịch sử Power BI.
- [ ] Đọc lại diff: không còn câu nào nói Power BI là dashboard hiện tại, trừ chữ “future work” và dòng lịch sử.

### Task 2: SQL KPI và tham số slice

**Files:** các file mới kể ở mục 6, và `src/sql/olap_queries/03_slice_category_late_sellers.sql` (literal → `{p}`).

- [ ] Chép nguyên câu SQL ở mục 6 vào đúng tên file. Giữ header comment của rule `08-sql-olap` trên file OLAP: `operator`, `question`, `requirement`, `tables`.
- [ ] File KPI ghi `requirement: R09` và câu “rates from numerator and denominator”.
- [ ] Không sửa `01`, `02`, `04`, `05` ngoài bước catalog do loader làm lúc chạy.

### Task 3: `lib/db.py` và `lib/queries.py`

**Files:** `src/frontend/lib/db.py`, `src/frontend/lib/queries.py`, `src/frontend/lib/__init__.py`.

**Produces:** `settings`, `query`, `execute`, và các hàm ở bảng mục 2.2.

- [ ] Viết hai module đúng chữ ký mục 2.1 và 2.2.
- [ ] `execute` từ chối câu không phải `INSERT` vào `decision_log`.
- [ ] Catalog không qua regex thì không nối warehouse.

### Task 4: Bốn trang và entry

**Files:** `src/frontend/app.py`, `src/frontend/pages/kpi.py`, `olap.py`, `seller_risk.py`, `policy.py`. Sửa `src/frontend/dss_app.py` thành launcher.

- [ ] Mỗi trang một `render(settings)`.
- [ ] Trang KPI hiện năm số từ `kpi_seller_month` và `kpi_orders`.
- [ ] Trang OLAP: năm visual, drill-down cộng tử và mẫu trước khi chia.
- [ ] Trang risk: `min_orders` mặc định 5, một hồ sơ seller.
- [ ] Trang policy: slider, ba phương án, goal seek, tornado, CSV, một `INSERT`.
- [ ] `X` và `N` không có ô nhập.
- [ ] `dss_app.py` gọi `app.main` và không còn câu SQL riêng.

### Task 5: Dependency và env mẫu

**Files:** `src/frontend/requirements.txt`, `.env.example`.

`src/frontend/requirements.txt`:

```text
streamlit>=1.36
databricks-sql-connector
pandas
numpy
```

Không tạo `requirements.txt` ở root. Không thêm `python-dotenv`. `db.py` tự đọc file `.env`. Không cài gói trong bước docs. Chỉ cài khi thực hiện Task 5 và người duyệt plan này đã đồng ý danh sách trên.

`.env.example`: thêm `DATABRICKS_SERVER_HOSTNAME=` cạnh `DATABRICKS_HOST=`. Comment một dòng: app đọc `DATABRICKS_SERVER_HOSTNAME`, và đọc `DATABRICKS_HOST` khi tên mới trống. `DATABRICKS_TOKEN=` vẫn trống.

- [ ] Hai file đúng nội dung trên. `git status` không thấy `.env`.

### Task 6: Kiểm tra, chưa được quyền khai là đã chạy warehouse

- [ ] `grep` `SELECT` trong `src/frontend/pages` không có kết quả.
- [ ] `grep` `read_csv`, `data/raw`, `data/sample`, `/Volumes/` trong `src/frontend` và `src/dss` không có kết quả mới.
- [ ] Parse được `app.py` bằng `python -m ast` qua `.venv` nếu venv có sẵn. Lệnh này không chứng minh app nối warehouse.
- [ ] Nếu `.env` có đủ ba biến và connector import được: chạy `SELECT 1`, rồi chạy checklist mục 6 với “Tất cả” và với một năm + một vùng. Ghi số tử/mẫu vào PROGRESS_LOG vì chính phiên đó đã chạy.
- [ ] Nếu thiếu token, thiếu package, hoặc warehouse lỗi: PROGRESS_LOG ghi “đã code, chưa chạy trên SQL Warehouse”, kèm lỗi ngắn. Không điền số KPI. Không tick PLAN.

### Task 7: Commit và PR

Hai commit, sau khi Task 6 xong:

```text
docs(phase4): record one Streamlit app as the consumption layer
```

```text
feat(frontend): add the KPI, OLAP, and DSS Streamlit app
```

- [ ] Không commit `.env`, token, `data/raw`.
- [ ] `gh pr create` từ `feat/phase4-5-streamlit-app`. Phần test plan của PR nói rõ warehouse đã chạy hay chưa, theo đúng kết quả Task 6.
- [ ] PROGRESS_LOG: một mục mới trên cùng, ngày làm bước 2. Khối “Trạng thái hiện tại” đổi “Đang làm” sang app Streamlit. Không tick RTM. Không viết “đã khớp KPI” nếu Task 6 không có output SQL Editor.

### DoD của cả PR

Đo được khi review diff, không cần cảm tính:

1. SPEC §7 liệt kê bốn trang Streamlit và một câu Power BI là future work.
2. `architecture.md` không còn cạnh SQL Warehouse → Power BI.
3. `src/frontend/app.py` mở bốn trang.
4. Mọi câu `SELECT` của app nằm trong `src/sql/` hoặc `lib/queries.py` (loader). `pages/` không có `SELECT`.
5. Năm file OLAP `01`–`05` còn đúng phép. File 03 nhận `category_group` bằng tham số.
6. Năm thẻ KPI dùng đúng câu mục 6.2 và 6.3.
7. Diff `src/etl/` trống.
8. Diff không đổi `X`, `N`, grain, hay công thức `gmv`.
9. `INSERT` vào `decision_log` là câu ghi duy nhất trong `src/frontend/`.
10. PROGRESS_LOG phân biệt “đã code” và “đã chạy”.

---

## Self-review

- Phạm vi người dùng hỏi (tám mục) có chỗ trong file: mục 1 docs, mục 2 cấu trúc, mục 3 KPI, mục 4 DSS, mục 5 DDL, mục 6 đối soát, mục 7 rủi ro, mục 8 thứ tự và DoD.
- Không có công thức KPI nào lấy `AVG(late_ship_rate)` hay `SUM(aov)`.
- Chỗ SPEC không có số thì nằm trong bảng mục 4.2, không bị điền thêm vào `params.py` bởi plan này.
- Job DSS đã có. Plan không tạo notebook thứ hai.
- ETL Phase 3 không nằm trong danh sách file sửa.
- Hai subsystem OLAP và DSS ở trong một plan vì quyết định 10/11/2026 gộp chúng thành một app. Tách plan sẽ dựng lại hai UI.

**Conflict ETL đã thấy lúc viết plan:** không có conflict buộc phải sửa `src/etl/`. Điểm cần nhớ khi đối soát là `gmv_from_items` và `SUM(fact_seller_monthly.gmv)` phải bằng nhau. Lệch thì báo, không vá.
