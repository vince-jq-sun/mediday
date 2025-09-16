#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick test for Google Cloud Translation LLM (with optional glossary), wired to your creds & project.

Prereqs:
  pip install --upgrade google-cloud-translate
"""

import os
from typing import List, Optional
from google.cloud import translate_v3 as translate
from google.api_core.exceptions import GoogleAPICallError, InvalidArgument

# ====== 🔧 固定到你的环境 ======
# 你的服务账号凭证（来自你之前脚本）
os.environ.setdefault(
    "GOOGLE_APPLICATION_CREDENTIALS",
    "/Users/vince/Documents/mediday/config/storied-fuze-454117-i9-731b06659d58.json",
)

# 你的项目 ID（从凭证文件名推断；如需覆盖，也可导出 GOOGLE_CLOUD_PROJECT）
PROJECT_ID = "storied-fuze-454117-i9"

# 模型与（可选）glossary 所在的区域
LOCATION = "us-central1"

# 在这里直接写入你要测试的英文句子
TEXTS: List[str] = [
    "Remind yourself. That you're here. You're awake and aware.",
    "And spend this first few moments of the meditation just settling. And sensing into being here.",
    "Sense of being awake in the midst of this moment."
]

# ====== 📘 可选：术语表（glossary）资源名 ======
# 没有就留 None；若已创建，填成类似：
# "projects/storied-fuze-454117/locations/us-central1/glossaries/mediday_zh_terms"
GLOSSARY_RESOURCE: Optional[str] = None

# 语言方向
SOURCE_LANG = "en"
TARGET_LANG = "zh-CN"  # 简体中文

def translate_with_llm(
    texts: List[str],
    project_id: str,
    location: str,
    source_lang: str,
    target_lang: str,
    glossary_resource: Optional[str] = None,
    timeout: int = 30,
) -> List[str]:
    """
    调用 Cloud Translation Advanced v3 的 translateText，
    并指定使用 Translation LLM 模型（general/translation-llm）。
    """
    client = translate.TranslationServiceClient(transport="rest")  # 用 REST 更稳
    parent = f"projects/{project_id}/locations/{location}"
    model_path = f"projects/{project_id}/locations/{location}/models/general/translation-llm"

    request = {
        "parent": parent,
        "contents": texts,
        "mime_type": "text/plain",
        "source_language_code": source_lang,
        "target_language_code": target_lang,
        "model": model_path,
    }

    if glossary_resource:
        request["glossary_config"] = {"glossary": glossary_resource}

    resp = client.translate_text(request=request, timeout=timeout)

    # 如果启用了 glossary，优先读取 glossary_translations
    out: List[str] = []
    if glossary_resource and getattr(resp, "glossary_translations", None):
        for t in resp.glossary_translations:
            out.append(t.translated_text)
    else:
        for t in resp.translations:
            out.append(t.translated_text)
    return out

def estimate_cost(chars_in: int, chars_out: int) -> float:
    """
    Translation LLM 价格：$10/百万输入字符 + $10/百万输出字符（粗略估算）。
    """
    return (chars_in / 1_000_000.0) * 10.0 + (chars_out / 1_000_000.0) * 10.0

def main():
    print(f"Project : {PROJECT_ID}")
    print(f"Location: {LOCATION}")
    print(f"Model   : projects/{PROJECT_ID}/locations/{LOCATION}/models/general/translation-llm")
    if GLOSSARY_RESOURCE:
        print(f"Glossary: {GLOSSARY_RESOURCE}")
    else:
        print("Glossary: (none)")

    print("\n=== Source texts ===")
    for i, s in enumerate(TEXTS, 1):
        print(f"{i}. {s}")

    try:
        translations = translate_with_llm(
            TEXTS, PROJECT_ID, LOCATION, SOURCE_LANG, TARGET_LANG, GLOSSARY_RESOURCE
        )
    except InvalidArgument as e:
        print(f"\n❌ INVALID_ARGUMENT: {e}")
        print("  - 检查 model 与 glossary 是否在同一区域（LOCATION）。")
        print("  - 目标语言/源语言代码是否正确（如 zh-CN / en）。")
        return
    except GoogleAPICallError as e:
        print(f"\n❌ API 调用失败（网络/权限等）：{repr(e)}")
        print("  - 若网络不通，请确认可直连 Google 或配置 HTTPS_PROXY。")
        print("  - 确认已在该项目启用 Cloud Translation API 并开通结算。")
        return

    print("\n=== Translations ===")
    for i, zh in enumerate(translations, 1):
        print(f"{i}. {zh}")

    # 粗略费用估算（方便你感知量级）
    chars_in = sum(len(x) for x in TEXTS)
    chars_out = sum(len(x) for x in translations)
    approx = estimate_cost(chars_in, chars_out)
    print(f"\n[Cost estimate] input={chars_in} chars, output={chars_out} chars -> ~${approx:.4f}")

if __name__ == "__main__":
    main()
