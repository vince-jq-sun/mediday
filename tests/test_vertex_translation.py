#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
from pathlib import Path
from typing import List, Dict, Any

from google.api_core.retry import Retry
from google.cloud import aiplatform
from google.oauth2 import service_account  # ★ 新增

# ====== 你的环境 ======
PROJECT_ID = "storied-fuze-454117-i9"
LOCATION = "us-central1"
ENDPOINT = f"{LOCATION}-aiplatform.googleapis.com"

# ★ 你的服务账号 JSON（你之前用过的那份）
SA_KEY = "/Users/vince/Documents/mediday/config/storied-fuze-454117-i9-731b06659d58.json"

TEXTS: List[str] = [
    "{Remind yourself that you're here, awake and aware.} {Spend the first moments settling in and sensing being here.} {Feel awake in the midst of this moment.}"
]

TERMINOLOGY_FILE = Path(__file__).parent.parent / "data" / "terminology" / "terminology.json"
SOURCE_LANG = "en"
TARGET_LANG = "zh-CN"  # 建议写 zh-CN

def load_terminology(path: Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {k: v for k, v in data.items() if not k.startswith("_")}

def make_terminology_hint(terminology: Dict[str, Any]) -> str:
    lines = []
    for en, zh in terminology.items():
        if isinstance(zh, list):
            lines.append(f"- {en} → " + " 或 ".join(zh))
        else:
            lines.append(f"- {en} → {zh}")
    if not lines:
        return ""
    return (
        "You are translating mindfulness meditation instructions into Simplified Chinese.\n"
        "Respect the following terminology preferences where appropriate (not strict word-for-word):\n"
        + "\n".join(lines)
        + "\nTranslate naturally and fluently. Keep braces { } as-is.\n\n"
    )

def build_instances(texts: List[str], hint: str) -> List[Dict[str, Any]]:
    instances = []
    for t in texts:
        contents = t if not hint else (hint + t)
        instances.append({
            "model": f"projects/{PROJECT_ID}/locations/{LOCATION}/models/general/translation-llm",
            "source_language_code": SOURCE_LANG,
            "target_language_code": TARGET_LANG,
            "contents": [contents],
        })
    return instances

def main():
    terminology = load_terminology(TERMINOLOGY_FILE)
    hint = make_terminology_hint(terminology)

    print("=== Source Texts ===")
    for i, s in enumerate(TEXTS, 1):
        print(f"{i}. {s}")

    # ★ 用服务账号 JSON 显式创建凭据（cloud-platform 全权限）
    scopes = ["https://www.googleapis.com/auth/cloud-platform"]
    credentials = service_account.Credentials.from_service_account_file(SA_KEY, scopes=scopes)

    # ★ 用 REST + 显式凭据创建客户端（避免 gRPC/ADC 的坑）
    client = aiplatform.gapic.PredictionServiceClient(
        client_options={"api_endpoint": ENDPOINT},
        transport="rest",
        credentials=credentials,  # 关键
    )

    endpoint_id = f"projects/{PROJECT_ID}/locations/{LOCATION}/publishers/google/models/cloud-translate-text"
    instances = build_instances(TEXTS, hint)

    retry = Retry(initial=1.0, maximum=10.0, multiplier=2.0, deadline=60.0)

    response = client.predict(
        endpoint=endpoint_id,
        instances=instances,
        timeout=60.0,
        retry=retry,
    )

    print("\n=== Translations ===")
    for i, pred in enumerate(response.predictions, 1):
        translations = pred.get("translations", [])
        print(f"{i}. {translations[0].get('translatedText', '') if translations else ''}")

if __name__ == "__main__":
    main()
