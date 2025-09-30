# 项目选择器使用指南

## 概述

翻译审查GUI现在支持动态项目选择功能，您可以在GUI中直接切换处理不同的项目，无需手动修改 `project_config.sh` 配置文件。

## 功能特点

### 📁 项目选择器区域

在GUI顶部新增了一个"Project Selector"区域，包含以下组件：

1. **Collection 下拉列表**
   - 自动读取 `temp/` 目录下的所有文件夹
   - 显示所有可用的项目集合（如 `awake_where_you_are_english`）
   - 默认选中当前项目所属的集合

2. **Project 下拉列表**
   - 根据选中的 Collection 动态更新
   - 显示该集合下所有包含翻译文件的项目
   - 只显示有 `translations/` 子目录的项目

3. **Switch Project 按钮**
   - 点击后切换到选中的项目
   - 自动加载新项目的翻译数据
   - 重置到第一个片段

4. **当前项目标签**
   - 显示当前正在处理的项目
   - 格式：`Current: {collection}/{project}`

## 使用方法

### 基本操作

1. **启动GUI**
   ```bash
   ./process/4_review-record.sh
   # 或
   ./test_project_selector.sh
   ```

2. **浏览可用项目**
   - 点击 Collection 下拉列表查看所有集合
   - 选择一个集合后，Project 下拉列表会自动更新

3. **切换项目**
   - 从 Collection 下拉列表选择目标集合
   - 从 Project 下拉列表选择目标项目
   - 点击 "✓ Switch Project" 按钮
   - GUI 会自动加载新项目的数据

### 注意事项

#### 未保存的更改
- 切换项目前，如果当前片段有未保存的更改，系统会提示您：
  - **Yes（是）**: 保存更改后切换
  - **No（否）**: 放弃更改并切换
  - **Cancel（取消）**: 取消切换操作

#### 项目验证
- 系统会检查目标项目的翻译文件是否存在
- 如果文件不存在，会显示错误信息

#### 自动停止播放
- 切换项目时，系统会自动停止所有正在播放的音频
- 录音状态也会被重置

## 目录结构要求

项目选择器要求以下目录结构：

```
temp/
├── awake_where_you_are_english/           # Collection
│   ├── 1-1_introduction/                   # Project 1
│   │   ├── segments/
│   │   ├── transcripts/
│   │   ├── translations/                   # 必须存在
│   │   │   └── 1-1_introduction_translations.json
│   │   └── manual_recording/
│   ├── 1-2_foundational_meditation/        # Project 2
│   │   ├── segments/
│   │   ├── transcripts/
│   │   ├── translations/                   # 必须存在
│   │   │   └── 1-2_foundational_meditation_translations.json
│   │   └── manual_recording/
│   └── ...
└── other_collection/                       # Another Collection
    └── ...
```

**要点**：
- Collection 是 `temp/` 下的一级目录
- Project 是 Collection 下的二级目录
- 每个 Project 必须包含 `translations/` 子目录才会出现在列表中

## 与配置文件的关系

虽然您现在可以在GUI中动态切换项目，但 `project_config.sh` 中的设置仍然用于：

1. **初始项目选择**: GUI启动时使用配置文件中的项目
2. **其他脚本**: 如合成、组装等步骤仍使用配置文件

### 不等同于修改配置文件

**重要**: GUI中切换项目**不会**修改 `project_config.sh` 文件。这意味着：

- ✅ 您可以在GUI中自由切换和查看不同项目
- ✅ 翻译修改会保存到相应项目的文件中
- ❌ GUI关闭后，再次打开仍会加载配置文件中指定的项目
- ❌ 后续的合成和组装步骤仍使用配置文件中的项目

### 推荐工作流程

**方案1: 使用GUI浏览，配置文件处理**
```bash
# 1. 在GUI中浏览和修改多个项目的翻译
./process/4_review-record.sh

# 2. 修改配置文件来处理特定项目
vim process/project_config.sh  # 设置 CURRENT_PROJECT

# 3. 运行后续步骤
./process/5_synthesize.sh
./process/6_assemble.sh
```

**方案2: 完全使用配置文件**
```bash
# 每次处理新项目时修改配置文件
vim process/project_config.sh  # 设置 CURRENT_PROJECT

# 运行完整流程
./process/4_review-record.sh
./process/5_synthesize.sh
./process/6_assemble.sh
```

## 示例场景

### 场景1: 快速浏览多个项目的翻译质量

```bash
# 1. 启动GUI（默认加载配置文件中的项目）
./process/4_review-record.sh

# 2. 在GUI中：
#    - 选择 Collection: awake_where_you_are_english
#    - 选择 Project: 1-1_introduction
#    - 点击 Switch Project
#    - 查看翻译质量

# 3. 继续切换到其他项目查看
#    - 选择 Project: 1-2_foundational_meditation
#    - 点击 Switch Project
```

### 场景2: 修正多个项目的翻译错误

```bash
# 1. 启动GUI
./process/4_review-record.sh

# 2. 在GUI中逐个项目修改：
#    - 切换到项目A，修改并保存
#    - 切换到项目B，修改并保存
#    - 切换到项目C，修改并保存

# 3. 关闭GUI后，所有修改都已保存到各自的翻译文件中
```

## 技术细节

### 自动发现机制
- 扫描 `temp/` 目录查找 Collection
- 扫描 Collection 目录查找 Project
- 验证 Project 是否包含 `translations/` 目录
- 只显示有效的项目

### 路径解析
- 从翻译文件路径自动提取 Collection 和 Project 信息
- 格式: `temp/{collection}/{project}/translations/{project}_translations.json`

### 状态管理
- 切换项目时重置片段索引到0
- 清空重翻译区域
- 更新录音目录路径
- 重新加载所有数据

## 故障排除

### 问题：下拉列表中没有项目
**原因**: 项目目录下没有 `translations/` 子目录
**解决**: 确保已运行翻译步骤 `./process/3_translate.sh`

### 问题：切换项目后提示文件不存在
**原因**: 翻译文件命名不正确或路径错误
**解决**: 检查文件命名格式 `{project}_translations.json`

### 问题：切换项目很慢
**原因**: 大型翻译文件加载需要时间
**解决**: 这是正常的，请等待加载完成

## 未来改进计划

- [ ] 记住最后一次选择的项目
- [ ] 添加项目搜索功能
- [ ] 显示项目统计信息（片段数、完成度等）
- [ ] 支持批量项目操作
- [ ] 集成到配置文件更新（可选）
