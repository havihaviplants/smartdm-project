import os
import json

def load_manual_text():
    try:
        path = os.path.join("utils", "manual.json")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # 'manual.json'이 딕셔너리 형태라면, 전체를 이어붙이기
        return "\n".join(f"{k}: {v}" for k, v in data.items())
    except Exception as e:
        return f"상담 매뉴얼을 찾을 수 없습니다. ({e})"
