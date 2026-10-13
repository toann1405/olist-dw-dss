# Dữ liệu — Olist Brazilian E-Commerce

> **Trạng thái (10/10/2026): Đã tải ngày 10/10/2026.** 9 CSV Olist có trong `data/raw/` (không thiếu, không thừa so với danh sách tham khảo). Marketing Funnel có trong `data/external/`. Số liệu dưới đây lấy từ `python src/notebooks/00_verify_and_sample.py` cùng ngày. Chi tiết: `docs/PROGRESS_LOG.md`.

## 1. Nguồn và license

| Mục | Nội dung | Đã kiểm chứng? |
|---|---|---|
| Dataset chính | *Brazilian E-Commerce Public Dataset by Olist* — https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce | ✔ (đọc trang Kaggle 10/10/2026); **đã tải** vào `data/raw/` ngày 10/10/2026 |
| License | **CC BY-NC-SA 4.0** (Attribution – NonCommercial – ShareAlike) | ✔ đọc trực tiếp trên trang Kaggle 10/10/2026 |
| Mô tả nguồn (theo trang Kaggle) | Khoảng 100 nghìn đơn hàng 2016–2018 trên nhiều marketplace ở Brazil; dữ liệu thương mại thật đã ẩn danh; một đơn có thể có nhiều item, mỗi item có thể do một seller khác giao | ✔; script: **99,441** đơn, `order_purchase_timestamp` **2016-09-04 21:15:19 → 2018-10-17 17:30:18** (99,441/99,441 non-null) |
| Nguồn bổ sung | *Marketing Funnel by Olist* — https://www.kaggle.com/datasets/olistbr/marketing-funnel-olist — 2 file (`olist_closed_deals_dataset.csv`, `olist_marketing_qualified_leads_dataset.csv`), nối với dataset chính qua `seller_id` | ✔ license **CC BY-NC-SA 4.0** (đọc trang Kaggle 10/10/2026); **đã tải** vào `data/external/` ngày 10/10/2026 (842 closed deals, 8,000 MQL — từ output script) |
| Nguồn bổ sung (dự kiến) | Lịch ngày lễ quốc gia Brazil 2016–2018 (ví dụ thư viện Python `holidays` hoặc API công khai Nager.Date) | ✖ chưa kiểm tra license — kiểm tra ở Phase 1 |
| Nguồn bổ sung (dự kiến) | Bảng ánh xạ bang (UF) → vùng (Norte, Nordeste, Centro-Oeste, Sudeste, Sul) theo IBGE — bảng tham chiếu nhỏ, nhóm tự lập và ghi nguồn | ✖ ghi nguồn khi lập ở Phase 1 |

**Hệ quả của license CC BY-NC-SA 4.0 (suy luận, không phải tư vấn pháp lý):** dùng cho bài tập học thuật phi thương mại là phù hợp; khi đưa `data/sample/` lên GitHub/Drive phải **ghi nguồn Olist/Kaggle** và **giữ cùng license** cho phần dữ liệu chia sẻ lại.

## 2. Cách tải (làm thủ công)

