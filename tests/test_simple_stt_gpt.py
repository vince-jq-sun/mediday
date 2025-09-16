#!/usr/bin/env python3
import os, time, wave
from pathlib import Path
from google.cloud import speech

# 1) 凭证放在系统环境里更稳（也可保留你原来的写法）
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/Users/vince/Documents/mediday/config/storied-fuze-454117-i9-731b06659d58.json'

AUDIO = Path('temp/segments/test_sample/test_sample_segment_000.wav')

def wav_meta(p: Path):
    with wave.open(str(p), 'rb') as wf:
        fr = wf.getframerate()
        ch = wf.getnchannels()
        sw = wf.getsampwidth() * 8
        dur = wf.getnframes() / fr
    return fr, ch, sw, dur

def make_client():
    # 2) 如网络容易卡住（尤其中国大陆），强制走 REST 以绕开 gRPC 卡顿
    return speech.SpeechClient(transport="rest")
    # 如果你网络通畅，也可用默认 gRPC：
    # return speech.SpeechClient()

def main():
    if not AUDIO.exists():
        print(f"Audio file not found: {AUDIO}")
        return

    sr, ch, bits, dur = wav_meta(AUDIO)
    size = AUDIO.stat().st_size
    print(f"Testing with: {AUDIO}")
    print(f"File size: {size} bytes, duration: {dur:.2f}s, sr: {sr}, ch: {ch}, bits: {bits}")

    # 3) 建议使用 ≤60s 的片段给同步接口；更长用 long_running
    use_long = dur > 58 or size > 9_000_000

    with open(AUDIO, "rb") as f:
        audio = speech.RecognitionAudio(content=f.read())

    config = speech.RecognitionConfig(
        # 注意：只有当 WAV 真的是 16-bit PCM 时才写 LINEAR16
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=sr,                 # 与实际采样率一致
        language_code="en-US",
        enable_automatic_punctuation=True,
        audio_channel_count=ch,               # 立体声也能用；必要时自动下混
        enable_separate_recognition_per_channel=False,
    )

    client = make_client()

    try:
        print("Sending request...")
        t0 = time.time()
        if use_long:
            op = client.long_running_recognize(config=config, audio=audio)
            print("Waiting on long-running operation (with timeout=180s)...")
            response = op.result(timeout=180)
        else:
            # 4) 设置超时，避免无限卡住；网络问题会尽快抛错
            response = client.recognize(config=config, audio=audio, timeout=30)

        print(f"Response received in {time.time()-t0:.1f}s")

        if not response.results:
            print("No speech detected")
            return

        for i, result in enumerate(response.results, 1):
            alt = result.alternatives[0]
            print(f"[{i}] {alt.transcript}  (conf={alt.confidence:.2f})")

    except Exception as e:
        print("Error:", repr(e))
        print("排查建议：\n"
              " - 若是超时/网络相关：确认能直连 Google，或继续使用 transport='rest' 并配置 HTTPS 代理。\n"
              " - 若是编码错误：确保 WAV 为 16-bit PCM；否则先转码（见下）。\n"
              " - 若是权限/计费：确认已在对应 GCP 项目启用 Speech-to-Text 且账号可用。")

if __name__ == "__main__":
    main()
