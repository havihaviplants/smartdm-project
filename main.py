from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI
from utils.parser import parse_question, get_manual_text
import os

# 🔐 환경 변수 로드
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

if not openai_api_key:
    raise RuntimeError("[환경설정 오류] OPENAI_API_KEY가 .env에 정의되어 있지 않습니다.")

# 🤖 OpenAI 클라이언트 초기화
client: OpenAI = OpenAI(api_key=openai_api_key)

# 🌐 FastAPI 인스턴스 생성
app = FastAPI()

# ✅ CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 📥 요청 모델 정의
class Question(BaseModel):
    question: str
    use_gpt4: bool = False

# 🏠 기본 루트
@app.get("/")
async def root():
    return {"message": "Smart Parser API is running."}

# 🧪 매뉴얼 확인용 테스트 엔드포인트
@app.get("/test-manual")
async def test_manual():
    try:
        manual = get_manual_text()
        return {"manual": manual[:300]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"❌ 매뉴얼 로딩 실패: {e}")

# 📦 매뉴얼 기반 응답 처리
@app.post("/ask")
async def ask_question(payload: Question):
    try:
        parsed = parse_question(payload.question)
        manual = get_manual_text()

        if not manual or "상담 매뉴얼을 찾을 수 없습니다." in manual:
            return {
                "answer": "❗ 상담 매뉴얼이 존재하지 않아 정확한 답변을 제공할 수 없습니다.",
                "model": "manual_missing",
                "parsed": parsed
            }

        prompt = (
            f"다음은 상담 매뉴얼입니다. 납기일, 마감일, 응대 기준 등의 정보가 포함되어 있습니다:\n\n"
            f"{manual}\n\n"
            f"위 매뉴얼을 바탕으로 아래 질문에 명확하고 친절하게 답변해 주세요.\n\n"
            f"질문: {payload.question}"
        )

        model_name = "gpt-4" if payload.use_gpt4 else "gpt-3.5-turbo"

        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "system",
                    "content": "너는 상담 매뉴얼을 기준으로 정확하고 친절하게 답하는 스마트한 상담 도우미야."
                },
                {"role": "user", "content": prompt}
            ]
        )

        answer = response.choices[0].message.content.strip()

        return {
            "answer": answer,
            "model": model_name,
            "parsed": parsed
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"❌ GPT 응답 실패: {e}")
