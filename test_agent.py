# test_agent.py
from agent.router import get_ai_response

# 模擬住戶的提問
test_query = "請問 1A 車位資訊是什麼？"

print(f"正在測試問題：{test_query}")
response = get_ai_response(test_query)

print("-" * 20)
print("AI 的回答：")
print(response)