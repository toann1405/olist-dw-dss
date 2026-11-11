# Thuật ngữ

Định nghĩa khớp `src/frontend/lib/glossary.py`, SPEC §1 và DESIGN §3.6. Tỷ lệ trên app = tổng tử / tổng mẫu, không `AVG` cột `*_rate`.

| Thuật ngữ | Nghĩa |
|---|---|
| GMV | Doanh thu hàng hóa seller đã bán, không gồm cước. `SUM(price)` của item thuộc đơn không `canceled` và không `unavailable`. |
| Số đơn (hợp lệ) | Đơn còn hiệu lực trong bộ lọc: không `canceled`, không `unavailable`. |
| AOV | GMV / số đơn hợp lệ trong cùng bộ lọc. |
| Đơn trải nghiệm xấu | Review ≤ 2 **hoặc** giao trễ so với ngày hẹn. Hủy không nằm trong cờ này. KPI sàn giữ đơn nhiều seller và review `cross_seller`. |
| Bàn giao trễ | Seller bàn giao cho đối tác vận chuyển sau hạn (`seller_ship_late_flag`). Lỗi seller. **Không** phải giao trễ tới khách. |
| Giao trễ tới khách | Đơn tới khách sau ngày hẹn (`late_flag`). |
| Review xấu (theo seller) | Điểm ≤ 2, quy cho seller. Loại đơn nhiều seller và `shared_review_type = cross_seller`. |
| Review xấu (toàn sàn) | Điểm ≤ 2 trên cả sàn, kể cả đơn nhiều seller và `cross_seller`. |
| Cancel rate | Đơn `canceled` hoặc `unavailable`. Không phải đơn trải nghiệm xấu. |
| Seller đang hoạt động | Seller có ít nhất một đơn hợp lệ trong khoảng đang xem. |
| Xác suất đơn xấu (`p_bad`) | M1: xác suất một đơn **tháng tới** của seller là đơn trải nghiệm xấu. Đây là **dự báo**. |
| P0 | Không can thiệp. Mốc so sánh. |
| P1 | Can thiệp theo ngưỡng KPI đã xảy ra (bàn giao trễ hoặc điểm review). |
| P2 | Can thiệp theo xác suất đơn xấu do mô hình dự báo. |
| X, N | Trần đã chốt 15/10/2026: GMV bị ảnh hưởng ≤ **10%**, số seller xử lý ≤ **40**/tháng. |
| Tháng chấm | `AS_OF_MONTH` = **2018-08**. Không lấy `MAX(month)` vì 2018-09/10 thưa. |
| `snapshot_date` | Hằng số Gold `DATE '2018-10-17'`, không suy từ watermark. |
| Thực tế vs dự báo | 📊 số đã xảy ra trên Gold. 🔮 M1 (tháng tới) hoặc M2 (mô phỏng chính sách). |

Nguồn dữ liệu: [Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) và [Marketing Funnel by Olist](https://www.kaggle.com/datasets/olistbr/marketing-funnel-olist), giấy phép [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/).
