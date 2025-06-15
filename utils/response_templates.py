# utils/response_templates.py

delivery_data = {
    "ZA509": 13,
    "ZA026": 22,
    "ZA233": 23,
    "ZA384": 17
}

def get_template_response(parsed: dict) -> str:
    intent = parsed.get("intent")

    if intent == "query_delivery_deadline":
        return "납기의 최대 기한은 23일입니다."

    elif intent == "query_delivery_per_item":
        codes = parsed.get("product_codes", [])
        parts = []
        for code in codes:
            if code in delivery_data:
                parts.append(f"상품 코드 {code}의 납기일은 {delivery_data[code]}일입니다.")
            else:
                parts.append(f"상품 코드 {code}의 납기일 정보를 찾을 수 없습니다.")
        return " ".join(parts)

    elif intent == "filter_by_date_and_tags":
        date = parsed.get("filters", {}).get("date", "알 수 없는 날짜")
        tags = parsed.get("filters", {}).get("tags", [])
        tag_list = ", ".join(tags)
        return f"{date}에 {tag_list} 관련 기록을 조회합니다. (※ 실제 연동은 추후 구현)"

    elif intent == "summary_request":
        return "최근 기록 요약은 다음과 같습니다: ... (요약 기능은 아직 개발 중)"

    return "질문을 이해하지 못했습니다. 다시 입력해 주세요."
