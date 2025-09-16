# Google Cloud APIs 测试指南

本指南将帮助您设置和测试 Google Cloud APIs，用于音频处理管道。

## 1. Google Cloud 项目设置

### 1.1 创建 Google Cloud 项目
1. 访问 [Google Cloud Console](https://console.cloud.google.com/)
2. 创建新项目或选择现有项目
3. 记录项目 ID

### 1.2 启用必要的 APIs
在 Google Cloud Console 中启用以下 APIs：
- **Cloud Speech-to-Text API**
- **Cloud Translation API** 
- **Cloud Text-to-Speech API**

```bash
# 使用 gcloud CLI 启用 APIs
gcloud services enable speech.googleapis.com
gcloud services enable translate.googleapis.com  
gcloud services enable texttospeech.googleapis.com
```

### 1.3 创建服务账户
1. 在 Google Cloud Console 中，转到 "IAM & Admin" > "Service Accounts"
2. 点击 "Create Service Account"
3. 填写服务账户详情
4. 分配以下角色：
   - Cloud Speech Client
   - Cloud Translation API User
   - Cloud Text-to-Speech Client
5. 创建并下载 JSON 密钥文件

## 2. 环境配置

### 2.1 设置环境变量
复制 `.env.example` 到 `.env` 并填写配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件：
```bash
# Google Cloud 配置
GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/service-account-key.json
GOOGLE_CLOUD_PROJECT_ID=your-project-id

# 可选：指定输出目录
OUTPUT_DIR=./output
TEMP_DIR=./temp
```

### 2.2 安装依赖
激活您的 mediday 虚拟环境并安装依赖：

```bash
# 激活虚拟环境
conda activate mediday
# 或者如果使用 venv:
# source mediday/bin/activate

# 安装依赖
pip install -r requirements.txt
```

## 3. API 测试

### 3.1 测试 Speech-to-Text API

创建测试脚本 `test_stt.py`：

```python
from google.cloud import speech
import io

def test_speech_to_text():
    client = speech.SpeechClient()
    
    # 使用一个简短的音频文件进行测试
    audio_file = "path/to/test/audio.wav"
    
    with io.open(audio_file, "rb") as f:
        content = f.read()
    
    audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code="en-US",
    )
    
    response = client.recognize(config=config, audio=audio)
    
    for result in response.results:
        print(f"Transcript: {result.alternatives[0].transcript}")
        print(f"Confidence: {result.alternatives[0].confidence}")

if __name__ == "__main__":
    test_speech_to_text()
```

运行测试：
```bash
python test_stt.py
```

### 3.2 测试 Translation API

创建测试脚本 `test_translate.py`：

```python
from google.cloud import translate_v2 as translate

def test_translation():
    client = translate.Client()
    
    # 测试文本
    text = "Hello, this is a test of the translation service."
    
    result = client.translate(
        text,
        source_language='en',
        target_language='zh-CN'
    )
    
    print(f"Original: {text}")
    print(f"Translation: {result['translatedText']}")
    print(f"Detected language: {result.get('detectedSourceLanguage', 'N/A')}")

if __name__ == "__main__":
    test_translation()
```

运行测试：
```bash
python test_translate.py
```

### 3.3 测试 Text-to-Speech API

创建测试脚本 `test_tts.py`：

```python
from google.cloud import texttospeech

def test_text_to_speech():
    client = texttospeech.TextToSpeechClient()
    
    # 测试文本
    text = "你好，这是文本转语音服务的测试。"
    
    synthesis_input = texttospeech.SynthesisInput(text=text)
    
    voice = texttospeech.VoiceSelectionParams(
        language_code="zh-CN",
        name="zh-CN-Wavenet-A"
    )
    
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )
    
    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config
    )
    
    with open("test_output.mp3", "wb") as out:
        out.write(response.audio_content)
        print("Audio saved to test_output.mp3")

def list_voices():
    client = texttospeech.TextToSpeechClient()
    voices = client.list_voices()
    
    print("Available Chinese voices:")
    for voice in voices.voices:
        if "zh" in voice.language_codes:
            print(f"  {voice.name} ({voice.ssml_gender.name})")

if __name__ == "__main__":
    list_voices()
    test_text_to_speech()
```

运行测试：
```bash
python test_tts.py
```

## 4. 管道测试

### 4.1 测试完整管道

```bash
# 进入脚本目录
cd scripts

# 运行完整管道（使用默认的 awake_where_you_are 目录）
python -m audio_pipeline.pipeline full

# 或指定自定义输入目录
python -m audio_pipeline.pipeline full --input-dir /path/to/your/audio/files

# 使用术语表
python -m audio_pipeline.pipeline full --terminology audio_pipeline/terminology.json
```

### 4.2 分步测试

```bash
# 1. 仅预处理
python -m audio_pipeline.pipeline preprocess --input-dir ../awake_where_you_are

# 2. 仅语音识别
python -m audio_pipeline.pipeline transcribe

# 3. 仅翻译
python -m audio_pipeline.pipeline translate --terminology audio_pipeline/terminology.json

# 4. 仅语音合成
python -m audio_pipeline.pipeline synthesize --voice zh-CN-Wavenet-A

# 5. 启动 GUI 进行人工校对
python -m audio_pipeline.pipeline gui

# 6. 组装最终音频
python -m audio_pipeline.pipeline assemble --translation-file ../temp/translations/filename_translations.json
```

### 4.3 查看可用语音

```bash
python -m audio_pipeline.pipeline voices --language zh-CN
```

## 5. 故障排除

### 5.1 常见错误

**认证错误**：
```
google.auth.exceptions.DefaultCredentialsError
```
解决方案：
- 确保 `GOOGLE_APPLICATION_CREDENTIALS` 环境变量正确设置
- 检查服务账户 JSON 文件路径是否正确
- 验证服务账户是否有正确的权限

**API 未启用错误**：
```
google.api_core.exceptions.Forbidden: 403 API has not been used
```
解决方案：
- 在 Google Cloud Console 中启用相应的 API
- 等待几分钟让 API 激活

**音频格式错误**：
```
google.api_core.exceptions.InvalidArgument: 400 Invalid audio encoding
```
解决方案：
- 检查音频文件格式是否支持
- 确保采样率设置正确
- 尝试转换音频格式

### 5.2 调试技巧

1. **启用详细日志**：
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

2. **检查音频文件**：
```python
import librosa
y, sr = librosa.load("audio_file.mp3", sr=None)
print(f"Duration: {len(y)/sr:.2f}s, Sample rate: {sr}Hz")
```

3. **测试小文件**：
先用短音频文件（< 1分钟）测试管道

## 6. 成本优化建议

### 6.1 API 使用限制
- **Speech-to-Text**: 每月前60分钟免费
- **Translation**: 每月前500,000字符免费  
- **Text-to-Speech**: 每月前100万字符免费

### 6.2 优化策略
1. 使用音频预处理去除静音，减少 STT 使用量
2. 批量处理以提高效率
3. 缓存翻译结果避免重复调用
4. 选择合适的语音质量（Standard vs WaveNet）

## 7. 高级配置

### 7.1 自定义语音设置
```python
voice_settings = {
    'voice_name': 'zh-CN-Wavenet-B',  # 女声
    'speaking_rate': 0.9,             # 稍慢
    'pitch': 2.0                      # 稍高
}
```

### 7.2 音频压缩设置
```python
compression_settings = {
    'bitrate': '64k',    # 较小文件
    'format': 'mp3'
}
```

### 7.3 术语表管理
编辑 `terminology.json` 文件添加专业术语：
```json
{
    "mindfulness": "正念",
    "meditation": "冥想",
    "awareness": "觉知"
}
```

## 8. 下一步

完成 API 测试后，您可以：

1. 运行完整管道处理您的音频文件
2. 使用 GUI 进行人工校对和录音
3. 生成最终的中文音频文件
4. 根据需要调整参数和设置

如有问题，请检查 Google Cloud Console 中的日志和配额使用情况。
