#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google Cloud Text-to-Speech 中文最小脚本（强制 REST，避开 gRPC 卡住）
- 直接尝试常见中文人声：Neural2-A -> Standard-A -> 仅按语言自动选
- 同时导出 MP3 与 WAV(16k 16-bit PCM)
"""

import os
from pathlib import Path
from google.cloud import texttospeech as tts
from google.api_core.exceptions import GoogleAPICallError, InvalidArgument

# 1) 服务账号
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/Users/vince/Documents/mediday/config/storied-fuze-454117-i9-731b06659d58.json"

# 2) 强制走 REST 以规避 gRPC 503
client = tts.TextToSpeechClient(transport="rest")

TEXT = " 花几分钟的冥想时间来安定下来。感受存在于此刻。感受在这一刻保持清醒的状态。"
OUT = Path("output_tts"); OUT.mkdir(exist_ok=True, parents=True)


def synthesize_once(text: str, voice_sel: tts.VoiceSelectionParams, fmt: str):
    if fmt == "mp3":
        audio_cfg = tts.AudioConfig(audio_encoding=tts.AudioEncoding.MP3, speaking_rate=1.0)
    elif fmt == "wav":
        audio_cfg = tts.AudioConfig(
            audio_encoding=tts.AudioEncoding.LINEAR16,  # 16-bit PCM
            sample_rate_hertz=16000,                   # 通用且稳定
            speaking_rate=1.0
        )
    else:
        raise ValueError("fmt must be 'mp3' or 'wav'")

    req = tts.SynthesizeSpeechRequest(
        input=tts.SynthesisInput(text=text),
        voice=voice_sel,
        audio_config=audio_cfg,
    )
    # 设置超时，防止“半天没反应”
    resp = client.synthesize_speech(request=req, timeout=30)
    return resp.audio_content

def main():
    # 依次尝试更具体 -> 更宽松的 voice 选择
    # trials = [
    #     tts.VoiceSelectionParams(language_code="cmn-CN", name="cmn-CN-Neural2-A"),
    #     tts.VoiceSelectionParams(language_code="cmn-CN", name="cmn-CN-Standard-A"),
    #     tts.VoiceSelectionParams(language_code="cmn-CN", ssml_gender=tts.SsmlVoiceGender.FEMALE),
    # ]
    voice_name = "Achird"
    trials = [tts.VoiceSelectionParams(
        language_code="cmn-CN",
        name=f"cmn-CN-Chirp3-HD-{voice_name}",   # 可换：Achird / Aoede / Sulafat 等
    )]

    last_err = None
    for v in trials:
        try:
            print(f"Trying voice: lang={v.language_code}, name={getattr(v, 'name', None)}, gender={v.ssml_gender}")
            mp3 = synthesize_once(TEXT, v, "mp3")
            wav = synthesize_once(TEXT, v, "wav")

            (OUT / f"demo_zh_cn_{voice_name}.mp3").write_bytes(mp3)
            # (OUT / "demo_zh_cn_16k.wav").write_bytes(wav)
            print(f"✅ 成功！已保存：{(OUT / f'demo_zh_cn_{voice_name}.mp3').resolve()}")
            # print(f"✅ 成功！已保存：{(OUT / 'demo_zh_cn_16k.wav').resolve()}")
            return
        except InvalidArgument as e:
            # 常见于指定的 voice 名称在你的项目/区域不可用
            print(f"⚠️ 该人声不可用，换一个试试：{e.message if hasattr(e,'message') else e}")
            last_err = e
            continue
        except GoogleAPICallError as e:
            # 网络/代理/超时等问题
            print(f"❌ 网络或服务调用失败：{repr(e)}")
            last_err = e
            # 这里不立即退出，给后续 trial 一个机会（有时仅某个 voice 触发 4xx）
            continue
        except Exception as e:
            print(f"❌ 其他异常：{repr(e)}")
            last_err = e
            continue

    raise SystemExit(f"全部尝试仍失败，最后错误：{repr(last_err)}")

if __name__ == "__main__":
    main()