**Cách A — Kaggle CLI** (cần tài khoản Kaggle):
1. Kaggle → *Settings* → *API* → *Create New Token* → lưu `kaggle.json` vào `~/.kaggle/` (Windows: `C:\Users\<user>\.kaggle\`), hoặc điền `KAGGLE_USERNAME`/`KAGGLE_KEY` vào `.env`.
2. Từ thư mục gốc repo:
   ```bash
   pip install kaggle
   kaggle datasets download -d olistbr/brazilian-ecommerce -p data/raw --unzip
   # nguồn bổ sung (khi nhóm chốt dùng):
   kaggle datasets download -d olistbr/marketing-funnel-olist -p data/external --unzip
   ```

**Cách B — `kagglehub`**: `pip install kagglehub` → `python -c "import kagglehub; print(kagglehub.dataset_download('olistbr/brazilian-ecommerce'))"` → chép các file CSV từ đường dẫn in ra vào `data/raw/`.

**Cách C — trình duyệt**: đăng nhập Kaggle → mở link dataset → *Download* → giải nén toàn bộ CSV vào `data/raw/`.

**Sau khi tải xong**:
```bash
python src/notebooks/00_verify_and_sample.py      # in bảng thống kê + tạo data/sample/
```
Dán bảng in ra vào mục 3, ghi ngày tải, và cập nhật `docs/PROGRESS_LOG.md`.

## 3. Danh sách file (từ output script, 10/10/2026)

Ngày tải: **10/10/2026**. Số dòng / số cột / dung lượng: từ `python src/notebooks/00_verify_and_sample.py` (10/10/2026).

| File (danh sách tham khảo) | Số dòng | Số cột | Dung lượng | Mô tả ngắn (theo schema công khai — kiểm tra ở Phase 1) |
|---|---:|---:|---:|---|
| `olist_customers_dataset.csv` | 99,441 | 5 | 8.62 MB | Khách hàng: `customer_id` (theo đơn) và `customer_unique_id` (theo người), zip prefix, thành phố, bang |
| `olist_geolocation_dataset.csv` | 1,000,163 | 5 | 58.44 MB | Zip prefix → lat/lng, thành phố, bang; nhiều dòng cho cùng một zip prefix |
| `olist_order_items_dataset.csv` | 112,650 | 7 | 14.72 MB | 1 dòng/item trong đơn; `product_id`, `seller_id`, hạn bàn giao cho vận chuyển (`shipping_limit_date`), giá, phí vận chuyển |
| `olist_order_payments_dataset.csv` | 103,886 | 5 | 5.51 MB | Thanh toán theo đơn; một đơn có thể nhiều dòng (nhiều phương thức), số kỳ trả góp, giá trị |
| `olist_order_reviews_dataset.csv` | 99,224 | 7 | 13.78 MB | Đánh giá của khách: điểm 1–5, tiêu đề/nội dung (tiếng Bồ Đào Nha), ngày tạo và ngày trả lời khảo sát |
| `olist_orders_dataset.csv` | 99,441 | 8 | 16.84 MB | Bảng trung tâm: 1 dòng/đơn; trạng thái đơn và các mốc thời gian (mua, duyệt, giao cho đơn vị vận chuyển, giao tới khách, ngày giao dự kiến) |
| `olist_products_dataset.csv` | 32,951 | 9 | 2.27 MB | Sản phẩm: danh mục (tiếng Bồ Đào Nha), kích thước, khối lượng, số ảnh, độ dài mô tả |
| `olist_sellers_dataset.csv` | 3,095 | 4 | 0.17 MB | Người bán: zip prefix, thành phố, bang |
| `product_category_name_translation.csv` | 71 | 2 | 0.00 MB | Bảng dịch tên danh mục Bồ Đào Nha → tiếng Anh |

**Khác biệt so với danh sách tham khảo:** none (script: Missing vs expected: none; Extra vs expected: none).

**Marketing Funnel** (`data/external/`, cùng lần chạy script):

| File | Số dòng | Số cột | Dung lượng |
|---|---:|---:|---:|
| `olist_closed_deals_dataset.csv` | 842 | 14 | 0.16 MB |
| `olist_marketing_qualified_leads_dataset.csv` | 8,000 | 4 | 0.67 MB |

**Khoảng thời gian (nhẹ, không profiling):** `order_purchase_timestamp` min=**2016-09-04 21:15:19**, max=**2018-10-17 17:30:18** (non-null=99,441/99,441).

## 4. Thư mục

| Thư mục | Nội dung | Commit lên git? |
|---|---|---|
| `raw/` | 9 file CSV gốc từ Kaggle, giữ nguyên tên, **không sửa tay** | Không (gitignore) |
| `external/` | Nguồn bổ sung (Marketing Funnel đã tải; ngày lễ, bang → vùng: Phase 1) | File tham chiếu nhỏ: có; file lớn: không |
| `sample/` | Mẫu **5,000** đơn hàng (seed **42**, mặc định script), giữ toàn vẹn khóa giữa các bảng, cùng tên file với `raw/` | Có (dùng để nộp bài và chạy demo nhanh với `USE_SAMPLE=1`) |

Mẫu được tạo bằng `src/notebooks/00_verify_and_sample.py` (chọn ngẫu nhiên đơn hàng với seed cố định, rồi lấy toàn bộ item/payment/review/customer/product/seller/geolocation liên quan). Lần chạy 10/10/2026: `--orders` mặc định 5,000, `--seed` mặc định 42; integrity asserts passed; các file mẫu: orders 5,000 · items 5,712 · payments 5,237 · reviews 4,980 · customers 5,000 · products 3,844 · sellers 1,222 · geolocation 481,054 · translation 71. Bản dữ liệu đầy đủ: đặt link Kaggle/Drive tại đây khi nộp (đề mục 5.1 cho phép dữ liệu qua GitHub/Google Drive).

## 5. Upload lên Unity Catalog Volume

Làm sau khi có workspace Databricks (spike S1). Đây là các bước mức hướng dẫn, chưa chạy.

1. Tạo Unity Catalog Volume trong workspace Free Edition.
2. Upload 9 CSV từ `data/raw/` và các CSV Marketing Funnel từ `data/external/`. Giữ nguyên nội dung file, không sửa tay.
3. Bronze đọc Volume bằng `spark.read`. Đường dẫn Volume là **[GIẢ ĐỊNH]** đến khi S1 ghi lại, dạng `/Volumes/<UC_CATALOG>/<schema>/<volume>/`. `UC_CATALOG` để trống trong `.env.example` cho đến khi S1 chốt tên catalog.
4. `data/sample/` dùng cho đường chạy local (pyspark + delta-spark), không thay cho bản upload đầy đủ trên Databricks.
