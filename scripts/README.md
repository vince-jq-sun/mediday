# Audio Processing Pipeline

完整的英文正念音频转中文音频处理管道，使用 Google Cloud 服务。

## 🚀 快速开始

### 1. 环境设置
```bash
# 激活虚拟环境
conda activate mediday

# 运行环境设置脚本
python setup_environment.py
```

### 2. Google Cloud 配置
按照 `audio_pipeline/API_TESTING_GUIDE.md` 设置：
- 创建 Google Cloud 项目
- 启用 APIs (Speech-to-Text, Translation, Text-to-Speech)
- 创建服务账户并下载密钥
- 配置 `.env` 文件

### 3. 运行管道
```bash
# 完整管道
python run_pipeline.py full

# 或使用模块方式
python -m audio_pipeline.pipeline full --terminology audio_pipeline/terminology.json
```

## 📁 项目结构

```
scripts/
├── audio_pipeline/           # 核心管道模块
│   ├── config.py            # 配置和路径
│   ├── audio_preprocessor.py # 音频预处理
│   ├── speech_recognition.py # 语音识别
│   ├── translator.py        # 翻译服务
│   ├── translation_gui.py   # 校对GUI
│   ├── text_to_speech.py    # 语音合成
│   ├── audio_assembler.py   # 音频组装
│   ├── pipeline.py          # 主管道
│   ├── utils.py             # 工具函数
│   ├── quick_test.py        # 快速测试
│   ├── terminology.json     # 术语表
│   └── API_TESTING_GUIDE.md # API设置指南
├── setup_environment.py     # 环境设置
├── run_pipeline.py          # 简单运行器
└── README.md               # 本文件
```

## 🎯 使用方法

### 完整工作流
```bash
# 1. 运行完整管道
python run_pipeline.py full

# 2. 启动GUI进行人工校对
python run_pipeline.py gui

# 3. 组装最终音频
python run_pipeline.py assemble --translation-file ../temp/translations/file_translations.json
```

### 分步执行
```bash
# 音频预处理
python run_pipeline.py preprocess --input-dir ../awake_where_you_are

# 语音识别
python run_pipeline.py transcribe

# 翻译
python run_pipeline.py translate --terminology audio_pipeline/terminology.json

# 语音合成
python run_pipeline.py synthesize --voice zh-CN-Wavenet-A

# 启动GUI
python run_pipeline.py gui

# 组装音频
python run_pipeline.py assemble --translation-file ../temp/translations/file_translations.json
```

### 测试和调试
```bash
# 快速测试所有组件
python audio_pipeline/quick_test.py

# 查看可用语音
python run_pipeline.py voices --language zh-CN

# 环境检查
python setup_environment.py
```

## 🎛️ 配置选项

### 语音合成设置
```bash
# 不同语音
python run_pipeline.py synthesize --voice zh-CN-Wavenet-B

# 调整语速和音调
python run_pipeline.py synthesize --speaking-rate 0.9 --pitch 2.0
```

### 术语表
编辑 `audio_pipeline/terminology.json` 添加专业术语：
```json
{
    "mindfulness": "正念",
    "meditation": "冥想",
    "awareness": "觉知"
}
```

## 📊 输出目录

- `temp/segments/` - 分段音频文件
- `temp/transcripts/` - 转录结果
- `temp/translations/` - 翻译结果
- `temp/synthesis/` - 合成音频
- `temp/manual_recordings/` - 手动录音
- `output/` - 最终输出文件

## 🛠️ GUI 功能

翻译校对GUI包含：
- 🎵 播放原始音频片段
- ✏️ 编辑英文和中文文本
- 🔄 一键重新翻译
- 🎤 手动录音功能
- 📋 分段导航 (i/N)
- 💾 保存和前进/后退

## ⚠️ 注意事项

1. **API 配额**：注意 Google Cloud API 的免费配额限制
2. **音频格式**：支持 MP3, WAV, M4A, FLAC, OGG
3. **静音阈值**：默认3秒，可在配置中调整
4. **磁盘空间**：确保有足够空间存储临时文件

## 🔧 故障排除

### 常见问题
- **认证错误**：检查 `.env` 文件和服务账户密钥
- **API未启用**：在 Google Cloud Console 启用相应API
- **音频格式错误**：检查文件格式和采样率
- **依赖缺失**：运行 `pip install -r requirements.txt`

### 获取帮助
```bash
python run_pipeline.py --help
python run_pipeline.py [command] --help
```

## 📈 性能优化

- 使用音频预处理去除静音节省API调用
- 批量处理提高效率
- 缓存翻译结果避免重复
- 选择合适的语音质量平衡效果和成本
