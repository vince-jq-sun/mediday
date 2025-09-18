#!/bin/bash
set -euo pipefail

# ================= 配置（可改） =================
INPUT_FILE="/Users/vince/Documents/mediday/temp/awake_where_you_are_english/1-2_foundational_meditation_sample-1/segments/1-2_foundational_meditation_sample-1_segment_002.wav"
OUTPUT_DIR="/Users/vince/Documents/mediday/temp/awake_where_you_are_english/1-2_foundational_meditation_sample-1/transcripts"
# MODEL_PATH="$HOME/.cache/huggingface/hub/models--ggerganov--whisper.cpp/snapshots/5359861c739e955e79d9a303bcbc70fb988958b1/ggml-large-v3-q5_0.bin"
MODEL_PATH="$HOME/.cache/huggingface/hub/models--ggerganov--whisper.cpp/snapshots/5359861c739e955e79d9a303bcbc70fb988958b1/ggml-large-v3.bin"

# whisper 可执行：使用 whisper-cli（已用 GGML_METAL=1 编译会自动用 Metal GPU）
WHISPER_BIN="${WHISPER_BIN:-$HOME/whisper.cpp/build/bin/whisper-cli}"

# 语言（en/zh/ja/auto）
LANG_OPT="${LANG_OPT:-en}"

# 线程数
NTHREAD="${NTHREAD:-4}"

# CPU-only 开关（1 表示禁用 GPU）
DISABLE_GPU="${DISABLE_GPU:-0}"

# 停顿检测阈值（秒）
PAUSE_THRESHOLD="${PAUSE_THRESHOLD:-1.0}"
# =================================================

# 基本检查
[ -f "$INPUT_FILE" ] || { echo "❌ 输入文件不存在: $INPUT_FILE"; exit 1; }
mkdir -p "$OUTPUT_DIR"
[ -f "$MODEL_PATH" ] || { echo "❌ 模型文件不存在: $MODEL_PATH"; exit 1; }
[ -x "$WHISPER_BIN" ] || { echo "❌ 找不到 whisper-cli: $WHISPER_BIN"; echo "提示: 在 ~/whisper.cpp 执行 make GGML_METAL=1"; exit 1; }

# 统一转 16kHz / mono / PCM16
BASENAME="$(basename "$INPUT_FILE")"
STEM="${BASENAME%.*}"
WAV_FILE="$OUTPUT_DIR/${STEM}.wav"

echo "🎧 规范化音频为 16kHz mono PCM16..."
ffmpeg -y -loglevel error -i "$INPUT_FILE" -ar 16000 -ac 1 -c:a pcm_s16le "$WAV_FILE"

# GPU 标志（whisper-cli 没有 -ngl；用 GGML_METAL=1 编译即默认启用 GPU）
GPU_FLAG=""
if [ "$DISABLE_GPU" = "1" ]; then
  GPU_FLAG="--no-gpu"
fi

echo "🚀 开始转录..."
set +e
"$WHISPER_BIN" \
  -m "$MODEL_PATH" \
  -f "$WAV_FILE" \
  -l "$LANG_OPT" \
  -t "$NTHREAD" \
  -otxt -osrt -ojf \
  --output-words \
  -of "$OUTPUT_DIR/${STEM}" \
  -bs 5 \
  -tp 0.2 \
  --max-context 256 \
  --suppress-nst 0 \
  --prompt " " \
  $GPU_FLAG
STATUS=$?
set -e

if [ $STATUS -ne 0 ]; then
  echo "❌ 转录失败（退出码 $STATUS）"; exit $STATUS
fi

echo "✅ 转录完成："
echo "   TXT: $OUTPUT_DIR/${STEM}.txt"
echo "   SRT: $OUTPUT_DIR/${STEM}.srt"
echo "   JSON: $OUTPUT_DIR/${STEM}.json"

# 整合 JSON 和 SRT 输出，合并句子为完整文本
INTEGRATOR_SCRIPT="/Users/vince/Documents/mediday/scripts/whisper_output_integrator.py"
if [ -f "$INTEGRATOR_SCRIPT" ] && [ -f "$OUTPUT_DIR/${STEM}.json" ] && [ -f "$OUTPUT_DIR/${STEM}.srt" ]; then
    echo "🔄 整合 JSON 和 SRT 输出，合并句子为完整文本..."
    python3 "$INTEGRATOR_SCRIPT" \
        "$OUTPUT_DIR/${STEM}.json" \
        "$OUTPUT_DIR/${STEM}.srt" \
        -o "$OUTPUT_DIR/${STEM}_integrated.json" \
        -p "$PAUSE_THRESHOLD"
    
    if [ $? -eq 0 ]; then
        echo "✅ 整合完成: $OUTPUT_DIR/${STEM}_integrated.json"
        echo "   - 句子层面：所有句子合并为一句完整文本"
        echo "   - 词级时间戳：保留精确的词级时间信息"
    else
        echo "⚠️  整合失败，但转录文件已生成"
    fi
else
    echo "⚠️  跳过整合步骤（缺少必要文件或整合脚本）"
fi
