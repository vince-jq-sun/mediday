# TTS 设置指南

## 音频生成参数控制

在 `process/project_config.sh` 文件中，现在可以通过以下变量控制音频生成的参数：

### 可配置参数

1. **TTS_SPEAKING_RATE** - 语音播放速度
   - 范围: 0.25 - 4.0
   - 默认值: 1.0 (正常速度)
   - 示例:
     - `0.5` - 半速播放 (更慢)
     - `1.2` - 1.2倍速播放 (稍快)
     - `1.5` - 1.5倍速播放 (明显加快)

2. **TTS_VOICE** - TTS 语音类型
   - 默认值: `cmn-CN-Chirp3-HD-Achird`
   - 其他可选语音可通过 `python -m scripts.audio_pipeline.pipeline voices` 查看

3. **TTS_PITCH** - 音调调整
   - 范围: -20.0 到 20.0
   - 默认值: 0.0 (原始音调)
   - 正值提高音调，负值降低音调

### 使用方法

1. **修改配置文件**
   ```bash
   # 编辑 process/project_config.sh
   export TTS_SPEAKING_RATE="1.2"  # 设置为1.2倍速
   export TTS_VOICE="cmn-CN-Chirp3-HD-Achird"
   export TTS_PITCH="2.0"  # 稍微提高音调
   ```

2. **运行合成**
   ```bash
   # 运行第5步，会自动使用配置的参数
   ./process/5_synthesize.sh
   ```

3. **查看当前设置**
   运行 `5_synthesize.sh` 时会显示当前使用的参数：
   ```
   🎵 Step 5: Text-to-Speech Synthesis
   ===================================
   Project: 1-2_foundational_meditation_sample-1
   Collection: awake_where_you_are_english
   Speaking Rate: 1.2
   Voice: cmn-CN-Chirp3-HD-Achird
   Pitch: 2.0
   ```

### 常用速率设置建议

- **0.8-0.9**: 适合冥想指导，语速较慢，便于跟随
- **1.0**: 正常语速
- **1.1-1.3**: 适合日常听取，稍快但仍清晰
- **1.4-1.6**: 快速浏览内容时使用

### 注意事项

- 修改配置后需要重新运行 `5_synthesize.sh` 才能生效
- 过快或过慢的语速可能影响音频质量
- 建议在 0.7-1.5 范围内调整获得最佳效果
- 音调调整建议在 -5.0 到 5.0 范围内，避免过度失真
