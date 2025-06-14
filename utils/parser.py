# utils/parser.py

import re

def parse_question(question: str) -> dict:
    q = question.strip()

    if "납기" in q and "최대" in q:
        return {"intent": "query_delivery_deadline"}

    if "상품 코드" in q or ("제품" in q and "납기" in q):
        codes = extract_product_codes(q)
        return {"intent": "query_delivery_per_item", "product_codes": codes}

    if "|" in q or "," in q:
        return parse_date_tag_filter(q)

    if "최근" in q:
        return {"intent": "summary_request"}

    return {"intent": "unknown"}

def extract_product_codes(text: str):
    return re.findall(r"ZA\d{3}", text)

def parse_date_tag_filter(text: str):
    try:
        date_part, tags_part = map(str.strip, text.split("|", 1))
        tags = [t.strip() for t in tags_part.split(",")]
        return {
            "intent": "filter_by_date_and_tags",
            "filters": {
                "date": date_part,
                "tags": tags
            }
        }
    except:
        return {"intent": "unknown"}
