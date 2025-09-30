# 项目选择器功能更新日志

## 版本：2025-09-30

### 新增功能：GUI内项目动态选择

#### 概述
翻译审查GUI现在支持在界面内直接切换项目，无需修改配置文件或重启GUI。

#### 主要变更

**修改的文件**：
- `scripts/audio_pipeline/translation_gui.py`

**新增的GUI组件**：
1. **📁 Project Selector 区域**（位于GUI顶部）
   - Collection 下拉列表：显示 `temp/` 下的所有项目集合
   - Project 下拉列表：显示选中集合下的所有项目
   - ✓ Switch Project 按钮：切换到选中的项目
   - Current 标签：显示当前正在处理的项目

**新增的功能方法**：
- `get_current_project_info()`: 从文件路径提取collection和project信息
- `populate_collections()`: 填充collection下拉列表
- `on_collection_selected()`: 处理collection选择，更新project列表
- `switch_project()`: 切换到新项目并重新加载数据

#### 功能特点

✅ **自动发现项目**
- 自动扫描 `temp/` 目录下的所有集合和项目
- 只显示包含翻译文件的有效项目

✅ **智能默认选择**
- 启动时自动选中当前项目所属的集合和项目
- 切换集合时自动选择该集合的第一个项目

✅ **数据保护**
- 切换前检查未保存的更改
- 提供保存/放弃/取消三个选项
- 自动停止音频播放

✅ **状态管理**
- 切换后重置到第一个片段
- 清空重翻译区域
- 更新录音目录路径
- 重新加载所有项目数据

#### 使用方法

```bash
# 方法1: 使用现有脚本启动
./process/4_review-record.sh

# 方法2: 使用测试脚本
./test_project_selector.sh
```

在GUI中：
1. 点击 Collection 下拉列表选择项目集合
2. Project 下拉列表会自动更新显示该集合下的项目
3. 选择目标项目
4. 点击 "✓ Switch Project" 按钮
5. GUI自动加载新项目的数据

#### 重要说明

⚠️ **GUI切换不会修改配置文件**

在GUI中切换项目**不等同于**修改 `project_config.sh` 中的变量。这意味着：

- GUI中的切换只影响当前会话
- 翻译修改会保存到相应项目的文件
- GUI关闭后，再次打开仍加载配置文件中的项目
- 后续的合成(step 5)和组装(step 6)仍使用配置文件中的设置

**推荐工作流**：
- 使用GUI浏览和修改多个项目的翻译
- 需要运行后续步骤时，修改配置文件指定项目
- 或者为每个项目单独运行完整流程

#### 目录结构要求

```
temp/
├── {collection}/              # 项目集合
│   ├── {project1}/            # 项目1
│   │   ├── segments/
│   │   ├── transcripts/
│   │   ├── translations/      # ← 必须存在
│   │   └── manual_recording/
│   ├── {project2}/            # 项目2
│   │   └── ...
│   └── ...
└── ...
```

#### 测试建议

1. **测试项目切换**
   ```bash
   ./test_project_selector.sh
   ```

2. **测试未保存更改提示**
   - 修改某个片段的翻译（不保存）
   - 尝试切换项目
   - 应该看到保存提示

3. **测试跨集合切换**
   - 在不同的collection之间切换
   - 验证project列表正确更新

4. **测试音频停止**
   - 播放音频时切换项目
   - 验证音频自动停止

#### 文档

详细使用指南：`docs/PROJECT_SELECTOR_GUIDE.md`

#### 技术细节

- 使用 `ttk.Combobox` 实现下拉列表
- 绑定 `<<ComboboxSelected>>` 事件实现联动
- 使用 `Path.iterdir()` 扫描目录
- 保持与现有代码结构的兼容性

#### 向后兼容性

✅ 完全向后兼容
- 不影响现有脚本和工作流程
- 配置文件仍然有效
- 命令行参数仍然支持
- 所有原有功能保持不变
