import json
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests
from bs4 import BeautifulSoup

# -------------------- 인증 --------------------
def get_google_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON"), scope
    )
    return gspread.authorize(creds)

# -------------------- 시트 파싱 --------------------
def parse_sheet():
    try:
        sheet_id = os.getenv("GOOGLE_SHEET_ID")
        client = get_google_client()
        sheet = client.open_by_key(sheet_id).sheet1
        data = sheet.get_all_values()

        if not data or len(data) < 2:
            return "시트에 데이터가 없습니다."

        headers = [h.strip().lower() for h in data[0]]
        rows = data[1:]

        text_rows = []
        for row in rows:
            if all(not cell.strip() for cell in row):
                continue  # 완전히 빈 행은 무시

            entry = []
            for h, v in zip(headers, row):
                v = v.strip()
                if not v or h in ['비고', '참고']:  # 무의미한 열 제거
                    continue
                entry.append(f"{h}: {v}")

            if entry:
                text_rows.append(", ".join(entry))

        return "\n".join(text_rows)

    except Exception as e:
        return f"시트 파싱 실패: {e}"

# -------------------- 문서 파싱 --------------------
def parse_doc():
    try:
        doc_url = os.getenv("GOOGLE_DOC_URL")
        response = requests.get(doc_url)

        if not response.ok:
            return f"문서 접근 실패: {response.status_code}"

        soup = BeautifulSoup(response.content, "html.parser")
        body = soup.find('body')
        if not body:
            return "문서 구조 분석 실패: body 태그 없음"

        lines = []
        for tag in body.find_all(['h1', 'h2', 'h3', 'p', 'li']):
            text = tag.get_text().strip()

            # 필터링 기준
            if not text:
                continue
            if any(text.lower().startswith(prefix) for prefix in ["참고", "비고", "추가"]):
                continue

            # 태그 구조 강조
            if tag.name in ['h1', 'h2', 'h3']:
                lines.append(f"\n📌 {text}\n")
            elif tag.name == 'li':
                if len(text) < 3:  # 너무 짧은 리스트 항목 제거
                    continue
                lines.append(f"- {text}")
            elif tag.name == 'p':
                if len(text.split()) < 3:  # 의미 없는 문장 제거
                    continue
                lines.append(text)

        # 중복 제거 + 정제 출력
        unique_lines = list(dict.fromkeys(lines))  # 순서 보존 + 중복 제거
        return "\n".join(unique_lines).strip()

    except Exception as e:
        return f"문서 파싱 실패: {e}"
    
# parser.py

def get_manual_text():
    """refiner.py와 공유할 수 있도록 상담 매뉴얼 불러오기"""
    manual_path = os.getenv("MANUAL_PATH", "data/manual.txt")
    if not os.path.exists(manual_path):
        return "상담 매뉴얼을 찾을 수 없습니다."
    with open(manual_path, "r", encoding="utf-8") as f:
        return f.read()
