"""One glossary for tooltips and the home-page explainer.

Definitions follow SPEC §1 and DESIGN §3.6. Marketplace bad experience is the
order flag. The seller-month rate is a different measure and is not used here.
"""

from __future__ import annotations

# Locked snapshot date in the Gold load config (DESIGN §3.6), not a query result.
DATA_AS_OF = "2018-10-17"
DATA_SPAN = "2016–2018"
DATA_PLACE = "Brazil"

# SPEC: a dense month has at least this many orders. Home lists the rest from a query.
DENSE_MONTH_MIN_ORDERS = 1000

OLIST_DATASET_URL = "https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce"
FUNNEL_DATASET_URL = "https://www.kaggle.com/datasets/olistbr/marketing-funnel-olist"
LICENSE_NAME = "CC BY-NC-SA 4.0"
LICENSE_URL = "https://creativecommons.org/licenses/by-nc-sa/4.0/"
REPO_URL = "https://github.com/toann1405/olist-dw-dss"

MODEL_M1 = (
    "M1 là phân loại (logistic regression): dự báo xác suất một đơn tháng tới của seller là đơn xấu."
)
MODEL_M2 = (
    "M2 là mô phỏng chính sách, có ràng buộc GMV bị ảnh hưởng và số seller được can thiệp."
)

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
        "denominator": "Số đơn tính được cờ trải nghiệm xấu.",
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
        "label": "Xác suất đơn xấu",
        "definition": (
            "Xác suất một đơn tháng tới của seller là đơn trải nghiệm xấu "
            "(review ≤ 2 hoặc giao trễ), từ mô hình logistic regression. "
            "18% nghĩa là khoảng 18/100 đơn nếu mô hình hiệu chỉnh tốt. Xem mục Độ tin cậy."
        ),
        "numerator": "p_bad trên dss.seller_risk_score.",
        "denominator": "Không phải tỷ lệ cộng dồn. Seller dưới số đơn tối thiểu không được xếp hạng.",
    },
    "active_sellers": {
        "label": "Seller đang hoạt động",
        "definition": "Seller có ít nhất một đơn hợp lệ trong khoảng dữ liệu.",
        "numerator": "Số seller phân biệt có ít nhất một đơn hợp lệ.",
        "denominator": "Không phải tỷ lệ.",
    },
    "policy_p0": {
        "label": "P0",
        "definition": "Không can thiệp. Giữ nguyên để làm mốc so sánh.",
        "numerator": "Không gắn cờ seller.",
        "denominator": "Không phải tỷ lệ.",
    },
    "policy_p1": {
        "label": "P1",
        "definition": "Can thiệp theo ngưỡng KPI đã xảy ra (bàn giao trễ hoặc điểm review).",
        "numerator": "Seller vượt ngưỡng KPI cố định.",
        "denominator": "Không phải tỷ lệ.",
    },
    "policy_p2": {
        "label": "P2",
        "definition": "Can thiệp theo xác suất đơn xấu do mô hình dự báo.",
        "numerator": "Seller có xác suất đơn xấu vượt ngưỡng hạng.",
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

HOME_SHORT_TERMS = (
    "gmv",
    "bad_experience",
    "late_ship",
    "late_delivery",
    "risk_score",
    "policy_p0",
    "policy_p1",
    "policy_p2",
)


def explain(term: str) -> str:
    """Definition plus numerator and denominator, for a tooltip or expander."""
    row = GLOSSARY[term]
    return f"{row['definition']} Tử: {row['numerator']} Mẫu: {row['denominator']}"


def short_label(term: str) -> str:
    return GLOSSARY[term]["label"]


def short_text(term: str) -> str:
    """Plain definition, without the numerator and denominator."""
    return GLOSSARY[term]["definition"]


def freshness_line() -> str:
    return f"Dữ liệu cập nhật đến {DATA_AS_OF} · đơn {DATA_SPAN} · {DATA_PLACE}"
