import os
import json
import gspread
from typing import Dict
from oauth2client.service_account import ServiceAccountCredentials
import requests
from bs4 import BeautifulSoup
from pathlib import Path


# -------------------- 매뉴얼 불러오기 (JSON 기반) --------------------
def get_manual_text() -> str:
    manual_path = Path("utils/manual.json")
    if not manual_path.exists():
        return "상담 매뉴얼을 찾을 수 없습니다."

    try:
        with manual_path.open(encoding="utf-8") as f:
            manual_data = json.load(f)

        if isinstance(manual_data, list):
            return "\n\n".join(f"Q: {item.get('Q', '')}\nA: {item.get('A', '')}" for item in manual_data)
        elif isinstance(manual_data, dict):
            return "\n\n".join(f"Q: {k}\nA: {v}" for k, v in manual_data.items())
        else:
            return "상담 매뉴얼 포맷 오류: list 또는 dict 형태여야 합니다."

    except Exception as e:
        return f"상담 매뉴얼 로딩 중 오류: {e}"

# -------------------- 구글 시트 불러오기 --------------------
def get_google_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON"), scope
    )
    return gspread.authorize(creds)

def get_sheet_info() -> str:
    """
    구글 시트 데이터를 요약된 텍스트로 파싱
    """
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

# -------------------- 구글 문서 불러오기 --------------------
def parse_doc() -> str:
    """
    구글 문서를 파싱하여 텍스트 추출
    """
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

            if tag.name in ['h1', 'h2', 'h3']:
                lines.append(f"\n📌 {text}\n")
            elif tag.name == 'li':
                if len(text) < 3:
                    continue
                lines.append(f"- {text}")
            elif tag.name == 'p':
                if len(text.split()) < 3:
                    continue
                lines.append(text)

        unique_lines = list(dict.fromkeys(lines))  # 순서 보존 + 중복 제거
        return "\n".join(unique_lines).strip()

    except Exception as e:
        return f"문서 파싱 실패: {e}"
