# 项目选择器 - 快速参考

## 一分钟上手

### 启动
```bash
./process/4_review-record.sh
```

### GUI布局（从上到下）
```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ 📁 Project Selector                       ┃
┃ Collection: [下拉列表▼] Project: [下拉列表▼] [✓ Switch Project] ┃
┃ Current: awake_where_you_are_english/1-1_introduction_sample-1  ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Segment 1 / 10                            ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Audio Playback                            ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Text Editing                              ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
... (其他部分)
```

## 三步切换项目

1. **选择Collection** 👉 点击第一个下拉列表
2. **选择Project** 👉 点击第二个下拉列表（自动更新）
3. **切换** 👉 点击 "✓ Switch Project" 按钮

## 常见操作

### 快速浏览所有项目
```
1. 选择 awake_where_you_are_english
2. 依次选择: 1-1_introduction → Switch
3. 依次选择: 1-2_foundational_meditation → Switch
4. ... 继续浏览其他项目
```

### 修改多个项目的翻译
```
1. 切换到项目A → 修改 → 保存 → 切换
2. 切换到项目B → 修改 → 保存 → 切换
3. 切换到项目C → 修改 → 保存
```

## 关键提示

| 符号 | 说明 |
|------|------|
| ⚠️ | GUI切换**不会**改变配置文件 |
| ✅ | 翻译修改会保存到对应项目 |
| 🔄 | 切换会重置到第一个片段 |
| 💾 | 切换前会提示保存未保存的更改 |
| 🎵 | 切换会自动停止音频播放 |

## 配合配置文件使用

### 工作流A：GUI浏览 + 配置文件处理
```bash
# 1. GUI中浏览和修改
./process/4_review-record.sh

# 2. 修改配置文件处理特定项目
vim process/project_config.sh
# 设置: CURRENT_PROJECT="1-2_foundational_meditation"

# 3. 运行后续步骤
./process/5_synthesize.sh
./process/6_assemble.sh
```

### 工作流B：全用配置文件
```bash
vim process/project_config.sh  # 修改项目
./process/4_review-record.sh   # 启动GUI
./process/5_synthesize.sh      # 合成
./process/6_assemble.sh        # 组装
```

## 故障速查

| 问题 | 解决方案 |
|------|----------|
| 下拉列表空白 | 检查temp/目录是否存在 |
| 没有项目显示 | 运行 `./process/3_translate.sh` |
| 切换后报错 | 检查翻译文件是否存在 |
| 保存提示反复出现 | 先保存当前片段再切换 |

## 键盘快捷键

当前GUI不支持键盘快捷键切换项目，需要用鼠标操作。

## 更多信息

- 详细指南: `docs/PROJECT_SELECTOR_GUIDE.md`
- 更新日志: `CHANGELOG_PROJECT_SELECTOR.md`
- 测试脚本: `./test_project_selector.sh`
