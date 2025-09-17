import json
from openai import OpenAI

# 读取 API key
with open("config/openai.json", "r") as f:
    config = json.load(f)
api_key = config["api"]

client = OpenAI(api_key=api_key)

# 发送 hello，reasoning 设置为 low
resp = client.chat.completions.create(
    model="gpt-4.1-mini",
    messages=[{"role": "user", "content": "hello"}],
    extra_body={  
        "reasoning": {"effort": "low"}
    }
)

print(resp.choices[0].message.content)
