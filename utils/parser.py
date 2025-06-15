import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials

def parse_question(question: str) -> dict:
    # 추후 개선 가능
    return {"keywords": question.lower().split()[:5]}

def get_manual_text() -> str:
    try:
        with open("manual.txt", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "상담 매뉴얼을 찾을 수 없습니다."

def get_sheet_info(sheet_id: str) -> str:
    try:
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
        client = gspread.authorize(creds)

        sheet = client.open_by_key(sheet_id).sheet1
        records = sheet.get_all_records()

        summary_lines = []
        for i, row in enumerate(records[:3]):
            summary = ", ".join(f"{k}: {v}" for k, v in row.items())
            summary_lines.append(f"행 {i+1} → {summary}")
        return "\n".join(summary_lines)

    except Exception as e:
        return f"[시트 로딩 실패] {e}"
