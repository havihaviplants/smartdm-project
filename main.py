from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import openai
import json

# 🔐 환경 변수 로드
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")

if not OPENAI_API_KEY:
    raise RuntimeError("❌ OPENAI_API_KEY가 설정되어 있지 않습니다.")
if not GOOGLE_SHEET_ID:
    raise RuntimeError("❌ GOOGLE_SHEET_ID가 설정되어 있지 않습니다.")

openai.api_key = OPENAI_API_KEY

# 📦 유틸 함수
from utils.parser import parse_question, get_manual_text, get_sheet_info

# 🌐 FastAPI 앱 정의
app = FastAPI(
    title="Smart Parser API",
    description="DM 및 상담용 AI 파서 API",
    version="0.1.0"
)

# ✅ CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 📥 요청 모델
class Question(BaseModel):
    question: str
    use_gpt4: bool = False

# 🔍 Health Check
@app.get("/")
async def root():
    return {"message": "Smart Parser API is running."}

# 📘 상담 매뉴얼 반환
@app.get("/api/manual")
def get_manual():
    try:
        return {"manual": get_manual_text()}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="manual.json not found")
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="manual.json is not valid JSON")

# 🧪 매뉴얼 테스트
@app.get("/test-manual")
async def test_manual():
    try:
        return {"manual": get_manual_text()[:300]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"매뉴얼 로딩 실패: {e}")

# 🧪 디버깅용 전체 매뉴얼
@app.get("/debug-manual")
def debug_manual():
    return {"manual": get_manual_text()}

# 🤖 GPT 응답 생성
@app.post("/ask")
async def ask_question(payload: Question):
    try:
        parsed = parse_question(payload.question)
        manual = get_manual_text()
        sheet_summary = get_sheet_info(GOOGLE_SHEET_ID)

        # 🔻 프롬프트 사이즈 제한 (1000자 초과 시 잘라냄)
        def truncate(text: str, limit: int = 1000) -> str:
            return text[:limit] + "\n(이하 생략)" if len(text) > limit else text

        manual = truncate(manual)
        sheet_summary = truncate(sheet_summary)

        if not manual or "상담 매뉴얼을 찾을 수 없습니다." in manual:
            return {
                "answer": "❗ 상담 매뉴얼이 존재하지 않아 정확한 답변을 제공할 수 없습니다.",
                "model": "manual_missing",
                "parsed": parsed
            }

        prompt = f"""
아래는 상담을 위한 매뉴얼과 참고용 시트 정보입니다.

📘 상담 매뉴얼:
{manual}

📊 참고용 시트 요약:
{sheet_summary}

이 자료를 바탕으로 다음 질문에 대해 정확하고 친절하게 답변해 주세요.
질문: {payload.question}
"""

        model = "gpt-4" if payload.use_gpt4 else "gpt-3.5-turbo"

        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": "너는 매뉴얼과 시트 데이터를 참고해 정확하게 응답하는 스마트 상담 도우미야."},
                {"role": "user", "content": prompt}
            ]
        )

        return {
            "answer": response.choices[0].message.content.strip(),
            "model": model,
            "parsed": parsed
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GPT 응답 실패: {e}")

# 🧪 시트 파싱 (더미용)
@app.get("/parse-sheet")
def parse_sheet(sheet_id: str = Query(...), cell_range: str = Query(...)):
    dummy_data = [
        {"날짜": "2025-06-27", "내용": "예시 내용입니다", "태그": ["문의", "우선응답"]},
        {"날짜": "2025-06-26", "내용": "다른 항목입니다", "태그": ["캠페인"]}
    ]
    return dummy_data

# 🖥 콘솔 디버깅용 출력
print("🔑 OPENAI_API_KEY 존재 여부:", bool(OPENAI_API_KEY))
print("📄 GOOGLE_SHEET_ID:", GOOGLE_SHEET_ID)
