import os
import json
import gspread
from typing import Dict
from oauth2client.service_account import ServiceAccountCredentials
import requests
from bs4 import BeautifulSoup

# -------------------- 매뉴얼 불러오기 --------------------
def get_manual_text() -> str:
    """
    manual.json을 불러와 텍스트로 변환 (GPT 입력용)
    """
    try:
        manual_path = os.path.join(os.path.dirname(__file__), "manual.json")
        print(f"📂 manual.json 경로: {manual_path}")
        with open(manual_path, "r", encoding="utf-8") as f:
            manual_data: Dict[str, str] = json.load(f)
        print(f"📄 매뉴얼 항목 수: {len(manual_data)}")
        return "\n".join([f"{k}: {v}" for k, v in manual_data.items()])
    except Exception as e:
        print(f"❌ get_manual_text 실패: {e}")
        return f"상담 매뉴얼을 찾을 수 없습니다. ({e})"

# -------------------- 키워드 파싱 --------------------
def parse_question(question: str) -> dict:
    return {"keywords": question.lower().split()[:5]}

# -------------------- 시트 파싱 --------------------
def get_google_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_path = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    print(f"🔐 서비스 계정 경로: {creds_path}")
    creds = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)
    return gspread.authorize(creds)

def get_sheet_info(sheet_id: str) -> str:
    try:
        print(f"📊 시트 ID: {sheet_id}")
        client = get_google_client()
        sheet = client.open_by_key(sheet_id).sheet1
        data = sheet.get_all_values()

        if not data or len(data) < 2:
            print("⚠️ 시트에 데이터 없음 또는 헤더만 존재")
            return "시트에 데이터가 없습니다."

        headers = [h.strip().lower() for h in data[0]]
        rows = data[1:]

        text_rows = []
        for row in rows:
            if all(not cell.strip() for cell in row):
                continue

            entry = []
            for h, v in zip(headers, row):
                v = v.strip()
                if not v or h in ['비고', '참고']:
                    continue
                entry.append(f"{h}: {v}")

            if entry:
                text_rows.append(", ".join(entry))

        print(f"✅ 시트 파싱 성공, 유효 행 수: {len(text_rows)}")
        return "\n".join(text_rows)

    except Exception as e:
        print(f"❌ get_sheet_info 실패: {e}")
        return f"시트 파싱 실패: {e}"

# -------------------- 구글 문서 파싱 --------------------
def parse_doc() -> str:
    try:
        doc_url = os.getenv("GOOGLE_DOC_URL")
        print(f"🌐 문서 URL: {doc_url}")
        response = requests.get(doc_url)

        if not response.ok:
            print(f"❌ 문서 접근 실패: status {response.status_code}")
            return f"문서 접근 실패: {response.status_code}"

        soup = BeautifulSoup(response.content, "html.parser")
        body = soup.find('body')
        if not body:
            print("❌ 문서 구조 분석 실패: body 없음")
            return "문서 구조 분석 실패: body 태그 없음"

        lines = []
        for tag in body.find_all(['h1', 'h2', 'h3', 'p', 'li']):
            text = tag.get_text().strip()
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

        unique_lines = list(dict.fromkeys(lines))
        print(f"✅ 문서 파싱 성공, 라인 수: {len(unique_lines)}")
        return "\n".join(unique_lines).strip()

    except Exception as e:
        print(f"❌ parse_doc 실패: {e}")
        return f"문서 파싱 실패: {e}"
