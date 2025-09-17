# 音频处理Pipeline使用指南

## 🚀 快速开始

### 1. 最简单的方式 - 处理单个文件
```bash
# 处理单个音频文件（使用GPT翻译）
python scripts/quick_process.py audio.mp3

# 使用Google翻译
python scripts/quick_process.py audio.mp3 --google
```

### 2. 批量处理 - 处理整个目录
```bash
# 处理目录中所有音频文件
python scripts/quick_process.py /path/to/audio/directory/

# 使用通配符模式
python scripts/quick_process.py "day*.mp3"
python scripts/quick_process.py "wu_day*.mp3"
```

### 3. 高级选项
```bash
# GPT翻译 + 自定义上下文窗口
python scripts/quick_process.py audio.mp3 --gpt --context 2

# 自定义输出目录和语音
python scripts/quick_process.py audio.mp3 --output /results/ --voice zh-CN-Wavenet-B

# 预览模式（不实际处理）
python scripts/quick_process.py /audio/dir/ --dry-run
```

## 📋 所有可用的处理方式

### 方式1: 快速处理脚本（推荐）
```bash
# 单文件处理
python scripts/quick_process.py your_audio.mp3

# 批量处理
python scripts/quick_process.py /audio/directory/
python scripts/quick_process.py "*.mp3"

# 高级选项
python scripts/quick_process.py audio.mp3 \
  --gpt \
  --context 2 \
  --voice zh-CN-Wavenet-B \
  --output /custom/output/
```

### 方式2: 单文件专用脚本
```bash
# 基本用法
python scripts/process_single_file.py audio.mp3

# 完整选项
python scripts/process_single_file.py audio.mp3 \
  --output-dir /results/ \
  --translation-provider gpt \
  --context-window 2 \
  --voice zh-CN-Wavenet-B
```

### 方式3: 原始Pipeline（目录处理）
```bash
# 完整pipeline
python scripts/run_pipeline.py full --input-dir /audio/directory/

# 分步处理
python scripts/run_pipeline.py preprocess --input-dir /audio/directory/
python scripts/run_pipeline.py transcribe
python scripts/run_pipeline.py translate --provider gpt --context-window 2
python scripts/run_pipeline.py synthesize
```

## ⚙️ 配置选项详解

### 翻译提供商
- `--gpt` 或 `--translation-provider gpt`: 使用GPT翻译（推荐，质量最高）
- `--google` 或 `--translation-provider google`: 使用Google翻译（速度快）
- `--translation-provider llm`: 使用其他LLM

### GPT翻译专用选项
- `--context 1`: 上下文窗口大小（默认1，包含前后1个片段）
- `--context 2`: 更大上下文（更好的连贯性，但成本更高）
- `--context 0`: 无上下文（独立翻译每个片段）

### 语音识别
- `--stt-provider google`: Google语音识别（默认）
- `--stt-provider openai`: OpenAI Whisper

### 语音合成
- `--voice zh-CN-Wavenet-A`: 默认中文语音
- `--voice zh-CN-Wavenet-B`: 女声
- `--voice zh-CN-Wavenet-C`: 男声
- `--voice zh-CN-Wavenet-D`: 男声

### 术语表
- `--terminology /path/to/custom_terminology.json`: 使用自定义术语表

## 📁 输出结构

处理完成后，每个文件会生成一个 `文件名_processed` 目录：

```
audio_processed/
├── segments/           # 音频分段
├── transcripts/        # 英文转录
├── translations/       # 中文翻译
├── synthesis/          # 语音合成
└── processing_summary.json  # 处理摘要
```

## 🎯 使用场景推荐

### 场景1: 快速测试单个文件
```bash
python scripts/quick_process.py test_audio.mp3 --dry-run
python scripts/quick_process.py test_audio.mp3
```

### 场景2: 批量处理冥想音频
```bash
# 处理所有wu_day开头的文件
python scripts/quick_process.py "data/waking-up_intro-50_chinese/wu_day*.mp3" \
  --gpt --context 2 --output results/
```

### 场景3: 高质量翻译（成本较高）
```bash
python scripts/process_single_file.py important_audio.mp3 \
  --translation-provider gpt \
  --context-window 2 \
  --voice zh-CN-Wavenet-B
```

### 场景4: 快速批量处理（成本较低）
```bash
python scripts/quick_process.py /audio/directory/ \
  --google \
  --continue-on-error
```

## 🔧 后续步骤

处理完成后，你可以：

1. **审查翻译质量**：
   ```bash
   python scripts/run_pipeline.py gui --translation-file results/translations/xxx.json
   ```

2. **组装最终音频**：
   ```bash
   python scripts/run_pipeline.py assemble --translation-file results/translations/xxx.json
   ```

3. **查看可用语音**：
   ```bash
   python scripts/run_pipeline.py voices
   ```

## 💡 最佳实践

1. **首次使用**：先用 `--dry-run` 预览要处理的文件
2. **质量优先**：使用 `--gpt --context 2` 获得最佳翻译质量
3. **成本控制**：批量处理时使用 `--google` 或 `--context 1`
4. **错误处理**：批量处理时添加 `--continue-on-error`
5. **自定义术语**：为特定领域内容准备自定义术语表

## 🚨 注意事项

- 确保已设置 `OPENAI_API_KEY` 环境变量（使用GPT时）
- 确保已配置Google Cloud凭据（使用Google服务时）
- 支持的音频格式：.mp3, .wav, .m4a, .flac, .aac, .ogg
- GPT翻译质量更高但成本更高，Google翻译速度更快但质量略低
