# from faster_whisper import WhisperModel

# # 模型："large-v2" 可换成 "medium" / "small"
# # Apple Silicon: device="cpu" + compute_type="int8_float16" 性能/内存很均衡
# # NVIDIA GPU: device="cuda", compute_type="float16"
# model = WhisperModel("large-v2", device="cpu", compute_type="float32")
file = "/Users/vince/Documents/mediday/temp/awake_where_you_are_english/test_sample_types_of_medidation/segments/test_sample_types_of_medidation_segment_000.wav"

# segments, info = model.transcribe(
#     file,
#     language="zh",        # 或 "en"/"auto"
#     vad_filter=True,      # 轻量VAD，减少噪声段
#     beam_size=5           # 质量更稳（也可用 temperature=0）
# )

# print("language:", info.language, "prob:", info.language_probability)
# for s in segments:
#     print(f"{s.start:.2f} -> {s.end:.2f}: {s.text}")

import whisper
import torch

device = "mps" if torch.backends.mps.is_available() else "cpu"
print(device)

model = whisper.load_model("large-v2", device=device)

result = model.transcribe(file, language="zh")
for seg in result["segments"]:
    print(f"{seg['start']:.2f} -> {seg['end']:.2f}: {seg['text']}")