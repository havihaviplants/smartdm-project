from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import openai
from utils.parser import parse_question, get_manual_text  # utils에 통합 가정

# 🔐 환경변수 로드 및 OpenAI 클라이언트 생성
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise RuntimeError("OPENAI_API_KEY가 .env에 정의되지 않았습니다.")

client = openai.OpenAI(api_key=openai_api_key)

# 🌐 FastAPI 앱 초기화
app = FastAPI()

# ✅ CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 📥 요청 데이터 모델
class Question(BaseModel):
    question: str
    use_gpt4: bool = False

# ✅ 기본 루트
@app.get("/")
async def root():
    return {"message": "Smart Parser API is running."}

# 🧪 상담 매뉴얼 테스트용 엔드포인트
@app.get("/test-manual")
async def test_manual():
    try:
        manual = get_manual_text()
        return {"manual": manual[:300]}  # 앞부분만 확인용
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"매뉴얼 로드 실패: {e}")

# 🎯 질문 응답 엔드포인트
@app.post("/ask")
async def ask_question(payload: Question):
    try:
        parsed = parse_question(payload.question)
        manual = get_manual_text()

        if "상담 매뉴얼을 찾을 수 없습니다." in manual:
            return {
                "answer": "죄송하지만 상담 매뉴얼을 불러올 수 없어 정확한 답변이 어렵습니다.",
                "model": "none",
                "parsed": parsed
            }

        prompt = f"""
다음은 상담 매뉴얼입니다. 납기일, 마감일, 응대 기준 등의 정보가 포함되어 있습니다:

{manual}

위 매뉴얼을 바탕으로 아래 질문에 명확하고 친절하게 답변해 주세요.

질문: {payload.question}
"""

        model = "gpt-4" if payload.use_gpt4 else "gpt-3.5-turbo"

        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "너는 상담 매뉴얼을 잘 이해하고 친절하게 응답하는 스마트한 상담 도우미야."
                },
                {"role": "user", "content": prompt}
            ]
        )

        return {
            "answer": response.choices[0].message.content,
            "model": model,
            "parsed": parsed
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GPT 응답 실패: {e}")
