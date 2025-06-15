from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import openai
import os
from dotenv import load_dotenv
from parser import parse_doc
from parser import parse_sheet
from parser import get_manual_text
from refiner import refine_question

from utils.parser import parse_question  # ✅ 질문 파서 import

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()

class Question(BaseModel):
    question: str


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------- Models --------------------
class Question(BaseModel):
    question: str
    use_gpt4: bool = False  # 선택적으로 GPT-4 사용할 수 있게 함

class ParseRequest(BaseModel):
    source: str  # "sheet" or "doc"

# -------------------- Core Logic --------------------
def get_parsed_context():
    try:
        doc_text = parse_doc()
    except Exception as e:
        doc_text = f"[문서 파싱 오류: {e}]"

    try:
        sheet_text = parse_sheet()
    except Exception as e:
        sheet_text = f"[시트 파싱 오류: {e}]"

    combined = f"구글 문서:\n{doc_text}\n\n구글 시트:\n{sheet_text}"
    return combined[:8000]

# -------------------- Routes --------------------
@app.get("/")
async def root():
    return {"message": "Smart Parser API is running."}

@app.post("/ask")
async def ask_question(payload: Question):
    try:
        # ✅ 질문 파싱
        parsed = parse_question(payload.question)

        # ✅ 문맥 불러오기
        context = get_parsed_context()

        # ✅ GPT 프롬프트 구성
        prompt = f"""
다음은 사용자의 데이터입니다.

{context}

이 데이터를 바탕으로 아래 질문에 자연어로 답해 주세요.
질문: {payload.question}
        """

        model_name = "gpt-4" if payload.use_gpt4 else "gpt-3.5-turbo"

        response = openai.ChatCompletion.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "너는 스마트한 도우미야. 사용자의 데이터 문맥을 바탕으로 질문에 친절하고 정확하게 답해줘."},
                {"role": "user", "content": prompt}
            ]
        )

        return {
            "answer": response['choices'][0]['message']['content'],
            "model": model_name,
            "parsed": parsed
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ask-all")
async def ask_all(payload: Question):
    return await ask_question(payload)

@app.post("/parse")
async def parse_data(req: ParseRequest):
    try:
        if req.source == "doc":
            return {"parsed": parse_doc()}
        elif req.source == "sheet":
            return {"parsed": parse_sheet()}
        else:
            raise HTTPException(status_code=400, detail="지원하지 않는 소스입니다.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"파싱 중 오류 발생: {e}")
