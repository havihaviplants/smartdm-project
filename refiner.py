# refiner.py
import openai
import os

# API 키 설정 (main.py 또는 초기화 위치에서 dotenv를 불러왔다는 가정)
openai.api_key = os.getenv("OPENAI_API_KEY")

def load_manual(filepath="data/manual.txt") -> str:
    """상담 매뉴얼 텍스트 파일 불러오기"""
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()

def refine_question(manual_text: str, question: str) -> str:
    """
    상담 매뉴얼과 고객 질문을 기반으로, 자연어 응답 생성
    """
    prompt = f"""
다음은 상담 매뉴얼입니다. 이 매뉴얼을 기반으로 고객 질문에 정중하고 실무적으로 정확하게 응답해주세요.

[상담 매뉴얼]
{manual_text}

[고객 질문]
"{question}"

[응답]
"""
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    return response["choices"][0]["message"]["content"].strip()
