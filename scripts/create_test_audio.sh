#!/bin/bash

# 音频切片测试脚本
# 使用方法：
#   从根目录: bash scripts/create_test_audio.sh
#   从scripts目录: ./create_test_audio.sh

# ========== 配置参数 - 您只需要在这里修改 ==========
INPUT_FILE="data/awake_where_you_are_english/1-1_Introduction.mp3"  # 输入文件路径
OUTPUT_FILE="data/awake_where_you_are_english/1-1_Introduction.mp3_sample-1.mp3"                                                 # 输出文件路径 (支持 .wav 或 .mp3)
START_TIME=0                                                                      # 开始时间（秒）
DURATION=100                                                                       # 持续时间（秒）
# ================================================

# 检测当前执行目录并调整路径
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ "$(basename "$PWD")" == "mediday" ]]; then
    # 从根目录执行 - 路径保持不变
    PYTHON_SCRIPT="scripts/audio_pipeline/audio_slicer.py"
    TEMP_DIR="temp"
else
    # 从scripts目录执行 - 添加相对路径前缀
    INPUT_FILE="../$INPUT_FILE"
    OUTPUT_FILE="../$OUTPUT_FILE"
    PYTHON_SCRIPT="audio_pipeline/audio_slicer.py"
    TEMP_DIR="../temp"
fi

# 创建输出目录
mkdir -p "$TEMP_DIR"

echo "🎵 创建测试音频片段..."
echo "📁 输入文件: $INPUT_FILE"
echo "⏱️  时间范围: ${START_TIME}s - $((START_TIME + DURATION))s"
echo "💾 输出文件: $OUTPUT_FILE"
echo ""

# 运行音频切片工具
python "$PYTHON_SCRIPT" "$INPUT_FILE" \
    --output "$OUTPUT_FILE" \
    --start $START_TIME \
    --duration $DURATION

# 检查是否成功
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 测试音频创建成功！"
    echo "📂 文件位置: $OUTPUT_FILE"
    
    # 显示文件信息
    if [ -f "$OUTPUT_FILE" ]; then
        FILE_SIZE=$(ls -lh "$OUTPUT_FILE" | awk '{print $5}')
        echo "📊 文件大小: $FILE_SIZE"
        
        echo ""
        echo "🚀 现在可以用这个文件测试管道："
        if [[ "$(basename "$PWD")" == "mediday" ]]; then
            echo "   python scripts/run_pipeline.py preprocess temp/test_sample.wav"
        else
            echo "   cd /Users/vince/Documents/mediday"
            echo "   python scripts/run_pipeline.py preprocess temp/test_sample.wav"
        fi
    else
        echo "❌ 文件未创建成功"
    fi
else
    echo "❌ 创建失败，请检查输入文件路径和依赖"
fi
