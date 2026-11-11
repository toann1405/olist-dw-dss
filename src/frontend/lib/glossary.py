"""One glossary for tooltips and the home-page explainer.

Definitions follow SPEC §1 and DESIGN §3.6. Marketplace bad experience is the
order flag. The seller-month rate is a different measure and is not used here.
"""

from __future__ import annotations

# Locked snapshot date in the Gold load config (DESIGN §3.6), not a query result.
DATA_AS_OF = "2018-10-17"
DATA_SPAN = "2016–2018"
DATA_PLACE = "Brazil"

GLOSSARY: dict[str, dict[str, str]] = {
    "valid_orders": {
        "label": "Số đơn",
        "definition": "Đơn còn hiệu lực trong bộ lọc.",
        "numerator": "COUNT(DISTINCT order_id) không canceled và không unavailable.",
        "denominator": "Không phải tỷ lệ.",
    },
    "gmv": {
        "label": "GMV",
        "definition": "Doanh thu hàng hóa seller đã bán, không gồm cước vận chuyển.",
        "numerator": "SUM(price) của item thuộc đơn không canceled và không unavailable.",
        "denominator": "Không phải tỷ lệ.",
    },
    "aov": {
        "label": "AOV",
        "definition": "Giá trị trung bình một đơn còn hiệu lực.",
        "numerator": "GMV trong cùng bộ lọc.",
        "denominator": "Số đơn phân biệt không canceled và không unavailable.",
    },
    "bad_experience": {
        "label": "Đơn trải nghiệm xấu",
        "definition": (
            "Đơn có review ≤ 2 hoặc giao trễ so với ngày hẹn. "
            "Hủy không nằm trong cờ này. KPI sàn giữ đơn nhiều seller và review cross_seller."
        ),
        "numerator": "Số đơn có bad_experience_flag = 1.",
        "denominator": "Số đơn có bad_experience_flag khác null, seller khác −1 và ngày mua khác −1.",
    },
    "late_ship": {
        "label": "Bàn giao trễ",
        "definition": "Seller bàn giao cho đối tác vận chuyển sau hạn. Đây là lỗi seller, không phải giao trễ tới khách.",
        "numerator": "Số item có seller_ship_late_flag = 1.",
        "denominator": "Số item có seller_ship_late_flag khác null.",
    },
    "late_delivery": {
        "label": "Giao trễ tới khách",
        "definition": "Đơn tới khách sau ngày hẹn. Khác với bàn giao trễ của seller.",
        "numerator": "Số đơn phân biệt có late_flag = 1.",
        "denominator": "Số đơn phân biệt có late_flag khác null.",
    },
    "negative_review": {
        "label": "Review xấu (theo seller)",
        "definition": (
            "Đơn điểm review ≤ 2, quy cho seller. "
            "Loại đơn nhiều seller và shared_review_type = cross_seller."
        ),
        "numerator": "Số đơn phân biệt có negative_review_flag = 1 trong tập seller.",
        "denominator": "COUNT(DISTINCT order_id) có điểm trong cùng tập.",
    },
    "negative_review_market": {
        "label": "Review xấu (toàn sàn)",
        "definition": "Đơn điểm review ≤ 2 trên cả sàn, kể cả đơn nhiều seller và cross_seller.",
        "numerator": "Số đơn có negative_review_flag = 1.",
        "denominator": "Số đơn có negative_review_flag khác null.",
    },
    "cancel_rate": {
        "label": "Cancel rate",
        "definition": "Đơn bị hủy hoặc unavailable. Đây không phải đơn trải nghiệm xấu.",
        "numerator": "Số đơn phân biệt có trạng thái canceled hoặc unavailable.",
        "denominator": "Số đơn phân biệt mọi trạng thái.",
    },
    "risk_score": {
        "label": "Điểm rủi ro",
        "definition": (
            "M1, logistic regression. Xác suất một đơn của seller ở tháng sau là trải nghiệm xấu, "
            "học từ các tháng đã qua trên fact_seller_monthly."
        ),
        "numerator": "p_bad trên dss.seller_risk_score.",
        "denominator": "Không phải tỷ lệ cộng dồn. Seller dưới min_orders không được xếp hạng.",
    },
    "active_sellers": {
        "label": "Seller đang hoạt động",
        "definition": "Seller có ít nhất một đơn hợp lệ trong khoảng dữ liệu.",
        "numerator": "Số seller phân biệt có n_orders_valid ≥ 1. Không tính member −1.",
        "denominator": "Không phải tỷ lệ.",
    },
}

HOME_TERMS = (
    "gmv",
    "aov",
    "bad_experience",
    "late_ship",
    "negative_review",
    "negative_review_market",
    "late_delivery",
    "cancel_rate",
    "risk_score",
)


def explain(term: str) -> str:
    """Definition plus numerator and denominator, for a tooltip or expander."""
    row = GLOSSARY[term]
    return f"{row['definition']} Tử: {row['numerator']} Mẫu: {row['denominator']}"


def freshness_line() -> str:
    return f"Dữ liệu cập nhật đến {DATA_AS_OF} · đơn {DATA_SPAN} · {DATA_PLACE}"
