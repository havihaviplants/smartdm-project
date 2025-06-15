from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
import os
from dotenv import load_dotenv
from parser import get_manual_text
from utils.parser import parse_question  # 선택적 파서 (구조화 파싱)

# 🔐 환경 변수 및 클라이언트 초기화
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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

# 🧾 요청 모델 정의
class Question(BaseModel):
    question: str
    use_gpt4: bool = False

# ✅ 홈 테스트 라우트
@app.get("/")
async def root():
    return {"message": "Smart Parser API with Manual Only is running."}

# 🎯 핵심 라우트: GPT 질의응답
@app.post("/ask")
async def ask_question(payload: Question):
    try:
        # 🔍 질문 파싱 (선택사항)
        parsed = parse_question(payload.question)

        # 📖 상담 매뉴얼 불러오기
        manual = get_manual_text()

        # 🧠 GPT 프롬프트 구성
        prompt = f"""
다음은 상담 매뉴얼입니다. 이 문서에는 납기일, 마감일, 응대 기준 등 중요한 정보가 포함되어 있습니다:

{manual}

이 매뉴얼을 바탕으로 다음 질문에 명확하고 친절하게 답해 주세요.
질문: {payload.question}
"""

        model_name = "gpt-4" if payload.use_gpt4 else "gpt-3.5-turbo"

        # 🤖 GPT 호출
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "system",
                    "content": "너는 스마트한 상담 도우미야. 사용자의 매뉴얼을 바탕으로 질문에 정확하고 친절하게 답해줘."
                },
                {"role": "user", "content": prompt}
            ]
        )

        return {
            "answer": response.choices[0].message.content,
            "model": model_name,
            "parsed": parsed
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/test-manual")
async def test_manual():
    manual = get_manual_text()
    return {"manual": manual[:300]}  # 앞 300자만 확인

def get_manual_text():
    manual_path = os.getenv("MANUAL_PATH", "data/manual.txt")
    print(f"[DEBUG] 현재 매뉴얼 경로: {manual_path}")  # ✅ 디버깅용 출력
    if not os.path.exists(manual_path):
        print("[DEBUG] 매뉴얼 파일이 존재하지 않음.")
        return "상담 매뉴얼을 찾을 수 없습니다."
    with open(manual_path, "r", encoding="utf-8") as f:
        return f.read()

