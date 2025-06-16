# manual_loader.py
import os
import json

def load_manual():
    manual_path = os.path.join(os.path.dirname(__file__), "utils", "manual.json")
    try:
        with open(manual_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print("⚠️ manual.json 파일을 찾을 수 없습니다.")
        return {}
